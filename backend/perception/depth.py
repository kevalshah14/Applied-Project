import depthai as dai
import numpy as np
from perception.stream import manager

import time

def get_depth_at_point(x: float, y: float) -> dict:
    """Calculates the spatial coordinates (depth) at a specific x, y point using manual calculation.

    Args:
        x: The x-coordinate (0.0 to 1.0) of the point of interest.
        y: The y-coordinate (0.0 to 1.0) of the point of interest.

    Returns:
        dict: A dictionary containing x, y, z coordinates in mm, or an error message.
    """
    if not manager.running or not manager.pipeline:
        return {"error": "Camera is not running"}

    try:
        print(f"DEBUG: Calculating depth at {x}, {y}")
        
        # Get depth frame
        depth_frame = manager.get_depth_frame()
        if depth_frame is None:
             # Try a few times to get a frame if None
            for _ in range(5):
                time.sleep(0.05)
                depth_frame = manager.get_depth_frame()
                if depth_frame is not None:
                    break
        
        if depth_frame is None:
            return {"error": "Could not get depth frame"}
            
        # Get dimensions
        height, width = depth_frame.shape
        
        # Convert normalized coordinates to pixel coordinates
        pixel_x = int(x * width)
        pixel_y = int(y * height)
        
        # Clamp
        pixel_x = max(0, min(width - 1, pixel_x))
        pixel_y = max(0, min(height - 1, pixel_y))
        
        # Get depth at center point
        z = depth_frame[pixel_y, pixel_x]
        
        # If invalid depth (0), try small ROI median
        if z == 0:
            roi_size = 5
            x1 = max(0, pixel_x - roi_size)
            x2 = min(width, pixel_x + roi_size + 1)
            y1 = max(0, pixel_y - roi_size)
            y2 = min(height, pixel_y + roi_size + 1)
            
            roi = depth_frame[y1:y2, x1:x2]
            valid_depths = roi[roi > 0]
            if len(valid_depths) > 0:
                z = np.median(valid_depths)
            else:
                z = 0 # Still 0
        
        if z == 0:
            return {"error": "Invalid depth (0) at point"}
            
        # Manual X, Y calculation using intrinsics
        # Ensure we have intrinsics
        fx = manager.fx if manager.fx else 882.5 # Fallback
        fy = manager.fy if manager.fy else 882.5
        cx = manager.cx if manager.cx else width / 2
        cy = manager.cy if manager.cy else height / 2
        
        # Calculate X, Y
        # Note: Y is negated to match standard World Y-up convention if desired,
        # or keep as Y-down matching image coords.
        # The reference code uses: y_mm = -(center_y - cy) * (z_mm / fy)
        # This implies Y-up world coordinates.
        
        x_mm = (pixel_x - cx) * z / fx
        y_mm = -(pixel_y - cy) * z / fy 
        
        print(f"DEBUG: Manual Calc: x={x_mm}, y={y_mm}, z={z}")
        
        # Get the corresponding RGB frame for visualization (best effort)
        frame = manager.get_frame()
        
        return {
            "x": int(x_mm),
            "y": int(y_mm),
            "z": int(z),
            "frame": frame
        }

    except Exception as e:
        return {"error": f"Failed to calculate depth: {str(e)}"}
