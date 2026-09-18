"""
Main application window for GestureFlow.

This module contains the primary Qt window used by the
GestureFlow desktop application.
"""

from PySide6.QtWidgets import (
    QMainWindow,
)

from ui.dashboard import Dashboard
from ui.styles import get_app_style
from utils.config import WINDOW_TITLE


class MainWindow(QMainWindow):
    """
    Main desktop window for GestureFlow.
    """

    def __init__(self):
        """
        Initialize the main application window.
        """

        super().__init__()

        # -----------------------------------------------------
        # Basic window configuration.
        # -----------------------------------------------------

        self.setWindowTitle(
            WINDOW_TITLE
        )

        self.setMinimumSize(
            900,
            600,
        )

        # -----------------------------------------------------
        # Apply the global application stylesheet.
        # -----------------------------------------------------

        self.setStyleSheet(
            get_app_style()
        )

        # -----------------------------------------------------
        # Create the dashboard.
        # -----------------------------------------------------

        self.dashboard = Dashboard()

        # -----------------------------------------------------
        # Set the dashboard as the central widget.
        # -----------------------------------------------------

        self.setCentralWidget(
            self.dashboard
        )
