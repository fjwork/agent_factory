"""
Auth Verification Remote Agent

This is a simple A2A agent that receives authentication context from orchestrator agents
and verifies it was properly forwarded through the A2A protocol.
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

# Add agent-template src to path for imports
template_src = os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent-template", "src")
sys.path.insert(0, template_src)

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from auth.auth_config import load_auth_config
from agent_a2a.server import create_authenticated_a2a_server
from tools.auth_verification_tool import AuthVerificationTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_agent() -> Agent:
    """Create a remote auth verification agent."""

    # Load configuration
    auth_config = load_auth_config()

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "AuthVerificationRemote")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating remote agent: {agent_name} (env: {environment})")

    # Create auth verification tool
    auth_tool = AuthVerificationTool()
    auth_function_tool = FunctionTool(auth_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a remote authentication verification agent.

Your primary purpose is to receive authentication context from orchestrator agents via the A2A protocol
and verify that authentication information is properly forwarded.

Core capabilities:
1. **Authentication Context Verification**: Receive and verify auth context from remote agents
2. **A2A Protocol Testing**: Test authentication forwarding through A2A protocol
3. **Detailed Auth Reporting**: Provide comprehensive reports on received authentication data

When you receive requests:
1. Always use your auth_verification_tool to analyze the authentication context
2. Provide detailed feedback about what authentication information was received
3. Report on the success/failure of authentication forwarding
4. Include specific details about user context, tokens, and authentication method

Available tools:
- auth_verification_tool: Analyzes received authentication context

Authentication Testing Commands:
- Any request will trigger authentication verification
- "Verify authentication" - Explicitly test auth context
- "Show auth details" - Display detailed authentication information
- "Test remote auth" - Verify A2A authentication forwarding

Always respond with:
- Clear indication of authentication success/failure
- Details about the user context received
- Information about tokens and authentication method
- Timestamp of verification
- Any authentication-related errors or issues

This agent serves as a verification endpoint for testing end-to-end authentication flows
from orchestrator agents through the A2A protocol.
        """,
        tools=[auth_function_tool],
        description=f"{agent_name} - Remote agent for testing A2A authentication forwarding"
    )

    return agent


def main():
    """Main application entry point."""
    try:
        # Load environment variables
        environment = os.getenv("ENVIRONMENT", "development")
        host = os.getenv("A2A_HOST", "0.0.0.0")
        port = int(os.getenv("A2A_PORT", "8002"))

        logger.info(f"Starting auth verification remote agent in {environment} environment")

        # Create agent
        agent = create_agent()

        # Create authenticated A2A server
        server = create_authenticated_a2a_server(
            agent=agent,
            config_dir=os.path.join(os.path.dirname(__file__), "..", "config"),
            environment=environment
        )

        # Build Starlette app
        app = server.build()

        logger.info(f"🚀 Starting Auth Verification Remote Agent at http://{host}:{port}")
        logger.info(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")
        logger.info(f"💚 Health Check: http://{host}:{port}/health")
        logger.info(f"🔐 Authentication: OAuth + Bearer Token enabled")
        logger.info(f"🔧 Auth Status: http://{host}:{port}/auth/dual-status")

        if environment == "development":
            logger.info("🔧 Development mode: CORS enabled, detailed logging")

        # Run server
        if environment == "development":
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
        logger.error(f"Failed to start auth verification remote agent: {e}")
        sys.exit(1)


# For uvicorn direct loading
def create_app():
    """Create app for uvicorn."""
    try:
        environment = os.getenv("ENVIRONMENT", "development")
        agent = create_agent()

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