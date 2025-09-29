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
from tools.example_tool import ExampleTool, BearerTokenPrintTool
from agent_factory.remote_agent_factory import RemoteAgentFactory

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
    example_tool = ExampleTool()
    bearer_token_print_tool = BearerTokenPrintTool()

    # Convert to FunctionTool for ADK - tools will access user context from session state
    example_function_tool = FunctionTool(example_tool.execute_with_context)
    bearer_token_print_function_tool = FunctionTool(bearer_token_print_tool.execute_with_context)

    tools = [example_function_tool, bearer_token_print_function_tool]

    # Load remote agents if configured (optional)
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    remote_factory = RemoteAgentFactory(config_dir)
    remote_agents = await remote_factory.load_remote_agents_if_configured()

    # Build dynamic instruction based on available remote agents
    instruction = _build_agent_instruction(agent_name, remote_agents)

    # Create agent with optional sub-agents
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=instruction,
        tools=tools,
        sub_agents=remote_agents if remote_agents else None,  # Only add if configured
        description=f"{agent_name} with OAuth authentication and A2A protocol support"
    )

    # Log agent creation details
    if remote_agents:
        logger.info(f"✅ Created agent with {len(remote_agents)} remote sub-agents:")
        for remote_agent in remote_agents:
            logger.info(f"   - {remote_agent.name}: {remote_agent.description}")
    else:
        logger.info("✅ Created agent in standalone mode (no remote agents)")

    return agent


def _build_agent_instruction(agent_name: str, remote_agents: List) -> str:
    """Build dynamic instruction based on available remote agents."""
    base_instruction = f"""
You are {agent_name}, an AI assistant with secure OAuth authentication capabilities.

Your primary purpose is to help users access authenticated services and information safely and securely.

Key capabilities:
- Secure OAuth authentication with multiple providers (Google, Azure, Okta, custom)
- Access to authenticated APIs and user data
- Agent-to-Agent (A2A) protocol communication
- Secure token management and user data protection

When users need authenticated services:
1. If they're not authenticated, guide them through the OAuth flow
2. Use their authenticated context to access authorized services
3. Format responses in a user-friendly way
4. Respect their privacy and only access authorized data

Available tools:
- example_tool: Example authenticated tool (customize for your needs)
- bearer_token_print_tool: Testing tool that prints received bearer token information"""

    if remote_agents:
        delegation_instruction = f"""

🤖 Remote Agent Delegation:
You can delegate specialized tasks to the following remote agents. Authentication context will be automatically forwarded.

Available remote agents:"""

        for agent in remote_agents:
            delegation_instruction += f"""
- {agent.name}: {agent.description}"""

        delegation_instruction += """

When delegating to remote agents:
1. Choose the most appropriate agent for the task based on their descriptions
2. Provide clear and specific task instructions
3. Authentication context (bearer tokens, OAuth) will be automatically forwarded
4. You can delegate complex tasks that require specialized capabilities

Example delegation requests:
- "Delegate this data analysis to the data_analysis_agent"
- "Send a notification using the notification_agent"
- "Route this approval request to the approval_agent"
"""

        base_instruction += delegation_instruction
    else:
        standalone_note = """

Operating Mode: Standalone (no remote agents configured)
You handle all requests directly using your available tools."""
        base_instruction += standalone_note

    base_instruction += """

Example requests you can handle:
- "Help me access my authenticated data"
- "What can you do with my authentication?"
- "Show me my information"
- "Print my bearer token" (for testing token forwarding)

Always be helpful, secure, and transparent about what information you can access.

Note: This is a template agent. Customize the tools and instructions for your specific use case.
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