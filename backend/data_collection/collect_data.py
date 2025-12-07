"""
Data collection script for Dobot Magician robot.

This script records demonstrations on your Dobot Magician robot and saves them
in HDF5 format. The data can then be converted to LeRobot format
for training ACT (Action Chunking with Transformers) policies.

The Dobot Magician has 4 DOF (x, y, z, r) plus a suction gripper.

Usage:
    python collect_data.py --task "pick red cube" --num-episodes 50
"""

import dataclasses
import datetime
import logging
import pathlib
import sys
import time
from pathlib import Path

import h5py
import numpy as np

try:
    import tyro
except ImportError:
    logging.error("tyro not installed! Run: pip install tyro")
    raise

try:
    import pydobot
    from pydobot.dobot import MODE_PTP
except ImportError:
    logging.error("pydobot not installed! Run: pip install pydobot")
    raise

try:
    import cv2
except ImportError:
    logging.error("opencv-python not installed!")
    raise

try:
    import depthai as dai
except ImportError:
    logging.error("depthai not installed! Run: pip install depthai")
    raise


class OAKDCamera:
    """Camera class for OAK-D depth camera using DepthAI."""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.pipeline = None
        self.device = None
        self.rgb_queue = None
        self._setup_pipeline()
    
    def _setup_pipeline(self):
        """Setup the DepthAI pipeline for RGB capture."""
        self.pipeline = dai.Pipeline()
        
        # Create RGB camera node
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setPreviewSize(self.width, self.height)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
        cam_rgb.setFps(30)
        
        # Create output for RGB
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.preview.link(xout_rgb.input)
        
        # Start the device
        self.device = dai.Device(self.pipeline)
        self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        
        logging.info(f"OAK-D camera initialized at {self.width}x{self.height}")
    
    def read(self):
        """Read a frame from the camera. Returns (success, frame) tuple."""
        try:
            in_rgb = self.rgb_queue.tryGet()
            if in_rgb is not None:
                frame = in_rgb.getCvFrame()
                return True, frame
            return False, None
        except Exception as e:
            logging.error(f"Error reading from OAK-D: {e}")
            return False, None
    
    def release(self):
        """Close the camera connection."""
        if self.device:
            self.device.close()
            self.device = None
        logging.info("OAK-D camera released")


@dataclasses.dataclass
class Args:
    # Data collection
    task: str = "pick_and_place"
    num_episodes: int = 50
    output_dir: str = "data/dobot/demonstrations"
    
    # Robot connection
    robot_port: str = "/dev/tty.usbmodem101"  # Default Dobot port on macOS
    
    # Camera settings
    camera_width: int = 640
    camera_height: int = 480
    
    # Recording settings
    record_hz: int = 20  # Recording frequency
    
    # Mode
    # Kinesthetic teaching: manually move the robot while recording
    kinesthetic_mode: bool = True


def main(args: Args) -> None:
    logging.info("=" * 60)
    logging.info("Dobot Magician Data Collection")
    logging.info("=" * 60)
    logging.info(f"Task: {args.task}")
    logging.info(f"Episodes: {args.num_episodes}")
    logging.info(f"Mode: {'Kinesthetic Teaching' if args.kinesthetic_mode else 'Teleoperation'}")
    logging.info("=" * 60)
    
    # Create output directory
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to robot
    logging.info(f"Connecting to Dobot on {args.robot_port}...")
    try:
        robot = pydobot.Dobot(port=args.robot_port)
        logging.info("✓ Robot connected!")
    except Exception as e:
        logging.error(f"Failed to connect to Dobot: {e}")
        logging.error("Make sure the robot is connected and powered on.")
        raise
    
    # Initialize camera
    logging.info("Initializing OAK-D camera...")
    try:
        camera = OAKDCamera(width=args.camera_width, height=args.camera_height)
        logging.info("✓ Camera connected!")
    except Exception as e:
        logging.error(f"Failed to connect to camera: {e}")
        robot.close()
        raise
    
    # Warm up camera
    logging.info("Warming up camera...")
    for _ in range(10):
        camera.read()
        time.sleep(0.1)
    logging.info("✓ Camera ready!")
    
    # Collect episodes
    collected_episodes = 0
    for ep_idx in range(args.num_episodes):
        logging.info(f"\n{'=' * 60}")
        logging.info(f"Episode {ep_idx + 1}/{args.num_episodes}")
        logging.info("=" * 60)
        
        # Wait for user to be ready
        input("Press Enter when ready to start demonstration...")
        
        logging.info("Recording in 3...")
        time.sleep(1)
        logging.info("Recording in 2...")
        time.sleep(1)
        logging.info("Recording in 1...")
        time.sleep(1)
        logging.info("🔴 RECORDING! Perform the demonstration. Press Ctrl+C when done.")
        
        # Record episode
        episode_data = record_episode(
            robot=robot,
            camera=camera,
            record_hz=args.record_hz,
        )
        
        if episode_data is None:
            logging.info("Episode cancelled or empty, skipping...")
            continue
        
        # Save episode
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        episode_file = output_dir / f"episode_{ep_idx:04d}_{timestamp}.hdf5"
        save_episode(episode_file, episode_data, args.task)
        
        collected_episodes += 1
        logging.info(f"✓ Saved episode with {len(episode_data['observations'])} timesteps")
        logging.info(f"  File: {episode_file}")
        
        # Ask if user wants to continue
        if ep_idx < args.num_episodes - 1:
            cont = input("\nContinue to next episode? [Y/n]: ").strip().lower()
            if cont == 'n':
                logging.info("Stopping data collection.")
                break
    
    # Cleanup
    robot.close()
    camera.release()
    
    logging.info(f"\n{'=' * 60}")
    logging.info("Data collection complete!")
    logging.info(f"Collected {collected_episodes} episodes")
    logging.info(f"Data saved to: {output_dir}")
    logging.info(f"\nNext step: Convert to LeRobot format:")
    logging.info(f"  python convert_to_lerobot.py --input-dir {output_dir}")
    logging.info("=" * 60)


def record_episode(
    robot,
    camera: OAKDCamera,
    record_hz: int,
) -> dict | None:
    """
    Record a single episode.
    
    Dobot Magician state: (x, y, z, r, j1, j2, j3, j4) in mm and degrees.
    We record position (x, y, z, r) plus suction state.
    
    Returns dict with keys:
    - observations: list of obs dicts
    - actions: list of action arrays
    """
    observations = []
    actions = []
    prev_state = None
    
    record_interval = 1.0 / record_hz
    
    try:
        while True:
            start_time = time.time()
            
            # Get robot state
            state = get_robot_state(robot)
            
            # Capture image (resized to 224x224 for model input)
            image = capture_image(camera)
            
            # Store observation
            obs = {
                "qpos": state,
                "image": image,
            }
            observations.append(obs)
            
            # Compute action (change in state)
            if prev_state is not None:
                action = state - prev_state
            else:
                action = np.zeros_like(state)
            actions.append(action)
            
            prev_state = state.copy()
            
            # Maintain consistent recording frequency
            elapsed = time.time() - start_time
            sleep_time = record_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logging.info("\n✓ Recording stopped")
    except Exception as e:
        logging.error(f"Error during recording: {e}")
        return None
    
    if len(observations) == 0:
        return None
    
    # Remove the last action (it's just zeros from the stop)
    if len(actions) > 1:
        actions = actions[:-1]
        observations = observations[:-1]
    
    return {
        "observations": observations,
        "actions": actions,
    }


def get_robot_state(robot) -> np.ndarray:
    """
    Get current robot state from Dobot Magician.
    
    Returns state as shape (5,):
    [X, Y, Z, R, Suction]
    
    Where:
    - X, Y, Z: End-effector position in mm
    - R: End-effector rotation in degrees
    - Suction: 0.0 for off, 1.0 for on
    
    Note: Dobot Magician is a 4-DOF robot. We use Cartesian coordinates
    rather than joint angles for simplicity and intuitive demonstration.
    """
    try:
        pose, joints = robot.get_pose()
        # pose = (x, y, z, r)
        # joints = (j1, j2, j3, j4) - we don't use these directly
        
        x, y, z, r = pose[0], pose[1], pose[2], pose[3]
        
        # Get suction state - Dobot doesn't have a direct query,
        # so we track this separately if possible, or default to 0
        # For kinesthetic teaching, user controls suction manually
        suction = 0.0  # Default to off
        
        state = np.array([x, y, z, r, suction], dtype=np.float32)
        return state
    except Exception as e:
        logging.warning(f"Error getting robot state: {e}")
        return np.zeros(5, dtype=np.float32)


def capture_image(camera: OAKDCamera, target_size=(224, 224)) -> np.ndarray:
    """
    Capture image from camera and resize to consistent size.
    
    Returns RGB image with shape (height, width, 3).
    """
    ret, frame = camera.read()
    if not ret or frame is None:
        # Return black placeholder image
        return np.zeros((*target_size, 3), dtype=np.uint8)
    
    # OAK-D returns RGB by default based on our pipeline config
    # Resize to consistent size for model input
    frame_resized = cv2.resize(frame, target_size)
    
    return frame_resized


def save_episode(filepath: pathlib.Path, episode_data: dict, task: str) -> None:
    """
    Save episode data to HDF5 file.
    
    Format is compatible with ALOHA and can be converted to LeRobot format.
    
    Dobot Magician schema:
    - qpos: (5,) array [x, y, z, r, suction]
    - image: (224, 224, 3) RGB uint8
    - action: (5,) array [dx, dy, dz, dr, dsuction]
    """
    observations = episode_data["observations"]
    actions = episode_data["actions"]
    
    num_timesteps = len(observations)
    
    with h5py.File(filepath, "w") as f:
        # Store metadata
        f.attrs["task"] = task
        f.attrs["num_timesteps"] = num_timesteps
        f.attrs["robot_type"] = "dobot_magician"
        f.attrs["state_dim"] = 5  # x, y, z, r, suction
        
        # Store observations
        obs_group = f.create_group("observations")
        
        # Positions (qpos equivalent for Dobot)
        qpos_data = np.array([obs["qpos"] for obs in observations])
        obs_group.create_dataset("qpos", data=qpos_data)
        
        # Images
        images_group = obs_group.create_group("images")
        images = np.stack([obs["image"] for obs in observations])
        images_group.create_dataset("camera", data=images, compression="gzip")
        
        # Store actions
        actions_data = np.array(actions)
        f.create_dataset("action", data=actions_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main(tyro.cli(Args))
