
# Save this code as "profile_agent.py"

import asyncio
import logging
import os
import time
import uvicorn
import httpx

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response

from authlib.integrations.httpx_client import OAuth2Client
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard, AgentSkill, AgentCapabilities, TransportProtocol,
    RequestContext, EventQueue, new_agent_text_message
)
from a2a.server.agent_execution import AgentExecutor
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH


# --- 1. Configuration for Google OAuth 2.0 Device Flow ---

# IMPORTANT: Replace this with the Client ID you just created in the GCP Console.
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "41903238982-n9gs7i48f0glooti4h5eavpv7cads8i1.apps.googleusercontent.com")

# These are the official Google OAuth 2.0 endpoints for the Device Flow.
IDP_DEVICE_AUTH_URL = os.getenv("IDP_DEVICE_AUTH_URL", "https://oauth2.googleapis.com/device/code")
IDP_TOKEN_URL = os.getenv("IDP_TOKEN_URL", "https://oauth2.googleapis.com/token")
SCOPES = os.getenv("SCOPES", "openid https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email")


# This is the standard Google API endpoint to get information about the authenticated user.
PROFILE_API_URL = os.getenv("PROFILE_API_URL", "https://www.googleapis.com/oauth2/v3/userinfo")

# --- 2. Core Agent Logic ---
class ProfileAgentLogic:
    def __init__(self):
        self._session_store = {}

    async def handle_message(self, session_id: str, text: str) -> str:
        if "log in" in text.lower() or "logged in" in text.lower():
            return await self._complete_login_and_fetch_profile(session_id)
        else:
            return await self._initiate_login(session_id)

    async def _initiate_login(self, session_id: str) -> str:
        print(f"--- LOGIC [{session_id}]: Initiating Google login ---")
        async with httpx.AsyncClient() as client:
            response = await client.post(IDP_DEVICE_AUTH_URL, data={"client_id": CLIENT_ID, "scope": SCOPES})
            if response.status_code != 200: return f"Error: {response.text}"
            data = response.json()
            self._session_store[session_id] = {"device_code": data["device_code"], "login_expiry": time.time() + data["expires_in"]}
            return f"Login required. Go to: {data['verification_url']} and enter code: {data['user_code']}. Then tell me 'I have logged in'."

    async def _complete_login_and_fetch_profile(self, session_id: str) -> str:
        print(f"--- LOGIC [{session_id}]: Completing Google login ---")
        session = self._session_store.get(session_id)
        if not session or "device_code" not in session: return "Error: Login process not started."
        if time.time() > session.get("login_expiry", 0): return "Error: Login code expired."
        async with OAuth2Client(client_id=CLIENT_ID, grant_type="urn:ietf:params:oauth:grant-type:device_code") as client:
            try:
                token = await client.fetch_token(url=IDP_TOKEN_URL, device_code=session["device_code"])
                session["user_token"] = token
                del session["device_code"]
            except Exception as e: return f"Login failed or pending. Error: {e}"
        async with httpx.AsyncClient() as api_client:
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            response = await api_client.get(PROFILE_API_URL, headers=headers)
            return response.text if response.status_code == 200 else f"Error: API status {response.status_code}."

# --- 3. The AgentExecutor ---
class ProfileAgentExecutor(AgentExecutor):
    def __init__(self):
        self._agent_logic = ProfileAgentLogic()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_message_text = ""
        if context.message and context.message.parts and context.message.parts[0].type == 'text':
            user_message_text = context.message.parts[0].text
        session_id = context.task.id
        response_text = await self._agent_logic.handle_message(session_id, user_message_text)
        await event_queue.enqueue_event(new_agent_text_message(response_text))

# --- 4. Define the A2A AgentCard ---
user_profile_agent_card = AgentCard(
    name="UserProfileAgent",
    url="http://localhost:8000/", # ** THE API LIVES AT THE ROOT URL **
    description="Fetches Google profile info via Device Flow.",
    version="1.0",
    preferred_transport=TransportProtocol.http_json, # Explicitly state HTTP transport
    skills=[AgentSkill(
        id="get_google_user_profile", name="Get Google User Profile",
        description="Looks up a user's Google profile via OAuth device flow.",
        tags=["user", "profile", "oauth", "login", "google"],
        examples=["Can you get my profile?", "I have logged in"],
    )],
)

# --- 5. Main execution block to build and run the server ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if "YOUR_CLIENT_ID_HERE" in CLIENT_ID:
        raise ValueError("Please replace the placeholder 'CLIENT_ID'.")

    agent_executor = ProfileAgentExecutor()
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    # ** THE DEFINITIVE FIX IS HERE **
    # We manually construct the Starlette application with explicit routes.
    # The A2A handler will now correctly listen for POST requests at the root URL.
    app = Starlette(routes=[
        Route("/", endpoint=request_handler.handle_post, methods=["POST"]),
        Route(AGENT_CARD_WELL_KNOWN_PATH, endpoint=lambda req: request_handler.handle_get_card(user_profile_agent_card)),
    ])

    host = "127.0.0.1"
    port = 8000
    print(f"🚀 Server starting up at http://{host}:{port}")
    print(f"✅ Agent Card available at: http://{host}:{port}{AGENT_CARD_WELL_KNOWN_PATH}")
    print(f"✅ HTTP API endpoint available at: http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port)
