"""
Simplified ADK Agent with Auth Forwarding

This is the main entry point for a simplified ADK agent that:
1. Uses bearer token authentication forwarding without OAuth complexity
2. Supports HTTPS communication for secure A2A protocol
3. Leverages ADK native authentication capabilities
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

from auth import auth_forwarding_callback, load_auth_config
from a2a_server import create_simplified_a2a_server, create_https_uvicorn_config
from tools import create_authenticated_tools

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_agent() -> Agent:
    """Create a simplified agent with auth forwarding capabilities."""

    # Get environment-specific settings
    environment = os.getenv("ENVIRONMENT", "development")
    agent_name = os.getenv("AGENT_NAME", "SimplifiedAgent")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating simplified agent: {agent_name} (env: {environment})")

    # Load auth configuration
    auth_config = load_auth_config(environment)

    # Create authenticated tools
    tools = create_authenticated_tools()

    # Load remote agents if configured (optional)
    remote_agents = await _load_remote_agents_if_configured()

    # Build dynamic instruction based on capabilities
    instruction = _build_agent_instruction(agent_name, remote_agents, auth_config)

    # Create agent with auth forwarding callback
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=instruction,
        tools=tools,
        sub_agents=remote_agents if remote_agents else None,
        description=f"{agent_name} with simplified auth forwarding and HTTPS support",
        before_agent_callback=auth_forwarding_callback  # Enable auth forwarding
    )

    # Log agent creation details
    if remote_agents:
        logger.info(f"✅ Created agent with {len(remote_agents)} remote sub-agents:")
        for remote_agent in remote_agents:
            logger.info(f"   - {remote_agent.name}: {remote_agent.description}")
    else:
        logger.info("✅ Created agent in standalone mode (no remote agents)")

    logger.info(f"Auth forwarding: {'enabled' if auth_config.forward_auth_headers else 'disabled'}")
    logger.info(f"HTTPS required: {'yes' if auth_config.require_https else 'no'}")

    return agent


async def _load_remote_agents_if_configured() -> Optional[List]:
    """Load remote agents from configuration if available."""
    try:
        # Check for remote agent configuration
        config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        remote_config_path = os.path.join(config_dir, "remote_agents.yaml")

        if not os.path.exists(remote_config_path):
            logger.debug("No remote agents configuration found")
            return None

        # Import and use simplified remote agent factory if needed
        # For now, return None to keep it simple
        logger.debug("Remote agents configuration found but not implemented in simplified template")
        return None

    except Exception as e:
        logger.warning(f"Failed to load remote agents: {e}")
        return None


def _build_agent_instruction(agent_name: str, remote_agents: Optional[List], auth_config) -> str:
    """Build dynamic instruction based on agent capabilities."""
    base_instruction = f"""
You are {agent_name}, a simplified AI agent with secure authentication forwarding capabilities.

Your primary purpose is to help users while securely forwarding authentication context to tools and remote agents.

Key capabilities:
- Simplified authentication forwarding (Bearer tokens, API keys)
- Secure HTTPS communication with remote agents
- ADK native authentication patterns
- Tool authentication context

Authentication forwarding is {'enabled' if auth_config.forward_auth_headers else 'disabled'}.
HTTPS enforcement is {'enabled' if auth_config.require_https else 'disabled'}.

Available tools:
- example_authenticated_tool: Demonstrates auth context usage
- bearer_token_validation_tool: Validates and displays token information

When users interact with you:
1. Authentication context is automatically extracted from requests
2. This context is forwarded to all tools and remote agents
3. Tools can access authentication information securely
4. Remote agents receive auth headers via HTTPS

Example requests you can handle:
- "Show me my authentication info"
- "Test the authenticated request"
- "Validate my bearer token"
- "What authentication headers are available?"
"""

    if remote_agents:
        delegation_instruction = f"""

🤖 Remote Agent Delegation:
You can delegate tasks to {len(remote_agents)} remote agents. Authentication context will be automatically forwarded via HTTPS.

Available remote agents:"""

        for agent in remote_agents:
            delegation_instruction += f"""
- {agent.name}: {agent.description}"""

        delegation_instruction += """

When delegating to remote agents:
1. Choose the appropriate agent for the task
2. Provide clear task instructions
3. Authentication headers are automatically forwarded via HTTPS
4. All communication uses secure protocols
"""

        base_instruction += delegation_instruction
    else:
        standalone_note = """

Operating Mode: Standalone (no remote agents configured)
You handle all requests directly using your available authenticated tools."""
        base_instruction += standalone_note

    base_instruction += """

Security features:
- Bearer token authentication forwarding
- HTTPS-only communication (in production)
- Secure header transmission
- No complex OAuth flows required

Always be helpful and transparent about authentication capabilities while maintaining security.
"""

    return base_instruction


def main():
    """Main application entry point."""
    try:
        # Load environment variables
        environment = os.getenv("ENVIRONMENT", "development")
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))

        # SSL certificate paths (for HTTPS)
        cert_file = os.getenv("SSL_CERT_FILE")
        key_file = os.getenv("SSL_KEY_FILE")

        logger.info(f"Starting simplified agent in {environment} environment")

        # Create agent
        agent = asyncio.run(create_agent())

        # Create simplified A2A server
        server = create_simplified_a2a_server(
            agent=agent,
            config_dir=os.path.join(os.path.dirname(__file__), "..", "config"),
            environment=environment
        )

        # Build Starlette app
        app = server.build()

        # Create uvicorn configuration with optional HTTPS
        uvicorn_config = create_https_uvicorn_config(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            environment=environment
        )

        # Log startup information
        protocol = "https" if cert_file and key_file and environment == "production" else "http"
        logger.info(f"🚀 Starting server at {protocol}://{host}:{port}")
        logger.info(f"📋 Agent Card: {protocol}://{host}:{port}/.well-known/agent-card.json")
        logger.info(f"💚 Health Check: {protocol}://{host}:{port}/health")
        logger.info(f"🔐 Auth Status: {protocol}://{host}:{port}/auth/status")

        if environment == "development":
            logger.info("🔧 Development mode: CORS enabled, detailed logging")
        else:
            logger.info("🏭 Production mode: HTTPS enforced, security headers enabled")

        # Run server
        uvicorn.run(app, **uvicorn_config)

    except Exception as e:
        logger.error(f"Failed to start simplified agent: {e}")
        sys.exit(1)


# For uvicorn direct loading
def create_app():
    """Create app for uvicorn."""
    try:
        environment = os.getenv("ENVIRONMENT", "development")
        agent = asyncio.run(create_agent())

        server = create_simplified_a2a_server(
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