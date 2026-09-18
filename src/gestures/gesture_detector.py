from dataclasses import dataclass
from math import acos, degrees, sqrt
from time import monotonic


@dataclass
class HandData:
    """
    Wrapper around MediaPipe hand landmarks.
    """

    landmarks: list

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

    Gestures:

        Index + Thumb
            -> Left Click
            -> Drag when held

        Middle + Thumb
            -> Right Click

        Ring + Thumb
            -> Double Click

        Index + Middle
            -> Continuous scrolling
    """

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(
        self,
        pinch_start_threshold=0.075,
        pinch_release_threshold=0.095,
        finger_extension_angle=160,
        click_stable_frames=3,
        right_click_cooldown=0.4,
        drag_hold_duration=0.5,
        scroll_threshold=0.015,
        scroll_speed=12,
        scroll_direction_change_threshold=0.012,
    ):

        self.pinch_start_threshold = pinch_start_threshold
        self.pinch_release_threshold = pinch_release_threshold
        self.finger_extension_angle = finger_extension_angle

        self.click_stable_frames = click_stable_frames
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

        # -----------------------------------------------------
        # Left click / drag state.
        # -----------------------------------------------------

        self.previous_left_pinching = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False

        # -----------------------------------------------------
        # Right click state.
        # -----------------------------------------------------

        self.previous_right_pinching = False
        self.right_stable_count = 0
        self.last_right_click_time = 0

        # -----------------------------------------------------
        # Double click state.
        # -----------------------------------------------------

        self.previous_double_click_pinching = False
        self.double_click_stable_count = 0

        # -----------------------------------------------------
        # Continuous scroll state.
        # -----------------------------------------------------

        self.previous_scroll_active = False
        self.previous_scroll_y = None

        # 1  = scrolling up
        # -1 = scrolling down
        # 0  = direction not selected
        self.scroll_direction = 0

        # Time of the most recent scroll event.
        self.last_scroll_update_time = 0

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
    def get_hand(landmarks):
        """
        Convert raw MediaPipe landmarks into HandData.

        The rest of the application can continue passing the
        raw MediaPipe landmark list into detect_gesture().
        """

        if landmarks is None:
            return None

        if isinstance(landmarks, HandData):
            return landmarks

        return HandData(landmarks)

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

    # =========================================================
    # Left click / drag
    # =========================================================

    def _update_left_gesture(self, hand):

        pinching = self.is_thumb_index_pinching(hand)

        middle_extended = self.is_middle_extended(hand)

        ring_pinching = self.is_thumb_ring_pinching(hand)

        valid = (
            pinching
            and middle_extended
            and not ring_pinching
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
            ):

                action = "LEFT_CLICK"

            self.left_pinch_start_time = None

        self.previous_left_pinching = valid

        return action

    # =========================================================
    # Right click
    # =========================================================

    def detect_right_click(self, hand):

        pinching = self.is_thumb_middle_pinching(hand)

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

        pinching = self.is_thumb_ring_pinching(hand)

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
        ):

            action = "DOUBLE_CLICK"

        self.previous_double_click_pinching = pinching

        return action

    # =========================================================
    # Continuous scrolling
    # =========================================================

    def is_scroll_gesture_active(self, landmarks):
        """
        Detect the Index + Middle scroll gesture.

        Both the index and middle fingers must be extended.

        Accepts either raw MediaPipe landmarks or HandData.
        """

        hand = self.get_hand(landmarks)

        if hand is None:
            return False

        return (
            self.is_index_extended(hand)
            and self.is_middle_extended(hand)
        )

    def detect_scroll(self, hand):
        """
        Continuous scrolling.

        Interaction:

            1. Extend Index + Middle.
            2. Move the hand slightly up or down.
            3. Direction is selected.
            4. Scrolling continues automatically.
            5. Release either finger to stop.

        Returns:

            Positive integer -> scroll up
            Negative integer -> scroll down
            0                 -> no scroll event
        """

        active = self.is_scroll_gesture_active(hand)

        # -----------------------------------------------------
        # Gesture released.
        # -----------------------------------------------------

        if not active:

            self.previous_scroll_active = False
            self.previous_scroll_y = None
            self.scroll_direction = 0
            self.last_scroll_update_time = 0

            return 0

        current_y = hand.wrist.y

        # -----------------------------------------------------
        # First frame of the scroll gesture.
        # -----------------------------------------------------

        if not self.previous_scroll_active:

            self.previous_scroll_active = True
            self.previous_scroll_y = current_y
            self.scroll_direction = 0
            self.last_scroll_update_time = monotonic()

            return 0

        # -----------------------------------------------------
        # Calculate movement.
        #
        # MediaPipe Y increases downward.
        #
        # Upward movement:
        #     previous_y - current_y > 0
        #
        # Downward movement:
        #     previous_y - current_y < 0
        # -----------------------------------------------------

        movement = (
            self.previous_scroll_y
            - current_y
        )

        self.previous_scroll_y = current_y

        # -----------------------------------------------------
        # Select / change direction.
        #
        # A relatively small movement is enough to change
        # direction. Once selected, the direction remains
        # active even when the hand stops moving.
        # -----------------------------------------------------

        if (
            abs(movement)
            >= self.scroll_direction_change_threshold
        ):

            if movement > 0:
                self.scroll_direction = 1
            else:
                self.scroll_direction = -1

        # -----------------------------------------------------
        # Direction has not been selected yet.
        # -----------------------------------------------------

        if self.scroll_direction == 0:
            return 0

        # -----------------------------------------------------
        # Generate scroll events continuously.
        #
        # 0.02 seconds = up to 50 scroll events per second.
        # -----------------------------------------------------

        now = monotonic()

        if (
            now - self.last_scroll_update_time
            < 0.02
        ):
            return 0

        self.last_scroll_update_time = now

        # -----------------------------------------------------
        # Continuous scrolling.
        # -----------------------------------------------------

        return (
            self.scroll_direction
            * self.scroll_speed
        )

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
            return None

        # -----------------------------------------------------
        # Double click.
        # -----------------------------------------------------

        double_click = self.detect_double_click(hand)

        if double_click:
            return double_click

        # -----------------------------------------------------
        # Left click / drag.
        # -----------------------------------------------------

        left_action = self.detect_left_action(hand)

        if left_action:
            return left_action

        # -----------------------------------------------------
        # Right click.
        # -----------------------------------------------------

        right_click = self.detect_right_click(hand)

        if right_click:
            return right_click

        # -----------------------------------------------------
        # Continuous scroll.
        # -----------------------------------------------------

        scroll = self.detect_scroll(hand)

        if scroll != 0:
            return scroll

        return None

    # =========================================================
    # Reset
    # =========================================================

    def reset(self):

        self.previous_left_pinching = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False

        self.previous_right_pinching = False
        self.right_stable_count = 0
        self.last_right_click_time = 0

        self.previous_double_click_pinching = False
        self.double_click_stable_count = 0

        self.previous_scroll_active = False
        self.previous_scroll_y = None
        self.scroll_direction = 0
        self.last_scroll_update_time = 0
