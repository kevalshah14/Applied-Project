import os
from typing import List, Generator
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from ai.tools import access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object, place_object, get_robot_pose

load_dotenv()

api_key = os.getenv("APIKEY")
if not api_key:
    print("Warning: APIKEY environment variable not set")

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Failed to initialize client: {e}")
    client = None

MODEL_ID = "gemini-2.5-flash"

class Message(BaseModel):
    role: str
    content: str

def generate_chat_stream(message: str, history: List[Message]) -> Generator[str, None, None]:
    if not client:
        yield "Error: Gemini client not initialized. Check API key."
        return

    try:
        chat_history = []
        for msg in history:
            chat_history.append(types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.content)]
            ))

        config = types.GenerateContentConfig(
            tools=[access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object, place_object, get_robot_pose],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False, maximum_remote_calls=5),
            system_instruction="""
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
            7. place_object: Use this when the user asks to place, put, or drop an object into/onto another (e.g., "place in the box").
               - Finds the target object and moves to its X,Y coordinates while maintaining current Z height.
            
            8. get_robot_pose: Use this when the user asks for the robot's position, status, or "where are you?".

            IMPORTANT:
            - If the user asks to find an object, use `find_object`.
            - If the user asks to see the camera, you MUST use the `access_camera` tool.
            - If the user asks to control the gripper, use the appropriate gripper tool.
            - If the user asks to go home, use `go_home`.
            - If the user asks to pick up an object, use `pickup_object` with coordinates from chat history if available.
            - If the user asks to place an object, use `place_object`.
            - If the user asks for status or position, use `get_robot_pose`.
            - ALWAYS use a tool if the user request matches a tool's capability. Do not just say you will do it.
            """
        )

        chat = client.chats.create(model=MODEL_ID, history=chat_history, config=config)
        
        print(f"DEBUG: Sending tools to model: {[t.__name__ for t in [access_camera, find_object, open_gripper, close_gripper, go_home, pickup_object, place_object, get_robot_pose]]}")
        
        response = chat.send_message_stream(message)
        
        for chunk in response:
            if chunk.text:
                print(f"DEBUG: Chunk text: {chunk.text[:50]}...") # Log first 50 chars
                yield chunk.text

    except Exception as e:
        yield f"Error: {str(e)}"
