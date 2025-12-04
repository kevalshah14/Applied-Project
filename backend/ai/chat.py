import os
from typing import List, Generator
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from ai.tools import access_camera

load_dotenv()

# Initialize Gemini Client
api_key = os.getenv("APIKEY")
if not api_key:
    print("Warning: APIKEY environment variable not set")

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Failed to initialize client: {e}")
    client = None

MODEL_ID = "gemini-2.0-flash"

class Message(BaseModel):
    role: str
    content: str

def generate_chat_stream(message: str, history: List[Message]) -> Generator[str, None, None]:
    if not client:
        yield "Error: Gemini client not initialized. Check API key."
        return

    try:
        # Convert history to the format expected by the SDK
        chat_history = []
        for msg in history:
            chat_history.append(types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        # Configure tools
        config = types.GenerateContentConfig(
            tools=[access_camera],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )

        # Create chat session
        chat = client.chats.create(model=MODEL_ID, history=chat_history, config=config)
        
        # Send message and stream response
        response = chat.send_message_stream(message)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"Error: {str(e)}"

