import math
import time
from dataclasses import dataclass


@dataclass
class HandData:
    """
    Clean representation of a detected hand.
    """

    landmarks: list

    @property
    def wrist(self):
        return self.landmarks[0]

    @property
    def thumb_tip(self):
        return self.landmarks[4]

    @property
    def index_tip(self):
        return self.landmarks[8]

    @property
    def middle_tip(self):
        return self.landmarks[12]

    @property
    def ring_tip(self):
        return self.landmarks[16]

    @property
    def pinky_tip(self):
        return self.landmarks[20]


class GestureDetector:
    """
    Processes MediaPipe hand landmarks and detects gestures.

    Gesture mapping:

        Thumb + Index  -> Left Click / Drag
        Thumb + Middle -> Right Click
        Thumb + Ring   -> Double Click
        Index + Middle -> Scroll
    """

    WRIST = 0

    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(
        self,
        pinch_start_threshold=0.075,
        pinch_release_threshold=0.095,
        finger_extension_angle=160,
        click_stable_frames=3,
        right_click_cooldown=0.4,
        drag_hold_duration=0.5,
        scroll_threshold=0.008,
        scroll_multiplier=180,
        max_scroll_speed=12,
    ):
        """
        Initialize gesture detection.

        pinch_start_threshold:
            Distance required to start a pinch.

        pinch_release_threshold:
            Distance required to release a pinch.

        finger_extension_angle:
            Minimum finger angle considered extended.

        click_stable_frames:
            Number of consecutive frames required
            before a gesture is considered stable.

        right_click_cooldown:
            Minimum time between right-click events.

        drag_hold_duration:
            Time an index + thumb pinch must be held
            before drag mode starts.

        scroll_threshold:
            Minimum normalized vertical movement required
            before scrolling starts.

        scroll_multiplier:
            Controls the overall scrolling speed.

        max_scroll_speed:
            Maximum scroll amount generated per frame.
        """

        self.pinch_start_threshold = pinch_start_threshold
        self.pinch_release_threshold = pinch_release_threshold

        self.finger_extension_angle = finger_extension_angle
        self.click_stable_frames = click_stable_frames

        self.right_click_cooldown = right_click_cooldown
        self.drag_hold_duration = drag_hold_duration

        self.scroll_threshold = scroll_threshold
        self.scroll_multiplier = scroll_multiplier
        self.max_scroll_speed = max_scroll_speed

        # Left-click / drag state.
        self.previous_left_pinching = False
        self.left_stable_count = 0
        self.left_pinch_start_time = None
        self.dragging = False

        # Right-click state.
        self.previous_right_pinching = False
        self.right_stable_count = 0
        self.last_right_click_time = 0

        # Double-click state.
        self.previous_double_click_pinching = False
        self.double_click_stable_count = 0

        # Scroll state.
        self.previous_scroll_active = False
        self.previous_scroll_y = None

    # ---------------------------------------------------------
    # Basic geometry
    # ---------------------------------------------------------

    @staticmethod
    def distance(point1, point2):
        """
        Calculate 3D distance between two MediaPipe landmarks.
        """

        dx = point1.x - point2.x
        dy = point1.y - point2.y
        dz = point1.z - point2.z

        return math.sqrt(
            dx * dx +
            dy * dy +
            dz * dz
        )

    @staticmethod
    def calculate_angle(point1, point2, point3):
        """
        Calculate the angle formed by three landmarks.
        """

        vector1 = (
            point1.x - point2.x,
            point1.y - point2.y,
            point1.z - point2.z,
        )

        vector2 = (
            point3.x - point2.x,
            point3.y - point2.y,
            point3.z - point2.z,
        )

        magnitude1 = math.sqrt(
            vector1[0] ** 2 +
            vector1[1] ** 2 +
            vector1[2] ** 2
        )

        magnitude2 = math.sqrt(
            vector2[0] ** 2 +
            vector2[1] ** 2 +
            vector2[2] ** 2
        )

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        dot_product = (
            vector1[0] * vector2[0]
            + vector1[1] * vector2[1]
            + vector1[2] * vector2[2]
        )

        cosine = dot_product / (
            magnitude1 * magnitude2
        )

        cosine = max(-1.0, min(1.0, cosine))

        return math.degrees(
            math.acos(cosine)
        )

    # ---------------------------------------------------------
    # Landmark helpers
    # ---------------------------------------------------------

    def get_index_tip(self, landmarks):
        return landmarks[self.INDEX_TIP]

    def get_thumb_tip(self, landmarks):
        return landmarks[self.THUMB_TIP]

    def get_middle_tip(self, landmarks):
        return landmarks[self.MIDDLE_TIP]

    def get_ring_tip(self, landmarks):
        return landmarks[self.RING_TIP]

    def get_pinky_tip(self, landmarks):
        return landmarks[self.PINKY_TIP]

    def get_wrist(self, landmarks):
        return landmarks[self.WRIST]

    # ---------------------------------------------------------
    # Pinch detection
    # ---------------------------------------------------------

    def get_pinch_distance(self, landmarks):
        """
        Thumb + index distance.
        """

        return self.distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.INDEX_TIP],
        )

    def get_middle_pinch_distance(self, landmarks):
        """
        Thumb + middle finger distance.
        """

        return self.distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.MIDDLE_TIP],
        )

    def get_ring_pinch_distance(self, landmarks):
        """
        Thumb + ring finger distance.
        """

        return self.distance(
            landmarks[self.THUMB_TIP],
            landmarks[self.RING_TIP],
        )

    def is_pinching(self, landmarks):
        """
        Detect thumb + index pinch using hysteresis.
        """

        distance = self.get_pinch_distance(landmarks)

        if not self.previous_left_pinching:
            return distance < self.pinch_start_threshold

        return distance < self.pinch_release_threshold

    def is_middle_pinching(self, landmarks):
        """
        Detect thumb + middle finger pinch using hysteresis.
        """

        distance = self.get_middle_pinch_distance(landmarks)

        if not self.previous_right_pinching:
            return distance < self.pinch_start_threshold

        return distance < self.pinch_release_threshold

    def is_ring_pinching(self, landmarks):
        """
        Detect thumb + ring finger pinch using hysteresis.
        """

        distance = self.get_ring_pinch_distance(landmarks)

        if not self.previous_double_click_pinching:
            return distance < self.pinch_start_threshold

        return distance < self.pinch_release_threshold

    # ---------------------------------------------------------
    # Finger extension detection
    # ---------------------------------------------------------

    def is_index_extended(self, landmarks):
        angle = self.calculate_angle(
            landmarks[self.INDEX_MCP],
            landmarks[self.INDEX_PIP],
            landmarks[self.INDEX_DIP],
        )

        return angle >= self.finger_extension_angle

    def is_middle_extended(self, landmarks):
        angle = self.calculate_angle(
            landmarks[self.MIDDLE_MCP],
            landmarks[self.MIDDLE_PIP],
            landmarks[self.MIDDLE_DIP],
        )

        return angle >= self.finger_extension_angle

    def is_ring_extended(self, landmarks):
        angle = self.calculate_angle(
            landmarks[self.RING_MCP],
            landmarks[self.RING_PIP],
            landmarks[self.RING_DIP],
        )

        return angle >= self.finger_extension_angle

    def is_pinky_extended(self, landmarks):
        angle = self.calculate_angle(
            landmarks[self.PINKY_MCP],
            landmarks[self.PINKY_PIP],
            landmarks[self.PINKY_DIP],
        )

        return angle >= self.finger_extension_angle

    # ---------------------------------------------------------
    # Left click / Drag
    # ---------------------------------------------------------

    def _update_left_gesture(self, landmarks):
        """
        Update the left-click / drag gesture state.

        Left click / drag requires:

        - Thumb + index pinch
        - Middle finger extended
        - Ring finger not pinching
        - Stable gesture
        """

        index_pinch = self.is_pinching(landmarks)
        middle_pinch = self.is_middle_pinching(landmarks)
        ring_pinch = self.is_ring_pinching(landmarks)

        middle_extended = self.is_middle_extended(
            landmarks
        )

        gesture_detected = (
            index_pinch
            and middle_extended
            and not middle_pinch
            and not ring_pinch
        )

        if gesture_detected:
            self.left_stable_count += 1
        else:
            self.left_stable_count = 0

        self.left_stable_count = min(
            self.left_stable_count,
            self.click_stable_frames,
        )

        return (
            self.left_stable_count
            >= self.click_stable_frames
        )

    def detect_left_action(self, landmarks):
        """
        Detect left-click and drag events.

        Returns:

            "LEFT_CLICK"  -> short pinch
            "DRAG_START"  -> pinch held long enough
            "DRAGGING"    -> drag is active
            "DRAG_END"    -> pinch released after dragging
            None          -> no left action
        """

        pinching = self._update_left_gesture(
            landmarks
        )

        current_time = time.monotonic()

        # -----------------------------------------------------
        # Pinch started.
        # -----------------------------------------------------

        if pinching and not self.previous_left_pinching:
            self.left_pinch_start_time = current_time
            self.dragging = False

        # -----------------------------------------------------
        # Pinch is being held.
        # -----------------------------------------------------

        if pinching and self.previous_left_pinching:

            if (
                not self.dragging
                and self.left_pinch_start_time is not None
                and current_time - self.left_pinch_start_time
                >= self.drag_hold_duration
            ):
                self.dragging = True
                self.previous_left_pinching = True

                return "DRAG_START"

            if self.dragging:
                self.previous_left_pinching = True
                return "DRAGGING"

        # -----------------------------------------------------
        # Pinch released.
        # -----------------------------------------------------

        if not pinching and self.previous_left_pinching:

            was_dragging = self.dragging

            self.previous_left_pinching = False
            self.left_pinch_start_time = None
            self.dragging = False

            if was_dragging:
                return "DRAG_END"

            return "LEFT_CLICK"

        # -----------------------------------------------------
        # Update current state.
        # -----------------------------------------------------

        self.previous_left_pinching = pinching

        return None

    # ---------------------------------------------------------
    # Right click
    # ---------------------------------------------------------

    def _update_right_gesture(self, landmarks):
        """
        Update the right-click gesture state.

        Right click requires:

        - Thumb + middle pinch
        - Index finger extended
        - Thumb + index must NOT be pinching
        - Ring finger must NOT be pinching
        - Stable gesture
        """

        middle_pinch = self.is_middle_pinching(
            landmarks
        )

        index_pinch = self.is_pinching(
            landmarks
        )

        ring_pinch = self.is_ring_pinching(
            landmarks
        )

        index_extended = self.is_index_extended(
            landmarks
        )

        gesture_detected = (
            middle_pinch
            and index_extended
            and not index_pinch
            and not ring_pinch
        )

        if gesture_detected:
            self.right_stable_count += 1
        else:
            self.right_stable_count = 0

        self.right_stable_count = min(
            self.right_stable_count,
            self.click_stable_frames,
        )

        return (
            self.right_stable_count
            >= self.click_stable_frames
        )

    def detect_right_click(self, landmarks):
        """
        Detect a new right-click gesture.

        Returns:

            True  -> new right click detected
            False -> no new click
        """

        pinching = self._update_right_gesture(
            landmarks
        )

        current_time = time.monotonic()

        click_detected = False

        if (
            pinching
            and not self.previous_right_pinching
        ):
            if (
                current_time
                - self.last_right_click_time
                >= self.right_click_cooldown
            ):
                click_detected = True

                self.last_right_click_time = (
                    current_time
                )

        self.previous_right_pinching = pinching

        return click_detected

    # ---------------------------------------------------------
    # Double click
    # ---------------------------------------------------------

    def _update_double_click_gesture(self, landmarks):
        """
        Update the double-click gesture state.

        Double click requires:

        - Thumb + ring finger pinch
        - Index finger not pinching
        - Middle finger not pinching
        - Stable gesture
        """

        ring_pinch = self.is_ring_pinching(
            landmarks
        )

        index_pinch = self.is_pinching(
            landmarks
        )

        middle_pinch = self.is_middle_pinching(
            landmarks
        )

        gesture_detected = (
            ring_pinch
            and not index_pinch
            and not middle_pinch
        )

        if gesture_detected:
            self.double_click_stable_count += 1
        else:
            self.double_click_stable_count = 0

        self.double_click_stable_count = min(
            self.double_click_stable_count,
            self.click_stable_frames,
        )

        return (
            self.double_click_stable_count
            >= self.click_stable_frames
        )

    def detect_double_click(self, landmarks):
        """
        Detect a new double-click gesture.

        Thumb + ring finger pinch generates
        one DOUBLE_CLICK event.

        Returns:

            True  -> double click detected
            False -> no double click
        """

        pinching = self._update_double_click_gesture(
            landmarks
        )

        double_click_detected = (
            pinching
            and not self.previous_double_click_pinching
        )

        self.previous_double_click_pinching = pinching

        return double_click_detected

    # ---------------------------------------------------------
    # Scroll
    # ---------------------------------------------------------

    def detect_scroll(self, landmarks):
        """
        Detect continuous vertical scrolling.

        Scroll gesture:

        - Index finger extended
        - Middle finger extended
        - Ring finger folded
        - No thumb pinch

        Moving the hand upward produces a positive
        scroll amount.

        Moving the hand downward produces a negative
        scroll amount.

        The amount is proportional to the movement
        of the wrist.
        """

        index_extended = self.is_index_extended(
            landmarks
        )

        middle_extended = self.is_middle_extended(
            landmarks
        )

        ring_extended = self.is_ring_extended(
            landmarks
        )

        index_pinch = self.is_pinching(landmarks)
        middle_pinch = self.is_middle_pinching(landmarks)
        ring_pinch = self.is_ring_pinching(landmarks)

        scroll_active = (
            index_extended
            and middle_extended
            and not ring_extended
            and not index_pinch
            and not middle_pinch
            and not ring_pinch
            and not self.dragging
        )

        current_y = landmarks[self.WRIST].y

        # -----------------------------------------------------
        # Gesture is not active.
        # -----------------------------------------------------

        if not scroll_active:
            self.previous_scroll_active = False
            self.previous_scroll_y = None
            return 0

        # -----------------------------------------------------
        # First frame of scroll gesture.
        # -----------------------------------------------------

        if not self.previous_scroll_active:
            self.previous_scroll_active = True
            self.previous_scroll_y = current_y
            return 0

        # -----------------------------------------------------
        # Calculate vertical movement.
        # -----------------------------------------------------

        movement = self.previous_scroll_y - current_y

        self.previous_scroll_y = current_y

        # -----------------------------------------------------
        # Ignore tiny hand movements.
        # -----------------------------------------------------

        if abs(movement) < self.scroll_threshold:
            return 0

        # -----------------------------------------------------
        # Convert movement into scroll speed.
        # -----------------------------------------------------

        scroll_amount = (
            movement * self.scroll_multiplier
        )

        # -----------------------------------------------------
        # Limit maximum scroll speed.
        # -----------------------------------------------------

        scroll_amount = max(
            -self.max_scroll_speed,
            min(
                scroll_amount,
                self.max_scroll_speed,
            ),
        )

        # PyAutoGUI requires an integer scroll amount.
        scroll_amount = int(scroll_amount)

        # Make sure a valid movement always produces
        # at least one scroll unit.
        if scroll_amount == 0:
            scroll_amount = (
                1 if movement > 0 else -1
            )

        return scroll_amount

    # ---------------------------------------------------------
    # Combined gesture detection
    # ---------------------------------------------------------

    def detect_gesture(self, landmarks):
        """
        Detect the highest-priority mouse gesture.

        Returns:

            "DOUBLE_CLICK"
            "LEFT_CLICK"
            "RIGHT_CLICK"
            "DRAG_START"
            "DRAGGING"
            "DRAG_END"
            integer scroll amount
            "LEFT_PINCH"
            "RIGHT_PINCH"
            "DOUBLE_PINCH"
            None
        """

        # Check double click first because it uses
        # the ring finger and should have priority.
        double_click = self.detect_double_click(
            landmarks
        )

        if double_click:
            return "DOUBLE_CLICK"

        # Check left click / drag.
        left_action = self.detect_left_action(
            landmarks
        )

        if left_action is not None:
            return left_action

        # Check right click.
        right_click = self.detect_right_click(
            landmarks
        )

        if right_click:
            return "RIGHT_CLICK"

        # Check scrolling.
        scroll = self.detect_scroll(
            landmarks
        )

        if scroll != 0:
            return scroll

        # Return the current active gesture.
        if self.previous_double_click_pinching:
            return "DOUBLE_PINCH"

        if self.previous_left_pinching:
            if self.dragging:
                return "DRAGGING"

            return "LEFT_PINCH"

        if self.previous_right_pinching:
            return "RIGHT_PINCH"

        return None

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    def reset(self):
        """
        Reset all gesture states.
        """

        self.previous_left_pinching = False
        self.previous_right_pinching = False
        self.previous_double_click_pinching = False

        self.left_stable_count = 0
        self.right_stable_count = 0
        self.double_click_stable_count = 0

        self.left_pinch_start_time = None
        self.dragging = False

        self.last_right_click_time = 0

        self.previous_scroll_active = False
        self.previous_scroll_y = None
