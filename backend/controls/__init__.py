"""
Robot control module for movement and manipulation.
"""

from .robot_control import RobotController

# Global singleton instance
robot_controller = RobotController()

__all__ = ["RobotController", "robot_controller"]
