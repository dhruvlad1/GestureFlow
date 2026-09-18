"""Lifecycle tests for the camera worker and controller."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from app.camera_controller import CameraController
from app.camera_worker import CameraWorker


def test_worker_stop_releases_resources_and_finishes_once():
    worker = CameraWorker()
    capture = MagicMock()
    worker.cap = capture
    hand_detector = MagicMock()
    worker.hand_detector = hand_detector
    worker.running = True
    frame_timer = MagicMock()
    worker.frame_timer = frame_timer

    finished = MagicMock()
    worker.finished.connect(finished)

    worker.stop()
    worker.stop()

    capture.release.assert_called_once()
    hand_detector.close.assert_called_once()
    frame_timer.stop.assert_called_once()
    finished.assert_called_once_with()
    assert not worker.running


def test_worker_start_opens_pipeline_and_starts_timer():
    worker = CameraWorker()
    capture = MagicMock()
    capture.isOpened.return_value = True
    timer = MagicMock()

    with patch("app.camera_worker.cv2.VideoCapture", return_value=capture), \
            patch("app.camera_worker.HandDetector"), \
            patch("app.camera_worker.GestureDetector"), \
            patch("app.camera_worker.CursorController"), \
            patch("app.camera_worker.Overlay"), \
            patch("app.camera_worker.QTimer", return_value=timer):
        worker.start()

    assert worker.running
    capture.isOpened.assert_called_once_with()
    timer.start.assert_called_once_with()

    worker.stop()


def test_worker_reports_unavailable_camera_and_releases_capture():
    worker = CameraWorker()
    capture = MagicMock()
    capture.isOpened.return_value = False
    finished = MagicMock()
    worker.finished.connect(finished)

    with patch("app.camera_worker.cv2.VideoCapture", return_value=capture):
        worker.start()

    capture.release.assert_called_once()
    finished.assert_called_once_with()
    assert not worker.running


def test_controller_rejects_duplicate_start():
    app = QCoreApplication.instance() or QCoreApplication([])
    controller = CameraController()

    with patch("app.camera_worker.CameraWorker") as worker_type:
        worker = worker_type.return_value
        controller.start()
        first_thread = controller.thread
        first_worker = controller.worker
        controller.start()

    assert controller.is_running()
    assert controller.thread is first_thread
    assert controller.worker is first_worker
    assert worker_type.call_count == 1

    controller.thread.quit()
    controller.thread.wait()
    app.processEvents()