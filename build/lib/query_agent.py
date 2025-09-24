import asyncio
import importlib
from typing import Optional, Sequence, Union

import vertexai
from google.adk.sessions import VertexAiSessionService
from vertexai.preview import reasoning_engines
from google.cloud.storage.client import Client as StorageClient
from vertexai import agent_engines


async def create_session(project: str, location: str, resource_id: str, resource_name: str, user_id: str) -> VertexAiSessionService:
# create + tie to existing session
    session_service = VertexAiSessionService(project=project, location=location, agent_engine_id=resource_id)
    session = await session_service.create_session(app_name=resource_name, user_id=user_id)
    print(f"Session ID: {session.id}")
    return session


def extract_and_concatenate_text(events):
    result = ""
    for event in events:
        parts = event.get("content", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                result += part["text"] + " "
    return result.strip()

async def query_agent(
    message: str,
    session: VertexAiSessionService,
    user_id: str,
    agent: agent_engines.AgentEngine,
) -> None:

    events = agent.stream_query(user_id=user_id, message=message, session_id=session.id)
    result = extract_and_concatenate_text(events)
    print(result)

    # # log messages
    # for event in events:
    #     print(f"Event content: {event}")

if __name__ == "__main__":
    AGENT_NAME = "salesforce_agent"
    PROJECT_ID = "heb-dsol-ai-platform-nonprod"
    LOCATION = "us-central1"
    RESOURCE_ID = "4812192958868619264"
    # SERVICE_ACCOUNT = "598349980718-compute@developer.gserviceaccount.com"
    #SERVICE_ACCOUNT = "service-598349980718@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    #STAGING_BUCKET = f"genai_platform_{AGENT_NAME}_bucket"
    USER_ID = "user_salesforce_1"

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        #service_account=SERVICE_ACCOUNT,
        #staging_bucket=STAGING_BUCKET,
    )

    resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"
    session = asyncio.run(create_session(project=PROJECT_ID, location=LOCATION, resource_id=RESOURCE_ID, resource_name=resource_name, user_id=USER_ID))
    agent = agent_engines.get(resource_name=resource_name)

    prompt = "what is the dress code in  H-E-B stores ?"
    print(prompt)
    # to query the agent
    asyncio.run(
        query_agent(
            message=prompt,
            session=session,
            user_id=USER_ID,
            agent=agent
        )
    )

    prompt = "What is 2 + 4?"
    print(prompt)

    asyncio.run(
        query_agent(
            message=prompt,
            session=session,
            user_id=USER_ID,
            agent=agent
        )
    )

    prompt = "what are the meat cutting standards in HEB"
    print(prompt)
    # to query the agent
    asyncio.run(
        query_agent(
            message=prompt,
            session=session,
            user_id=USER_ID,
            agent=agent
        )
    )

    prompt = "Add 10 to the result of previous addition problem  you have done in this session."
    print(prompt)

    asyncio.run(
        query_agent(
            message=prompt,
            session=session,
            user_id=USER_ID,
            agent=agent
        )
    )    