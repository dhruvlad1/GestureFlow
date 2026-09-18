"""
Unit tests for GestureFlow hand tracking.

These tests mock the MediaPipe detector so that they do not
require a webcam or load the actual hand landmark model.

Run with:

    python -m pytest tests/test_hand_detector.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np


# -------------------------------------------------------------
# Make the src directory importable when pytest is run from
# the project root.
# -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from hand_tracking.hand_detector import HandDetector


# =============================================================
# Test helpers
# =============================================================


def create_mock_detector():
    """
    Create a HandDetector instance without initializing the
    real MediaPipe model.

    This allows the tests to focus on the wrapper behavior.
    """

    detector = HandDetector.__new__(HandDetector)

    detector.detector = MagicMock()

    return detector


def create_test_frame():
    """
    Create a small synthetic BGR OpenCV frame.
    """

    return np.zeros(
        (100, 100, 3),
        dtype=np.uint8,
    )


# =============================================================
# Initialization tests
# =============================================================


@patch(
    "hand_tracking.hand_detector.vision.HandLandmarker.create_from_options"
)
def test_detector_initializes(mock_create):
    """
    HandDetector should create the MediaPipe HandLandmarker
    using the configured options.
    """

    mock_detector = MagicMock()

    mock_create.return_value = mock_detector

    detector = HandDetector()

    assert detector.detector is mock_detector

    mock_create.assert_called_once()


@patch(
    "hand_tracking.hand_detector.vision.HandLandmarker.create_from_options"
)
def test_detector_uses_custom_configuration(mock_create):
    """
    Custom constructor values should be passed to MediaPipe.
    """

    mock_detector = MagicMock()

    mock_create.return_value = mock_detector

    detector = HandDetector(
        max_num_hands=2,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.85,
    )

    assert detector.detector is mock_detector

    mock_create.assert_called_once()

    options = mock_create.call_args.args[0]

    assert options.num_hands == 2
    assert options.min_hand_detection_confidence == 0.8
    assert options.min_hand_presence_confidence == 0.85
    assert options.min_tracking_confidence == 0.85


# =============================================================
# Frame conversion tests
# =============================================================


def test_find_hands_converts_bgr_to_rgb():
    """
    OpenCV provides BGR frames while MediaPipe expects RGB.

    Verify that find_hands() performs the conversion.
    """

    detector = create_mock_detector()

    detector.detector.detect_for_video.return_value = "result"

    # ---------------------------------------------------------
    # Create a frame with clearly different B, G and R values.
    # ---------------------------------------------------------

    frame = np.array(
        [
            [
                [10, 20, 30],
            ]
        ],
        dtype=np.uint8,
    )

    with patch(
        "hand_tracking.hand_detector.mp.Image"
    ) as mock_image:

        mock_image_instance = MagicMock()

        mock_image.return_value = mock_image_instance

        result = detector.find_hands(
            frame,
            100,
        )

    assert result == "result"

    mock_image.assert_called_once()

    call_kwargs = mock_image.call_args.kwargs

    rgb_data = call_kwargs["data"]

    assert rgb_data[0, 0].tolist() == [30, 20, 10]


# =============================================================
# MediaPipe image creation tests
# =============================================================


def test_find_hands_creates_mp_image():
    """
    find_hands() should create an mp.Image from the RGB frame.
    """

    detector = create_mock_detector()

    detector.detector.detect_for_video.return_value = "result"

    frame = create_test_frame()

    with patch(
        "hand_tracking.hand_detector.mp.Image"
    ) as mock_image:

        mock_image.return_value = MagicMock()

        detector.find_hands(
            frame,
            123,
        )

    mock_image.assert_called_once()

    call_kwargs = mock_image.call_args.kwargs

    assert (
        call_kwargs["image_format"]
        == detector_module_image_format()
    )


def detector_module_image_format():
    """
    Return the expected MediaPipe SRGB image format.

    Kept as a small helper to make the test explicit about
    the format used by HandDetector.
    """

    import mediapipe as mp

    return mp.ImageFormat.SRGB


# =============================================================
# Detection call tests
# =============================================================


def test_find_hands_calls_detect_for_video():
    """
    find_hands() should call MediaPipe's detect_for_video()
    method exactly once.
    """

    detector = create_mock_detector()

    detector.detector.detect_for_video.return_value = "result"

    frame = create_test_frame()

    with patch(
        "hand_tracking.hand_detector.mp.Image"
    ) as mock_image:

        mock_image.return_value = MagicMock()

        result = detector.find_hands(
            frame,
            500,
        )

    assert result == "result"

    detector.detector.detect_for_video.assert_called_once_with(
        mock_image.return_value,
        500,
    )


def test_find_hands_forwards_timestamp():
    """
    The timestamp supplied to find_hands() should be passed
    directly to MediaPipe.
    """

    detector = create_mock_detector()

    detector.detector.detect_for_video.return_value = "result"

    frame = create_test_frame()

    with patch(
        "hand_tracking.hand_detector.mp.Image"
    ) as mock_image:

        mock_image.return_value = MagicMock()

        detector.find_hands(
            frame,
            9876,
        )

    call_args = (
        detector.detector.detect_for_video.call_args
    )

    assert call_args.args[1] == 9876


def test_find_hands_returns_mediapipe_result():
    """
    find_hands() should return the result produced by
    MediaPipe without modifying it.
    """

    detector = create_mock_detector()

    expected_result = MagicMock()

    detector.detector.detect_for_video.return_value = (
        expected_result
    )

    frame = create_test_frame()

    with patch(
        "hand_tracking.hand_detector.mp.Image"
    ) as mock_image:

        mock_image.return_value = MagicMock()

        result = detector.find_hands(
            frame,
            100,
        )

    assert result is expected_result


# =============================================================
# Cleanup tests
# =============================================================


def test_close_releases_detector():
    """
    close() should release the MediaPipe detector.
    """

    detector = create_mock_detector()

    detector.close()

    detector.detector.close.assert_called_once_with()


# =============================================================
# Configuration tests
# =============================================================


def test_detector_uses_config_defaults():
    """
    Verify that the constructor defaults come from config.py.
    """

    from utils import config

    with patch(
        "hand_tracking.hand_detector.vision.HandLandmarker.create_from_options"
    ) as mock_create:

        mock_create.return_value = MagicMock()

        HandDetector()

        mock_create.assert_called_once()

        options = mock_create.call_args.args[0]

        assert options.num_hands == config.MAX_NUM_HANDS

        assert (
            options.min_hand_detection_confidence
            == config.MIN_DETECTION_CONFIDENCE
        )

        assert (
            options.min_hand_presence_confidence
            == config.MIN_TRACKING_CONFIDENCE
        )

        assert (
            options.min_tracking_confidence
            == config.MIN_TRACKING_CONFIDENCE
        )
