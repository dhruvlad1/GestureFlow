"""Compact runtime settings for GestureFlow."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from utils import config


class SettingsDialog(QDialog):
    """Expose the cursor controls that can be changed safely at runtime."""

    settings_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GestureFlow settings")
        self.setMinimumWidth(390)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        message = QLabel("Tune how hand movement maps to your cursor.")
        message.setObjectName("dialogMessage")
        message.setWordWrap(True)
        layout.addWidget(message)

        form = QFormLayout()
        form.setVerticalSpacing(16)
        form.setHorizontalSpacing(18)

        self.smoothing_slider, self.smoothing_value = self.create_slider(
            10, 100, round(config.CURSOR_SMOOTHING * 100), "%"
        )
        self.margin_slider, self.margin_value = self.create_slider(
            0, 35, round(config.CAMERA_MIN_X * 100), "%"
        )
        self.padding_slider, self.padding_value = self.create_slider(
            0, 30, config.SCREEN_PADDING, " px"
        )

        form.addRow("Responsiveness", self.slider_row(self.smoothing_slider, self.smoothing_value))
        form.addRow("Camera margin", self.slider_row(self.margin_slider, self.margin_value))
        form.addRow("Screen padding", self.slider_row(self.padding_slider, self.padding_value))
        layout.addLayout(form)
        layout.addStretch()

        actions = QHBoxLayout()
        actions.addStretch()
        reset_button = QPushButton("Reset")
        reset_button.setObjectName("textButton")
        reset_button.clicked.connect(self.reset_values)
        actions.addWidget(reset_button)
        close_button = QPushButton("Done")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.close)
        actions.addWidget(close_button)
        layout.addLayout(actions)

        self.smoothing_slider.valueChanged.connect(self.emit_settings)
        self.margin_slider.valueChanged.connect(self.emit_settings)
        self.padding_slider.valueChanged.connect(self.emit_settings)

    def create_slider(self, minimum, maximum, value, suffix):
        slider = QSlider()
        slider.setOrientation(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        value_label = QLabel(f"{value}{suffix}")
        slider.value_label = value_label
        slider.suffix = suffix
        slider.valueChanged.connect(
            lambda current: value_label.setText(f"{current}{suffix}")
        )
        return slider, value_label

    @staticmethod
    def slider_row(slider, value_label):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(slider, 1)
        layout.addWidget(value_label)
        return row

    def reset_values(self):
        self.smoothing_slider.setValue(round(config.CURSOR_SMOOTHING * 100))
        self.margin_slider.setValue(round(config.CAMERA_MIN_X * 100))
        self.padding_slider.setValue(config.SCREEN_PADDING)

    def emit_settings(self):
        self.settings_changed.emit(
            {
                "smoothing": self.smoothing_slider.value() / 100,
                "camera_min": self.margin_slider.value() / 100,
                "screen_padding": self.padding_slider.value(),
            }
        )
