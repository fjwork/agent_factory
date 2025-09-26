"""
A2A Server Implementation

This module implements the A2A server with OAuth authentication integration.
"""

import logging
from typing import Dict, Any, Optional
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from .agent_card import AgentCardBuilder
from .handlers import AuthenticatedRequestHandler
from auth.oauth_middleware import OAuthMiddleware

logger = logging.getLogger(__name__)


class AuthenticatedA2AServer:
    """A2A Server with OAuth authentication."""

    def __init__(
        self,
        agent: Agent,
        config_dir: str = "config",
        environment: str = "development"
    ):
        self.agent = agent
        self.config_dir = config_dir
        self.environment = environment

        # Initialize authentication
        self.oauth_middleware = OAuthMiddleware()

        # Create agent card
        self.card_builder = AgentCardBuilder(config_dir)
        self.agent_card = self.card_builder.create_agent_card(environment)

        # Create ADK components
        self.runner = self._create_runner()
        self.executor = self._create_executor()

        # Create request handler with authentication
        self.request_handler = AuthenticatedRequestHandler(
            agent_executor=self.executor,
            task_store=InMemoryTaskStore(),
            oauth_middleware=self.oauth_middleware,
            card_builder=self.card_builder,
            runner=self.runner  # Pass runner for session management
        )

        # Create Starlette application
        self.app = self._create_app()

    def _create_runner(self) -> Runner:
        """Create ADK runner."""
        return Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _create_executor(self) -> A2aAgentExecutor:
        """Create A2A agent executor."""
        return A2aAgentExecutor(
            runner=self.runner,
            config=A2aAgentExecutorConfig()
        )

    def _create_app(self) -> Starlette:
        """Create Starlette application with routes."""
        # CORS middleware for development
        middleware = []
        if self.environment == "development":
            middleware.append(
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            )

        # Define routes
        routes = [
            # A2A protocol routes
            Route("/", endpoint=self._handle_a2a_request, methods=["POST"]),
            Route("/.well-known/agent-card.json", endpoint=self._handle_agent_card, methods=["GET"]),
            Route("/agent/authenticatedExtendedCard", endpoint=self._handle_extended_card, methods=["GET"]),

            # OAuth authentication routes
            Route("/auth/initiate", endpoint=self._handle_auth_initiate, methods=["POST"]),
            Route("/auth/complete", endpoint=self._handle_auth_complete, methods=["POST"]),
            Route("/auth/status", endpoint=self._handle_auth_status, methods=["GET"]),
            Route("/auth/revoke", endpoint=self._handle_auth_revoke, methods=["POST"]),

            # Dual authentication status (includes bearer token support)
            Route("/auth/dual-status", endpoint=self._handle_dual_auth_status, methods=["GET", "POST"]),

            # Health check
            Route("/health", endpoint=self._handle_health, methods=["GET"]),
        ]

        app = Starlette(
            routes=routes,
            middleware=middleware
        )

        return app

    async def _handle_a2a_request(self, request: Request) -> Response:
        """Handle A2A protocol requests."""
        return await self.request_handler.handle_post(request)

    async def _handle_agent_card(self, request: Request) -> Response:
        """Handle agent card requests."""
        return await self.request_handler.handle_get_card(self.agent_card)

    async def _handle_extended_card(self, request: Request) -> Response:
        """Handle authenticated extended agent card requests."""
        return await self.request_handler.handle_authenticated_extended_card(request)

    async def _handle_auth_initiate(self, request: Request) -> Response:
        """Handle OAuth initiation."""
        try:
            data = await request.json()
            user_id = data.get("user_id")
            provider = data.get("provider")

            if not user_id:
                return JSONResponse({"error": "user_id required"}, status_code=400)

            auth_info = await self.oauth_middleware.initiate_auth(user_id, provider)
            return JSONResponse(auth_info)

        except Exception as e:
            logger.error(f"Auth initiation failed: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _handle_auth_complete(self, request: Request) -> Response:
        """Handle OAuth completion."""
        try:
            data = await request.json()
            session_id = data.get("session_id")

            if not session_id:
                return JSONResponse({"error": "session_id required"}, status_code=400)

            # Extract additional parameters for authorization code flow
            auth_code = data.get("authorization_code")

            result = await self.oauth_middleware.complete_auth(
                session_id,
                authorization_code=auth_code
            )
            return JSONResponse(result)

        except Exception as e:
            logger.error(f"Auth completion failed: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _handle_auth_status(self, request: Request) -> Response:
        """Handle authentication status check."""
        try:
            user_id = request.query_params.get("user_id")
            provider = request.query_params.get("provider")

            if not user_id:
                return JSONResponse({"error": "user_id required"}, status_code=400)

            token = await self.oauth_middleware.get_valid_token(user_id, provider)
            user_info = None

            if token:
                user_info = await self.oauth_middleware.get_user_info(user_id, provider)

            return JSONResponse({
                "authenticated": token is not None,
                "provider": provider or self.oauth_middleware.config.default_provider,
                "user_info": user_info,
                "expires_at": token.expires_at if token else None
            })

        except Exception as e:
            logger.error(f"Auth status check failed: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _handle_auth_revoke(self, request: Request) -> Response:
        """Handle token revocation."""
        try:
            data = await request.json()
            user_id = data.get("user_id")
            provider = data.get("provider")

            if not user_id:
                return JSONResponse({"error": "user_id required"}, status_code=400)

            success = await self.oauth_middleware.revoke_token(user_id, provider)
            return JSONResponse({"revoked": success})

        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    async def _handle_dual_auth_status(self, request: Request) -> Response:
        """Handle dual authentication status check (bearer token + OAuth)."""
        return await self.request_handler.handle_auth_status(request)

    async def _handle_health(self, request: Request) -> Response:
        """Handle health check."""
        auth_status = self.request_handler.get_auth_status()
        return JSONResponse({
            "status": "healthy",
            "agent": self.agent.name,
            "version": self.agent_card.version,
            "authentication": {
                "enabled": True,
                "dual_auth": auth_status["dual_authentication_enabled"],
                "methods": auth_status["supported_methods"],
                "bearer_validation": auth_status["bearer_token_validation"]
            }
        })

    def build(self) -> Starlette:
        """Build and return the Starlette application."""
        return self.app


def create_authenticated_a2a_server(
    agent: Agent,
    config_dir: str = "config",
    environment: str = "development"
) -> AuthenticatedA2AServer:
    """Factory function to create an authenticated A2A server."""
    return AuthenticatedA2AServer(agent, config_dir, environment)


# Legacy compatibility function for non-authenticated A2A server
def create_agent_a2a_server(agent: Agent, agent_card: AgentCard) -> A2AStarletteApplication:
    """Create a standard A2A server (for backward compatibility)."""
    runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    executor = A2aAgentExecutor(runner=runner, config=A2aAgentExecutorConfig())
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )