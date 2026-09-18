from dataclasses import dataclass
from math import acos, degrees, sqrt
from time import monotonic

from utils.config import (
    PINCH_START_THRESHOLD,
    PINCH_RELEASE_THRESHOLD,
    FINGER_EXTENSION_ANGLE,
    CLICK_STABLE_FRAMES,
    CLICK_COOLDOWN,
    RIGHT_CLICK_COOLDOWN,
    DRAG_HOLD_DURATION,
    SCROLL_THRESHOLD,
    SCROLL_SPEED,
    SCROLL_DIRECTION_CHANGE_THRESHOLD,
    SCROLL_AXIS_DOMINANCE,
    SCROLL_UPDATE_INTERVAL,
)


@dataclass
class HandData:
    """
    Wrapper around MediaPipe hand landmarks.
    """

    landmarks: list
    handedness: str | None = None

    @property
    def wrist(self):
        return self.landmarks[0]

    # ---------------------------------------------------------
    # Thumb
    # ---------------------------------------------------------

    @property
    def thumb_cmc(self):
        return self.landmarks[1]

    @property
    def thumb_mcp(self):
        return self.landmarks[2]

    @property
    def thumb_ip(self):
        return self.landmarks[3]

    @property
    def thumb_tip(self):
        return self.landmarks[4]

    # ---------------------------------------------------------
    # Index finger
    # ---------------------------------------------------------

    @property
    def index_mcp(self):
        return self.landmarks[5]

    @property
    def index_pip(self):
        return self.landmarks[6]

    @property
    def index_dip(self):
        return self.landmarks[7]

    @property
    def index_tip(self):
        return self.landmarks[8]

    # ---------------------------------------------------------
    # Middle finger
    # ---------------------------------------------------------

    @property
    def middle_mcp(self):
        return self.landmarks[9]

    @property
    def middle_pip(self):
        return self.landmarks[10]

    @property
    def middle_dip(self):
        return self.landmarks[11]

    @property
    def middle_tip(self):
        return self.landmarks[12]

    # ---------------------------------------------------------
    # Ring finger
    # ---------------------------------------------------------

    @property
    def ring_mcp(self):
        return self.landmarks[13]

    @property
    def ring_pip(self):
        return self.landmarks[14]

    @property
    def ring_dip(self):
        return self.landmarks[15]

    @property
    def ring_tip(self):
        return self.landmarks[16]

    # ---------------------------------------------------------
    # Pinky
    # ---------------------------------------------------------

    @property
    def pinky_mcp(self):
        return self.landmarks[17]

    @property
    def pinky_pip(self):
        return self.landmarks[18]

    @property
    def pinky_dip(self):
        return self.landmarks[19]

    @property
    def pinky_tip(self):
        return self.landmarks[20]


class GestureDetector:
    """
    Detects hand gestures and converts them into mouse actions.

    The left hand supplies edge-triggered mouse actions while
    the right hand supplies cursor position. The exact action
    state machine is implemented by detect_action_gesture().
    """

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(
        self,
        pinch_start_threshold=PINCH_START_THRESHOLD,
        pinch_release_threshold=PINCH_RELEASE_THRESHOLD,
        finger_extension_angle=FINGER_EXTENSION_ANGLE,
        click_stable_frames=CLICK_STABLE_FRAMES,
        click_cooldown=CLICK_COOLDOWN,
        right_click_cooldown=RIGHT_CLICK_COOLDOWN,
        drag_hold_duration=DRAG_HOLD_DURATION,
        scroll_threshold=SCROLL_THRESHOLD,
        scroll_speed=SCROLL_SPEED,
        scroll_direction_change_threshold=(
            SCROLL_DIRECTION_CHANGE_THRESHOLD
        ),
        scroll_axis_dominance=SCROLL_AXIS_DOMINANCE,
        scroll_update_interval=SCROLL_UPDATE_INTERVAL,
    ):

        self.pinch_start_threshold = pinch_start_threshold
        self.pinch_release_threshold = pinch_release_threshold
        self.finger_extension_angle = finger_extension_angle

        self.click_stable_frames = click_stable_frames
        self.click_cooldown = click_cooldown
        self.right_click_cooldown = right_click_cooldown
        self.drag_hold_duration = drag_hold_duration

        # -----------------------------------------------------
        # Continuous scrolling configuration.
        # -----------------------------------------------------

        self.scroll_threshold = scroll_threshold
        self.scroll_speed = scroll_speed

        self.scroll_direction_change_threshold = (
            scroll_direction_change_threshold
        )

        self.scroll_axis_dominance = scroll_axis_dominance

        self.scroll_update_interval = scroll_update_interval

        # -----------------------------------------------------
        # Left click / drag state.
        # -----------------------------------------------------

        self.previous_left_pinching = False
        self.left_pinch_active = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False
        self.last_left_click_time = 0

        # -----------------------------------------------------
        # Two-hand action state.
        # -----------------------------------------------------

        self.previous_action_gesture = None
        self.action_dragging = False

        # -----------------------------------------------------
        # Right click state.
        # -----------------------------------------------------

        self.previous_right_pinching = False
        self.right_pinch_active = False
        self.right_stable_count = 0
        self.last_right_click_time = 0

        # -----------------------------------------------------
        # Double click state.
        # -----------------------------------------------------

        self.previous_double_click_pinching = False
        self.double_pinch_active = False
        self.double_click_stable_count = 0
        self.last_double_click_time = 0

        # -----------------------------------------------------
        # Continuous scroll state.
        # -----------------------------------------------------

        self.previous_scroll_active = False

        self.previous_scroll_x = None
        self.previous_scroll_y = None

        # Scroll axis:
        #
        # "vertical"   = vertical scrolling
        # "horizontal" = horizontal scrolling
        # None         = direction not selected yet
        self.scroll_axis = None

        # Direction:
        #
        # Vertical:
        #     1  = up
        #     -1 = down
        #
        # Horizontal:
        #     1  = right
        #     -1 = left
        #
        # 0 = direction not selected
        self.scroll_direction = 0

        # Time of the most recent scroll event.
        self.last_scroll_update_time = 0

        # Most recent horizontal scroll amount.
        #
        # This is kept separately so the existing vertical
        # scrolling return value remains backward compatible.
        self.horizontal_scroll_amount = 0

    # =========================================================
    # Geometry helpers
    # =========================================================

    @staticmethod
    def distance(point_a, point_b):
        """
        Calculate Euclidean distance between two landmarks.
        """

        dx = point_a.x - point_b.x
        dy = point_a.y - point_b.y
        dz = point_a.z - point_b.z

        return sqrt(
            dx * dx
            + dy * dy
            + dz * dz
        )

    @staticmethod
    def calculate_angle(point_a, point_b, point_c):
        """
        Calculate angle ABC in degrees.
        """

        ba = (
            point_a.x - point_b.x,
            point_a.y - point_b.y,
            point_a.z - point_b.z,
        )

        bc = (
            point_c.x - point_b.x,
            point_c.y - point_b.y,
            point_c.z - point_b.z,
        )

        dot_product = (
            ba[0] * bc[0]
            + ba[1] * bc[1]
            + ba[2] * bc[2]
        )

        magnitude_ba = sqrt(
            ba[0] ** 2
            + ba[1] ** 2
            + ba[2] ** 2
        )

        magnitude_bc = sqrt(
            bc[0] ** 2
            + bc[1] ** 2
            + bc[2] ** 2
        )

        if magnitude_ba == 0 or magnitude_bc == 0:
            return 0

        cosine = dot_product / (
            magnitude_ba * magnitude_bc
        )

        cosine = max(-1.0, min(1.0, cosine))

        return degrees(acos(cosine))

    # =========================================================
    # Hand conversion
    # =========================================================

    @staticmethod
    def get_hand(landmarks, handedness=None):
        """
        Convert raw MediaPipe landmarks into HandData.

        The rest of the application can continue passing the
        raw MediaPipe landmark list into detect_gesture().
        """

        if landmarks is None:
            return None

        if isinstance(landmarks, HandData):
            return landmarks

        return HandData(landmarks, handedness)

    # =========================================================
    # Pinch detection
    # =========================================================

    def is_thumb_index_pinching(self, hand):
        """
        Detect thumb + index pinch.
        """

        return (
            self.distance(
                hand.thumb_tip,
                hand.index_tip,
            )
            < self.pinch_start_threshold
        )

    def is_thumb_middle_pinching(self, hand):
        """
        Detect thumb + middle pinch.
        """

        return (
            self.distance(
                hand.thumb_tip,
                hand.middle_tip,
            )
            < self.pinch_start_threshold
        )

    def is_thumb_ring_pinching(self, hand):
        """
        Detect thumb + ring pinch.
        """

        return (
            self.distance(
                hand.thumb_tip,
                hand.ring_tip,
            )
            < self.pinch_start_threshold
        )

    # =========================================================
    # Finger extension detection
    # =========================================================

    def is_index_extended(self, hand):
        angle = self.calculate_angle(
            hand.index_mcp,
            hand.index_pip,
            hand.index_tip,
        )

        return angle >= self.finger_extension_angle

    def is_middle_extended(self, hand):
        angle = self.calculate_angle(
            hand.middle_mcp,
            hand.middle_pip,
            hand.middle_tip,
        )

        return angle >= self.finger_extension_angle

    def is_ring_extended(self, hand):
        angle = self.calculate_angle(
            hand.ring_mcp,
            hand.ring_pip,
            hand.ring_tip,
        )

        return angle >= self.finger_extension_angle

    def is_pinky_extended(self, hand):
        angle = self.calculate_angle(
            hand.pinky_mcp,
            hand.pinky_pip,
            hand.pinky_tip,
        )

        return angle >= self.finger_extension_angle

    def is_thumb_extended(self, hand):
        angle = self.calculate_angle(
            hand.thumb_cmc,
            hand.thumb_mcp,
            hand.thumb_tip,
        )

        return angle >= self.finger_extension_angle

    def is_open_palm(self, hand):
        hand = self.get_hand(hand)

        if hand is None:
            return False

        return all(
            (
                self.is_thumb_extended(hand),
                self.is_index_extended(hand),
                self.is_middle_extended(hand),
                self.is_ring_extended(hand),
                self.is_pinky_extended(hand),
            )
        )

    def is_closed_fist(self, hand):
        hand = self.get_hand(hand)

        if hand is None:
            return False

        return not any(
            (
                self.is_thumb_extended(hand),
                self.is_index_extended(hand),
                self.is_middle_extended(hand),
                self.is_ring_extended(hand),
                self.is_pinky_extended(hand),
            )
        )

    def is_index_only(self, hand):
        """Return whether only the index finger is extended."""

        hand = self.get_hand(hand)

        if hand is None:
            return False

        return (
            self.is_index_extended(hand)
            and not self.is_thumb_extended(hand)
            and not self.is_middle_extended(hand)
            and not self.is_ring_extended(hand)
            and not self.is_pinky_extended(hand)
        )

    def is_middle_only(self, hand):
        """Return whether only the middle finger is extended."""

        hand = self.get_hand(hand)

        if hand is None:
            return False

        return (
            self.is_middle_extended(hand)
            and not self.is_thumb_extended(hand)
            and not self.is_index_extended(hand)
            and not self.is_ring_extended(hand)
            and not self.is_pinky_extended(hand)
        )

    def is_pinky_only(self, hand):
        """Return whether only the pinky finger is extended."""

        hand = self.get_hand(hand)

        if hand is None:
            return False

        return (
            self.is_pinky_extended(hand)
            and not self.is_thumb_extended(hand)
            and not self.is_index_extended(hand)
            and not self.is_middle_extended(hand)
            and not self.is_ring_extended(hand)
        )

    def detect_action_gesture(self, hand):
        """Detect edge-triggered actions from the left hand."""

        hand = self.get_hand(hand)

        if hand is None:
            if self.action_dragging:
                self.action_dragging = False
                self.previous_action_gesture = None
                return "DRAG_END"

            self.previous_action_gesture = None
            return None

        if self.is_scroll_gesture_active(hand):
            if self.action_dragging:
                self.action_dragging = False
                self.previous_action_gesture = None
                return "DRAG_END"

            self.previous_action_gesture = None
            return None

        if self.is_open_palm(hand):
            if self.action_dragging:
                self.action_dragging = False
                self.previous_action_gesture = None
                return "DRAG_END"

            self.previous_action_gesture = "OPEN_PALM"
            return None

        if self.is_closed_fist(hand):
            if not self.action_dragging:
                self.action_dragging = True
                self.previous_action_gesture = "CLOSED_FIST"
                return "DRAG_START"

            self.previous_action_gesture = "CLOSED_FIST"
            return "DRAGGING"

        if self.action_dragging:
            self.action_dragging = False
            self.previous_action_gesture = None
            return "DRAG_END"

        if self.is_index_only(hand):
            if self.previous_action_gesture != "INDEX_ONLY":
                self.previous_action_gesture = "INDEX_ONLY"
                return "LEFT_CLICK"

            return None

        if self.is_middle_only(hand):
            if self.previous_action_gesture != "MIDDLE_ONLY":
                self.previous_action_gesture = "MIDDLE_ONLY"
                return "DOUBLE_CLICK"

            return None

        if self.is_pinky_only(hand):
            if self.previous_action_gesture != "PINKY_ONLY":
                self.previous_action_gesture = "PINKY_ONLY"
                return "RIGHT_CLICK"

            return None

        self.previous_action_gesture = None
        return None

    # =========================================================
    # Left click / drag
    # =========================================================

    def _update_pinch_state(
        self,
        point_a,
        point_b,
        active,
    ):
        """Apply hysteresis so small tracking noise cannot toggle a pinch."""

        distance = self.distance(point_a, point_b)

        if active:
            return distance < self.pinch_release_threshold

        return distance < self.pinch_start_threshold

    def _update_left_gesture(self, hand):

        self.left_pinch_active = self._update_pinch_state(
            hand.thumb_tip,
            hand.index_tip,
            self.left_pinch_active,
        )

        middle_extended = self.is_middle_extended(hand)

        ring_pinching = self.is_thumb_ring_pinching(hand)
        middle_pinching = self.is_thumb_middle_pinching(hand)

        valid = (
            self.left_pinch_active
            and middle_extended
            and not ring_pinching
            and not middle_pinching
        )

        if valid:
            self.left_stable_count += 1
        else:
            self.left_stable_count = 0

        return (
            valid
            and self.left_stable_count
            >= self.click_stable_frames
        )

    def detect_left_action(self, hand):

        hand = self.get_hand(hand)

        if hand is None:
            return None

        valid = self._update_left_gesture(hand)

        now = monotonic()

        if valid and not self.previous_left_pinching:
            self.left_pinch_start_time = now

        action = None

        if valid:

            if (
                self.left_pinch_start_time is not None
                and not self.dragging
                and now - self.left_pinch_start_time
                >= self.drag_hold_duration
            ):

                self.dragging = True

                action = "DRAG_START"

            elif self.dragging:

                action = "DRAGGING"

        elif self.previous_left_pinching:

            if self.dragging:

                self.dragging = False

                action = "DRAG_END"

            elif (
                self.left_pinch_start_time is not None
                and now - self.left_pinch_start_time
                < self.drag_hold_duration
                and now - self.last_left_click_time
                >= self.click_cooldown
            ):

                action = "LEFT_CLICK"
                self.last_left_click_time = now

            self.left_pinch_start_time = None

        self.previous_left_pinching = valid

        return action

    # =========================================================
    # Right click
    # =========================================================

    def detect_right_click(self, hand):

        hand = self.get_hand(hand)

        if hand is None:
            return None

        self.right_pinch_active = self._update_pinch_state(
            hand.thumb_tip,
            hand.middle_tip,
            self.right_pinch_active,
        )

        pinching = (
            self.right_pinch_active
            and not self.is_thumb_index_pinching(hand)
            and not self.is_thumb_ring_pinching(hand)
        )

        if pinching:
            self.right_stable_count += 1
        else:
            self.right_stable_count = 0

        action = None

        now = monotonic()

        if (
            pinching
            and not self.previous_right_pinching
            and self.right_stable_count
            >= self.click_stable_frames
            and now - self.last_right_click_time
            >= self.right_click_cooldown
        ):

            action = "RIGHT_CLICK"

            self.last_right_click_time = now

        self.previous_right_pinching = pinching

        return action

    # =========================================================
    # Double click
    # =========================================================

    def detect_double_click(self, hand):

        hand = self.get_hand(hand)

        if hand is None:
            return None

        self.double_pinch_active = self._update_pinch_state(
            hand.thumb_tip,
            hand.ring_tip,
            self.double_pinch_active,
        )

        pinching = (
            self.double_pinch_active
            and not self.is_thumb_index_pinching(hand)
            and not self.is_thumb_middle_pinching(hand)
        )

        if pinching:
            self.double_click_stable_count += 1
        else:
            self.double_click_stable_count = 0

        action = None

        if (
            pinching
            and not self.previous_double_click_pinching
            and self.double_click_stable_count
            >= self.click_stable_frames
            and monotonic() - self.last_double_click_time
            >= self.click_cooldown
        ):

            action = "DOUBLE_CLICK"
            self.last_double_click_time = monotonic()

        self.previous_double_click_pinching = pinching

        return action

    # =========================================================
    # Continuous scrolling
    # =========================================================

    def is_scroll_gesture_active(self, landmarks):
        """
        Detect the Index + Middle scroll gesture.

        Index, middle, and thumb must be extended while ring
        and pinky remain folded.

        Accepts either raw MediaPipe landmarks or HandData.
        """

        hand = self.get_hand(landmarks)

        if hand is None:
            return False

        return (
            self.is_thumb_extended(hand)
            and self.is_index_extended(hand)
            and self.is_middle_extended(hand)
            and not self.is_ring_extended(hand)
            and not self.is_pinky_extended(hand)
        )

    def detect_scroll(self, hand):
        """
        Continuous vertical and horizontal scrolling.

        Interaction:

            1. Extend Index + Middle + Thumb.
            2. Keep Ring + Pinky folded.
            2. Move the hand up/down/left/right.
            3. The dominant movement direction is selected.
            4. Scrolling continues automatically.
            5. Release either finger to stop.

        Returns:

            Positive integer -> vertical scroll up
            Negative integer -> vertical scroll down
            0                 -> no vertical scroll event

        Horizontal scrolling is stored in
        self.horizontal_scroll_amount so the main application
        can perform a horizontal mouse-wheel action.
        """

        hand = self.get_hand(hand)
        active = self.is_scroll_gesture_active(hand)

        # Reset the horizontal amount at the beginning of
        # every frame.
        self.horizontal_scroll_amount = 0

        # -----------------------------------------------------
        # Gesture released.
        # -----------------------------------------------------

        if not active:

            self.previous_scroll_active = False
            self.previous_scroll_x = None
            self.previous_scroll_y = None

            self.scroll_axis = None
            self.scroll_direction = 0

            self.last_scroll_update_time = 0

            return 0

        current_x = hand.wrist.x
        current_y = hand.wrist.y

        # -----------------------------------------------------
        # First frame of the scroll gesture.
        # -----------------------------------------------------

        if not self.previous_scroll_active:

            self.previous_scroll_active = True

            self.previous_scroll_x = current_x
            self.previous_scroll_y = current_y

            self.scroll_axis = None
            self.scroll_direction = 0

            self.last_scroll_update_time = monotonic()

            return 0

        # -----------------------------------------------------
        # Calculate movement.
        #
        # MediaPipe coordinates:
        #
        # X increases from left to right.
        # Y increases from top to bottom.
        #
        # Therefore:
        #
        # movement_x > 0 -> hand moved right
        # movement_x < 0 -> hand moved left
        #
        # movement_y > 0 -> hand moved up
        # movement_y < 0 -> hand moved down
        # -----------------------------------------------------

        movement_x = (
            current_x
            - self.previous_scroll_x
        )

        movement_y = (
            self.previous_scroll_y
            - current_y
        )

        self.previous_scroll_x = current_x
        self.previous_scroll_y = current_y

        # -----------------------------------------------------
        # Select the dominant scroll axis.
        #
        # The larger movement determines whether the user
        # intends to scroll vertically or horizontally.
        # -----------------------------------------------------

        movement_x_abs = abs(movement_x)
        movement_y_abs = abs(movement_y)

        if (
            self.scroll_axis is None
            and max(
                movement_x_abs,
                movement_y_abs,
            )
            >= self.scroll_direction_change_threshold
        ):

            if (
                movement_y_abs
                >= movement_x_abs * self.scroll_axis_dominance
            ):

                self.scroll_axis = "vertical"

                if movement_y > 0:
                    self.scroll_direction = 1
                else:
                    self.scroll_direction = -1

            elif (
                movement_x_abs
                >= movement_y_abs * self.scroll_axis_dominance
            ):

                self.scroll_axis = "horizontal"

                if movement_x > 0:
                    self.scroll_direction = 1
                else:
                    self.scroll_direction = -1

        # -----------------------------------------------------
        # Change direction while remaining on the same axis.
        # -----------------------------------------------------

        elif self.scroll_axis == "vertical":

            if (
                movement_y_abs
                >= self.scroll_direction_change_threshold
            ):

                if movement_y > 0:
                    self.scroll_direction = 1
                else:
                    self.scroll_direction = -1

        elif self.scroll_axis == "horizontal":

            if (
                movement_x_abs
                >= self.scroll_direction_change_threshold
            ):

                if movement_x > 0:
                    self.scroll_direction = 1
                else:
                    self.scroll_direction = -1

        # -----------------------------------------------------
        # Direction has not been selected yet.
        # -----------------------------------------------------

        if (
            self.scroll_axis is None
            or self.scroll_direction == 0
        ):
            return 0

        # -----------------------------------------------------
        # Generate scroll events continuously.
        # -----------------------------------------------------

        now = monotonic()

        if (
            now - self.last_scroll_update_time
            < self.scroll_update_interval
        ):
            return 0

        self.last_scroll_update_time = now

        # -----------------------------------------------------
        # Continuous vertical scrolling.
        # -----------------------------------------------------

        if self.scroll_axis == "vertical":

            return (
                self.scroll_direction
                * self.scroll_speed
            )

        # -----------------------------------------------------
        # Continuous horizontal scrolling.
        #
        # Store the value separately because pyautogui.scroll()
        # handles vertical scrolling.
        # -----------------------------------------------------

        self.horizontal_scroll_amount = (
            self.scroll_direction
            * self.scroll_speed
        )

        return 0

    # =========================================================
    # Main gesture detection
    # =========================================================

    def detect_gesture(self, landmarks):
        """
        Detect the highest-priority gesture.

        Accepts raw MediaPipe landmarks.
        """

        hand = self.get_hand(landmarks)

        if hand is None:
            self.reset()
            return None

        action = self.detect_action_gesture(hand)
        scroll = self.detect_scroll(hand)

        if action:
            return action

        if scroll != 0:
            return scroll

        # Horizontal scrolling is handled separately by main.py.
        if self.horizontal_scroll_amount != 0:
            return "HORIZONTAL_SCROLL"

        return None

    def _neutralize_gestures(self):
        """Clear gesture history when the hand is explicitly neutral."""

        drag_end = "DRAG_END" if self.action_dragging else None
        self.reset()
        return drag_end

    def _cancel_click_gestures(self):
        """Cancel click gestures when scrolling takes ownership."""

        drag_end = None

        if self.dragging:
            drag_end = "DRAG_END"

        self.previous_left_pinching = False
        self.left_pinch_active = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False

        self.previous_right_pinching = False
        self.right_pinch_active = False
        self.right_stable_count = 0

        self.previous_double_click_pinching = False
        self.double_pinch_active = False
        self.double_click_stable_count = 0

        return drag_end

    # =========================================================
    # Reset
    # =========================================================

    def reset(self):

        self.previous_left_pinching = False
        self.left_pinch_active = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False
        self.last_left_click_time = 0

        self.previous_action_gesture = None
        self.action_dragging = False

        self.previous_right_pinching = False
        self.right_pinch_active = False
        self.right_stable_count = 0
        self.last_right_click_time = 0

        self.previous_double_click_pinching = False
        self.double_pinch_active = False
        self.double_click_stable_count = 0
        self.last_double_click_time = 0

        self.previous_scroll_active = False
        self.previous_scroll_x = None
        self.previous_scroll_y = None

        self.scroll_axis = None
        self.scroll_direction = 0

        self.last_scroll_update_time = 0

        self.horizontal_scroll_amount = 0
