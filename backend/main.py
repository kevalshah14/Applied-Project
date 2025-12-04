from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
import json
import cv2
from ai.chat import generate_chat_stream, Message
from perception.stream import router as perception_router, manager
from state import image_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting camera manager...")
    try:
        manager.start()
    except Exception as e:
        print(f"Failed to start camera on startup: {e}")
    
    yield
    
    # Shutdown
    print("Stopping camera manager...")
    manager.stop()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(perception_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(request.message, request.history),
        media_type="text/plain"
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/image/{image_id}")
async def get_image(image_id: str):
    print(f"DEBUG: Fetching image {image_id}. Store keys: {list(image_store.keys())}")
    if image_id in image_store:
        img = image_store[image_id]
        ret, buffer = cv2.imencode('.jpg', img)
        if ret:
            return Response(content=buffer.tobytes(), media_type="image/jpeg")
    else:
        print(f"DEBUG: Image {image_id} not found in store")
    return Response(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
