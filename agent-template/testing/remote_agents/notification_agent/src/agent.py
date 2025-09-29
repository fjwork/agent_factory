"""
Notification Remote Agent

A sample remote agent that handles notification and communication tasks while
demonstrating authentication context forwarding via A2A protocol.
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

from notification_tool import NotificationTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_notification_agent() -> Agent:
    """Create the notification remote agent."""

    agent_name = "notification_agent"
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating notification agent: {agent_name}")

    # Create notification tool
    notification_tool = NotificationTool()
    notification_function_tool = FunctionTool(notification_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a specialized AI agent for notifications, alerts, and communication management.

Your expertise includes:
- Email notifications and campaigns
- SMS and push notifications
- Slack and team communication
- Alert management and escalation
- Authentication context verification

Core capabilities:
- Send notifications via multiple channels (email, SMS, push, Slack)
- Manage notification preferences and delivery options
- Handle communication workflows and escalations
- Verify authentication context forwarding from parent agents

When you receive a task:
1. Verify that authentication context was properly forwarded
2. Determine the appropriate notification channel
3. Send the notification with proper formatting
4. Include authentication verification in your response

Available tools:
- notification_tool: Sends notifications with auth context verification

You excel at:
- Multi-channel notification delivery
- User preference management
- Emergency alert systems
- Communication workflow automation

Always verify authentication context and provide detailed notification delivery confirmations.
        """,
        tools=[notification_function_tool],
        description="Specialized agent for notifications, alerts, and communication management with authentication context verification"
    )

    logger.info(f"✅ Created notification agent: {agent_name}")
    return agent


def create_notification_a2a_app(port: int = 8003):
    """Create A2A-compatible app for the notification agent."""
    agent = create_notification_agent()

    # Make agent A2A-compatible
    a2a_app = to_a2a(agent, port=port)

    logger.info(f"✅ Notification agent A2A app created on port {port}")
    return a2a_app


# For direct execution
if __name__ == "__main__":
    import asyncio
    import uvicorn

    async def main():
        port = int(os.getenv("NOTIFICATION_PORT", "8003"))
        host = os.getenv("NOTIFICATION_HOST", "0.0.0.0")

        logger.info(f"🚀 Starting Notification Agent on {host}:{port}")

        # Create A2A app
        app = create_notification_a2a_app(port)

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
        logger.info(f"🔍 A2A Endpoint: http://{host}:{port}/a2a/notification_agent")

        await server.serve()

    asyncio.run(main())