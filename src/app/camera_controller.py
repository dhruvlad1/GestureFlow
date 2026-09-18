"""
Camera controller for GestureFlow.

This module manages the Qt thread used by CameraWorker.
It keeps camera processing separate from the user-interface
thread.
"""

from PySide6.QtCore import QObject, QThread, Qt, Signal


class CameraController(QObject):
    """
    Controls the lifecycle of the GestureFlow camera worker.
    """

    # ---------------------------------------------------------
    # Signals exposed to the UI.
    # ---------------------------------------------------------

    frame_ready = Signal(object)

    status_changed = Signal(str)

    gesture_changed = Signal(str)

    error = Signal(str)

    started = Signal()

    stopped = Signal()

    paused_changed = Signal(bool)

    stop_requested = Signal()

    pause_requested = Signal(bool)

    def __init__(self):
        """
        Initialize the camera controller.
        """

        super().__init__()

        # -----------------------------------------------------
        # Thread and worker references.
        # -----------------------------------------------------

        self.thread = None
        self.worker = None

        # -----------------------------------------------------
        # Runtime state.
        # -----------------------------------------------------

        self.running = False

        self.paused = False

    # =========================================================
    # Start
    # =========================================================

    def start(self):
        """
        Start the camera worker in a dedicated Qt thread.
        """

        if self.running:
            return

        # -----------------------------------------------------
        # Import here to keep the controller lightweight during
        # module import and to avoid unnecessary initialization.
        # -----------------------------------------------------

        from app.camera_worker import CameraWorker

        # -----------------------------------------------------
        # Create thread and worker.
        # -----------------------------------------------------

        self.thread = QThread()

        self.worker = CameraWorker()

        # -----------------------------------------------------
        # Move the worker to the dedicated thread.
        # -----------------------------------------------------

        self.worker.moveToThread(
            self.thread
        )

        # -----------------------------------------------------
        # Start the worker when the thread starts.
        # -----------------------------------------------------

        self.thread.started.connect(
            self.worker.start
        )

        # -----------------------------------------------------
        # Forward worker signals to the UI/controller.
        # -----------------------------------------------------

        self.worker.frame_ready.connect(
            self.frame_ready
        )

        self.worker.status_changed.connect(
            self.status_changed
        )

        self.worker.gesture_changed.connect(
            self.gesture_changed
        )

        self.worker.error.connect(
            self.error
        )

        # -----------------------------------------------------
        # Worker completion.
        # -----------------------------------------------------

        self.worker.finished.connect(
            self.on_worker_finished
        )

        self.stop_requested.connect(
            self.worker.stop,
            Qt.ConnectionType.QueuedConnection,
        )

        self.pause_requested.connect(
            self.worker.set_paused,
            Qt.ConnectionType.QueuedConnection,
        )

        self.thread.finished.connect(
            self.on_thread_finished
        )

        # -----------------------------------------------------
        # Start the Qt thread.
        # -----------------------------------------------------

        self.running = True
        self.paused = False

        self.thread.start()

        self.started.emit()

    # =========================================================
    # Stop
    # =========================================================

    def stop(self):
        """
        Request the camera worker to stop.
        """

        if not self.running:
            return

        if self.worker is not None:
            self.stop_requested.emit()

        # -----------------------------------------------------
        # The worker will emit finished after cleanup.
        # -----------------------------------------------------

    def set_paused(self, paused):
        """Pause or resume gesture interaction without stopping capture."""

        self.paused = paused

        if self.worker is not None:
            self.pause_requested.emit(paused)

        self.paused_changed.emit(paused)

    def toggle_paused(self):
        """Toggle the current gesture interaction pause state."""

        self.set_paused(not self.paused)

    # =========================================================
    # Worker completion
    # =========================================================

    def on_worker_finished(self):
        """
        Handle completion of the camera worker.
        """

        self.running = False

        # -----------------------------------------------------
        # Stop the Qt thread event loop.
        # -----------------------------------------------------

        if self.thread is not None:

            self.thread.quit()

        else:

            self.cleanup()

    def on_thread_finished(self):
        """
        Release thread and worker references after the thread
        has completely stopped.
        """

        self.cleanup()

        self.stopped.emit()

    # =========================================================
    # Cleanup
    # =========================================================

    def cleanup(self):
        """
        Release controller resources.
        """

        self.worker = None

        self.thread = None

        self.running = False

        self.paused = False

    # =========================================================
    # Status
    # =========================================================

    def is_running(self):
        """
        Return whether camera processing is currently running.
        """

        return self.running
