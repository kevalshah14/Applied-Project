"""
Robot controller for handling movement and manipulation commands.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
import numpy as np

# Try importing pydobot, handle if missing (mock mode or error)
try:
    import pydobot
    from pydobot.dobot import MODE_PTP
except ImportError:
    pydobot = None
    MODE_PTP = None
    print("Warning: pydobot not installed. Robot control will fail.")

logger = logging.getLogger(__name__)


class RobotController:
    """Main controller for robot movements and gripper actions."""
    
    def __init__(self):
        """Initialize the robot controller."""
        self.device = None
        self.is_connected = False
        self.affine_matrix = None
        self.default_port = '/dev/tty.usbmodem101'  # Default from provided tools
        
        # Current state tracking (approximate, as we might not query continuously)
        self.current_pose = {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "orientation": {"r": 0.0}
        }
        self.gripper_state = "unknown"
        
        logger.info("Robot controller initialized")
    
    def _ensure_device(self):
        """Helper to ensure device is connected."""
        if self.device is None:
            if pydobot:
                try:
                    self.device = pydobot.Dobot(port=self.default_port)
                    self.is_connected = True
                    logger.info(f"Connected to Dobot on {self.default_port}")
                except Exception as e:
                    logger.error(f"Failed to connect to Dobot: {e}")
                    raise e
            else:
                raise ImportError("pydobot not installed")
        return self.device

    async def connect(self, port: Optional[str] = None) -> bool:
        """
        Connect to the robot hardware.
        """
        target_port = port or self.default_port
        try:
            if self.is_connected and self.device:
                return True

            logger.info(f"Attempting to connect to robot on {target_port}...")
            
            # Run blocking connection in thread
            def _connect():
                if not pydobot:
                    raise ImportError("pydobot library not found")
                return pydobot.Dobot(target_port)

            self.device = await asyncio.to_thread(_connect)
            self.is_connected = True
            self.default_port = target_port
            logger.info("Robot connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to robot: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> bool:
        """Disconnect from the robot hardware."""
        try:
            if self.device:
                await asyncio.to_thread(self.device.close)
            self.device = None
            self.is_connected = False
            logger.info("Robot disconnected")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from robot: {e}")
            return False

    async def get_pose(self) -> Dict[str, Any]:
        """Get the current pose of the robot end-effector."""
        if not self.is_connected or not self.device:
            return self.current_pose
        
        try:
            def _get_pose():
                pose, joint = self.device.get_pose()
                return pose, joint

            pose, _ = await asyncio.to_thread(_get_pose)
            # pose is typically (x, y, z, r, j1, j2, j3, j4)
            # pydobot get_pose returns (x, y, z, r, j1, j2, j3, j4)
            
            self.current_pose = {
                "position": {"x": pose[0], "y": pose[1], "z": pose[2]},
                "orientation": {"r": pose[3]}
            }
            return self.current_pose
        except Exception as e:
            logger.error(f"Error getting pose: {e}")
            return self.current_pose

    async def move_to_pose(
        self, 
        x: float, 
        y: float, 
        z: float, 
        r: float = 0.0
    ) -> bool:
        """
        Move the robot to a specific Cartesian pose (x, y, z, r).
        """
        if not self.is_connected or not self.device:
            logger.error("Robot not connected")
            try:
                await self.connect()
            except:
                return False
            if not self.is_connected:
                return False

        try:
            logger.info(f"Moving to x={x}, y={y}, z={z}, r={r}")
            
            def _move():
                self.device.speed(50, 50)
                self.device.move_to(mode=int(MODE_PTP.MOVJ_XYZ), x=x, y=y, z=z, r=r)
                # pydobot move_to might not block until completion depending on config,
                # but usually we wait a bit or poll. The tool example used sleep.
                time.sleep(2)

            await asyncio.to_thread(_move)
            
            # Update pose cache
            self.current_pose["position"] = {"x": x, "y": y, "z": z}
            self.current_pose["orientation"] = {"r": r}
            return True
        except Exception as e:
            logger.error(f"Failed to move to pose: {e}")
            return False

    async def go_home(self) -> bool:
        """Home the Dobot."""
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.info("Homing the robot...")
            def _home():
                self.device.home()
                time.sleep(2)
                
            await asyncio.to_thread(_home)
            logger.info("Robot homed")
            return True
        except Exception as e:
            logger.error(f"Error homing robot: {e}")
            return False

    async def suction_on(self) -> bool:
        """Turn suction ON (close gripper equivalent)."""
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.info("Turning suction ON")
            await asyncio.to_thread(self.device.suck, True)
            self.gripper_state = "closed" # effectively holding something
            return True
        except Exception as e:
            logger.error(f"Error turning suction ON: {e}")
            return False

    async def suction_off(self) -> bool:
        """Turn suction OFF (open gripper equivalent)."""
        if not self.is_connected:
            await self.connect()
            
        try:
            logger.info("Turning suction OFF")
            await asyncio.to_thread(self.device.suck, False)
            self.gripper_state = "open"
            return True
        except Exception as e:
            logger.error(f"Error turning suction OFF: {e}")
            return False

    # Aliases for compatibility with existing interface
    async def open_gripper(self, speed: float = 1.0) -> bool:
        return await self.suction_off()

    async def close_gripper(self, speed: float = 1.0, force: Optional[float] = None) -> bool:
        return await self.suction_on()

    # =========================================================
    # AFFINE + PIXEL->ROBOT HELPERS
    # =========================================================
    def set_affine_matrix(self, matrix_flat: List[float]) -> bool:
        """Set the global affine matrix from a flat list of 9 values."""
        try:
            arr = np.array(matrix_flat, dtype=np.float64).reshape(3, 3)
            self.affine_matrix = arr
            logger.info("Affine matrix updated")
            return True
        except Exception as e:
            logger.error(f"Error setting affine matrix: {e}")
            return False

    def apply_affine(self, u: float, v: float) -> Tuple[float, float]:
        """Convert pixel (u, v) to robot (x, y) using affine matrix."""
        if self.affine_matrix is None:
            raise ValueError("Affine matrix not set")
            
        uv1 = np.array([u, v, 1.0], dtype=np.float64)
        XY = self.affine_matrix @ uv1
        return float(XY[0]), float(XY[1])

    async def move_above_pixel(self, u: float, v: float, z_above: float = -30.0) -> bool:
        """Move robot to a point ABOVE the block at image pixel (u, v)."""
        if self.affine_matrix is None:
            logger.error("Affine matrix not set")
            return False
            
        try:
            Xa, Ya = self.apply_affine(u, v)
            logger.info(f"Affine: pixel({u:.3f}, {v:.3f}) -> robot({Xa:.6f}, {Ya:.6f})")
            return await self.move_to_pose(Xa, Ya, z_above, 0.0)
        except Exception as e:
            logger.error(f"Error in move_above_pixel: {e}")
            return False

    async def move_to_block_pixel(self, u: float, v: float, block_height: float = -30.0) -> bool:
        """Move robot to the BLOCK height at image pixel (u, v)."""
        if self.affine_matrix is None:
            logger.error("Affine matrix not set")
            return False
            
        try:
            Xa, Ya = self.apply_affine(u, v)
            logger.info(f"Affine: pixel({u:.3f}, {v:.3f}) -> robot({Xa:.6f}, {Ya:.6f})")
            return await self.move_to_pose(Xa, Ya, block_height, 0.0)
        except Exception as e:
            logger.error(f"Error in move_to_block_pixel: {e}")
            return False
