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
        self.spatialLocationCalculator = None
        self.spatialQueue = None
        self.configQueue = None
        self.depthQueue = None
        self.running = False
        self.active_connections = 0
        self.calibration = None
        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None

    def load_calibration_from_device(self):
        """Load camera calibration from connected OAK-D device"""
        try:
            # Create temporary device to read calibration if main device not ready,
            # but if self.device exists, use it.
            if self.device:
                calib_handler = self.device.readCalibration()
            else:
                # This might be slow/problematic if main device is starting, but useful for dry run
                with dai.Device() as temp_device:
                    calib_handler = temp_device.readCalibration()
            
            self.calibration = calib_handler
            
            # Get intrinsics for RGB camera (CAM_A) at 1920x1080 resolution (assuming full res)
            # We should ideally match the resolution we configured for the camera
            # Default ColorCamera resolution depends on sensor, usually 1080p or 4K
            # Let's assume 1920x1080 for now as per request or use what we find
            
            # Note: In start(), we don't strictly set resolution for ColorCamera, so it defaults.
            # OAK-D Lite/Pro defaults: 1080p usually.
            resolution = (1920, 1440) 
            
            intrinsics = calib_handler.getCameraIntrinsics(
                dai.CameraBoardSocket.CAM_A, resolution[0], resolution[1]
            )
            
            self.fx = intrinsics[0][0]  # Focal length X
            self.fy = intrinsics[1][1]  # Focal length Y
            self.cx = intrinsics[0][2]  # Principal point X
            self.cy = intrinsics[1][2]  # Principal point Y
            
            print(f"📷 Camera Calibration Loaded:")
            print(f"   Focal Length: fx={self.fx:.2f}, fy={self.fy:.2f} pixels")
            print(f"   Principal Point: cx={self.cx:.2f}, cy={self.cy:.2f} pixels")
            print(f"   Note: Distortion correction handled by hardware")
            
            return True
        except Exception as e:
            print(f"Failed to load calibration: {e}")
            return False

    def start(self):
        if self.running:
            return

        try:
            # logic from user snippet
            self.device = dai.Device()
            
            # Load calibration immediately after device creation
            self.load_calibration_from_device()
            
            self.pipeline = dai.Pipeline(self.device)

            sockets = self.device.getConnectedCameras()
            if not sockets:
                raise RuntimeError("No cameras connected!")
            
            cam_a_socket = sockets[0]
            cam = self.pipeline.create(dai.node.Camera).build(cam_a_socket)
            
            # Create output queue with blocking=False to avoid filling up if client is slow
            self.queue = cam.requestFullResolutionOutput().createOutputQueue(maxSize=1, blocking=False)

            # Initialize SpatialLocationCalculator for depth
            # We always try to initialize stereo depth using CAM_B (Left) and CAM_C (Right)
            try:
                monoLeft = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
                monoRight = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)
                stereo = self.pipeline.create(dai.node.StereoDepth)
                self.spatialLocationCalculator = self.pipeline.create(dai.node.SpatialLocationCalculator)

                monoLeftOut = monoLeft.requestOutput((640, 400))
                monoRightOut = monoRight.requestOutput((640, 400))
                monoLeftOut.link(stereo.left)
                monoRightOut.link(stereo.right)

                stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DETAIL)
                # Align depth map to the perspective of RGB camera (CAM_A) for correct mapping
                stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
                
                # NOTE: We do NOT force output size anymore to allow full alignment with RGB camera.
                # However, OAK-D requires depth width to be multiple of 16.
                # If RGB camera is 4056, we must use a compatible resolution for RGB or scale depth.
                # Since we cannot easily resize RGB without losing FOV or detail in this setup without affecting the stream,
                # we will rely on the default behavior but ensure we handle the coordinate mapping correctly.
                # Actually, if we don't setOutputSize, it crashes if RGB width % 16 != 0.
                # Fix: Explicitly set RGB camera resolution to something standard like 1080P (1920x1080) which is divisible by 16 (1920/16=120).
                # cam is ColorCamera.
                # cam.setPreviewSize(1920, 1080) # Preview size for neural nets, but we use full resolution output?
                # We need to set the Video/Still size.
                # For OAK-D, we can set the sensor resolution or the ISP output.
                # cam.setVideoSize(1920, 1080)
                
                # We use 1920x1440 (4:3 aspect ratio) to match the raw sensor aspect ratio (4056x3040).
                # This prevents cropping/FOV mismatch between RGB and Depth.
                # 1920 is divisible by 16.
                stereo.setOutputSize(1920, 1440)
                
                # Initial Config
                config = dai.SpatialLocationCalculatorConfigData()
                config.depthThresholds.lowerThreshold = 100
                config.depthThresholds.upperThreshold = 10000
                calculationAlgorithm = dai.SpatialLocationCalculatorAlgorithm.MEDIAN
                # Initial ROI (center)
                topLeft = dai.Point2f(0.4, 0.4)
                bottomRight = dai.Point2f(0.6, 0.6)
                config.roi = dai.Rect(topLeft, bottomRight)
                
                self.spatialLocationCalculator.inputConfig.setWaitForMessage(False)
                self.spatialLocationCalculator.initialConfig.addROI(config)
                
                stereo.depth.link(self.spatialLocationCalculator.inputDepth)
                
                self.spatialQueue = self.spatialLocationCalculator.out.createOutputQueue(maxSize=1, blocking=False)
                self.configQueue = self.spatialLocationCalculator.inputConfig.createInputQueue()
                
                # Create depth queue directly from stereo output (like in DepthBoundingBox.py)
                self.depthQueue = stereo.depth.createOutputQueue(maxSize=1, blocking=False)
                print("Stereo depth initialized")
            except Exception as e:
                print(f"Could not initialize stereo depth: {e}")
                self.spatialLocationCalculator = None

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

    def get_depth_frame(self):
        if not self.running or self.depthQueue is None:
            return None
        frame_data = self.depthQueue.tryGet()
        if frame_data is not None:
            return frame_data.getFrame() # Returns numpy array
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
