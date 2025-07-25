from google.adk.sessions import DatabaseSessionService, Session
from google.adk.runners import Runner
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
import uuid
from config import get_config
import asyncio
from dealer_agent.agent import dealer_agent
from services.service_manager import service_manager

# check if user exists, if not, create user, unique ID is twitter username
configValues = get_config()

# Game parameters
app_name = "blackjack"

session_service = DatabaseSessionService(db_url=configValues.database.url)

user_id = "encrypred8532"  # This would be the Twitter username or unique identifier
tweet_id = "123456"

runner = Runner(
    agent=dealer_agent,
    app_name=app_name,
    session_service=session_service
)

async def ensure_user_and_session() -> Session:
    """
    Ensure user exists and create session if needed.
    Returns the session_id and user_id for the agent.
    """
    try:
        # Check if user exists, create if not
        await service_manager.user_manager.create_user_if_not_exists(user_id)

        session_id = await service_manager.user_manager.create_session(user_id)
        
        # Get user's current balance
        current_balance = await service_manager.user_manager.get_user_balance(user_id)
        print(f"Current balance: ${current_balance}")
        
        # Create session state with user_id
        state = {
            "session_id": session_id,
            "user_id": user_id,  # This is what the tools expect
            "user": {
                "id": user_id,
            }
        }

        # Create session in ADK
        session = await session_service.create_session(
            app_name=app_name, 
            user_id=user_id, 
            state=state, 
            session_id=session_id
        )
        
        print(f"Session created: {session_id}")
        return session
        
    except Exception as e:
        print(f"Error ensuring user and session: {e}")
        raise

async def call_agent_async(query: str, session: Session):
    """Main function to run the agent with proper user and session setup."""
    try:
        # Create a test message
        message = types.Content(
            role="user", 
            parts=[types.Part(text=query)]
        )
        
        # Run the agent
        print("🤖 Agent is thinking...")
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session.id, 
            new_message=message
        ):
            if event.is_final_response():
                print(event)
            
    except Exception as e:
        print(f"Error running agent: {e}")
        raise

async def interactive_chat():
    """Interactive chat interface for the blackjack agent."""
    print("🎰 Welcome to Blackjack Agent!")
    print("Type 'exit()' to quit the chat.")
    print("=" * 50)
    
    try:
        # Initialize services
        await service_manager.initialize()
        
        # Initialize user and session
        session = await ensure_user_and_session()
        print("✅ Session initialized successfully!")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                # Check for exit command
                if user_input.lower() == "exit()":
                    print("👋 Goodbye! Thanks for playing!")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Send to agent
                await call_agent_async(user_input, session)
                print()  # Add spacing between exchanges
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye! Thanks for playing!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again.")
                print()
                
    except Exception as e:
        print(f"❌ Failed to initialize session: {e}")
        return

if __name__ == "__main__":
    asyncio.run(interactive_chat())
