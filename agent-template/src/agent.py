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
from tools.tool_registry import get_tool_registry, create_tools_from_registry
from tools.mcp_toolkit import MCPToolsetWithAuth, create_mcp_auth_callback
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

    # Load tools from registry (combines traditional and MCP tools)
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    tools = create_tools_from_registry(config_dir, environment)

    # Get registry for additional tool management
    tool_registry = get_tool_registry(config_dir, environment)

    # Log tool information
    tool_status = tool_registry.get_tool_status()
    logger.info(f"📋 Loaded {tool_status['registered_tools']} tools from registry")

    # Create MCP auth callback if we have MCP toolsets
    mcp_toolsets = [tool for tool in tool_registry.tools.values() if isinstance(tool, MCPToolsetWithAuth)]
    mcp_auth_callback = create_mcp_auth_callback(mcp_toolsets) if mcp_toolsets else None

    if mcp_toolsets:
        logger.info(f"🔧 Created MCP auth callback for {len(mcp_toolsets)} toolsets")

    # Load remote agents if configured (optional) with authentication forwarding
    remote_factory = AuthenticatedRemoteAgentFactory(config_dir)

    # Load remote agents without auth context initially
    # Authentication context will be added dynamically per request
    remote_agents = await remote_factory.load_remote_agents_if_configured()

    # Build dynamic instruction based on available remote agents and tools
    instruction = _build_agent_instruction(agent_name, remote_agents, tool_registry)

    # Import the primary auth callback
    from auth.agent_auth_callback import auth_context_callback

    # Create combined auth callback (OAuth + MCP)
    def combined_auth_callback(callback_context):
        """Combined callback for OAuth context and MCP auth injection."""
        logger.info(f"🎯 Combined auth callback invoked")

        # First handle OAuth context injection for remote agents
        auth_context_callback(callback_context)

        # Then handle MCP authentication if we have MCP toolsets
        if mcp_auth_callback:
            logger.info(f"🔧 Calling MCP auth callback")
            mcp_auth_callback(callback_context)
        else:
            logger.warning(f"❌ No MCP auth callback configured")

        return None

    # Create agent with optional sub-agents and combined auth callback
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=instruction,
        tools=tools,
        sub_agents=remote_agents if remote_agents else None,  # Only add if configured
        description=f"{agent_name} with OAuth authentication, MCP toolkit, and A2A protocol support",
        before_agent_callback=combined_auth_callback
    )

    # Store the remote factory and tool registry on the agent for runtime access
    agent._remote_factory = remote_factory
    agent._config_dir = config_dir
    agent._tool_registry = tool_registry

    # Log agent creation details
    tool_count = len(tools)
    mcp_count = len(mcp_toolsets)
    traditional_count = tool_count - mcp_count

    logger.info(f"✅ Created agent with {tool_count} total tools:")
    logger.info(f"   - {traditional_count} traditional authenticated tools")
    logger.info(f"   - {mcp_count} MCP toolsets")

    if remote_agents:
        logger.info(f"✅ Agent has {len(remote_agents)} remote sub-agents:")
        for remote_agent in remote_agents:
            logger.info(f"   - {remote_agent.name}: {remote_agent.description}")
    else:
        logger.info("📱 Agent in standalone mode (no remote agents)")

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


def _build_agent_instruction(agent_name: str, remote_agents: List, tool_registry=None) -> str:
    """Build dynamic instruction based on available remote agents and tools."""
    base_instruction = f"""
You are {agent_name}, an AI assistant with secure OAuth authentication capabilities.

Your primary purpose is to help users access authenticated services and information safely and securely.

Key capabilities:
- Secure OAuth authentication with multiple providers (Google, Azure, Okta, custom)
- Access to authenticated APIs and user data
- Agent-to-Agent (A2A) protocol communication
- MCP (Model Context Protocol) toolkit integration
- Secure token management and user data protection

When users need authenticated services:
1. If they're not authenticated, guide them through the OAuth flow
2. Use their authenticated context to access authorized services
3. Format responses in a user-friendly way
4. Respect their privacy and only access authorized data

🛠️ Available Tools:"""

    # Add tool information from registry
    if tool_registry:
        available_tools = tool_registry.list_available_tools()
        if available_tools:
            tools_section = "\n"
            traditional_tools = []
            mcp_tools = []

            for tool_name, tool_info in available_tools.items():
                if tool_info.get("type") == "mcp":
                    mcp_tools.append(f"- {tool_name}: {tool_info.get('description', 'MCP toolset')}")
                else:
                    traditional_tools.append(f"- {tool_name}: {tool_info.get('description', 'Authenticated tool')}")

            if traditional_tools:
                tools_section += "\n🔧 Authentication Tools:\n" + "\n".join(traditional_tools)

            if mcp_tools:
                tools_section += "\n\n🌐 MCP Toolsets:\n" + "\n".join(mcp_tools)

            base_instruction += tools_section

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