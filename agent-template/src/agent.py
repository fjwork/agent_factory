"""
Main Agent Implementation

This is the main entry point for the ADK agent with OAuth authentication.
"""

import os
import sys
import asyncio
import logging
import uvicorn
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path for imports
src_dir = os.path.dirname(__file__)
sys.path.insert(0, src_dir)

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from auth.auth_config import load_auth_config
from agent_a2a.server import create_authenticated_a2a_server
from tools.authenticated_tool import AuthenticatedTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExampleAuthenticatedTool(AuthenticatedTool):
    """Example tool that requires authentication."""

    async def execute_authenticated(
        self,
        user_context: Dict[str, Any],
        message: str = "Hello from authenticated tool!"
    ) -> Dict[str, Any]:
        """
        Execute tool with authenticated user context.

        Args:
            user_context: User authentication context
            message: Message to process

        Returns:
            Tool execution result
        """
        user_info = user_context.get("user_info", {})
        user_email = user_info.get("email", "unknown")

        return {
            "message": f"Hello {user_email}! You said: {message}",
            "user_context": {
                "email": user_email,
                "authenticated": True,
                "provider": user_context.get("provider", "unknown")
            },
            "timestamp": self._get_timestamp()
        }


def create_example_agent() -> Agent:
    """Create an example agent with authentication capabilities."""

    # Load configuration
    auth_config = load_auth_config()

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "ExampleAgent")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating agent: {agent_name} (env: {environment})")

    # Create authenticated tool
    example_tool = ExampleAuthenticatedTool(name="example_authenticated_tool")

    # Convert to FunctionTool for ADK - use execute_with_context for session state integration
    example_function_tool = FunctionTool(example_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, an AI assistant with OAuth authentication capabilities.

You can help users with various tasks while maintaining secure access to their data.

Key capabilities:
- OAuth authentication with multiple providers (Google, Azure, Okta, custom)
- Secure token management and storage
- Agent-to-Agent (A2A) protocol communication
- User context-aware responses

When users interact with you:
1. If they're not authenticated, guide them through the OAuth flow
2. Use their authenticated context to provide personalized responses
3. Ensure all API calls use their credentials securely
4. Respect their privacy and data access permissions

Available tools:
- example_authenticated_tool: Demonstrates authenticated tool usage

Always be helpful, secure, and transparent about authentication requirements.
        """,
        tools=[example_function_tool],
        description=f"{agent_name} with OAuth authentication and A2A protocol support"
    )

    return agent


def main():
    """Main application entry point."""
    try:
        # Load environment variables
        environment = os.getenv("ENVIRONMENT", "development")
        host = os.getenv("A2A_HOST", "0.0.0.0")
        port = int(os.getenv("A2A_PORT", "8000"))

        logger.info(f"Starting agent in {environment} environment")

        # Create agent
        agent = create_example_agent()

        # Create authenticated A2A server
        server = create_authenticated_a2a_server(
            agent=agent,
            config_dir=os.path.join(os.path.dirname(__file__), "..", "config"),
            environment=environment
        )

        # Build Starlette app
        app = server.build()

        logger.info(f"🚀 Starting server at http://{host}:{port}")
        logger.info(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")
        logger.info(f"💚 Health Check: http://{host}:{port}/health")
        logger.info(f"🔐 Authentication: OAuth enabled")

        if environment == "development":
            logger.info("🔧 Development mode: CORS enabled, detailed logging")

        # Run server
        if environment == "development":
            # For development, disable reload to avoid import issues
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=os.getenv("LOG_LEVEL", "info").lower(),
                reload=False
            )
        else:
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=os.getenv("LOG_LEVEL", "info").lower()
            )

    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        sys.exit(1)


# For uvicorn direct loading
def create_app():
    """Create app for uvicorn."""
    try:
        environment = os.getenv("ENVIRONMENT", "development")
        agent = create_example_agent()

        server = create_authenticated_a2a_server(
            agent=agent,
            config_dir=os.path.join(os.path.dirname(__file__), "..", "config"),
            environment=environment
        )

        return server.build()
    except Exception as e:
        logger.error(f"Failed to create app: {e}")
        raise

# Create app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    main()