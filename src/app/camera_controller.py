"""
Camera controller for GestureFlow.

This module manages the Qt thread used by CameraWorker.
It keeps camera processing separate from the user-interface
thread.
"""

from PySide6.QtCore import QObject, QThread, Qt, Signal

from app.state import ApplicationState, can_transition


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

    state_changed = Signal(object)

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

        self.state = ApplicationState.INACTIVE

        self.paused = False

    def transition_to(self, target):
        """Apply a valid state transition and notify the UI."""

        if not can_transition(self.state, target):
            return False

        self.state = target
        self.paused = target == ApplicationState.PAUSED
        self.state_changed.emit(target)
        return True

    # =========================================================
    # Start
    # =========================================================

    def start(self):
        """
        Start the camera worker in a dedicated Qt thread.
        """

        if self.state not in (
            ApplicationState.INACTIVE,
            ApplicationState.ERROR,
        ):
            return False

        if self.state == ApplicationState.ERROR and (
            self.thread is not None or self.worker is not None
        ):
            return False

        if not self.transition_to(ApplicationState.STARTING):
            return False

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
            self.on_worker_error
        )

        self.worker.ready.connect(
            self.on_worker_ready
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

        self.paused = False

        self.thread.start()
        return True

    # =========================================================
    # Stop
    # =========================================================

    def stop(self):
        """
        Request the camera worker to stop.
        """

        if self.state == ApplicationState.INACTIVE:
            return False

        if self.state == ApplicationState.ERROR:
            if self.thread is None:
                self.transition_to(ApplicationState.INACTIVE)
                self.stopped.emit()
            elif self.worker is not None:
                self.stop_requested.emit()
            return True

        if self.state == ApplicationState.STOPPING:
            return True

        if not self.transition_to(ApplicationState.STOPPING):
            return False

        if self.worker is not None:
            self.stop_requested.emit()

        return True

        # -----------------------------------------------------
        # The worker will emit finished after cleanup.
        # -----------------------------------------------------

    def set_paused(self, paused):
        """Pause or resume gesture interaction without stopping capture."""

        if paused and self.state != ApplicationState.ACTIVE:
            return False

        if not paused and self.state != ApplicationState.PAUSED:
            return False

        target = (
            ApplicationState.PAUSED
            if paused
            else ApplicationState.ACTIVE
        )

        if not self.transition_to(target):
            return False

        if self.worker is not None:
            self.pause_requested.emit(paused)

        self.paused_changed.emit(paused)
        return True

    def toggle_paused(self):
        """Toggle the current gesture interaction pause state."""

        self.set_paused(not self.paused)

    # =========================================================
    # Worker completion
    # =========================================================

    def on_worker_ready(self):
        """Mark startup complete only after worker initialization."""

        if self.state == ApplicationState.STARTING:
            self.transition_to(ApplicationState.ACTIVE)
            self.started.emit()

    def on_worker_error(self, message):
        """Expose worker errors and move the pipeline to ERROR."""

        self.error.emit(message)

        if self.state in (
            ApplicationState.STARTING,
            ApplicationState.ACTIVE,
            ApplicationState.PAUSED,
            ApplicationState.STOPPING,
        ):
            self.transition_to(ApplicationState.ERROR)

    def on_worker_finished(self):
        """
        Handle completion of the camera worker.
        """

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

        if self.state == ApplicationState.STOPPING:
            self.transition_to(ApplicationState.INACTIVE)

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

        self.paused = False

    # =========================================================
    # Status
    # =========================================================

    def is_running(self):
        """
        Return whether camera processing is currently running.
        """

        return self.state in (
            ApplicationState.STARTING,
            ApplicationState.ACTIVE,
            ApplicationState.PAUSED,
            ApplicationState.STOPPING,
        )
