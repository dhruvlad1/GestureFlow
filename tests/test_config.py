"""
Unit tests for GestureFlow configuration.

These tests verify that the central configuration contains
valid values and that important configuration relationships
are maintained.

Run with:

    python -m pytest tests/test_config.py -v
"""

import sys
from pathlib import Path


# -------------------------------------------------------------
# Make the src directory importable when pytest is run from
# the project root.
# -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from utils import config


# =============================================================
# Camera / Hand Tracking Configuration
# =============================================================


def test_max_num_hands_is_valid():
    """
    MAX_NUM_HANDS should be a positive integer.
    """

    assert isinstance(
        config.MAX_NUM_HANDS,
        int,
    )

    assert config.MAX_NUM_HANDS >= 1


def test_detection_confidence_is_valid():
    """
    Detection confidence should be within the range [0, 1].
    """

    assert 0.0 <= config.MIN_DETECTION_CONFIDENCE <= 1.0


def test_tracking_confidence_is_valid():
    """
    Tracking confidence should be within the range [0, 1].
    """

    assert 0.0 <= config.MIN_TRACKING_CONFIDENCE <= 1.0


# =============================================================
# Gesture Detection Configuration
# =============================================================


def test_pinch_thresholds_are_valid():
    """
    Pinch start threshold should be smaller than the release
    threshold so that hysteresis can work correctly.
    """

    assert config.PINCH_START_THRESHOLD > 0
    assert config.PINCH_RELEASE_THRESHOLD > 0

    assert (
        config.PINCH_START_THRESHOLD
        < config.PINCH_RELEASE_THRESHOLD
    )


def test_finger_extension_angle_is_valid():
    """
    Finger extension angle should be within a valid
    geometric angle range.
    """

    assert (
        0
        < config.FINGER_EXTENSION_ANGLE
        <= 180
    )


def test_click_stable_frames_is_valid():
    """
    Stable frame count should be a positive integer.
    """

    assert isinstance(
        config.CLICK_STABLE_FRAMES,
        int,
    )

    assert config.CLICK_STABLE_FRAMES >= 1


def test_right_click_cooldown_is_valid():
    """
    Right-click cooldown should not be negative.
    """

    assert config.RIGHT_CLICK_COOLDOWN >= 0


def test_drag_hold_duration_is_valid():
    """
    Drag hold duration should not be negative.
    """

    assert config.DRAG_HOLD_DURATION >= 0


# =============================================================
# Scrolling Configuration
# =============================================================


def test_scroll_threshold_is_valid():
    """
    Scroll threshold should be positive.
    """

    assert config.SCROLL_THRESHOLD > 0


def test_scroll_speed_is_valid():
    """
    Scroll speed should be positive.
    """

    assert config.SCROLL_SPEED > 0


def test_scroll_direction_threshold_is_valid():
    """
    Direction-change threshold should be positive.
    """

    assert (
        config.SCROLL_DIRECTION_CHANGE_THRESHOLD
        > 0
    )


def test_scroll_update_interval_is_valid():
    """
    Scroll update interval should be positive.
    """

    assert config.SCROLL_UPDATE_INTERVAL > 0


# =============================================================
# Cursor Configuration
# =============================================================


def test_cursor_smoothing_is_valid():
    """
    Smoothing should be within the range (0, 1].
    """

    assert 0 < config.CURSOR_SMOOTHING <= 1.0


def test_camera_x_range_is_valid():
    """
    Horizontal camera coordinates should form a valid range.
    """

    assert 0.0 <= config.CAMERA_MIN_X < 1.0
    assert 0.0 < config.CAMERA_MAX_X <= 1.0

    assert (
        config.CAMERA_MIN_X
        < config.CAMERA_MAX_X
    )


def test_camera_y_range_is_valid():
    """
    Vertical camera coordinates should form a valid range.
    """

    assert 0.0 <= config.CAMERA_MIN_Y < 1.0
    assert 0.0 < config.CAMERA_MAX_Y <= 1.0

    assert (
        config.CAMERA_MIN_Y
        < config.CAMERA_MAX_Y
    )


def test_screen_padding_is_valid():
    """
    Screen padding should not be negative.
    """

    assert config.SCREEN_PADDING >= 0


# =============================================================
# Application Configuration
# =============================================================


def test_window_title_is_valid():
    """
    The application window title should be a non-empty string.
    """

    assert isinstance(
        config.WINDOW_TITLE,
        str,
    )

    assert config.WINDOW_TITLE.strip() != ""


def test_camera_index_is_valid():
    """
    Camera index should be a non-negative integer.
    """

    assert isinstance(
        config.CAMERA_INDEX,
        int,
    )

    assert config.CAMERA_INDEX >= 0


# =============================================================
# Configuration Consistency
# =============================================================


def test_camera_ranges_have_usable_area():
    """
    The configured camera ranges should leave a non-zero
    usable area for cursor mapping.
    """

    horizontal_range = (
        config.CAMERA_MAX_X
        - config.CAMERA_MIN_X
    )

    vertical_range = (
        config.CAMERA_MAX_Y
        - config.CAMERA_MIN_Y
    )

    assert horizontal_range > 0
    assert vertical_range > 0


def test_all_confidence_values_are_normalized():
    """
    All MediaPipe confidence values should use the standard
    normalized [0, 1] range.
    """

    confidence_values = [
        config.MIN_DETECTION_CONFIDENCE,
        config.MIN_TRACKING_CONFIDENCE,
    ]

    for confidence in confidence_values:
        assert 0.0 <= confidence <= 1.0
