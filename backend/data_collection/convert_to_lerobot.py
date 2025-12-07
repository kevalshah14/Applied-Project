"""
Convert Dobot Magician demonstration data to LeRobot format for training.

This script converts HDF5 files (collected with collect_data.py) to
LeRobot format that can be used for fine-tuning ACT.

Usage:
    python convert_to_lerobot.py \
        --input-dir data/dobot/demonstrations \
        --repo-id your_username/dobot_dataset \
        --task "pick and place"
"""

import dataclasses
import logging
import pathlib
from typing import Literal

import h5py
import numpy as np
import torch
import tqdm

try:
    import tyro
except ImportError:
    logging.error("tyro not installed! Run: pip install tyro")
    raise

try:
    from lerobot.common.datasets.lerobot_dataset import LEROBOT_HOME, LeRobotDataset
except ImportError:
    logging.error("lerobot not installed! See: https://github.com/huggingface/lerobot")
    raise


@dataclasses.dataclass
class Args:
    # Input HDF5 files
    input_dir: str = "data/dobot/demonstrations"
    
    # Output LeRobot dataset
    repo_id: str = "your_username/dobot_magician_dataset"
    task: str = "pick_and_place"
    
    # Dataset format
    mode: Literal["video", "image"] = "image"  # Use "video" for compression
    
    # Processing
    episodes: list[int] | None = None  # Which episodes to convert (None = all)
    push_to_hub: bool = False  # Upload to HuggingFace Hub


def main(args: Args) -> None:
    logging.info("=" * 60)
    logging.info("Converting Dobot Data to LeRobot Format")
    logging.info("=" * 60)
    
    input_dir = pathlib.Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Find all HDF5 files
    hdf5_files = sorted(input_dir.glob("episode_*.hdf5"))
    if not hdf5_files:
        raise FileNotFoundError(f"No episode_*.hdf5 files found in {input_dir}")
    
    logging.info(f"Found {len(hdf5_files)} episode files")
    
    # Create empty LeRobot dataset
    logging.info(f"Creating LeRobot dataset: {args.repo_id}")
    dataset = create_empty_dataset(
        repo_id=args.repo_id,
        mode=args.mode,
    )
    
    # Convert episodes
    logging.info("Converting episodes...")
    dataset = populate_dataset(
        dataset=dataset,
        hdf5_files=hdf5_files,
        task=args.task,
        episodes=args.episodes,
    )
    
    logging.info(f"✓ Dataset created with {len(dataset)} frames")
    logging.info(f"  Location: {LEROBOT_HOME / args.repo_id}")
    
    # Push to hub if requested
    if args.push_to_hub:
        logging.info("Pushing to HuggingFace Hub...")
        dataset.push_to_hub()
        logging.info(f"✓ Pushed to https://huggingface.co/datasets/{args.repo_id}")
    
    logging.info("=" * 60)
    logging.info("Conversion complete!")
    logging.info(f"\nDataset ready for ACT training.")
    logging.info(f"See: https://github.com/huggingface/lerobot")
    logging.info("=" * 60)


def create_empty_dataset(
    repo_id: str,
    mode: Literal["video", "image"] = "image",
) -> LeRobotDataset:
    """
    Create empty LeRobot dataset with Dobot Magician schema.
    
    Dobot Magician has:
    - 4 DOF Cartesian control (x, y, z, r)
    - 1 suction gripper (binary on/off)
    - 1 camera (OAK-D, external view)
    """
    
    # Define state names for Dobot Magician
    # Using Cartesian coordinates for intuitive control
    state_names = [
        "x",        # X position in mm
        "y",        # Y position in mm
        "z",        # Z position in mm
        "r",        # Rotation in degrees
        "suction",  # Suction gripper: 0=off, 1=on
    ]
    
    # Define cameras
    cameras = ["camera"]  # OAK-D camera
    
    # Define features
    features = {
        "observation.state": {
            "dtype": "float32",
            "shape": (len(state_names),),
            "names": [state_names],
        },
        "action": {
            "dtype": "float32",
            "shape": (len(state_names),),
            "names": [state_names],
        },
    }
    
    # Add camera features
    for cam in cameras:
        features[f"observation.images.{cam}"] = {
            "dtype": mode,
            "shape": (3, 224, 224),  # C, H, W
            "names": ["channels", "height", "width"],
        }
    
    # Create dataset
    dataset = LeRobotDataset.create(
        repo_id=repo_id,
        fps=20,  # Match recording frequency
        robot_type="dobot_magician",
        features=features,
    )
    
    return dataset


def populate_dataset(
    dataset: LeRobotDataset,
    hdf5_files: list[pathlib.Path],
    task: str,
    episodes: list[int] | None = None,
) -> LeRobotDataset:
    """Add episodes from HDF5 files to LeRobot dataset."""
    
    if episodes is None:
        episodes = range(len(hdf5_files))
    
    for ep_idx in tqdm.tqdm(episodes, desc="Converting episodes"):
        if ep_idx >= len(hdf5_files):
            logging.warning(f"Episode {ep_idx} not found, skipping")
            continue
        
        ep_path = hdf5_files[ep_idx]
        
        # Load episode data
        with h5py.File(ep_path, "r") as f:
            # Load observations
            qpos = torch.from_numpy(f["observations/qpos"][:])
            images = f["observations/images/camera"][:]
            
            # Load actions
            actions = torch.from_numpy(f["action"][:])
            
            num_frames = qpos.shape[0]
        
        # Add frames to dataset
        for i in range(num_frames):
            # Convert image from HWC to CHW format
            image = images[i]
            if image.shape[-1] == 3:  # HWC format
                image = np.transpose(image, (2, 0, 1))  # Convert to CHW
            
            frame = {
                "observation.state": qpos[i],
                "action": actions[i],
                "observation.images.camera": image,
            }
            
            dataset.add_frame(frame)
        
        # Save episode with task description
        dataset.save_episode(task=task)
    
    return dataset


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main(tyro.cli(Args))
