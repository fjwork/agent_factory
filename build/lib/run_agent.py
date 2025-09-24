from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from trail_agent.agent import root_agent
import asyncio

SESSION_ID = "session_trail_001"
USER_ID = "user_trail_1"
APP_NAME = "trail_agent_app"

async def create_session(session_service):
    # Create or retrieve a session
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    if not session:
        session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        print(f"Created new session: {SESSION_ID}")
    else:
        print(f"Loaded existing session: {SESSION_ID}")
    return session



async def ask_agent(user_input: str, session_service):
    """Sends input to the agent and prints the response."""
    await create_session(session_service)  # Ensure session is created before running
    # The Runner orchestrates the execution flow
    runner = Runner(
        agent=root_agent,
        session_service=session_service, # Use the service instance
        app_name=APP_NAME,
    )
    print(f"\n[USER]: {user_input}")
    user_message = Content(parts=[Part(text=user_input)], role="user")
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=user_message)

    for event in events:
        # print(f"event is: ", event)
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print(f"[AGENT]: {final_response}")


# Example Usage (you could run this in a main block or interactive session)
async def main():
    session_service = InMemorySessionService()    
    print("Salesforce Agnent Ready. Type 'quit' to exit.")

    # Initial interaction
    #await ask_agent("what is the dress code in  H-E-B stores", session_service)


    await ask_agent("What is 2 + 4?", session_service)


    #await ask_agent("what are the meat cutting standards in HEB", session_service)
   
    await ask_agent("Add 10 to the result of previous addition problem  you have done in this session.", session_service)

    while True:
       user_in = input("[USER]: ")
       if user_in.lower() == 'quit':
           break
       await ask_agent(user_in,session_service)

if __name__ == "__main__":
    asyncio.run(main())