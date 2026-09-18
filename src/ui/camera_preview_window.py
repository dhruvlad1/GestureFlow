"""Independent camera preview window for GestureFlow."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow

from ui.camera_view import CameraView


class CameraPreviewWindow(QMainWindow):
    """Small, independent preview that does not control camera processing."""

    hidden_by_user = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GestureFlow Camera")
        self.setObjectName("cameraPreviewWindow")
        self.setMinimumSize(360, 260)
        self.resize(520, 360)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.camera_view = CameraView()
        self.camera_view.setMinimumSize(320, 220)
        self.setCentralWidget(self.camera_view)

    def display_frame(self, frame):
        """Forward a processed frame to the preview widget."""

        self.camera_view.display_frame(frame)

    def clear_frame(self):
        """Clear the preview without affecting camera processing."""

        self.camera_view.clear_frame()

    def closeEvent(self, event):
        """Hide the preview so closing it does not stop GestureFlow."""

        event.ignore()
        self.hide()
        self.hidden_by_user.emit()
