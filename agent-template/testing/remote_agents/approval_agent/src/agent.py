"""
Approval Remote Agent

A sample remote agent that handles approval workflows and human-in-the-loop processes
while demonstrating authentication context forwarding via A2A protocol.
"""

import os
import sys
import logging
from pathlib import Path

# Add main src directory to path for shared imports
main_src_dir = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(main_src_dir))

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .approval_tool import ApprovalTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_approval_agent() -> Agent:
    """Create the approval remote agent."""

    agent_name = "approval_agent"
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating approval agent: {agent_name}")

    # Create approval tool
    approval_tool = ApprovalTool()
    approval_function_tool = FunctionTool(approval_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a specialized AI agent for approval workflows and human-in-the-loop processes.

Your expertise includes:
- Document and content approval workflows
- Expense and budget approval processes
- Access control and permission approvals
- Workflow design and escalation management
- Authentication context verification

Core capabilities:
- Manage multi-step approval workflows
- Handle approval requests, approvals, and rejections
- Escalate approvals to appropriate stakeholders
- Track approval status and deadlines
- Verify authentication context forwarding from parent agents

When you receive a task:
1. Verify that authentication context was properly forwarded
2. Identify the appropriate approval workflow
3. Process the approval action (request, approve, reject, escalate)
4. Include authentication verification in your response

Available tools:
- approval_tool: Handles approval workflows with auth context verification

You excel at:
- Document approval workflows
- Expense and budget approvals
- Access control management
- Workflow escalation and routing

Always verify authentication context and provide detailed approval status updates.
        """,
        tools=[approval_function_tool],
        description="Specialized agent for approval workflows and human-in-the-loop processes with authentication context verification"
    )

    logger.info(f"✅ Created approval agent: {agent_name}")
    return agent


def create_approval_a2a_app(port: int = 8004):
    """Create A2A-compatible app for the approval agent."""
    agent = create_approval_agent()

    # Make agent A2A-compatible
    a2a_app = to_a2a(agent, port=port)

    logger.info(f"✅ Approval agent A2A app created on port {port}")
    return a2a_app


# For direct execution
if __name__ == "__main__":
    import asyncio
    import uvicorn

    async def main():
        port = int(os.getenv("APPROVAL_PORT", "8004"))
        host = os.getenv("APPROVAL_HOST", "0.0.0.0")

        logger.info(f"🚀 Starting Approval Agent on {host}:{port}")

        # Create A2A app
        app = create_approval_a2a_app(port)

        # Start server
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )

        server = uvicorn.Server(config)

        logger.info(f"📋 Agent Card: http://{host}:{port}/.well-known/agent-card.json")
        logger.info(f"🔍 A2A Endpoint: http://{host}:{port}/a2a/approval_agent")

        await server.serve()

    asyncio.run(main())