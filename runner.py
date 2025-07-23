from google.adk.sessions import InMemorySessionService,DatabaseSessionService, Session
from google.adk.runners import Runner
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
import uuid
from config import get_config
import asyncio

MODEL_XAI_3_MINI = "xai/grok-3-mini"
grok3Mini = LiteLlm(model=MODEL_XAI_3_MINI)

def log_tool(tool_context:ToolContext) -> str:
    """
    This tool is used to log the session id from the state

    Arguments:
        tool_context: The tool context
    Returns:
        The session id from the state
    """
    print(tool_context.state.get("session_id"))
    print(tool_context.state.get("user"))
    return "Logged session id from the state"

log_agent = Agent(
    name="log_agent",
    model=grok3Mini,
    description="A tool that logs the session id from the state",
    instruction="You are a helpful assistant that logs the session id from the state",
    tools=[log_tool]
)

# check if user exists, if not, create user, unique ID is twitter username
session_service = InMemorySessionService()

app_name = "blackjack"
user_id = "encrypred8532"
session_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{app_name}:{user_id}"))
state = {
    "session_id": session_id,
    "user": {
        "id": user_id,
    }
}

runner = Runner(
    agent=log_agent,
    app_name=app_name,
    session_service=session_service
)

async def call_agent_async():
    session = await session_service.create_session(app_name=app_name, user_id=user_id, state=state, session_id=session_id)
    message = types.Content(role="user", parts=[types.Part(text="Can you call the log_tool?")])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        print(event)

asyncio.run(call_agent_async())
