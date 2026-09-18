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
from unittest.mock import MagicMock, patch

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


def make_extended_thumb(hand):
    hand[1] = point(0.30, 0.50)
    hand[2] = point(0.40, 0.50)
    hand[3] = point(0.50, 0.50)
    hand[4] = point(0.60, 0.50)


def make_folded_thumb(hand):
    hand[1] = point(0.35, 0.45)
    hand[2] = point(0.30, 0.40)
    hand[3] = point(0.28, 0.42)
    hand[4] = point(0.25, 0.45)


def make_valid_scroll_hand():
    hand = create_hand()
    make_extended_thumb(hand)
    make_extended_finger(hand, 5, 6, 8)
    make_extended_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 13, 14, 16)
    make_folded_finger(hand, 17, 18, 20)
    return hand


def make_open_palm_hand():
    hand = create_hand()
    make_extended_thumb(hand)
    make_extended_finger(hand, 5, 6, 8)
    make_extended_finger(hand, 9, 10, 12)
    make_extended_finger(hand, 13, 14, 16)
    make_extended_finger(hand, 17, 18, 20)
    return hand


def make_closed_fist_hand():
    hand = create_hand()
    make_folded_thumb(hand)
    make_folded_finger(hand, 5, 6, 8)
    make_folded_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 13, 14, 16)
    make_folded_finger(hand, 17, 18, 20)
    return hand


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


def create_left_click_hand():
    """Create a non-conflicting index-thumb pinch hand."""

    hand = create_hand(
        thumb_tip=(0.50, 0.50, 0.0),
        index_tip=(0.52, 0.50, 0.0),
        ring_tip=(0.90, 0.90, 0.0),
    )
    make_extended_finger(hand, 9, 10, 12)
    return hand


def create_right_click_hand():
    """Create a non-conflicting middle-thumb pinch hand."""

    hand = create_hand(
        thumb_tip=(0.50, 0.50, 0.0),
        index_tip=(0.90, 0.90, 0.0),
        middle_tip=(0.52, 0.50, 0.0),
        ring_tip=(0.90, 0.90, 0.0),
    )
    return hand


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


def test_thumb_and_pinky_extension_detection():
    detector = create_detector()
    hand_data = detector.get_hand(make_valid_scroll_hand())

    assert detector.is_thumb_extended(hand_data)
    assert not detector.is_pinky_extended(hand_data)


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


def test_pinch_hysteresis_keeps_active_pinch_stable():
    detector = create_detector()
    hand = create_left_click_hand()

    detector.detect_left_action(hand)
    hand[8] = point(0.58, 0.50)

    detector.detect_left_action(hand)

    assert detector.left_pinch_active


def test_left_click_requires_stable_release_and_cooldown():
    detector = create_detector()
    hand = create_left_click_hand()
    released = create_hand(
        thumb_tip=(0.10, 0.10, 0.0),
        index_tip=(0.90, 0.90, 0.0),
        ring_tip=(0.90, 0.90, 0.0),
    )
    make_extended_finger(released, 9, 10, 12)

    with pytest.MonkeyPatch.context() as patch:
        times = iter((1.0, 1.0, 1.0, 1.1, 1.2, 1.4))
        patch.setattr(
            "gestures.gesture_detector.monotonic",
            lambda: next(times),
        )

        assert detector.detect_left_action(hand) is None
        assert detector.detect_left_action(hand) is None
        assert detector.detect_left_action(hand) is None
        assert detector.detect_left_action(released) == "LEFT_CLICK"
        assert detector.detect_left_action(hand) is None
        assert detector.detect_left_action(released) is None


def test_right_click_cooldown_blocks_rapid_repinch():
    detector = create_detector()
    detector.click_stable_frames = 1
    detector.right_click_cooldown = 0.5
    hand = create_right_click_hand()
    released = create_hand(
        thumb_tip=(0.10, 0.10, 0.0),
        index_tip=(0.90, 0.90, 0.0),
        middle_tip=(0.90, 0.90, 0.0),
        ring_tip=(0.90, 0.90, 0.0),
    )

    with pytest.MonkeyPatch.context() as patch:
        times = iter((1.0, 1.1, 1.2, 1.3, 1.6))
        patch.setattr(
            "gestures.gesture_detector.monotonic",
            lambda: next(times),
        )

        assert detector.detect_right_click(hand) == "RIGHT_CLICK"
        assert detector.detect_right_click(released) is None
        assert detector.detect_right_click(hand) is None
        assert detector.detect_right_click(released) is None
        assert detector.detect_right_click(hand) == "RIGHT_CLICK"


def test_drag_start_and_end_are_stable():
    detector = create_detector()
    hand = create_left_click_hand()
    released = create_hand(
        thumb_tip=(0.10, 0.10, 0.0),
        index_tip=(0.90, 0.90, 0.0),
        ring_tip=(0.90, 0.90, 0.0),
    )
    make_extended_finger(released, 9, 10, 12)

    with pytest.MonkeyPatch.context() as patch:
        times = iter((1.0, 1.0, 1.0, 1.6, 1.7))
        patch.setattr(
            "gestures.gesture_detector.monotonic",
            lambda: next(times),
        )

        detector.detect_left_action(hand)
        detector.detect_left_action(hand)
        detector.detect_left_action(hand)
        assert detector.detect_left_action(hand) == "DRAG_START"
        assert detector.detect_left_action(released) == "DRAG_END"


def test_left_index_action_is_edge_triggered():
    detector = create_detector()
    hand = create_hand()
    make_folded_thumb(hand)
    make_extended_finger(hand, 5, 6, 8)
    make_folded_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 13, 14, 16)
    make_folded_finger(hand, 17, 18, 20)
    neutral = make_open_palm_hand()

    assert detector.detect_action_gesture(hand) == "LEFT_CLICK"
    assert detector.detect_action_gesture(hand) is None
    assert detector.detect_action_gesture(neutral) is None
    assert detector.detect_action_gesture(hand) == "LEFT_CLICK"


def test_left_middle_action_is_edge_triggered():
    detector = create_detector()
    hand = create_hand()
    make_folded_thumb(hand)
    make_folded_finger(hand, 5, 6, 8)
    make_extended_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 13, 14, 16)
    make_folded_finger(hand, 17, 18, 20)

    assert detector.detect_action_gesture(hand) == "DOUBLE_CLICK"
    assert detector.detect_action_gesture(hand) is None


def test_left_pinky_action_is_edge_triggered():
    detector = create_detector()
    hand = create_hand()
    make_folded_thumb(hand)
    make_folded_finger(hand, 5, 6, 8)
    make_folded_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 13, 14, 16)
    make_extended_finger(hand, 17, 18, 20)

    assert detector.detect_action_gesture(hand) == "RIGHT_CLICK"
    assert detector.detect_action_gesture(hand) is None


def test_left_fist_starts_once_and_open_palm_releases():
    detector = create_detector()
    fist = make_closed_fist_hand()
    open_palm = make_open_palm_hand()

    assert detector.detect_action_gesture(fist) == "DRAG_START"
    assert detector.detect_action_gesture(fist) == "DRAGGING"
    assert detector.detect_action_gesture(open_palm) == "DRAG_END"
    assert detector.detect_action_gesture(open_palm) is None


def test_lost_left_hand_releases_drag():
    detector = create_detector()
    fist = make_closed_fist_hand()

    assert detector.detect_action_gesture(fist) == "DRAG_START"
    assert detector.detect_action_gesture(None) == "DRAG_END"
    assert detector.detect_action_gesture(None) is None


def test_scroll_shape_does_not_trigger_left_action():
    detector = create_detector()

    assert detector.detect_action_gesture(
        make_valid_scroll_hand()
    ) is None


def test_worker_uses_right_hand_for_cursor_and_left_for_action():
    from app.camera_worker import CameraWorker

    worker = CameraWorker()
    worker.hand_detector = MagicMock()
    worker.gesture_detector = GestureDetector()
    worker.cursor_controller = MagicMock()
    worker.overlay = MagicMock()
    worker.paused = False

    right_hand = create_hand()
    make_extended_finger(right_hand, 5, 6, 8)

    left_hand = create_hand()
    make_folded_thumb(left_hand)
    make_extended_finger(left_hand, 5, 6, 8)
    make_folded_finger(left_hand, 9, 10, 12)
    make_folded_finger(left_hand, 13, 14, 16)
    make_folded_finger(left_hand, 17, 18, 20)

    results = SimpleNamespace(
        hand_landmarks=[right_hand, left_hand],
        handedness=[
            [SimpleNamespace(category_name="Left")],
            [SimpleNamespace(category_name="Right")],
        ],
    )
    worker.hand_detector.find_hands.return_value = results

    with patch(
        "app.camera_worker.cv2.flip",
        side_effect=lambda frame, _: frame,
    ):
        worker.process_frame(object())

    worker.cursor_controller.move_cursor.assert_called_once_with(
        right_hand[8].x,
        right_hand[8].y,
    )
    worker.cursor_controller.left_click.assert_called_once_with()


def test_worker_does_not_move_cursor_for_left_hand_only():
    from app.camera_worker import CameraWorker

    worker = CameraWorker()
    worker.hand_detector = MagicMock()
    worker.gesture_detector = GestureDetector()
    worker.cursor_controller = MagicMock()
    worker.overlay = MagicMock()
    worker.paused = False

    left_hand = make_open_palm_hand()
    worker.hand_detector.find_hands.return_value = SimpleNamespace(
        hand_landmarks=[left_hand],
        handedness=[
            [SimpleNamespace(category_name="Right")],
        ],
    )

    with patch(
        "app.camera_worker.cv2.flip",
        side_effect=lambda frame, _: frame,
    ):
        worker.process_frame(object())

    worker.cursor_controller.move_cursor.assert_not_called()


def test_worker_moves_cursor_for_open_right_hand():
    from app.camera_worker import CameraWorker

    worker = CameraWorker()
    worker.hand_detector = MagicMock()
    worker.gesture_detector = GestureDetector()
    worker.cursor_controller = MagicMock()
    worker.overlay = MagicMock()
    worker.paused = False

    right_hand = make_open_palm_hand()
    worker.hand_detector.find_hands.return_value = SimpleNamespace(
        hand_landmarks=[right_hand],
        handedness=[
            [SimpleNamespace(category_name=" left ")],
        ],
    )

    with patch(
        "app.camera_worker.cv2.flip",
        side_effect=lambda frame, _: frame,
    ):
        worker.process_frame(object())

    worker.cursor_controller.move_cursor.assert_called_once_with(
        right_hand[8].x,
        right_hand[8].y,
    )


def test_worker_releases_drag_when_right_hand_disappears():
    from app.camera_worker import CameraWorker

    worker = CameraWorker()
    worker.hand_detector = MagicMock()
    worker.gesture_detector = GestureDetector()
    worker.cursor_controller = MagicMock()
    worker.overlay = MagicMock()
    worker.paused = False
    worker.mouse_button_down = True

    left_hand = make_closed_fist_hand()
    worker.hand_detector.find_hands.return_value = SimpleNamespace(
        hand_landmarks=[left_hand],
        handedness=[
            [SimpleNamespace(category_name="Right")],
        ],
    )

    with patch(
        "app.camera_worker.cv2.flip",
        side_effect=lambda frame, _: frame,
    ), patch(
        "app.camera_worker.pyautogui.mouseUp",
    ) as mouse_up:
        worker.process_frame(object())

    mouse_up.assert_called_once_with()
    assert not worker.mouse_button_down


# =============================================================
# Scroll gesture tests
# =============================================================


def test_scroll_gesture_requires_index_and_middle():
    """
    Scrolling requires both index and middle fingers to be
    extended.
    """

    detector = create_detector()

    hand = make_valid_scroll_hand()

    hand_data = detector.get_hand(hand)

    assert detector.is_scroll_gesture_active(hand_data)


def test_open_palm_is_neutral_and_not_scroll():
    detector = create_detector()
    hand = make_open_palm_hand()

    assert detector.is_open_palm(hand)
    assert not detector.is_scroll_gesture_active(hand)
    assert detector.detect_gesture(hand) is None


def test_closed_fist_is_neutral_and_not_scroll():
    detector = create_detector()
    hand = make_closed_fist_hand()

    assert detector.is_closed_fist(hand)
    assert not detector.is_scroll_gesture_active(hand)
    assert detector.detect_gesture(hand) == "DRAG_START"


def test_invalid_scroll_finger_combinations_are_rejected():
    detector = create_detector()

    for finger in ((13, 14, 16), (17, 18, 20)):
        hand = make_valid_scroll_hand()
        make_extended_finger(hand, *finger)
        assert not detector.is_scroll_gesture_active(hand)


def test_index_middle_only_is_not_scroll():
    detector = create_detector()
    hand = create_hand()
    make_folded_thumb(hand)
    make_extended_finger(hand, 5, 6, 8)
    make_extended_finger(hand, 9, 10, 12)
    make_folded_finger(hand, 17, 18, 20)

    assert not detector.is_scroll_gesture_active(hand)


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


def test_diagonal_scroll_movement_does_not_select_an_axis():
    detector = create_detector()
    hand = make_valid_scroll_hand()

    hand_data = detector.get_hand(hand)
    detector.detect_scroll(hand_data)

    hand_data.wrist.x = 0.545
    hand_data.wrist.y = 0.46
    detector.detect_scroll(hand_data)

    assert detector.scroll_axis is None
    assert detector.scroll_direction == 0


def test_scroll_takes_priority_over_conflicting_click_state():
    detector = create_detector()
    hand = make_valid_scroll_hand()

    detector.action_dragging = True
    detector.previous_action_gesture = "CLOSED_FIST"

    assert detector.detect_gesture(hand) == "DRAG_END"
    assert not detector.action_dragging


def test_missing_hand_resets_all_gesture_state():
    detector = create_detector()
    detector.left_pinch_active = True
    detector.right_pinch_active = True
    detector.double_pinch_active = True
    detector.scroll_axis = "vertical"
    detector.dragging = True

    assert detector.detect_gesture(None) is None
    assert not detector.left_pinch_active
    assert not detector.right_pinch_active
    assert not detector.double_pinch_active
    assert detector.scroll_axis is None
    assert not detector.dragging


def test_open_palm_scroll_transition_is_neutral():
    detector = create_detector()
    open_palm = make_open_palm_hand()
    scroll_hand = make_valid_scroll_hand()

    assert detector.detect_gesture(open_palm) is None
    assert detector.detect_gesture(scroll_hand) is None
    scroll_hand[0].y = 0.45
    assert detector.detect_gesture(scroll_hand) == detector.scroll_speed
    assert detector.detect_gesture(open_palm) is None
    assert detector.scroll_axis is None


def test_closed_fist_to_scroll_requires_exact_shape():
    detector = create_detector()
    fist = make_closed_fist_hand()
    scroll_hand = make_valid_scroll_hand()

    assert detector.detect_gesture(fist) == "DRAG_START"
    assert detector.detect_gesture(scroll_hand) == "DRAG_END"
    assert detector.scroll_axis is None


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

    hand = make_valid_scroll_hand()

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

    hand = make_valid_scroll_hand()

    hand_data = detector.get_hand(hand)

    # First frame initializes the scroll gesture.
    detector.detect_scroll(hand_data)

    # Move the wrist right.
    hand_data.wrist.x = 0.55

    detector.detect_scroll(hand_data)

    assert detector.scroll_axis == "horizontal"
    assert detector.scroll_direction == 1
