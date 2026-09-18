"""Compact floating control panel for GestureFlow."""

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

class ControlPanel(QWidget):
    """Small utility panel that controls and reports application state."""

    show_camera_requested = Signal()
    settings_requested = Signal()

    def __init__(self, camera_controller):
        super().__init__()

        self.camera_controller = camera_controller
        self.camera_visible = False
        self.paused = False

        self.setObjectName("controlPanel")
        self.setMinimumSize(320, 360)
        self.setMaximumSize(420, 540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        layout.addLayout(self.create_header())
        layout.addWidget(self.create_status_section())
        layout.addWidget(self.create_divider())
        layout.addLayout(self.create_gesture_section())
        layout.addStretch()
        layout.addLayout(self.create_start_stop_row())
        layout.addLayout(self.create_action_row())
        layout.addWidget(self.create_settings_button())

        self.connect_signals()
        self.update_running_state(False)

    def create_header(self):
        header = QHBoxLayout()
        header.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("GestureFlow")
        title.setObjectName("panelTitle")

        subtitle = QLabel("Touchless control")
        subtitle.setObjectName("panelSubtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        header.addStretch()

        self.status_indicator = QLabel("●  Inactive")
        self.status_indicator.setObjectName("panelStatus")
        header.addWidget(
            self.status_indicator,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        return header

    def create_status_section(self):
        section = QFrame()
        section.setObjectName("statusSection")

        layout = QVBoxLayout(section)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        self.control_status = self.create_status_row(
            "Gesture Control",
            "Inactive",
        )
        self.camera_status = self.create_status_row(
            "Camera",
            "Inactive",
        )
        self.hand_status = self.create_status_row(
            "Hand Tracking",
            "Inactive",
        )

        for row in (
            self.control_status[0],
            self.camera_status[0],
            self.hand_status[0],
        ):
            layout.addLayout(row)

        return section

    def create_status_row(self, title, value):
        row = QHBoxLayout()
        row.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("statusTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statusValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        row.addWidget(title_label)
        row.addWidget(value_label)
        return row, value_label

    def create_divider(self):
        divider = QFrame()
        divider.setObjectName("panelDivider")
        divider.setFixedHeight(1)
        return divider

    def create_gesture_section(self):
        section = QVBoxLayout()
        section.setSpacing(3)

        heading = QLabel("Current Gesture")
        heading.setObjectName("sectionLabel")

        self.gesture_value = QLabel("Waiting")
        self.gesture_value.setObjectName("gestureValue")
        self.gesture_value.setWordWrap(True)

        section.addWidget(heading)
        section.addWidget(self.gesture_value)
        return section

    def create_action_row(self):
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("secondaryButton")
        self.pause_button.setMinimumHeight(38)

        self.camera_button = QPushButton("Show Camera")
        self.camera_button.setObjectName("secondaryButton")
        self.camera_button.setMinimumHeight(38)

        actions.addWidget(self.pause_button)
        actions.addWidget(self.camera_button)
        return actions

    def create_start_stop_row(self):
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.start_button = QPushButton("Start Gesture Control")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(38)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("secondaryButton")
        self.stop_button.setMinimumHeight(38)

        actions.addWidget(self.start_button, 2)
        actions.addWidget(self.stop_button, 1)
        return actions

    def create_settings_button(self):
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("textButton")
        self.settings_button.setMinimumHeight(34)
        return self.settings_button

    def connect_signals(self):
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.camera_button.clicked.connect(self.show_camera_requested)
        self.settings_button.clicked.connect(self.settings_requested)

        self.camera_controller.state_changed.connect(
            self.update_state
        )
        self.camera_controller.status_changed.connect(
            self.update_hand_status
        )
        self.camera_controller.gesture_changed.connect(
            self.update_gesture
        )
        self.camera_controller.error.connect(
            self.update_error
        )

    def toggle_pause(self):
        self.camera_controller.toggle_paused()

    def start_camera(self):
        self.camera_controller.start()

    def stop_camera(self):
        self.camera_controller.stop()

    def update_running_state(self, running):
        state = (
            ApplicationState.ACTIVE
            if running
            else ApplicationState.INACTIVE
        )
        self.update_state(state)

    def update_state(self, state):
        starting = state == ApplicationState.STARTING
        active = state == ApplicationState.ACTIVE
        paused = state == ApplicationState.PAUSED
        stopping = state == ApplicationState.STOPPING
        error = state == ApplicationState.ERROR

        self.start_button.setEnabled(
            state in (
                ApplicationState.INACTIVE,
                ApplicationState.ERROR,
            )
        )
        self.stop_button.setEnabled(
            state in (
                ApplicationState.STARTING,
                ApplicationState.ACTIVE,
                ApplicationState.PAUSED,
                ApplicationState.STOPPING,
            )
        )
        self.pause_button.setEnabled(active or paused)
        self.camera_button.setEnabled(active or paused)

        self.paused = paused
        self.pause_button.setText("Resume" if paused else "Pause")

        if starting:
            control_value = "Starting"
            camera_value = "Starting"
            status_text = "●  Starting"
        elif active:
            control_value = "Active"
            camera_value = "Active"
            status_text = "●  Active"
        elif paused:
            control_value = "Paused"
            camera_value = "Active"
            status_text = "●  Paused"
        elif stopping:
            control_value = "Stopping"
            camera_value = "Stopping"
            status_text = "●  Stopping"
        elif error:
            control_value = "Error"
            camera_value = "Error"
            status_text = "●  Error"
        else:
            control_value = "Inactive"
            camera_value = "Inactive"
            status_text = "●  Inactive"

        self.set_value(self.control_status[1], control_value)
        self.set_value(self.camera_status[1], camera_value)
        self.status_indicator.setText(status_text)

        if state == ApplicationState.INACTIVE:
            self.paused = False
            self.pause_button.setText("Pause")
            self.set_value(self.camera_status[1], "Inactive")
            self.set_value(self.hand_status[1], "Inactive")
            self.gesture_value.setText("Waiting")

        elif error:
            self.set_value(self.hand_status[1], "Pipeline error")

    def update_hand_status(self, status):
        self.set_value(self.hand_status[1], status)

    def update_gesture(self, gesture):
        self.gesture_value.setText(gesture.title())

    def update_error(self, message):
        self.set_value(self.camera_status[1], "Error")
        self.set_value(self.hand_status[1], message)
        self.status_indicator.setText("●  Error")

    def set_camera_visible(self, visible):
        self.camera_visible = visible
        self.camera_button.setText(
            "Hide Camera" if visible else "Show Camera"
        )

    @staticmethod
    def set_value(label, value):
        label.setText(value)
        label.setProperty(
            "state",
            "active" if value in ("Active", "Detected") else "muted",
        )
        label.style().unpolish(label)
        label.style().polish(label)
