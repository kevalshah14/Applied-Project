import os
from typing import List, Generator
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from ai.tools import access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object

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
            tools=[access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
            system_instruction="""
            You are a robot assistant with vision and manipulation capabilities.
            
            CRITICAL INSTRUCTIONS:
            1. If the user asks to "find" an object, "where is" an object, or asks for coordinates of an object, use the `find_object` tool.
            2. If the user asks to see the camera or "what do you see", use `access_camera`.
            3. If the user asks to open the gripper or release something, use `open_gripper`.
            4. If the user asks to close the gripper or grab something, use `close_gripper`.
            5. If the user asks to go home or move to home position, use `go_home`.
            6. If the user asks to pick up an object, use `pickup_object`. 
               - If coordinates were mentioned in recent messages, extract and pass them as x_mm, y_mm, z_mm.
               - If no coordinates available, the tool will return an error asking to find the object first.
            """
        )

        # Create chat session
        chat = client.chats.create(model=MODEL_ID, history=chat_history, config=config)
        
        # Add system instruction to encourage tool usage
        system_instruction = """
        You are a robot assistant with vision and manipulation capabilities.
        
        TOOLS:
        1. access_camera: Use this when the user wants to see the live camera feed or asks "what do you see?".
        2. find_object: Use this when the user asks to find an object or locate something (e.g., "where is the cup?", "find the banana").
        3. open_gripper: Use this when the user wants to open the gripper or release something.
        4. close_gripper: Use this when the user wants to close the gripper or grab something.
        5. go_home: Use this when the user wants to move the robot to its home position.
        6. pickup_object: Use this when the user asks to pick up, grab, or grasp an object.
           - Check conversation history for coordinates (x, y, z in mm) and pass them if available.
           - Otherwise, tell user to find the object first.
        
        IMPORTANT:
        - If the user asks to find an object, use `find_object`.
        - If the user asks to see the camera, you MUST use the `access_camera` tool.
        - If the user asks to control the gripper, use the appropriate gripper tool.
        - If the user asks to go home, use `go_home`.
        - If the user asks to pick up an object, use `pickup_object` with coordinates from chat history if available.
        """
        
        # We can't easily add system instructions to an existing chat session in this SDK version 
        # without recreating it or prepending to history.
        # Let's prepend it to the message as a temporary hint if it's the first message,
        # or just rely on the tool definitions.
        # Better yet, let's print what tools are being sent to debug.
        print(f"DEBUG: Sending tools to model: {[t.__name__ for t in [access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object]]}")
        
        # Send message and stream response
        response = chat.send_message_stream(message)
        
        for chunk in response:
            # Check if there are function calls in the chunk (if the SDK exposes them in the stream)
            # The google-genai SDK handles execution automatically, but we can sometimes see the thought process
            # or partial tool calls if we inspect carefully. 
            # For now, let's just yield the text.
            if chunk.text:
                print(f"DEBUG: Chunk text: {chunk.text[:50]}...") # Log first 50 chars
                yield chunk.text

    except Exception as e:
        yield f"Error: {str(e)}"
