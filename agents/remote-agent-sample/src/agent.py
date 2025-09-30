"""
Main Agent Implementation

This is the main entry point for the ADK agent with OAuth authentication.
"""

import os
import sys
import asyncio
import logging
import uvicorn
from typing import Dict, Any, List, Optional
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
# Removed unused tools
from tools.auth_validation_tool import AuthValidationTool
from agent_factory.remote_agent_factory import AuthenticatedRemoteAgentFactory

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)




async def create_agent() -> Agent:
    """Create an OAuth-authenticated agent with optional remote agents."""

    # Load configuration
    auth_config = load_auth_config()

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "AuthenticatedAgent")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating agent: {agent_name} (env: {environment})")

    # Create tools (customize this section for your specific agent)
    auth_validation_tool = AuthValidationTool()

    # Convert to FunctionTool for ADK - tools will access user context from session state
    auth_validation_function_tool = FunctionTool(auth_validation_tool.execute_with_context)

    tools = [auth_validation_function_tool]

    # This is a standalone remote agent - no sub-agents
    remote_agents = None

    # Build dynamic instruction based on available remote agents
    instruction = _build_agent_instruction(agent_name, remote_agents)

    # Import the callback
    from auth.agent_auth_callback import auth_context_callback

    # Create agent with optional sub-agents and auth callback
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=instruction,
        tools=tools,
        description=f"{agent_name} with OAuth authentication and A2A protocol support",
        before_agent_callback=auth_context_callback  # ADD THIS LINE
    )

    # Log agent creation details
    logger.info("✅ Created standalone auth validation agent (no remote agents)")

    return agent


async def reload_agent_with_auth_context(agent: Agent, auth_context: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Reload an agent's remote agents with authentication context.

    This function is called when we have authentication context available
    and need to update the agent's sub-agents with auth forwarding.

    Args:
        agent: The existing agent instance
        auth_context: Authentication context to forward to remote agents

    Returns:
        Updated agent with authentication-enabled remote agents
    """
    if not hasattr(agent, '_remote_factory') or not hasattr(agent, '_config_dir'):
        logger.debug("Agent does not have remote factory - no auth context injection needed")
        return agent

    try:
        # Load remote agents with authentication context
        remote_factory = agent._remote_factory
        remote_agents_with_auth = await remote_factory.load_remote_agents_if_configured(auth_context)

        # Update the agent's sub_agents if we have remote agents
        if remote_agents_with_auth:
            agent.sub_agents = remote_agents_with_auth

            if auth_context and auth_context.get("authenticated"):
                logger.info(f"🔐 Updated {len(remote_agents_with_auth)} remote agents with authentication context")
            else:
                logger.debug(f"📱 Loaded {len(remote_agents_with_auth)} remote agents without authentication context")
        else:
            agent.sub_agents = None
            logger.debug("No remote agents configured - agent remains in standalone mode")

        return agent

    except Exception as e:
        logger.error(f"Failed to reload agent with auth context: {e}")
        # Return original agent if reload fails
        return agent


def _build_agent_instruction(agent_name: str, remote_agents: List) -> str:
    """Build instruction for authentication validation agent."""
    base_instruction = f"""
You are {agent_name}, a remote agent that validates authentication context forwarding via A2A protocol.

Your purpose: When you receive any request, immediately use the auth_validation_tool to check if authentication was properly forwarded from the root agent.

Available tools:
- auth_validation_tool: Validates authentication context forwarding

Always start by validating authentication context when you receive a request. When reporting the authentication status, include both the user email and the bearer token that was used for authentication.
"""

    return base_instruction


def main():
    """Main application entry point."""
    try:
        # Load environment variables
        environment = os.getenv("ENVIRONMENT", "development")
        host = os.getenv("A2A_HOST", "0.0.0.0")
        port = int(os.getenv("A2A_PORT", "8000"))

        logger.info(f"Starting agent in {environment} environment")

        # Create agent (now async)
        agent = asyncio.run(create_agent())

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
        agent = asyncio.run(create_agent())

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