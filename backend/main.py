from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
import json
from ai.chat import generate_chat_stream, Message
from perception.stream import router as perception_router, manager

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
