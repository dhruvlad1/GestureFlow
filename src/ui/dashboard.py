"""
GestureFlow dashboard.

This module contains the main dashboard displayed inside
the GestureFlow desktop application.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.camera_controller import CameraController
from ui.camera_view import CameraView


class Dashboard(QWidget):
    """
    Main dashboard for GestureFlow.
    """

    def __init__(self):
        """
        Initialize the dashboard.
        """

        super().__init__()

        # -----------------------------------------------------
        # Camera controller.
        # -----------------------------------------------------

        self.camera_controller = CameraController()

        # -----------------------------------------------------
        # Main layout.
        # -----------------------------------------------------

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            32,
            32,
            32,
            32,
        )

        self.layout.setSpacing(
            24
        )

        # -----------------------------------------------------
        # Header.
        # -----------------------------------------------------

        title = QLabel(
            "GestureFlow"
        )

        title.setStyleSheet(
            """
            font-size: 30px;
            font-weight: 600;
            """
        )

        subtitle = QLabel(
            "Touchless computer interaction using hand gestures"
        )

        subtitle.setStyleSheet(
            """
            font-size: 14px;
            color: #777777;
            """
        )

        self.layout.addWidget(
            title
        )

        self.layout.addWidget(
            subtitle
        )

        # -----------------------------------------------------
        # Camera preview.
        # -----------------------------------------------------

        camera_frame = QFrame()

        camera_layout = QVBoxLayout(
            camera_frame
        )

        camera_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.camera_view = CameraView()

        camera_layout.addWidget(
            self.camera_view
        )

        self.layout.addWidget(
            camera_frame
        )

        # -----------------------------------------------------
        # Status cards.
        # -----------------------------------------------------

        cards_layout = QGridLayout()

        cards_layout.setSpacing(
            16
        )

        self.camera_card, self.camera_status = (
            self.create_status_card(
                "Camera",
                "Not Started",
            )
        )

        self.tracking_card, self.tracking_status = (
            self.create_status_card(
                "Hand Tracking",
                "Inactive",
            )
        )

        self.gesture_card, self.gesture_status = (
            self.create_status_card(
                "Gesture Control",
                "Inactive",
            )
        )

        cards_layout.addWidget(
            self.camera_card,
            0,
            0,
        )

        cards_layout.addWidget(
            self.tracking_card,
            0,
            1,
        )

        cards_layout.addWidget(
            self.gesture_card,
            0,
            2,
        )

        self.layout.addLayout(
            cards_layout
        )

        # -----------------------------------------------------
        # Quick controls.
        # -----------------------------------------------------

        controls_title = QLabel(
            "Quick Controls"
        )

        controls_title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: 600;
            """
        )

        self.layout.addWidget(
            controls_title
        )

        self.start_button = QPushButton(
            "Start Gesture Control"
        )

        self.start_button.setMinimumHeight(
            48
        )

        self.stop_button = QPushButton(
            "Stop Gesture Control"
        )

        self.stop_button.setMinimumHeight(
            48
        )

        self.stop_button.setEnabled(
            False
        )

        self.layout.addWidget(
            self.start_button
        )

        self.layout.addWidget(
            self.stop_button
        )

        # -----------------------------------------------------
        # Connect buttons.
        # -----------------------------------------------------

        self.start_button.clicked.connect(
            self.start_camera
        )

        self.stop_button.clicked.connect(
            self.stop_camera
        )

        # -----------------------------------------------------
        # Connect camera controller signals.
        # -----------------------------------------------------

        self.camera_controller.frame_ready.connect(
            self.camera_view.display_frame
        )

        self.camera_controller.status_changed.connect(
            self.update_tracking_status
        )

        self.camera_controller.gesture_changed.connect(
            self.update_gesture_status
        )

        self.camera_controller.error.connect(
            self.handle_camera_error
        )

        self.camera_controller.started.connect(
            self.on_camera_started
        )

        self.camera_controller.stopped.connect(
            self.on_camera_stopped
        )

        # -----------------------------------------------------
        # Gesture information.
        # -----------------------------------------------------

        gesture_title = QLabel(
            "Supported Gestures"
        )

        gesture_title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: 600;
            """
        )

        self.layout.addWidget(
            gesture_title
        )

        gesture_info = QLabel(
            "Left Click  •  Right Click  •  Double Click  •  "
            "Drag  •  Vertical Scroll  •  Horizontal Scroll"
        )

        gesture_info.setWordWrap(
            True
        )

        gesture_info.setStyleSheet(
            """
            font-size: 14px;
            color: #666666;
            """
        )

        self.layout.addWidget(
            gesture_info
        )

        # -----------------------------------------------------
        # Keep remaining space at the bottom.
        # -----------------------------------------------------

        self.layout.addStretch()

    # =========================================================
    # Camera controls
    # =========================================================

    def start_camera(self):
        """
        Start the GestureFlow camera worker.
        """

        self.camera_controller.start()

    def stop_camera(self):
        """
        Stop the GestureFlow camera worker.
        """

        self.camera_controller.stop()

    # =========================================================
    # Camera state callbacks
    # =========================================================

    def on_camera_started(self):
        """
        Update the dashboard after camera processing starts.
        """

        self.start_button.setEnabled(
            False
        )

        self.stop_button.setEnabled(
            True
        )

        self.camera_status.setText(
            "Active"
        )

        self.gesture_status.setText(
            "Active"
        )

    def on_camera_stopped(self):
        """
        Update the dashboard after camera processing stops.
        """

        self.start_button.setEnabled(
            True
        )

        self.stop_button.setEnabled(
            False
        )

        self.camera_status.setText(
            "Not Started"
        )

        self.tracking_status.setText(
            "Inactive"
        )

        self.gesture_status.setText(
            "Inactive"
        )

        self.camera_view.clear_frame()

    # =========================================================
    # Status updates
    # =========================================================

    def update_tracking_status(
        self,
        status,
    ):
        """
        Update the hand-tracking status card.
        """

        self.tracking_status.setText(
            status
        )

    def update_gesture_status(
        self,
        gesture,
    ):
        """
        Update the gesture status card.
        """

        self.gesture_status.setText(
            gesture
        )

    def handle_camera_error(
        self,
        message,
    ):
        """
        Display camera errors in the dashboard status.
        """

        self.camera_status.setText(
            "Error"
        )

        self.tracking_status.setText(
            message
        )

    # =========================================================
    # Status card creation
    # =========================================================

    def create_status_card(
        self,
        title,
        status,
    ):
        """
        Create a reusable status card.

        Returns
        -------
        tuple
            The card widget and its status label.
        """

        card = QFrame()

        card.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        card.setMinimumHeight(
            110
        )

        layout = QVBoxLayout(
            card
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label = QLabel(
            title
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label.setStyleSheet(
            """
            font-size: 15px;
            font-weight: 600;
            """
        )

        status_label = QLabel(
            status
        )

        status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        status_label.setStyleSheet(
            """
            font-size: 13px;
            color: #777777;
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            status_label
        )

        return card, status_label
