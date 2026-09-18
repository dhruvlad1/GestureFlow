"""Main window and desktop lifecycle coordinator for GestureFlow."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)

from app.camera_controller import CameraController
from ui.camera_preview_window import CameraPreviewWindow
from ui.control_panel import ControlPanel
from ui.settings import SettingsDialog
from ui.styles import get_app_style
from utils.config import WINDOW_TITLE


class MainWindow(QMainWindow):
    """Floating GestureFlow control panel and tray integration."""

    def __init__(self, application=None):
        super().__init__()

        self.application = application or QApplication.instance()
        self.camera_controller = CameraController()
        self.preview_window = CameraPreviewWindow()
        self.preview_window.setStyleSheet(get_app_style())
        self.settings_dialog = None
        self.allow_close = False
        self.exit_requested = False

        self.setObjectName("mainWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(self.tray_icon())
        self.setMinimumSize(320, 360)
        self.setMaximumSize(420, 540)
        self.resize(360, 430)
        self.setStyleSheet(get_app_style())

        self.control_panel = ControlPanel(self.camera_controller)
        self.setCentralWidget(self.control_panel)

        self.camera_controller.frame_ready.connect(
            self.preview_window.display_frame
        )
        self.camera_controller.stopped.connect(self.finish_exit)
        self.camera_controller.stopped.connect(self.on_camera_stopped)
        self.control_panel.show_camera_requested.connect(
            self.toggle_camera_preview
        )
        self.control_panel.settings_requested.connect(self.show_settings)
        self.preview_window.hidden_by_user.connect(
            lambda: self.control_panel.set_camera_visible(False)
        )

        self.create_tray_icon()

    def tray_icon(self):
        """Use a platform icon without introducing an image dependency."""

        return self.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )

    def create_tray_icon(self):
        self.tray = QSystemTrayIcon(self.tray_icon(), self)
        self.tray.setToolTip("GestureFlow")

        menu = QMenu()

        title_action = QAction("GestureFlow", self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        self.tray_status_action = QAction("Status: Inactive", self)
        self.tray_status_action.setEnabled(False)
        menu.addAction(self.tray_status_action)

        self.tray_pause_action = QAction("Pause", self)
        self.tray_pause_action.triggered.connect(
            self.control_panel.toggle_pause
        )
        menu.addAction(self.tray_pause_action)

        show_panel_action = QAction("Show Control Panel", self)
        show_panel_action.triggered.connect(self.show_panel)
        menu.addAction(show_panel_action)

        self.tray_camera_action = QAction("Show Camera", self)
        self.tray_camera_action.triggered.connect(
            self.toggle_camera_preview
        )
        menu.addAction(self.tray_camera_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        stop_action = QAction("Stop Gesture Control", self)
        stop_action.triggered.connect(self.stop_camera)
        menu.addAction(stop_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)

        self.camera_controller.started.connect(
            lambda: self.update_tray_state("Active")
        )
        self.camera_controller.stopped.connect(
            lambda: self.update_tray_state("Inactive")
        )
        self.camera_controller.paused_changed.connect(
            self.update_pause_tray_state
        )

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def toggle_camera_preview(self):
        if self.preview_window.isVisible():
            self.preview_window.hide()
            self.control_panel.set_camera_visible(False)
        elif self.camera_controller.is_running():
            self.preview_window.show()
            self.preview_window.raise_()
            self.preview_window.activateWindow()
            self.control_panel.set_camera_visible(True)

        self.update_camera_tray_text()

    def show_panel(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.setStyleSheet(get_app_style())

        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def stop_camera(self):
        self.camera_controller.stop()

    def on_camera_stopped(self):
        self.preview_window.clear_frame()
        self.preview_window.hide()
        self.control_panel.set_camera_visible(False)
        self.update_camera_tray_text()

    def update_tray_state(self, state):
        self.tray_status_action.setText(f"Status: {state}")
        self.tray_pause_action.setEnabled(state != "Inactive")
        self.update_camera_tray_text()

    def update_pause_tray_state(self, paused):
        self.tray_pause_action.setText("Resume" if paused else "Pause")

    def update_camera_tray_text(self):
        visible = self.preview_window.isVisible()
        text = "Hide Camera" if visible else "Show Camera"
        self.tray_camera_action.setText(text)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_panel()

    def exit_application(self):
        self.exit_requested = True
        self.allow_close = True
        self.preview_window.hide()
        self.tray.hide()

        if self.camera_controller.is_running():
            self.camera_controller.stop()
        else:
            self.finish_exit()

    def finish_exit(self):
        if self.exit_requested and self.application is not None:
            self.application.quit()

    def closeEvent(self, event):
        if self.allow_close or not QSystemTrayIcon.isSystemTrayAvailable():
            self.exit_application()
            event.accept()
            return

        event.ignore()
        self.hide()
