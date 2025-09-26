"""
Authenticated Flow Agent - Orchestrator

This agent tests end-to-end authentication flow by:
1. Using a local auth verification tool
2. Delegating tasks to a remote auth verification agent via A2A
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

from google.adk.agents import Agent, RemoteA2aAgent
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
    """Create an authenticated flow orchestrator agent with local and remote auth verification."""

    # Load configuration
    auth_config = load_auth_config()

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "AuthenticatedFlowAgent")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating agent: {agent_name} (env: {environment})")

    # Create local auth verification tool
    local_auth_tool = AuthVerificationTool()
    local_auth_function_tool = FunctionTool(local_auth_tool.execute_with_context)

    # Create remote agent connection
    remote_agent_url = os.getenv("REMOTE_AGENT_URL", "http://localhost:8002")
    logger.info(f"Configuring remote agent connection to: {remote_agent_url}")

    try:
        remote_auth_agent = RemoteA2aAgent(
            agent_card_url=f"{remote_agent_url}/.well-known/agent-card.json"
        )
        sub_agents = [remote_auth_agent]
        logger.info("✅ Remote agent configured successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to configure remote agent: {e}")
        logger.info("Continuing with local tool only")
        sub_agents = []

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, an orchestrator agent designed to test end-to-end authentication flows.

Your primary purpose is to verify that authentication context is properly received and forwarded through the system.

Core capabilities:
1. **Local Authentication Testing**: Use the auth_verification_tool to test local authentication
2. **Remote Agent Delegation**: Delegate tasks to remote agents to test A2A authentication forwarding
3. **Authentication Flow Analysis**: Analyze and report on authentication flow success/failure

When users request authentication testing:
1. First, test local authentication using your auth_verification_tool
2. Then, if available, delegate similar testing to remote agents
3. Compare results and provide comprehensive authentication flow analysis

Available tools:
- auth_verification_tool: Tests local authentication context reception

Available sub-agents:
- Remote Auth Verification Agent: Tests authentication forwarding via A2A protocol

Authentication Testing Commands:
- "Test local authentication" - Test local auth verification tool
- "Test remote authentication" - Delegate to remote agent
- "Test full authentication flow" - Test both local and remote authentication
- "Show authentication status" - Display current auth context

Always provide detailed feedback about:
- Authentication method used (Bearer token vs OAuth)
- User context details received
- Success/failure of each authentication step
- Any authentication forwarding results

Be thorough in your authentication testing and provide clear, actionable feedback.
        """,
        tools=[local_auth_function_tool],
        sub_agents=sub_agents,
        description=f"{agent_name} - Orchestrator for testing authentication flows with local and remote verification"
    )

    return agent


def main():
    """Main application entry point."""
    try:
        # Load environment variables
        environment = os.getenv("ENVIRONMENT", "development")
        host = os.getenv("A2A_HOST", "0.0.0.0")
        port = int(os.getenv("A2A_PORT", "8001"))

        logger.info(f"Starting authenticated flow agent in {environment} environment")

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

        logger.info(f"🚀 Starting Authenticated Flow Agent at http://{host}:{port}")
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
        logger.error(f"Failed to start authenticated flow agent: {e}")
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