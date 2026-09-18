"""Small placeholder settings window for GestureFlow."""

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class SettingsDialog(QDialog):
    """Provide a compact home for future user-configurable settings."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GestureFlow Settings")
        self.setMinimumSize(320, 180)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(8)

        title = QLabel("Settings")
        title.setObjectName("dialogTitle")

        message = QLabel(
            "GestureFlow settings will be available here in a future update."
        )
        message.setObjectName("dialogMessage")
        message.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
