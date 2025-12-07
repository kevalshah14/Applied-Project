"""
Data collection module for Dobot robot demonstrations.

This module provides tools for:
1. Collecting demonstration data in HDF5 format
2. Converting data to LeRobot format for pi0 fine-tuning
"""

from .collect_data import main as collect_main
from .convert_to_lerobot import main as convert_main

__all__ = ["collect_main", "convert_main"]
