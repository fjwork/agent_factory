"""
Simplified A2A Server with HTTPS Support

This module provides a simplified A2A server implementation that:
1. Handles authentication forwarding without complex OAuth flows
2. Supports HTTPS/TLS for secure inter-agent communication
3. Uses ADK native A2A capabilities
"""

import logging
import ssl
from typing import Dict, Any, Optional
from pathlib import Path
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

from auth import (
    extract_auth_from_request,
    set_auth_context,
    clear_auth_context,
    load_auth_config
)

logger = logging.getLogger(__name__)


class SimplifiedA2ARequestHandler(DefaultRequestHandler):
    """Request handler with simplified auth forwarding."""

    async def handle_post(self, request: Request) -> Response:
        """Handle A2A POST requests with auth context extraction."""
        try:
            # Extract authentication context from request
            auth_context = extract_auth_from_request(request)

            # Set auth context for this request
            set_auth_context(auth_context)

            if auth_context:
                logger.debug(f"Extracted auth context: {auth_context.auth_type.value}")

            # Process the A2A request normally
            response = await super().handle_post(request)

            return response

        except Exception as e:
            logger.error(f"A2A request handling failed: {e}")
            return JSONResponse({"error": "Internal server error"}, status_code=500)

        finally:
            # Clear auth context after request
            clear_auth_context()


class SimplifiedA2AServer:
    """Simplified A2A Server with HTTPS support and auth forwarding."""

    def __init__(
        self,
        agent: Agent,
        config_dir: str = "config",
        environment: str = "development"
    ):
        self.agent = agent
        self.config_dir = config_dir
        self.environment = environment

        # Load auth configuration
        self.auth_config = load_auth_config(environment)

        # Create agent card
        self.agent_card = self._create_agent_card()

        # Create ADK components
        self.runner = self._create_runner()
        self.executor = self._create_executor()

        # Create simplified request handler
        self.request_handler = SimplifiedA2ARequestHandler(
            agent_executor=self.executor,
            task_store=InMemoryTaskStore()
        )

        # Create Starlette application
        self.app = self._create_app()

    def _create_agent_card(self) -> AgentCard:
        """Create agent card for A2A protocol."""
        return AgentCard(
            name=self.agent.name,
            description=self.agent.description or f"{self.agent.name} with simplified auth forwarding",
            version="1.0.0",
            # URL will be set dynamically based on deployment
            url="",
            capabilities=["auth_forwarding", "https"],
            security_schemes={
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Bearer token authentication"
                },
                "apiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key authentication"
                }
            },
            security=[
                {"bearerAuth": []},
                {"apiKeyAuth": []}
            ]
        )

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

        # Add security middleware for HTTPS
        if self.auth_config.require_https and self.environment == "production":
            middleware.append(
                Middleware(self._https_redirect_middleware)
            )

        # Define routes
        routes = [
            # A2A protocol routes
            Route("/", endpoint=self._handle_a2a_request, methods=["POST"]),
            Route("/.well-known/agent-card.json", endpoint=self._handle_agent_card, methods=["GET"]),

            # Health check
            Route("/health", endpoint=self._handle_health, methods=["GET"]),

            # Auth status (simplified)
            Route("/auth/status", endpoint=self._handle_auth_status, methods=["GET"]),
        ]

        app = Starlette(
            routes=routes,
            middleware=middleware
        )

        return app

    async def _https_redirect_middleware(self, request: Request, call_next):
        """Middleware to enforce HTTPS in production."""
        if request.url.scheme != "https" and self.environment == "production":
            https_url = request.url.replace(scheme="https")
            return JSONResponse(
                {"error": "HTTPS required", "redirect": str(https_url)},
                status_code=426  # Upgrade Required
            )
        return await call_next(request)

    async def _handle_a2a_request(self, request: Request) -> Response:
        """Handle A2A protocol requests."""
        return await self.request_handler.handle_post(request)

    async def _handle_agent_card(self, request: Request) -> Response:
        """Handle agent card requests."""
        return JSONResponse(self.agent_card.model_dump())

    async def _handle_health(self, request: Request) -> Response:
        """Handle health check."""
        return JSONResponse({
            "status": "healthy",
            "agent": self.agent.name,
            "version": self.agent_card.version,
            "https_enabled": self.auth_config.require_https,
            "auth_forwarding": self.auth_config.forward_auth_headers,
            "environment": self.environment
        })

    async def _handle_auth_status(self, request: Request) -> Response:
        """Handle simplified auth status check."""
        auth_context = extract_auth_from_request(request)

        return JSONResponse({
            "authenticated": auth_context is not None,
            "auth_type": auth_context.auth_type.value if auth_context else None,
            "user_id": auth_context.user_id if auth_context else None,
            "provider": auth_context.provider if auth_context else None,
            "forwarding_enabled": self.auth_config.forward_auth_headers
        })

    def build(self) -> Starlette:
        """Build and return the Starlette application."""
        return self.app

    def get_ssl_context(self, cert_file: str, key_file: str) -> ssl.SSLContext:
        """Create SSL context for HTTPS."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE
        return context


def create_simplified_a2a_server(
    agent: Agent,
    config_dir: str = "config",
    environment: str = "development"
) -> SimplifiedA2AServer:
    """Factory function to create a simplified A2A server."""
    return SimplifiedA2AServer(agent, config_dir, environment)


def create_https_uvicorn_config(
    host: str = "0.0.0.0",
    port: int = 8000,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    environment: str = "development"
) -> Dict[str, Any]:
    """Create uvicorn configuration with optional HTTPS support."""
    config = {
        "host": host,
        "port": port,
        "log_level": "info",
        "access_log": True,
    }

    # Add SSL configuration for production
    if environment == "production" and cert_file and key_file:
        cert_path = Path(cert_file)
        key_path = Path(key_file)

        if cert_path.exists() and key_path.exists():
            config.update({
                "ssl_certfile": str(cert_path),
                "ssl_keyfile": str(key_path),
                "ssl_version": ssl.PROTOCOL_TLS_SERVER,
                "ssl_ciphers": "TLSv1.2:!aNULL:!MD5",
            })
            logger.info(f"HTTPS enabled with cert: {cert_path}")
        else:
            logger.warning(f"SSL certificates not found: {cert_path}, {key_path}")

    # Development settings
    if environment == "development":
        config.update({
            "reload": False,  # Disable reload to avoid import issues
            "log_level": "debug",
        })

    return config