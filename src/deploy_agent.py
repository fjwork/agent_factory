import os
from typing import Optional, Sequence, Union
import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
from trail_agent.agent import root_agent
from google.cloud.storage import Client as StorageClient


def deploy_agent(
    project: str,
    location: str,
    staging_bucket: str,
    display_name: str,
    extra_packages: Optional[Sequence[str]] = None,
    requirements: Optional[Union[str, Sequence[str]]] = None,
) -> None:


    storage_client = StorageClient(project=project)
    buckets = storage_client.list_buckets(project=project)

    existing_buckets = [bucket.name for bucket in buckets]

    if staging_bucket not in existing_buckets:
        storage_client.create_bucket(bucket_or_name=staging_bucket, location=location)


    vertexai.init(
        project=project,
        location=location,
        staging_bucket=f"gs://{staging_bucket}",
    )

    agent_app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True
    )


    agent_engine_dict = {agent_engine.display_name: agent_engine.resource_name for agent_engine in agent_engines.list()}

    if display_name in agent_engine_dict:
        deployed_agent = agent_engines.update(
            resource_name=agent_engine_dict[display_name],
            agent_engine=agent_app,
            extra_packages=extra_packages,
            requirements=requirements
        )
    else:
        deployed_agent = agent_engines.create(
            agent_engine=agent_app,
            display_name=display_name,
            extra_packages=extra_packages,
            requirements=requirements
        )

    print("Deployment successful!")
    print(f"Deployed Agent Name: {deployed_agent.resource_name}")


if __name__ == "__main__":
    AGENT_NAME = "salesforce_agent"
    PROJECT_ID = "heb-dsol-ai-platform-nonprod"
    LOCATION = "us-central1"
    STAGING_BUCKET = f"genai_platform_{AGENT_NAME}_bucket"

    # to deploy the agent
    deploy_agent(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=STAGING_BUCKET,
        display_name=AGENT_NAME,
        requirements=['google-cloud-aiplatform[adk,agent_engines]'],
        extra_packages=['./salesforce_agent']  
    )

    # # to query the agent
    # asyncio.run(
    #     query_agent(
    #         message="What is the weather is new york?",
    #         project=PROJECT_ID,
    #         location=LOCATION,
    #         resource_id=RESOURCE_ID,
    #         service_account=SERVICE_ACCOUNT,
    #         staging_bucket=STAGING_BUCKET
    #     )
    # )
