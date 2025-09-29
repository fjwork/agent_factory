"""
Simple Remote Agent for Bearer Token Forwarding Test

This is a minimal agent that receives bearer tokens via A2A protocol
and prints them for testing token forwarding functionality.
"""

import os
import sys
import asyncio
import logging
import uvicorn
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path for imports
src_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_dir)

from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext

from auth.auth_config import load_auth_config
from agent_a2a.server import create_authenticated_a2a_server

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RemoteBearerTokenPrintTool:
    """Simple tool for remote agent that prints bearer token information."""

    def __init__(self):
        self.name = "remote_bearer_token_print_tool"
        self.description = "Remote agent tool that prints received bearer token for A2A testing"

    async def execute_with_context(
        self,
        tool_context: ToolContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute bearer token print in remote agent.

        Args:
            tool_context: ADK ToolContext with session state
            **kwargs: Additional parameters

        Returns:
            Bearer token analysis from remote agent
        """
        # Get authentication context from session state
        session_state = tool_context.state or {}

        # Handle State object vs dict
        if hasattr(session_state, '__dict__'):
            state_dict = vars(session_state)
        else:
            state_dict = session_state

        # Extract OAuth/bearer token information from session
        session_debug = {
            "state_type": type(session_state).__name__,
            "session_keys": list(state_dict.keys()) if state_dict else [],
            "oauth_user_id": state_dict.get("oauth_user_id"),
            "oauth_provider": state_dict.get("oauth_provider"),
            "oauth_token_present": bool(state_dict.get("oauth_token")),
            "oauth_authenticated": state_dict.get("oauth_authenticated"),
            "remote_agent": True
        }

        token = state_dict.get("oauth_token")
        user_id = state_dict.get("oauth_user_id")

        logger.info(f"🔍 Remote Bearer Token Print Tool - Session Debug: {session_debug}")

        # Analyze bearer token if present
        token_info = {
            "present": bool(token),
            "type": type(token).__name__ if token else "None",
            "length": len(str(token)) if token else 0,
            "first_chars": str(token)[:20] + "..." if token and len(str(token)) > 20 else str(token) if token else None,
            "last_chars": "..." + str(token)[-10:] if token and len(str(token)) > 30 else None
        }

        # Check for JWT structure
        if token and isinstance(token, str) and "." in token:
            parts = token.split(".")
            token_info["jwt_structure"] = {
                "parts": len(parts),
                "header_length": len(parts[0]) if len(parts) > 0 else 0,
                "payload_length": len(parts[1]) if len(parts) > 1 else 0,
                "signature_length": len(parts[2]) if len(parts) > 2 else 0,
                "likely_jwt": len(parts) == 3
            }

        return {
            "success": True,
            "tool": "remote_bearer_token_print_tool",
            "agent_type": "remote_agent",
            "message": "🔍 Remote Agent Bearer Token Analysis Complete",
            "bearer_token": token_info,
            "session_debug": session_debug,
            "test_result": "✅ Bearer token successfully forwarded to remote agent via A2A!" if token else "❌ No bearer token received in remote agent",
            "a2a_forwarding_test": "SUCCESS" if token else "FAILED"
        }


def create_remote_agent() -> Agent:
    """Create a simple remote agent for bearer token testing."""

    agent_name = "RemoteBearerTokenTestAgent"
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating remote agent: {agent_name}")

    # Create bearer token print tool
    remote_tool = RemoteBearerTokenPrintTool()
    remote_function_tool = FunctionTool(remote_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a simple remote agent for testing bearer token forwarding via A2A protocol.

Your purpose is to receive bearer tokens from other agents and print their information to verify that A2A token forwarding works correctly.

Available tools:
- remote_bearer_token_print_tool: Prints bearer token information received via A2A

When asked to analyze bearer tokens or test A2A forwarding, use the remote tool to examine the token.

Example requests:
- "Print bearer token info"
- "Test A2A token forwarding"
- "Analyze token"
        """,
        tools=[remote_function_tool],
        description=f"{agent_name} for testing A2A bearer token forwarding"
    )

    return agent


async def main():
    """Main application entry point for remote agent."""
    try:
        # Configuration for remote agent
        host = os.getenv("REMOTE_A2A_HOST", "0.0.0.0")
        port = int(os.getenv("REMOTE_A2A_PORT", "8002"))  # Different port from main agent

        logger.info(f"Starting remote agent on {host}:{port}")

        # Create remote agent
        agent = create_remote_agent()

        # Create A2A server for remote agent
        server = create_authenticated_a2a_server(
            agent=agent,
            config_dir="config",
            environment="development"
        )

        logger.info(f"🚀 Remote agent server starting on http://{host}:{port}")
        logger.info(f"📋 Remote agent card: http://{host}:{port}/.well-known/agent-card.json")

        # Build the Starlette app from the server
        app = server.build()

        # Start the server
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info" if os.getenv("LOG_LEVEL", "INFO") == "INFO" else "debug",
            access_log=True
        )

        uvicorn_server = uvicorn.Server(config)
        await uvicorn_server.serve()

    except Exception as e:
        logger.error(f"Failed to start remote agent: {e}")
        raise


if __name__ == "__main__":
    # Run the remote agent
    asyncio.run(main())