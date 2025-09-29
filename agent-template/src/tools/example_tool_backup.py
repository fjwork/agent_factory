"""
Example Tool Implementation

This is an example authenticated tool that demonstrates OAuth integration patterns.
Customize this file for your specific agent's needs.
"""

import logging
from typing import Dict, Any, Optional
from google.adk.tools import ToolContext
from .authenticated_tool import AuthenticatedTool, AuthenticationError, ToolExecutionError

logger = logging.getLogger(__name__)


class ExampleTool(AuthenticatedTool):
    """Example tool demonstrating OAuth authentication patterns."""

    def __init__(self):
        super().__init__(
            name="example_tool",
            description="Example tool for OAuth-authenticated operations (customize for your needs)"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        action: str = "get_user_info",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Example authenticated operation.

        Args:
            user_context: User authentication context from OAuth
            action: Action to perform (get_user_info, demo_action)
            parameters: Optional parameters for the action

        Returns:
            Formatted response with user information
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "example_action",
            {"action": action, "parameters": parameters}
        )

        try:
            # Get user information from OAuth provider API
            user_info = await self.fetch_real_user_info(user_context)
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)

            # Perform action based on request
            if action == "get_user_info":
                return self._format_user_info(user_info, user_id, provider)
            elif action == "demo_action":
                return self._demo_authenticated_action(user_info, user_id, provider, parameters)
            else:
                return self._format_user_info(user_info, user_id, provider)

        except Exception as e:
            error_msg = f"Failed to execute tool action '{action}': {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)


class BearerTokenPrintTool(AuthenticatedTool):
    """Tool specifically for testing bearer token forwarding."""

    def __init__(self):
        super().__init__(
            name="bearer_token_print_tool",
            description="Prints received bearer token for testing token forwarding functionality"
        )

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Print bearer token information for testing.

        Args:
            user_context: User authentication context
            **kwargs: Additional parameters (ignored)

        Returns:
            Detailed bearer token information
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(user_context, "bearer_token_print")

        # Extract all authentication information
        user_id = self.get_user_id(user_context)
        provider = self.get_provider(user_context)
        auth_type = user_context.get("auth_type", "unknown")
        token = user_context.get("token")

        # Create detailed token analysis
        token_info = {
            "present": bool(token),
            "type": type(token).__name__ if token else "None",
            "length": len(str(token)) if token else 0,
            "first_chars": str(token)[:20] + "..." if token and len(str(token)) > 20 else str(token) if token else None,
            "last_chars": "..." + str(token)[-10:] if token and len(str(token)) > 30 else None
        }

        # Check for JWT structure
        if token and isinstance(token, str) and "." in token:
            parts = token.split(".")
            token_info["jwt_structure"] = {
                "parts": len(parts),
                "header_length": len(parts[0]) if len(parts) > 0 else 0,
                "payload_length": len(parts[1]) if len(parts) > 1 else 0,
                "signature_length": len(parts[2]) if len(parts) > 2 else 0,
                "likely_jwt": len(parts) == 3
            }

        return {
            "success": True,
            "tool": "bearer_token_print_tool",
            "message": "🔍 Bearer Token Analysis Complete",
            "user_authentication": {
                "user_id": user_id,
                "provider": provider,
                "auth_type": auth_type,
                "authenticated": user_context.get("authenticated", False)
            },
            "bearer_token": token_info,
            "full_user_context_keys": list(user_context.keys()),
            "timestamp": self._get_timestamp(),
            "test_result": "✅ Bearer token successfully forwarded to tool!" if token else "❌ No bearer token received in tool"
        }

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        action: str = "get_user_info",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Example authenticated operation.

        Args:
            user_context: User authentication context from OAuth
            action: Action to perform (get_user_info, demo_action)
            parameters: Optional parameters for the action

        Returns:
            Formatted response with user information
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(
            user_context,
            "example_action",
            {"action": action, "parameters": parameters}
        )

        try:
            # Get user information from OAuth provider API
            user_info = await self.fetch_real_user_info(user_context)
            user_id = self.get_user_id(user_context)
            provider = self.get_provider(user_context)

            # Perform action based on request
            if action == "get_user_info":
                return self._format_user_info(user_info, user_id, provider)
            elif action == "demo_action":
                return self._demo_authenticated_action(user_info, user_id, provider, parameters)
            else:
                return self._format_user_info(user_info, user_id, provider)

        except Exception as e:
            error_msg = f"Failed to execute tool action '{action}': {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(error_msg)

    def _format_user_info(self, user_info: Dict[str, Any], user_id: str, provider: str) -> Dict[str, Any]:
        """Format user information for display."""
        return {
            "success": True,
            "action": "get_user_info",
            "user_id": user_id,
            "provider": provider,
            "user_info": {
                "name": user_info.get("name", "Not available"),
                "email": user_info.get("email", "Not available"),
                "verified_email": user_info.get("verified_email", False)
            },
            "message": f"Hello {user_info.get('name', 'there')}! Your authentication is working correctly.",
            "timestamp": self._get_timestamp()
        }

    def _demo_authenticated_action(
        self,
        user_info: Dict[str, Any],
        user_id: str,
        provider: str,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Demonstrate an authenticated action with parameters."""
        return {
            "success": True,
            "action": "demo_action",
            "user_id": user_id,
            "provider": provider,
            "message": f"Demo action executed for {user_info.get('name', 'user')} with OAuth from {provider}",
            "parameters_received": parameters or {},
            "timestamp": self._get_timestamp(),
            "note": "This is a template - customize this method for your specific use case"
        }

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        action: str = "get_user_info",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute tool using ADK ToolContext for user authentication.

        Args:
            tool_context: ADK ToolContext with session state
            action: Action to perform (get_user_info, demo_action)
            parameters: Optional parameters for the action

        Returns:
            Formatted response
        """
        # Get user context from session state
        user_context = {
            "user_id": tool_context.state.get("oauth_user_id"),
            "provider": tool_context.state.get("oauth_provider"),
            "user_info": tool_context.state.get("oauth_user_info", {}),
            "token": tool_context.state.get("oauth_token")
        }

        # If session state doesn't have OAuth context, try global registry fallback
        if not user_context["user_id"] or not user_context["token"]:
            # Import here to avoid circular imports
            from agent_a2a.handlers import AuthenticatedRequestHandler

            # Check if there's OAuth context in the global registry
            if hasattr(AuthenticatedRequestHandler, '_oauth_registry'):
                registry = AuthenticatedRequestHandler._oauth_registry
                # Find any authenticated user (in practice there should be only one at a time)
                for user_id, oauth_context in registry.items():
                    if oauth_context.get("oauth_authenticated"):
                        # Normalize the context to ensure compatibility
                        user_context = {
                            "user_id": oauth_context.get("oauth_user_id"),
                            "oauth_user_id": oauth_context.get("oauth_user_id"),
                            "provider": oauth_context.get("oauth_provider"),
                            "oauth_provider": oauth_context.get("oauth_provider"),
                            "user_info": oauth_context.get("oauth_user_info", {}),
                            "oauth_user_info": oauth_context.get("oauth_user_info", {}),
                            "token": oauth_context.get("oauth_token"),
                            "oauth_token": oauth_context.get("oauth_token"),
                            "oauth_authenticated": True
                        }
                        logger.info(f"Using OAuth context from global registry for user: {user_id}")
                        break

        # Validate that user is authenticated
        user_id = user_context.get("oauth_user_id") or user_context.get("user_id")
        token = user_context.get("oauth_token") or user_context.get("token")

        if not user_id or not token:
            logger.warning(f"Authentication validation failed. user_context keys: {list(user_context.keys())}")
            logger.warning(f"user_id: {user_id}, token: {'present' if token else 'missing'}")
            return {
                "success": False,
                "error": "User authentication required. Please authenticate first.",
                "auth_required": True,
                "note": "This is a template - user needs to complete OAuth flow"
            }

        # Call the existing authenticated method
        try:
            return await self.execute_authenticated(user_context, action, parameters)
        except AuthenticationError as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}",
                "auth_required": True
            }
        except ToolExecutionError as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }


    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Print bearer token information for testing.

        Args:
            user_context: User authentication context
            **kwargs: Additional parameters (ignored)

        Returns:
            Detailed bearer token information
        """
        if not self.validate_user_context(user_context):
            raise AuthenticationError("Invalid user authentication context")

        self._log_tool_execution(user_context, "bearer_token_print")

        # Extract all authentication information
        user_id = self.get_user_id(user_context)
        provider = self.get_provider(user_context)
        auth_type = user_context.get("auth_type", "unknown")
        token = user_context.get("token")

        # Create detailed token analysis
        token_info = {
            "present": bool(token),
            "type": type(token).__name__ if token else "None",
            "length": len(str(token)) if token else 0,
            "first_chars": str(token)[:20] + "..." if token and len(str(token)) > 20 else str(token) if token else None,
            "last_chars": "..." + str(token)[-10:] if token and len(str(token)) > 30 else None
        }

        # Check for JWT structure
        if token and isinstance(token, str) and "." in token:
            parts = token.split(".")
            token_info["jwt_structure"] = {
                "parts": len(parts),
                "header_length": len(parts[0]) if len(parts) > 0 else 0,
                "payload_length": len(parts[1]) if len(parts) > 1 else 0,
                "signature_length": len(parts[2]) if len(parts) > 2 else 0,
                "likely_jwt": len(parts) == 3
            }

        return {
            "success": True,
            "tool": "bearer_token_print_tool",
            "message": "🔍 Bearer Token Analysis Complete",
            "user_authentication": {
                "user_id": user_id,
                "provider": provider,
                "auth_type": auth_type,
                "authenticated": user_context.get("authenticated", False)
            },
            "bearer_token": token_info,
            "full_user_context_keys": list(user_context.keys()),
            "timestamp": self._get_timestamp(),
            "test_result": "✅ Bearer token successfully forwarded to tool!" if token else "❌ No bearer token received in tool"
        }

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute bearer token print using ADK ToolContext.

        Args:
            tool_context: ADK ToolContext with session state
            **kwargs: Additional parameters

        Returns:
            Bearer token analysis
        """
        # Get authentication context from session state
        session_state = tool_context.state or {}

        # Extract OAuth/bearer token information from session
        user_context = {
            "user_id": session_state.get("oauth_user_id"),
            "provider": session_state.get("oauth_provider", "unknown"),
            "user_info": session_state.get("oauth_user_info", {}),
            "token": session_state.get("oauth_token"),
            "auth_type": "bearer",  # Assume bearer since we're testing bearer token forwarding
            "authenticated": session_state.get("oauth_authenticated", False)
        }

        # Add session state debugging information
        session_debug = {
            "session_keys": list(session_state.keys()),
            "oauth_user_id": session_state.get("oauth_user_id"),
            "oauth_provider": session_state.get("oauth_provider"),
            "oauth_token_present": bool(session_state.get("oauth_token")),
            "oauth_authenticated": session_state.get("oauth_authenticated")
        }

        logger.info(f"🔍 Bearer Token Print Tool - Session Debug: {session_debug}")

        # Check if we have bearer token in session
        if not user_context["user_id"] or not user_context["token"]:
            return {
                "success": False,
                "tool": "bearer_token_print_tool",
                "error": "No bearer token found in session state",
                "session_debug": session_debug,
                "message": "❌ Bearer token was not forwarded to tool session state",
                "timestamp": self._get_timestamp()
            }

        # Call the authenticated method with extracted context
        try:
            result = await self.execute_authenticated(user_context, **kwargs)
            result["session_debug"] = session_debug
            return result
        except Exception as e:
            return {
                "success": False,
                "tool": "bearer_token_print_tool",
                "error": f"Bearer token analysis failed: {str(e)}",
                "session_debug": session_debug,
                "timestamp": self._get_timestamp()
            }