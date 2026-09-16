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
        double_click_interval=0.6,
        right_click_cooldown=0.4,
    ):
        """
        Initialize gesture detection.
        """

        self.pinch_start_threshold = pinch_start_threshold
        self.pinch_release_threshold = pinch_release_threshold

        self.finger_extension_angle = finger_extension_angle
        self.click_stable_frames = click_stable_frames

        self.double_click_interval = double_click_interval
        self.right_click_cooldown = right_click_cooldown

        # Left-click state.
        self.previous_left_pinching = False
        self.left_stable_count = 0

        # Right-click state.
        self.previous_right_pinching = False
        self.right_stable_count = 0

        self.last_right_click_time = 0

        # Double-click state.
        self.pending_left_click = False
        self.previous_left_click_time = 0

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
    # Left click
    # ---------------------------------------------------------

    def _update_left_gesture(self, landmarks):
        """
        Update the left-click gesture state.

        Returns:
            True  -> left pinch is currently confirmed.
            False -> left pinch is not confirmed.
        """

        index_pinch = self.is_pinching(landmarks)
        middle_pinch = self.is_middle_pinching(landmarks)
        middle_extended = self.is_middle_extended(landmarks)

        gesture_detected = (
            index_pinch
            and middle_extended
            and not middle_pinch
        )

        if gesture_detected:
            self.left_stable_count += 1
        else:
            self.left_stable_count = 0

        self.left_stable_count = min(
            self.left_stable_count,
            self.click_stable_frames,
        )

        confirmed = (
            self.left_stable_count
            >= self.click_stable_frames
        )

        return confirmed

    def detect_click_event(self, landmarks):
        """
        Detect a left-click or double-click event.

        A click requires:
        - Thumb + index pinch
        - Middle finger extended
        - Stable gesture

        Two separate left-click gestures within
        double_click_interval are treated as a double-click.

        Returns:
            None
            "LEFT_CLICK"
            "DOUBLE_CLICK"
        """

        pinching = self._update_left_gesture(
            landmarks
        )

        current_time = time.monotonic()

        click_started = (
            pinching
            and not self.previous_left_pinching
        )

        event = None

        if click_started:

            # Second click of a double-click sequence.
            if (
                self.pending_left_click
                and (
                    current_time
                    - self.previous_left_click_time
                    <= self.double_click_interval
                )
            ):
                event = "DOUBLE_CLICK"

                self.pending_left_click = False
                self.previous_left_click_time = 0

            # First click.
            else:
                event = "LEFT_CLICK"

                self.pending_left_click = True
                self.previous_left_click_time = current_time

        # If the user takes too long to perform
        # the second click, cancel the pending sequence.
        if (
            self.pending_left_click
            and (
                current_time
                - self.previous_left_click_time
                > self.double_click_interval
            )
        ):
            self.pending_left_click = False
            self.previous_left_click_time = 0

        self.previous_left_pinching = pinching

        return event

    # ---------------------------------------------------------
    # Right click
    # ---------------------------------------------------------

    def detect_right_click(self, landmarks):
        """
        Detect a new right-click gesture.

        Requirements:
        - Thumb + middle pinch
        - Index finger extended
        - Thumb + index must NOT be pinching
        - Gesture must remain stable
        """

        middle_pinch = self.is_middle_pinching(
            landmarks
        )

        index_pinch = self.is_pinching(
            landmarks
        )

        index_extended = self.is_index_extended(
            landmarks
        )

        gesture_detected = (
            middle_pinch
            and index_extended
            and not index_pinch
        )

        if gesture_detected:
            self.right_stable_count += 1
        else:
            self.right_stable_count = 0

        self.right_stable_count = min(
            self.right_stable_count,
            self.click_stable_frames,
        )

        pinching = (
            self.right_stable_count
            >= self.click_stable_frames
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
                self.last_right_click_time = current_time

        self.previous_right_pinching = pinching

        return click_detected

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    def reset(self):
        """
        Reset all gesture states.
        """

        self.previous_left_pinching = False
        self.previous_right_pinching = False

        self.left_stable_count = 0
        self.right_stable_count = 0

        self.last_right_click_time = 0

        self.pending_left_click = False
        self.previous_left_click_time = 0