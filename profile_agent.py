# Save this code as "profile_agent.py"

import asyncio
import logging

import uvicorn
from google.adk.agents import Agent
from google.adk.tools import FunctionTool as tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)

# --- 1. Define a Custom Tool ---
# This tool represents the action our agent can take.
# For now, it's a placeholder that returns a hardcoded dictionary.
# In Step 2, we will add the OAuth logic here.

@tool
def fetch_profile(user_id: str) -> dict:
    """
    Fetches a user's profile from the internal user service.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A dictionary containing the user's profile information.
    """
    print(f"--- TOOL: Simulating fetch for user_id: {user_id} ---")
    # In a real scenario, this is where you would make an authenticated API call.
    return {
        "user_id": user_id,
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "department": "Engineering",
        "status": "Active",
    }


# --- 2. Create the ADK Agent ---
# This is the "brain" of our agent, powered by a Gemini model.
# We give it a name, instructions, and the tool(s) it's allowed to use.

user_profile_agent = Agent(
    model="gemini-2.5-pro",  # Or any other compatible Gemini model
    name="user_profile_agent",
    instruction="""
    You are a helpful User Profile assistant. Your job is to fetch user profiles
    from the company's internal service using the tools provided.
    When a user asks for profile information, you MUST use the `fetch_profile` tool.
    Do not make up information.
    """,
    tools=[fetch_profile],
)

# --- 3. Define the A2A AgentCard ---
# This is the agent's public "business card". It tells other agents
# how to find it, what it can do, and how to communicate with it.
user_profile_agent_card = AgentCard(
    name="UserProfileAgent",
    url="http://localhost:8000", # The address where this agent will be running
    description="Fetches user profile information from the internal company directory.",
    version="1.0",
    capabilities=AgentCapabilities(streaming=True),
    # --- FIX: Added the required input/output mode fields ---
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id="get_user_profile",
            name="Get User Profile",
            description="Looks up a user's profile by their user ID.",
            tags=["user", "profile", "directory", "employee lookup"],
            examples=[
                "Can you get the profile for user 'u-12345'?",
                "Find the details for u-98765.",
            ],
        )
    ],
)

# --- 4. Create the A2A Server Application ---
# This section contains the boilerplate code from the samples to wrap the
# ADK agent in a web server that speaks the A2A protocol.

def create_agent_a2a_server(agent: Agent, agent_card: AgentCard) -> A2AStarletteApplication:
    """Creates an A2A server application for any ADK agent."""
    runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    executor = A2aAgentExecutor(runner=runner, config=A2aAgentExecutorConfig())
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

# --- 5. Main execution block to run the server ---
if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    # Configure Google Cloud credentials (ensure you are logged in via gcloud CLI)
    # This is required for the ADK agent to access the Gemini model.
    # import os
    # os.environ['GOOGLE_CLOUD_PROJECT'] = "[your-gcp-project-id]"
    # os.environ['GOOGLE_CLOUD_LOCATION'] = "[your-gcp-location]"

    print("Creating A2A server for UserProfileAgent...")
    app = create_agent_a2a_server(user_profile_agent, user_profile_agent_card)

    host = "127.0.0.1"
    port = 8000

    print(f"🚀 Server starting up at http://{host}:{port}")
    print("Agent Card will be available at:")
    print(f"   http://{host}:{port}{AGENT_CARD_WELL_KNOWN_PATH}")
    print("Press Ctrl+C to stop the server.")

    # Run the web server
    uvicorn.run(app.build(), host=host, port=port)