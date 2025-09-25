"""
Authenticated Request Handlers

This module provides request handlers with OAuth authentication integration.
"""

import logging
from typing import Dict, Any, Optional
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor
from a2a.server.tasks import TaskStore
from a2a.types import AgentCard

from .agent_card import AgentCardBuilder
from auth.oauth_middleware import OAuthMiddleware

logger = logging.getLogger(__name__)


class AuthenticatedRequestHandler(DefaultRequestHandler):
    """Request handler with OAuth authentication."""

    def __init__(
        self,
        agent_executor: AgentExecutor,
        task_store: TaskStore,
        oauth_middleware: OAuthMiddleware,
        card_builder: AgentCardBuilder,
        runner=None
    ):
        super().__init__(agent_executor, task_store)
        self.oauth_middleware = oauth_middleware
        self.card_builder = card_builder
        self.runner = runner

    async def handle_post(self, request: Request) -> Response:
        """Handle A2A POST requests with authentication."""
        try:
            # Extract authentication information
            auth_info = await self._extract_auth_info(request)

            if not auth_info:
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer, OAuth"}
                )

            # Validate authentication
            user_context = await self._validate_authentication(auth_info)

            if not user_context:
                return JSONResponse(
                    {"error": "Invalid or expired authentication"},
                    status_code=401
                )

            # Add user context to request
            request.state.user_context = user_context

            # Parse the JSON-RPC request to determine which method to call
            body = await request.body()
            if body:
                # Store OAuth context in ADK session state with parsed body
                await self._store_oauth_in_session_state(user_context, body)
                import json
                from a2a.types import MessageSendParams
                from a2a.server.context import ServerCallContext

                data = json.loads(body)
                method = data.get("method")

                if method == "message/send":
                    # Extract params and create MessageSendParams object
                    params_data = data.get("params", {})
                    message_params = MessageSendParams.model_validate(params_data)

                    # Create server context
                    context = ServerCallContext(request=request)

                    # Call the parent method with correct parameters
                    result = await self.on_message_send(message_params, context)

                    # Return JSON-RPC response
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": result.model_dump() if hasattr(result, 'model_dump') else result
                    })

                elif method == "message/send_stream":
                    # Handle streaming if needed
                    params_data = data.get("params", {})
                    message_params = MessageSendParams.model_validate(params_data)
                    context = ServerCallContext(request=request)

                    # This would need to handle streaming response
                    async_gen = self.on_message_send_stream(message_params, context)
                    # For now, return error as streaming needs special handling
                    return JSONResponse(
                        {"error": "Streaming not implemented yet"},
                        status_code=501
                    )

            # Default fallback
            return JSONResponse(
                {"error": "Unsupported method"},
                status_code=400
            )

        except Exception as e:
            logger.error(f"Authentication error in POST handler: {e}")
            return JSONResponse(
                {"error": "Authentication failed"},
                status_code=500
            )

    async def handle_authenticated_extended_card(self, request: Request) -> Response:
        """Handle authenticated extended agent card requests."""
        try:
            # Extract authentication information
            auth_info = await self._extract_auth_info(request)

            if not auth_info:
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer, OAuth"}
                )

            # Validate authentication
            user_context = await self._validate_authentication(auth_info)

            if not user_context:
                return JSONResponse(
                    {"error": "Invalid or expired authentication"},
                    status_code=401
                )

            # Create extended agent card
            base_card = self.card_builder.create_agent_card()
            extended_card = self.card_builder.create_extended_agent_card(
                base_card,
                user_context
            )

            # Return extended card
            return JSONResponse(extended_card.model_dump())

        except Exception as e:
            logger.error(f"Extended card request failed: {e}")
            return JSONResponse(
                {"error": "Failed to retrieve extended agent card"},
                status_code=500
            )

    async def _extract_auth_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract authentication information from request."""
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        if auth_header:
            # Handle Bearer token
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                return {
                    "type": "bearer",
                    "token": token
                }

            # Handle Basic authentication (for client credentials)
            elif auth_header.startswith("Basic "):
                import base64
                try:
                    encoded = auth_header[6:]
                    decoded = base64.b64decode(encoded).decode()
                    username, password = decoded.split(":", 1)
                    return {
                        "type": "basic",
                        "username": username,
                        "password": password
                    }
                except Exception:
                    logger.warning("Invalid Basic authentication format")
                    return None

        elif api_key_header:
            # Handle API Key
            return {
                "type": "api_key",
                "key": api_key_header
            }

        # Try to extract from request body for some flows
        try:
            if request.method == "POST":
                body = await request.body()
                if body:
                    data = json.loads(body)

                    # Check for user_id in request (for identifying the user)
                    if "user_id" in data:
                        return {
                            "type": "user_context",
                            "user_id": data["user_id"]
                        }
        except Exception:
            pass

        return None

    async def _validate_authentication(self, auth_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate authentication and return user context."""
        auth_type = auth_info.get("type")

        if auth_type == "bearer":
            return await self._validate_bearer_token(auth_info["token"])

        elif auth_type == "api_key":
            return await self._validate_api_key(auth_info["key"])

        elif auth_type == "basic":
            return await self._validate_basic_auth(
                auth_info["username"],
                auth_info["password"]
            )

        elif auth_type == "user_context":
            # For development/testing - validate user has valid tokens
            user_id = auth_info["user_id"]
            token = await self.oauth_middleware.get_valid_token(user_id)
            if token:
                user_info = await self.oauth_middleware.get_user_info(user_id)
                return {
                    "user_id": user_id,
                    "provider": token.provider,
                    "user_info": user_info
                }

        return None

    async def _validate_bearer_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate Bearer token."""
        try:
            # First, try to validate as JWT
            jwt_payload = self.oauth_middleware.validate_jwt_token(token)

            if jwt_payload:
                # Extract user information from JWT
                user_id = jwt_payload.get("sub") or jwt_payload.get("user_id")
                email = jwt_payload.get("email")

                return {
                    "user_id": user_id,
                    "email": email,
                    "jwt_payload": jwt_payload,
                    "auth_type": "jwt_bearer"
                }

            # If not JWT, check if it's a stored access token
            # This requires matching the token with stored tokens
            # For now, we'll implement a simple approach

            # In a real implementation, you might:
            # 1. Hash the token and look it up in your token store
            # 2. Use token introspection endpoint
            # 3. Validate against your custom token format

            logger.debug("Bearer token validation not implemented for non-JWT tokens")
            return None

        except Exception as e:
            logger.error(f"Bearer token validation failed: {e}")
            return None

    async def _validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key."""
        # In a real implementation, you would:
        # 1. Look up the API key in your database
        # 2. Check if it's active and not expired
        # 3. Return associated user/service information

        # For this template, we'll implement a simple check
        # You should replace this with your actual API key validation logic

        logger.debug("API key validation not implemented in template")
        return None

    async def _validate_basic_auth(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate basic authentication (for client credentials)."""
        # Check if credentials match OAuth client credentials
        try:
            provider = self.oauth_middleware.config.providers.get(
                self.oauth_middleware.config.default_provider
            )

            if provider and provider.client_id == username and provider.client_secret == password:
                # Valid client credentials
                return {
                    "client_id": username,
                    "auth_type": "client_credentials",
                    "provider": provider.name
                }

        except Exception as e:
            logger.error(f"Basic auth validation failed: {e}")

        return None

    async def _get_user_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from request context."""
        # Check if user context was added during authentication
        if hasattr(request.state, 'user_context'):
            return request.state.user_context.get('user_id')

        # Try to extract from request body
        try:
            if request.method == "POST":
                body = await request.body()
                if body:
                    data = json.loads(body)
                    return data.get('user_id')
        except Exception:
            pass

        return None

    def _create_auth_required_response(self, schemes: list = None) -> Response:
        """Create a response indicating authentication is required."""
        schemes = schemes or ["Bearer", "Basic", "ApiKey"]
        www_auth_header = ", ".join(schemes)

        return JSONResponse(
            {
                "error": "Authentication required",
                "message": "This endpoint requires authentication",
                "supported_schemes": schemes
            },
            status_code=401,
            headers={"WWW-Authenticate": www_auth_header}
        )

    async def _store_oauth_in_session_state(self, user_context: Dict[str, Any], body: bytes) -> None:
        """Store OAuth context in ADK session state for tools to access."""
        try:
            user_id = user_context.get("user_id")
            if not user_id:
                logger.warning("No user_id in user context, cannot store OAuth context")
                return

            # Parse the JSON-RPC request to get session information
            if not body:
                logger.warning("No request body, cannot determine session")
                return

            import json
            data = json.loads(body)
            params_data = data.get("params", {})

            # Extract session info from the A2A request
            # ADK will create a session with the user_id from the A2A message
            message_params = params_data.get("message", {})
            context_id = params_data.get("context_id")

            # Get the session service from the runner
            if not self.runner:
                logger.warning("No runner available, cannot access session service")
                return

            session_service = self.runner.session_service

            # For A2A requests, ADK typically creates a user_id like "A2A_USER_<context_id>"
            # We need to store OAuth context in the session that will be used
            if context_id:
                # Try to create/get session with the context_id as user_id
                adk_user_id = f"A2A_USER_{context_id}"
                app_name = self.runner.app_name

                try:
                    # Try to get existing session or create new one
                    session = await session_service.get_session(
                        app_name=app_name,
                        user_id=adk_user_id,
                        session_id=context_id
                    )

                    if not session:
                        # Create a new session with OAuth context in state
                        oauth_state = {
                            "oauth_user_id": user_context.get("user_id"),
                            "oauth_provider": user_context.get("provider"),
                            "oauth_user_info": user_context.get("user_info", {}),
                            "oauth_token": user_context.get("token") or user_context.get("access_token"),
                            "oauth_authenticated": True
                        }

                        session = await session_service.create_session(
                            app_name=app_name,
                            user_id=adk_user_id,
                            session_id=context_id,
                            state=oauth_state
                        )
                        logger.info(f"Created new session with OAuth context for user: {adk_user_id}")
                    else:
                        # Update existing session with OAuth context
                        oauth_state = {
                            "oauth_user_id": user_context.get("user_id"),
                            "oauth_provider": user_context.get("provider"),
                            "oauth_user_info": user_context.get("user_info", {}),
                            "oauth_token": user_context.get("token") or user_context.get("access_token"),
                            "oauth_authenticated": True
                        }

                        # Update session state
                        session.state.update(oauth_state)
                        await session_service.save_session(session)
                        logger.info(f"Updated session with OAuth context for user: {adk_user_id}")

                except Exception as e:
                    logger.error(f"Failed to create/update session: {e}")
                    # Fallback to global registry
                    await self._store_oauth_in_global_registry(user_context)
            else:
                logger.warning("No context_id in request, using global registry fallback")
                await self._store_oauth_in_global_registry(user_context)

        except Exception as e:
            logger.error(f"Failed to store OAuth context in session: {e}")
            # Fallback to global registry
            await self._store_oauth_in_global_registry(user_context)

    async def _store_oauth_in_global_registry(self, user_context: Dict[str, Any]) -> None:
        """Fallback method to store OAuth context in global registry."""
        try:
            user_id = user_context.get("user_id")
            if not user_id:
                return

            oauth_context = {
                "oauth_user_id": user_context.get("user_id"),
                "oauth_provider": user_context.get("provider"),
                "oauth_user_info": user_context.get("user_info", {}),
                "oauth_token": user_context.get("token") or user_context.get("access_token"),
                "oauth_authenticated": True
            }

            # Store in a module-level registry
            if not hasattr(self.__class__, '_oauth_registry'):
                self.__class__._oauth_registry = {}

            self.__class__._oauth_registry[user_id] = oauth_context
            logger.info(f"Stored OAuth context in global registry for user: {user_id}")

        except Exception as e:
            logger.error(f"Failed to store OAuth context in global registry: {e}")

    @classmethod
    def get_oauth_context(cls, user_id: str) -> Dict[str, Any]:
        """Get OAuth context for a user."""
        if not hasattr(cls, '_oauth_registry'):
            return {}
        return cls._oauth_registry.get(user_id, {})