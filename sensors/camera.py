"""
Camera Module Placeholder.

This module is a minimal placeholder for future vision/camera-based focus tracking.
Camera processing is explicitly deferred and NOT implemented at this stage.
"""

from typing import Any, Dict


class CameraFeedPlaceholder:
    """Minimal placeholder class for future camera feed integration."""

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.is_active = False

    def start(self) -> bool:
        """Placeholder start method."""
        return False

    def stop(self) -> None:
        """Placeholder stop method."""
        self.is_active = False

    def get_status(self) -> Dict[str, Any]:
        """Return camera feature status."""
        return {
            "enabled": False,
            "status": "Placeholder (Vision processing disabled)",
            "camera_id": self.camera_id,
        }
