"""
Unit tests for GestureFlow visualization and overlay.

These tests verify that the overlay functions can process
frames and draw visualization elements without requiring
a webcam or an OpenCV display window.

Run with:

    python -m pytest tests/test_overlay.py -v
"""

import sys
from pathlib import Path

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


from visualization.overlay import Overlay


# =============================================================
# Test helpers
# =============================================================


def create_test_frame():
    """
    Create a synthetic BGR OpenCV frame.
    """

    return np.zeros(
        (480, 640, 3),
        dtype=np.uint8,
    )


def create_test_landmarks():
    """
    Create synthetic normalized hand landmarks.

    MediaPipe hand landmarks use normalized coordinates
    between 0.0 and 1.0.
    """

    return [
        (0.50, 0.50)
        for _ in range(21)
    ]


# =============================================================
# Initialization tests
# =============================================================


def test_overlay_initializes():
    """
    Overlay should initialize without requiring any external
    resources.
    """

    overlay = Overlay()

    assert overlay is not None


# =============================================================
# Frame tests
# =============================================================


def test_draw_landmarks_returns_frame():
    """
    Drawing landmarks should return a valid OpenCV frame.
    """

    overlay = Overlay()

    frame = create_test_frame()
    landmarks = create_test_landmarks()

    result = overlay.draw_landmarks(
        frame,
        landmarks,
    )

    assert result is not None
    assert isinstance(result, np.ndarray)

    assert result.shape == frame.shape
    assert result.dtype == frame.dtype


def test_draw_landmarks_does_not_change_frame_dimensions():
    """
    Landmark drawing should preserve the original frame
    dimensions.
    """

    overlay = Overlay()

    frame = create_test_frame()
    landmarks = create_test_landmarks()

    result = overlay.draw_landmarks(
        frame,
        landmarks,
    )

    assert result.shape[0] == 480
    assert result.shape[1] == 640
    assert result.shape[2] == 3


def test_draw_landmarks_modifies_frame():
    """
    Valid landmarks should produce visible drawing on the
    frame.
    """

    overlay = Overlay()

    frame = create_test_frame()

    # ---------------------------------------------------------
    # Use different coordinates so that the landmarks are
    # visibly separated.
    # ---------------------------------------------------------

    landmarks = []

    for index in range(21):
        x = 0.10 + (index % 5) * 0.15
        y = 0.10 + (index // 5) * 0.15

        landmarks.append((x, y))

    original = frame.copy()

    result = overlay.draw_landmarks(
        frame,
        landmarks,
    )

    assert not np.array_equal(
        result,
        original,
    )


# =============================================================
# Status / text overlay tests
# =============================================================


def test_draw_status_returns_frame():
    """
    Drawing status information should return a valid frame.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_status(
        frame,
        "Testing",
    )

    assert result is not None
    assert isinstance(result, np.ndarray)

    assert result.shape == frame.shape


def test_draw_status_modifies_frame():
    """
    Status text should modify the frame.
    """

    overlay = Overlay()

    frame = create_test_frame()

    original = frame.copy()

    result = overlay.draw_status(
        frame,
        "GestureFlow",
    )

    assert not np.array_equal(
        result,
        original,
    )


# =============================================================
# Gesture display tests
# =============================================================


def test_draw_gesture_returns_frame():
    """
    Drawing the current gesture should return a valid frame.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_gesture(
        frame,
        "Left Click",
    )

    assert result is not None
    assert isinstance(result, np.ndarray)

    assert result.shape == frame.shape


def test_draw_gesture_modifies_frame():
    """
    Gesture text should modify the frame.
    """

    overlay = Overlay()

    frame = create_test_frame()

    original = frame.copy()

    result = overlay.draw_gesture(
        frame,
        "Scroll",
    )

    assert not np.array_equal(
        result,
        original,
    )


# =============================================================
# Empty / edge-case tests
# =============================================================


def test_draw_landmarks_with_empty_landmarks():
    """
    The overlay should safely handle an empty landmark list.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_landmarks(
        frame,
        [],
    )

    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == frame.shape


def test_draw_status_with_empty_text():
    """
    The status overlay should handle an empty string.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_status(
        frame,
        "",
    )

    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == frame.shape


def test_draw_gesture_with_empty_text():
    """
    The gesture overlay should handle an empty string.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_gesture(
        frame,
        "",
    )

    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == frame.shape


# =============================================================
# Frame integrity tests
# =============================================================


def test_overlay_preserves_bgr_frame_format():
    """
    The overlay should preserve the three-channel BGR format
    expected by OpenCV.
    """

    overlay = Overlay()

    frame = create_test_frame()

    result = overlay.draw_status(
        frame,
        "GestureFlow",
    )

    assert result.ndim == 3
    assert result.shape[2] == 3


def test_overlay_works_with_non_square_frame():
    """
    Overlay drawing should work with a normal widescreen frame.
    """

    overlay = Overlay()

    frame = np.zeros(
        (720, 1280, 3),
        dtype=np.uint8,
    )

    result = overlay.draw_status(
        frame,
        "Tracking",
    )

    assert result.shape == frame.shape
