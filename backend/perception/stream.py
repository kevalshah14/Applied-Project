import cv2
import depthai as dai
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class CameraManager:
    def __init__(self):
        self.device = None
        self.pipeline = None
        self.queue = None
        self.running = False
        self.active_connections = 0

    def start(self):
        if self.running:
            return

        try:
            # logic from user snippet
            self.device = dai.Device()
            self.pipeline = dai.Pipeline(self.device)

            sockets = self.device.getConnectedCameras()
            if not sockets:
                raise RuntimeError("No cameras connected!")
            
            cam_a_socket = sockets[0]
            cam = self.pipeline.create(dai.node.Camera).build(cam_a_socket)
            # Create output queue with blocking=False to avoid filling up if client is slow
            self.queue = cam.requestFullResolutionOutput().createOutputQueue(maxSize=1, blocking=False)

            self.pipeline.start()
            self.running = True
            print(f"Camera started on socket {cam_a_socket}")

        except Exception as e:
            print(f"Failed to start camera: {e}")
            self.stop()
            raise

    def get_frame(self):
        if not self.running or self.queue is None:
            return None
        
        # tryGet is non-blocking
        frame = self.queue.tryGet()
        if frame is not None:
            return frame.getCvFrame()
        return None

    def stop(self):
        self.running = False
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                print(f"Error closing device: {e}")
            self.device = None
        self.pipeline = None
        self.queue = None
        print("Camera stopped")

manager = CameraManager()

@router.websocket("/ws/camera")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.active_connections += 1
    
    try:
        if not manager.running:
            manager.start()
            
        while True:
            frame = manager.get_frame()
            
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    await websocket.send_bytes(buffer.tobytes())
            
            # Yield control to allow other tasks to run
            await asyncio.sleep(0.001)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.active_connections -= 1
        # We don't auto-stop the camera anymore as it's managed by the app lifespan
        # if manager.active_connections == 0:
        #     manager.stop()
