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
from tools.profile_tool import ProfileTool, ProfileSummaryTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)




def create_profile_agent() -> Agent:
    """Create a profile agent with OAuth authentication capabilities."""

    # Load configuration
    auth_config = load_auth_config()

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "ProfileAgent")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating agent: {agent_name} (env: {environment})")

    # Create profile tools
    profile_tool = ProfileTool()
    profile_summary_tool = ProfileSummaryTool()

    # Convert to FunctionTool for ADK
    profile_function_tool = FunctionTool(profile_tool.execute_authenticated)
    summary_function_tool = FunctionTool(profile_summary_tool.execute_authenticated)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a specialized AI assistant that provides user profile information through secure OAuth authentication.

Your primary purpose is to help users access and understand their profile information safely and securely.

Key capabilities:
- Retrieve user profile information from OAuth providers (Google, Azure, Okta, custom)
- Generate formatted profile summaries and insights
- Secure token management and user data protection
- Agent-to-Agent (A2A) protocol communication

When users ask about their profile:
1. If they're not authenticated, guide them through the OAuth flow
2. Use their authenticated context to retrieve their profile information
3. Format responses in a user-friendly way
4. Respect their privacy and only access authorized data

Available tools:
- profile_tool: Retrieves user profile information
- profile_summary_tool: Generates formatted profile summaries

Example requests you can handle:
- "What is my profile?"
- "Show me my profile information"
- "What's my email address?"
- "Tell me about myself"
- "Give me a summary of my account"

Always be helpful, secure, and transparent about what information you can access.
        """,
        tools=[profile_function_tool, summary_function_tool],
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
        agent = create_profile_agent()

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
        agent = create_profile_agent()

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