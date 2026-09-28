"""Primary GestureFlow workspace and live tracking status."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.state import ApplicationState
from ui.camera_view import CameraView


class ControlPanel(QWidget):
    """Main workspace for the camera pipeline and its current state."""

    show_camera_requested = Signal()
    settings_requested = Signal()

    def __init__(self, camera_controller):
        super().__init__()

        self.camera_controller = camera_controller
        self.paused = False

        self.setObjectName("controlPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(16)

        layout.addLayout(self.create_header())
        layout.addWidget(self.create_camera_section(), 1)
        layout.addWidget(self.create_status_section())
        layout.addLayout(self.create_bottom_section())

        self.connect_signals()
        self.update_state(ApplicationState.INACTIVE)

    def create_header(self):
        header = QHBoxLayout()
        header.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("GestureFlow")
        title.setObjectName("panelTitle")

        subtitle = QLabel("Touchless cursor control using your hand")
        subtitle.setObjectName("panelSubtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        header.addStretch()

        self.status_indicator = QLabel("●  Ready")
        self.status_indicator.setObjectName("panelStatus")
        header.addWidget(
            self.status_indicator,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        return header

    def create_camera_section(self):
        section = QFrame()
        section.setObjectName("cameraSection")

        layout = QVBoxLayout(section)
        layout.setContentsMargins(10, 10, 10, 10)

        self.camera_view = CameraView()
        self.camera_view.setMinimumSize(420, 280)
        layout.addWidget(self.camera_view)
        return section

    def create_status_section(self):
        section = QFrame()
        section.setObjectName("statusSection")

        layout = QHBoxLayout(section)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(20)

        self.control_status = self.create_status_row("Cursor control", "Inactive")
        self.camera_status = self.create_status_row("Camera", "Inactive")
        self.hand_status = self.create_status_row("Hand", "Inactive")

        for row in (
            self.control_status[0],
            self.camera_status[0],
            self.hand_status[0],
        ):
            layout.addLayout(row, 1)

        return section

    def create_status_row(self, title, value):
        row = QVBoxLayout()
        row.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("statusTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statusValue")
        value_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        row.addWidget(title_label)
        row.addWidget(value_label)
        return row, value_label

    def create_bottom_section(self):
        section = QHBoxLayout()
        section.setSpacing(18)
        section.addLayout(self.create_gesture_section(), 1)
        section.addLayout(self.create_action_section(), 0)
        return section

    def create_gesture_section(self):
        section = QVBoxLayout()
        section.setSpacing(3)

        heading = QLabel("Current gesture")
        heading.setObjectName("sectionLabel")

        self.gesture_value = QLabel("Waiting for a hand")
        self.gesture_value.setObjectName("gestureValue")
        self.gesture_value.setWordWrap(True)

        section.addWidget(heading)
        section.addWidget(self.gesture_value)
        return section

    def create_action_section(self):
        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.start_button = QPushButton("Start tracking")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(40)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("secondaryButton")
        self.pause_button.setMinimumHeight(40)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("secondaryButton")
        self.settings_button.setMinimumHeight(40)

        actions.addWidget(self.start_button)
        actions.addWidget(self.pause_button)
        actions.addWidget(self.settings_button)
        return actions

    def connect_signals(self):
        self.start_button.clicked.connect(self.start_camera)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.settings_button.clicked.connect(self.settings_requested)

        self.camera_controller.state_changed.connect(self.update_state)
        self.camera_controller.status_changed.connect(self.update_hand_status)
        self.camera_controller.gesture_changed.connect(self.update_gesture)
        self.camera_controller.error.connect(self.update_error)

    def start_camera(self):
        self.camera_controller.start()

    def toggle_pause(self):
        self.camera_controller.toggle_paused()

    def update_state(self, state):
        starting = state == ApplicationState.STARTING
        active = state == ApplicationState.ACTIVE
        paused = state == ApplicationState.PAUSED
        stopping = state == ApplicationState.STOPPING
        error = state == ApplicationState.ERROR

        self.start_button.setEnabled(
            state in (ApplicationState.INACTIVE, ApplicationState.ERROR)
        )
        self.pause_button.setEnabled(active or paused)
        self.paused = paused
        self.pause_button.setText("Resume" if paused else "Pause")

        if starting:
            control_value = "Initializing"
            camera_value = "Initializing"
            status_text = "●  Initializing"
        elif active:
            control_value = "Active"
            camera_value = "Ready"
            status_text = "●  Tracking active"
        elif paused:
            control_value = "Paused"
            camera_value = "Ready"
            status_text = "●  Tracking paused"
        elif stopping:
            control_value = "Stopping"
            camera_value = "Stopping"
            status_text = "●  Stopping"
        elif error:
            control_value = "Unavailable"
            camera_value = "Unavailable"
            status_text = "●  Camera unavailable"
        else:
            control_value = "Inactive"
            camera_value = "Inactive"
            status_text = "●  Ready"

        self.set_value(self.control_status[1], control_value)
        self.set_value(self.camera_status[1], camera_value)
        self.status_indicator.setText(status_text)

        if state == ApplicationState.INACTIVE:
            self.paused = False
            self.pause_button.setText("Pause")
            self.set_value(self.hand_status[1], "Inactive")
            self.gesture_value.setText("Waiting for a hand")
        elif error:
            self.set_value(self.hand_status[1], "Unavailable")

    def update_hand_status(self, status):
        self.set_value(self.hand_status[1], status)

    def update_gesture(self, gesture):
        self.gesture_value.setText(gesture.title())

    def update_error(self, message):
        self.set_value(self.camera_status[1], "Unavailable")
        self.set_value(self.hand_status[1], "Check camera permissions")
        self.status_indicator.setText("●  Camera unavailable")

    def display_frame(self, frame):
        """Display a processed frame in the main workspace."""

        self.camera_view.display_frame(frame)

    def clear_frame(self):
        """Restore the camera placeholder after stopping."""

        self.camera_view.clear_frame()

    @staticmethod
    def set_value(label, value):
        label.setText(value)
        label.setProperty(
            "state",
            "active" if value in ("Active", "Ready", "Detected") else "muted",
        )
        label.style().unpolish(label)
        label.style().polish(label)
