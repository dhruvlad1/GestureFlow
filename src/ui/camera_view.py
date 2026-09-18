"""
Camera preview widget for GestureFlow.

This module provides a reusable Qt widget for displaying
camera frames inside the desktop application.
"""

import cv2

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel


class CameraView(QLabel):
    """
    Displays OpenCV camera frames inside a Qt interface.
    """

    def __init__(self):
        """
        Initialize the camera preview widget.
        """

        super().__init__()

        # -----------------------------------------------------
        # Basic widget configuration.
        # -----------------------------------------------------

        self.setMinimumSize(
            640,
            360,
        )

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setText(
            "Camera preview"
        )

        # -----------------------------------------------------
        # Prevent the preview from expanding indefinitely.
        # -----------------------------------------------------

        self.setScaledContents(
            False
        )

    def display_frame(self, frame):
        """
        Display an OpenCV BGR frame inside the Qt widget.

        Parameters
        ----------
        frame:
            OpenCV image in BGR format.
        """

        if frame is None:
            return

        # -----------------------------------------------------
        # Convert BGR to RGB.
        #
        # OpenCV uses BGR while Qt expects RGB.
        # -----------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        height, width, channels = rgb_frame.shape

        bytes_per_line = (
            channels * width
        )

        # -----------------------------------------------------
        # Create a Qt image from the OpenCV frame.
        # -----------------------------------------------------

        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )

        # -----------------------------------------------------
        # Scale the image while preserving its aspect ratio.
        # -----------------------------------------------------

        pixmap = QPixmap.fromImage(
            image
        )

        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(
            scaled_pixmap
        )

    def clear_frame(self):
        """
        Clear the current camera frame and restore the
        placeholder text.
        """

        self.clear()

        self.setText(
            "Camera preview"
        )
