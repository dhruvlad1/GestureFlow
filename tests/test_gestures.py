"""
Unit tests for GestureFlow gesture detection.

These tests use synthetic hand landmarks instead of a real
webcam or MediaPipe model.

Run with:

    python -m pytest tests/test_gestures.py -v
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


# -------------------------------------------------------------
# Make the src directory importable when pytest is run from
# the project root.
# -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from gestures.gesture_detector import GestureDetector


# =============================================================
# Test helpers
# =============================================================


def point(x, y, z=0.0):
    """
    Create a simple landmark-like object.
    """

    return SimpleNamespace(
        x=float(x),
        y=float(y),
        z=float(z),
    )


def create_hand(
    thumb_tip=(0.0, 0.0, 0.0),
    index_tip=(0.5, 0.5, 0.0),
    middle_tip=(0.5, 0.5, 0.0),
    ring_tip=(0.5, 0.5, 0.0),
):
    """
    Create a synthetic 21-landmark hand.

    Only the landmarks required by the current gesture
    detection logic are configured precisely.
    """

    landmarks = [
        point(0.0, 0.0)
        for _ in range(21)
    ]

    # ---------------------------------------------------------
    # Wrist
    # ---------------------------------------------------------

    landmarks[0] = point(0.5, 0.5)

    # ---------------------------------------------------------
    # Thumb
    # ---------------------------------------------------------

    landmarks[1] = point(0.35, 0.45)
    landmarks[2] = point(0.30, 0.40)
    landmarks[3] = point(0.20, 0.30)
    landmarks[4] = point(*thumb_tip[:2], thumb_tip[2])

    # ---------------------------------------------------------
    # Index finger
    # ---------------------------------------------------------

    landmarks[5] = point(0.50, 0.50)
    landmarks[6] = point(0.50, 0.40)
    landmarks[7] = point(0.50, 0.30)
    landmarks[8] = point(*index_tip[:2], index_tip[2])

    # ---------------------------------------------------------
    # Middle finger
    # ---------------------------------------------------------

    landmarks[9] = point(0.60, 0.50)
    landmarks[10] = point(0.60, 0.40)
    landmarks[11] = point(0.60, 0.30)
    landmarks[12] = point(*middle_tip[:2], middle_tip[2])

    # ---------------------------------------------------------
    # Ring finger
    # ---------------------------------------------------------

    landmarks[13] = point(0.70, 0.50)
    landmarks[14] = point(0.70, 0.40)
    landmarks[15] = point(0.70, 0.30)
    landmarks[16] = point(*ring_tip[:2], ring_tip[2])

    # ---------------------------------------------------------
    # Pinky
    # ---------------------------------------------------------

    landmarks[17] = point(0.80, 0.50)
    landmarks[18] = point(0.80, 0.40)
    landmarks[19] = point(0.80, 0.30)
    landmarks[20] = point(0.80, 0.20)

    return landmarks


def make_extended_finger(hand, mcp, pip, tip):
    """
    Configure a finger so that the MCP -> PIP -> TIP angle
    is approximately 180 degrees.
    """

    hand[mcp] = point(0.5, 0.5)
    hand[pip] = point(0.5, 0.4)
    hand[tip] = point(0.5, 0.3)


def make_folded_finger(hand, mcp, pip, tip):
    """
    Configure a finger so that its joint angle is below the
    extension threshold.
    """

    hand[mcp] = point(0.5, 0.5)
    hand[pip] = point(0.5, 0.4)
    hand[tip] = point(0.7, 0.4)


def create_detector():
    """
    Create a detector with short timing values suitable for
    deterministic unit tests.
    """

    return GestureDetector(
        pinch_start_threshold=0.075,
        pinch_release_threshold=0.095,
        finger_extension_angle=160,
        click_stable_frames=3,
        right_click_cooldown=0.0,
        drag_hold_duration=0.5,
        scroll_threshold=0.015,
        scroll_speed=60,
        scroll_direction_change_threshold=0.012,
        scroll_update_interval=0.0,
    )


def stabilize_left_gesture(detector, hand):
    """
    Feed the same left-click gesture for the required number
    of stable frames.
    """

    for _ in range(3):
        detector.detect_left_action(hand)


# =============================================================
# Basic geometry tests
# =============================================================


def test_distance_zero():
    """
    Identical points should have zero distance.
    """

    detector = create_detector()

    a = point(0.5, 0.5, 0.0)
    b = point(0.5, 0.5, 0.0)

    assert detector.distance(a, b) == pytest.approx(0.0)


def test_distance_calculation():
    """
    Verify Euclidean distance calculation.
    """

    detector = create_detector()

    a = point(0.0, 0.0, 0.0)
    b = point(0.03, 0.04, 0.0)

    assert detector.distance(a, b) == pytest.approx(0.05)


def test_straight_finger_angle():
    """
    A straight finger should produce an angle close to 180°.
    """

    detector = create_detector()

    a = point(0.5, 0.5)
    b = point(0.5, 0.4)
    c = point(0.5, 0.3)

    angle = detector.calculate_angle(a, b, c)

    assert angle == pytest.approx(180.0)


# =============================================================
# Finger extension tests
# =============================================================


def test_index_finger_extended():
    """
    A straight index finger should be detected as extended.
    """

    detector = create_detector()
    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_index_extended(hand_data)


def test_index_finger_folded():
    """
    A bent index finger should not be detected as extended.
    """

    detector = create_detector()
    hand = create_hand()

    make_folded_finger(
        hand,
        5,
        6,
        8,
    )

    hand_data = detector.get_hand(hand)

    assert not detector.is_index_extended(hand_data)


def test_middle_finger_extended():
    """
    A straight middle finger should be detected as extended.
    """

    detector = create_detector()
    hand = create_hand()

    make_extended_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_middle_extended(hand_data)


def test_ring_finger_extended():
    """
    A straight ring finger should be detected as extended.
    """

    detector = create_detector()
    hand = create_hand()

    make_extended_finger(
        hand,
        13,
        14,
        16,
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_ring_extended(hand_data)


# =============================================================
# Pinch tests
# =============================================================


def test_thumb_index_pinch():
    """
    Thumb and index tips within the configured threshold
    should be detected as a pinch.
    """

    detector = create_detector()

    hand = create_hand(
        thumb_tip=(0.50, 0.50, 0.0),
        index_tip=(0.52, 0.50, 0.0),
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_thumb_index_pinching(hand_data)


def test_thumb_index_not_pinching():
    """
    Thumb and index tips farther apart than the threshold
    should not be detected as a pinch.
    """

    detector = create_detector()

    hand = create_hand(
        thumb_tip=(0.20, 0.20, 0.0),
        index_tip=(0.50, 0.50, 0.0),
    )

    hand_data = detector.get_hand(hand)

    assert not detector.is_thumb_index_pinching(hand_data)


def test_thumb_middle_pinch():
    """
    Thumb and middle tips close together should be detected
    as a middle-thumb pinch.
    """

    detector = create_detector()

    hand = create_hand(
        thumb_tip=(0.50, 0.50, 0.0),
        middle_tip=(0.52, 0.50, 0.0),
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_thumb_middle_pinching(hand_data)


def test_thumb_ring_pinch():
    """
    Thumb and ring tips close together should be detected
    as a ring-thumb pinch.
    """

    detector = create_detector()

    hand = create_hand(
        thumb_tip=(0.50, 0.50, 0.0),
        ring_tip=(0.52, 0.50, 0.0),
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_thumb_ring_pinching(hand_data)


# =============================================================
# Scroll gesture tests
# =============================================================


def test_scroll_gesture_requires_index_and_middle():
    """
    Scrolling requires both index and middle fingers to be
    extended.
    """

    detector = create_detector()

    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    make_extended_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    assert detector.is_scroll_gesture_active(hand_data)


def test_scroll_gesture_inactive_without_middle():
    """
    An extended index finger alone should not activate
    scrolling.
    """

    detector = create_detector()

    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    make_folded_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    assert not detector.is_scroll_gesture_active(hand_data)


# =============================================================
# Reset tests
# =============================================================


def test_reset_clears_left_gesture_state():
    """
    Reset should clear left-click and drag state.
    """

    detector = create_detector()

    detector.previous_left_pinching = True
    detector.left_stable_count = 10
    detector.left_pinch_start_time = 100.0
    detector.dragging = True

    detector.reset()

    assert detector.previous_left_pinching is False
    assert detector.left_stable_count == 0
    assert detector.left_pinch_start_time is None
    assert detector.dragging is False


def test_reset_clears_scroll_state():
    """
    Reset should clear all scroll state.
    """

    detector = create_detector()

    detector.previous_scroll_active = True
    detector.previous_scroll_x = 0.5
    detector.previous_scroll_y = 0.5
    detector.scroll_axis = "vertical"
    detector.scroll_direction = 1
    detector.horizontal_scroll_amount = 60

    detector.reset()

    assert detector.previous_scroll_active is False
    assert detector.previous_scroll_x is None
    assert detector.previous_scroll_y is None
    assert detector.scroll_axis is None
    assert detector.scroll_direction == 0
    assert detector.horizontal_scroll_amount == 0


# =============================================================
# Hand conversion tests
# =============================================================


def test_get_hand_returns_hand_data():
    """
    Raw landmarks should be converted into HandData.
    """

    detector = create_detector()

    hand = create_hand()

    result = detector.get_hand(hand)

    assert result is not None
    assert result.landmarks is hand


def test_get_hand_accepts_existing_hand_data():
    """
    HandData should not be wrapped a second time.
    """

    detector = create_detector()

    hand = create_hand()

    hand_data = detector.get_hand(hand)

    result = detector.get_hand(hand_data)

    assert result is hand_data


def test_get_hand_none():
    """
    None should remain None.
    """

    detector = create_detector()

    assert detector.get_hand(None) is None


# =============================================================
# Gesture priority / basic behavior tests
# =============================================================


def test_detect_gesture_returns_none_for_none():
    """
    No landmarks should produce no gesture.
    """

    detector = create_detector()

    assert detector.detect_gesture(None) is None


def test_scroll_direction_starts_undefined():
    """
    A newly activated scroll gesture should initially have
    no selected axis or direction.
    """

    detector = create_detector()

    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    make_extended_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    result = detector.detect_scroll(hand_data)

    assert result == 0
    assert detector.scroll_axis is None
    assert detector.scroll_direction == 0


def test_vertical_scroll_direction():
    """
    Sufficient upward wrist movement should select vertical
    upward scrolling.
    """

    detector = create_detector()

    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    make_extended_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    # First frame initializes the scroll gesture.
    detector.detect_scroll(hand_data)

    # Move the wrist upward.
    hand_data.wrist.y = 0.45

    detector.detect_scroll(hand_data)

    assert detector.scroll_axis == "vertical"
    assert detector.scroll_direction == 1


def test_horizontal_scroll_direction():
    """
    Sufficient rightward wrist movement should select
    horizontal right scrolling.
    """

    detector = create_detector()

    hand = create_hand()

    make_extended_finger(
        hand,
        5,
        6,
        8,
    )

    make_extended_finger(
        hand,
        9,
        10,
        12,
    )

    hand_data = detector.get_hand(hand)

    # First frame initializes the scroll gesture.
    detector.detect_scroll(hand_data)

    # Move the wrist right.
    hand_data.wrist.x = 0.55

    detector.detect_scroll(hand_data)

    assert detector.scroll_axis == "horizontal"
    assert detector.scroll_direction == 1
