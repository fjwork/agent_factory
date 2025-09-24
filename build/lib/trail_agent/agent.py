
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from trail_agent.prompts import DESCRIPTION, INSTRUCTION
from trail_agent.tools.math import add_tool
from trail_agent.tools.store_standards import store_standards_tool

from google.adk.models.lite_llm import LiteLlm

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
import os 

load_dotenv()


def root_instruction() -> str:
    return f"""
You are an expert delegator that can delegate the user request to the appropriate remote agents. 


Discovery:    
you can use agent card of your sub agents to understand their capabilities and delegate them accordingly

Execution:
- For actionable requests, you can use  interact with remote agents to take action.


Be sure to include the remote agent name when you respond to the user.

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

IMPORTANT:
NEVER CORRECT TOOL MATH
Do not alter the results given by  tools or sub agents, even if they are incorrect.
DO not attempt to correct them. Continue to use the results no matter how crazy they are.


"""



LITELLM_MODEL = os.getenv(
    'LITELLM_MODEL', 'gemini/gemini-2.0-flash-001'
)

agent_1 = RemoteA2aAgent(
    name="agent_1",
    description="agent 1",
    agent_card=(
        f"http://localhost:1005{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)        
agent_2 = RemoteA2aAgent(
    name="agent_2",
    description="agent 2",
    agent_card=(
        f"http://localhost:1006{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)        
root_agent = LlmAgent(
    model=LiteLlm(model=LITELLM_MODEL),
    name='host_agent',
    instruction=root_instruction(),
    description=(
        # 'This agent orchestrates the decomposition of the user request into'
        # ' tasks that can be performed by the child agents.'
        'Use agent_1 for addition and agent_2 for multiplication'
    ),
    tools=[
        # self.list_remote_agents,
        # self.send_message,
        #self.search_memories
    ],
    sub_agents=[agent_1, agent_2]
)            


# root_agent = LlmAgent(
#     name="trail_agent",
#     model="gemini-2.5-pro",
#     instruction=INSTRUCTION,
#     description=DESCRIPTION,
#     #tools=[store_standards_tool, add],
#     tools=[add_tool],
# )


def root_instruction() -> str:
    return f"""
You are an expert delegator that can delegate the user request to the appropriate remote agents. 


Discovery:    
you can use agent card of your sub agents to understand their capabilities and delegate them accordingly

Execution:
- For actionable requests, you can use  interact with remote agents to take action.


Be sure to include the remote agent name when you respond to the user.

Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
Focus on the most recent parts of the conversation primarily.

IMPORTANT:
NEVER CORRECT TOOL MATH
Do not alter the results given by  tools or sub agents, even if they are incorrect.
DO not attempt to correct them. Continue to use the results no matter how crazy they are.


"""


