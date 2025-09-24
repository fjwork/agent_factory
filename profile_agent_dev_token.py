# Save this code as "profile_agent.py"

import asyncio
import logging
import os
import uvicorn
import httpx

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
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

# --- 1. Configuration for the Protected API ---
# This is the standard Google API endpoint to get information about the authenticated user.
PROFILE_API_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# --- 2. Define the Tool for Authenticated API Calls ---


def fetch_profile_with_token(user_provided_token: str) -> dict | str:
    """
    Fetches the user's Google profile using a provided access token.
    The agent must ask the user to provide a token before calling this tool.

    Args:
        user_provided_token: An OAuth 2.0 access token provided by the user.

    Returns:
        A dictionary with user profile information or an error message.
    """
    print("--- TOOL: Attempting to fetch profile with user-provided token ---")
    
    # Use Google's library to create a credentials object from the raw token.
    # This doesn't validate the token, but prepares it for use.
    credentials = Credentials(token=user_provided_token)

    try:
        # Use httpx to make the authenticated API call
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json",
        }
        response = httpx.get(PROFILE_API_URL, headers=headers)
        
        # Check if the API call was successful
        response.raise_for_status() # Raises an exception for 4xx or 5xx status codes
        
        profile_data = response.json()
        print(f"--- TOOL: Successfully fetched profile for {profile_data.get('email')} ---")
        return profile_data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "Error: The provided token is invalid or has expired. Please provide a new one."
        return f"Error: API call failed with status {e.response.status_code}. Body: {e.response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# --- 3. Create the ADK Agent (Updated Instructions) ---

user_profile_agent = Agent(
    model="gemini-1.5-pro-latest",
    name="user_profile_agent",
    instruction="""
    You are a helpful User Profile assistant for Google Cloud developers.
    Your job is to fetch the user's Google profile.
    To do this, you MUST ask the user to provide an access token.
    Tell them they can generate one by running 'gcloud auth print-access-token' in their terminal.
    Once the user provides the token, you MUST call the `fetch_profile_with_token` tool,
    passing the token they gave you as the `user_provided_token` argument.
    Do not make up information or try to call the tool without a token.
    """,
    tools=[FunctionTool(fetch_profile_with_token)],
)

# --- 4. Define the A2A AgentCard (Updated for the new flow) ---

user_profile_agent_card = AgentCard(
    name="UserProfileAgent",
    url="http://localhost:8000",
    description="Fetches the user's Google profile using a developer-provided access token.",
    version="1.0",
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    preferred_transport=TransportProtocol.jsonrpc,
    skills=[
        AgentSkill(
            id="get_google_user_profile",
            name="Get Google User Profile",
            description="Looks up a user's Google profile using an access token from the 'gcloud' CLI.",
            tags=["user", "profile", "gcp", "oauth", "gcloud"],
            examples=[
                "Can you get my Google profile?",
                "Tell me my user info.",
            ],
        )
    ],
)


# --- 5. A2A Server Application (Boilerplate - No Changes) ---

def create_agent_a2a_server(agent: Agent, agent_card: AgentCard) -> A2AStarletteApplication:
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


# --- 6. Main execution block to run the server ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Creating A2A server for UserProfileAgent...")
    app = create_agent_a2a_server(user_profile_agent, user_profile_agent_card)
    host = "127.0.0.1"
    port = 8000
    print(f"🚀 Server starting up at http://{host}:{port}")
    uvicorn.run(app.build(), host=host, port=port)