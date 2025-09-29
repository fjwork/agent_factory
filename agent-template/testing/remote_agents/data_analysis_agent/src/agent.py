"""
Data Analysis Remote Agent

A sample remote agent that handles data analysis tasks and demonstrates
authentication context forwarding via A2A protocol.
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

from .data_analysis_tool import DataAnalysisTool

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_data_analysis_agent() -> Agent:
    """Create the data analysis remote agent."""

    agent_name = "data_analysis_agent"
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    logger.info(f"Creating data analysis agent: {agent_name}")

    # Create data analysis tool
    data_tool = DataAnalysisTool()
    data_function_tool = FunctionTool(data_tool.execute_with_context)

    # Create agent
    agent = Agent(
        model=model_name,
        name=agent_name,
        instruction=f"""
You are {agent_name}, a specialized AI agent for data analysis and statistical computations.

Your expertise includes:
- Data analysis and statistical computations
- Data visualization and reporting
- Trend analysis and forecasting
- Pattern recognition and anomaly detection
- Authentication context verification

Core capabilities:
- Analyze datasets using various statistical methods
- Generate insights and recommendations
- Create data visualizations and reports
- Verify authentication context forwarding from parent agents

When you receive a task:
1. Verify that authentication context was properly forwarded
2. Perform the requested data analysis
3. Provide clear, actionable insights
4. Include authentication verification in your response

Available tools:
- data_analysis_tool: Performs data analysis with auth context verification

You excel at:
- Sales data analysis and revenue insights
- User behavior analysis and conversion metrics
- Trend analysis and forecasting
- Custom statistical analysis

Always verify authentication context and provide comprehensive analysis results.
        """,
        tools=[data_function_tool],
        description="Specialized agent for data analysis, statistical computations, and reporting with authentication context verification"
    )

    logger.info(f"✅ Created data analysis agent: {agent_name}")
    return agent


def create_data_analysis_a2a_app(port: int = 8002):
    """Create A2A-compatible app for the data analysis agent."""
    agent = create_data_analysis_agent()

    # Make agent A2A-compatible
    a2a_app = to_a2a(agent, port=port)

    logger.info(f"✅ Data analysis agent A2A app created on port {port}")
    return a2a_app


# For direct execution
if __name__ == "__main__":
    import asyncio
    import uvicorn

    async def main():
        port = int(os.getenv("DATA_ANALYSIS_PORT", "8002"))
        host = os.getenv("DATA_ANALYSIS_HOST", "0.0.0.0")

        logger.info(f"🚀 Starting Data Analysis Agent on {host}:{port}")

        # Create A2A app
        app = create_data_analysis_a2a_app(port)

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
        logger.info(f"🔍 A2A Endpoint: http://{host}:{port}/a2a/data_analysis_agent")

        await server.serve()

    asyncio.run(main())