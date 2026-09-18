"""
Unit tests for GestureFlow cursor control.

These tests mock PyAutoGUI so that they do not move or click
the real operating system mouse.

Run with:

    python -m pytest tests/test_cursor.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# -------------------------------------------------------------
# Make the src directory importable when pytest is run from
# the project root.
# -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from cursor.cursor_controller import CursorController


# =============================================================
# Test helpers
# =============================================================


def create_controller():
    """
    Create a cursor controller with the same configuration
    used by the current application.
    """

    with patch(
        "cursor.cursor_controller.pyautogui.size",
        return_value=(1920, 1080),
    ):
        controller = CursorController()

    return controller


# =============================================================
# Coordinate mapping tests
# =============================================================


def test_map_minimum_coordinates():
    """
    The minimum camera coordinates should map to the screen
    padding.
    """

    controller = create_controller()

    x, y = controller.map_coordinates(
        0.10,
        0.10,
    )

    assert x == pytest.approx(5)
    assert y == pytest.approx(5)


def test_map_maximum_coordinates():
    """
    The maximum camera coordinates should map to the opposite
    side of the usable screen area.
    """

    controller = create_controller()

    x, y = controller.map_coordinates(
        0.90,
        0.90,
    )

    assert x == pytest.approx(1914)
    assert y == pytest.approx(1074)


def test_map_center_coordinates():
    """
    The center of the camera range should map approximately
    to the center of the usable screen area.
    """

    controller = create_controller()

    x, y = controller.map_coordinates(
        0.50,
        0.50,
    )

    assert x == pytest.approx(959.5)
    assert y == pytest.approx(539.5)


# =============================================================
# Coordinate clamping tests
# =============================================================


def test_coordinates_below_minimum_are_clamped():
    """
    Camera coordinates below the configured range should be
    clamped to the minimum.
    """

    controller = create_controller()

    x, y = controller.map_coordinates(
        -1.0,
        -1.0,
    )

    assert x == pytest.approx(5)
    assert y == pytest.approx(5)


def test_coordinates_above_maximum_are_clamped():
    """
    Camera coordinates above the configured range should be
    clamped to the maximum.
    """

    controller = create_controller()

    x, y = controller.map_coordinates(
        2.0,
        2.0,
    )

    assert x == pytest.approx(1914)
    assert y == pytest.approx(1074)


# =============================================================
# Smoothing tests
# =============================================================


def test_first_smoothing_value_is_used_directly():
    """
    The first coordinate should initialize the smoothing state
    without modification.
    """

    controller = create_controller()

    x, y = controller.smooth_coordinates(
        500,
        300,
    )

    assert x == pytest.approx(500)
    assert y == pytest.approx(300)

    assert controller.previous_x == pytest.approx(500)
    assert controller.previous_y == pytest.approx(300)


def test_smoothing_factor_one_is_fully_responsive():
    """
    With smoothing = 1.0, the newest coordinates should be used
    directly.
    """

    controller = create_controller()

    controller.smooth_coordinates(
        500,
        300,
    )

    x, y = controller.smooth_coordinates(
        800,
        600,
    )

    assert x == pytest.approx(800)
    assert y == pytest.approx(600)


def test_smoothing_factor_reduces_movement():
    """
    A smoothing factor below 1.0 should interpolate between
    the previous and current coordinates.
    """

    controller = create_controller()
    controller.smoothing = 0.5

    controller.smooth_coordinates(
        100,
        100,
    )

    x, y = controller.smooth_coordinates(
        200,
        200,
    )

    assert x == pytest.approx(150)
    assert y == pytest.approx(150)


# =============================================================
# Cursor movement tests
# =============================================================


@patch("cursor.cursor_controller.pyautogui.moveTo")
def test_move_cursor_calls_pyautogui(mock_move_to):
    """
    move_cursor() should call PyAutoGUI with integer screen
    coordinates.
    """

    controller = create_controller()

    controller.move_cursor(
        0.50,
        0.50,
    )

    mock_move_to.assert_called_once_with(
        959,
        539,
        duration=0,
    )


@patch("cursor.cursor_controller.pyautogui.moveTo")
def test_move_cursor_uses_mapped_coordinates(mock_move_to):
    """
    Verify that normalized hand coordinates are mapped to the
    expected screen coordinates.
    """

    controller = create_controller()

    controller.move_cursor(
        0.10,
        0.10,
    )

    mock_move_to.assert_called_once_with(
        5,
        5,
        duration=0,
    )


# =============================================================
# Mouse action tests
# =============================================================


@patch("cursor.cursor_controller.pyautogui.click")
def test_left_click(mock_click):
    """
    left_click() should call PyAutoGUI click().
    """

    controller = create_controller()

    controller.left_click()

    mock_click.assert_called_once_with()


@patch("cursor.cursor_controller.pyautogui.rightClick")
def test_right_click(mock_right_click):
    """
    right_click() should call PyAutoGUI rightClick().
    """

    controller = create_controller()

    controller.right_click()

    mock_right_click.assert_called_once_with()


@patch("cursor.cursor_controller.pyautogui.doubleClick")
def test_double_click(mock_double_click):
    """
    double_click() should call PyAutoGUI doubleClick().
    """

    controller = create_controller()

    controller.double_click()

    mock_double_click.assert_called_once_with()


# =============================================================
# Reset tests
# =============================================================


def test_reset_clears_smoothing_state():
    """
    reset() should clear the previous cursor position.
    """

    controller = create_controller()

    controller.previous_x = 500
    controller.previous_y = 300

    controller.reset()

    assert controller.previous_x is None
    assert controller.previous_y is None


def test_reset_allows_new_position_to_initialize_smoothing():
    """
    After reset, the next position should become the new
    starting point rather than being blended with the old one.
    """

    controller = create_controller()

    controller.smoothing = 0.5

    controller.smooth_coordinates(
        100,
        100,
    )

    controller.smooth_coordinates(
        200,
        200,
    )

    controller.reset()

    x, y = controller.smooth_coordinates(
        800,
        600,
    )

    assert x == pytest.approx(800)
    assert y == pytest.approx(600)


# =============================================================
# Configuration tests
# =============================================================


def test_controller_uses_config_defaults():
    """
    Verify that the controller receives the centralized
    configuration values as its defaults.
    """

    from utils import config

    controller = create_controller()

    assert controller.smoothing == config.CURSOR_SMOOTHING

    assert controller.camera_min_x == config.CAMERA_MIN_X
    assert controller.camera_max_x == config.CAMERA_MAX_X

    assert controller.camera_min_y == config.CAMERA_MIN_Y
    assert controller.camera_max_y == config.CAMERA_MAX_Y

    assert controller.screen_padding == config.SCREEN_PADDING
