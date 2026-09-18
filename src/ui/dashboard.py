"""Compatibility export for the former dashboard widget."""

from ui.control_panel import ControlPanel
from app.camera_controller import CameraController


class Dashboard(ControlPanel):
    """Backward-compatible name for the compact GestureFlow panel."""

    def __init__(self, camera_controller=None):
        super().__init__(camera_controller or CameraController())
