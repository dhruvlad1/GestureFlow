"""
Camera processing worker for GestureFlow.

This module runs camera capture and frame processing outside
the Qt user-interface thread.
"""

import cv2

from PySide6.QtCore import QObject, Signal, Slot

from hand_tracking.hand_detector import HandDetector
from gestures.gesture_detector import GestureDetector
from cursor.cursor_controller import CursorController
from visualization.overlay import Overlay
from utils import config

import pyautogui


class CameraWorker(QObject):
    """
    Handles camera capture and GestureFlow processing.

    The worker is designed to run inside a dedicated QThread
    so that camera processing does not block the UI.
    """

    # ---------------------------------------------------------
    # Signals sent from the worker to the UI.
    # ---------------------------------------------------------

    frame_ready = Signal(object)

    status_changed = Signal(str)

    gesture_changed = Signal(str)

    finished = Signal()

    error = Signal(str)

    def __init__(self):
        """
        Initialize the camera worker.
        """

        super().__init__()

        # -----------------------------------------------------
        # Runtime state.
        # -----------------------------------------------------

        self.running = False

        self.cap = None

        self.timestamp_ms = 0

        self.mouse_button_down = False

        # -----------------------------------------------------
        # GestureFlow components.
        # -----------------------------------------------------

        self.hand_detector = None

        self.gesture_detector = None

        self.cursor_controller = None

        self.overlay = None

    # =========================================================
    # Worker lifecycle
    # =========================================================

    @Slot()
    def start(self):
        """
        Start camera capture and processing.

        This method is executed inside the worker thread.
        """

        if self.running:
            return

        # -----------------------------------------------------
        # Open camera.
        # -----------------------------------------------------

        self.cap = cv2.VideoCapture(
            config.CAMERA_INDEX
        )

        if not self.cap.isOpened():
            self.error.emit(
                "Could not open camera."
            )

            self.finished.emit()

            return

        # -----------------------------------------------------
        # Initialize GestureFlow components.
        # -----------------------------------------------------

        try:

            self.hand_detector = HandDetector()

            self.gesture_detector = GestureDetector()

            self.cursor_controller = CursorController()

            self.overlay = Overlay()

        except Exception as exc:

            self.error.emit(
                f"Failed to initialize GestureFlow: {exc}"
            )

            self.cleanup()

            self.finished.emit()

            return

        # -----------------------------------------------------
        # Start processing.
        # -----------------------------------------------------

        self.running = True

        self.status_changed.emit(
            "Camera active"
        )

        # -----------------------------------------------------
        # Camera processing loop.
        # -----------------------------------------------------

        while self.running:

            ret, frame = self.cap.read()

            if not ret:
                self.error.emit(
                    "Failed to read camera frame."
                )

                break

            frame = self.process_frame(
                frame
            )

            self.frame_ready.emit(
                frame
            )

        # -----------------------------------------------------
        # Worker has stopped.
        # -----------------------------------------------------

        self.cleanup()

        self.finished.emit()

    @Slot()
    def stop(self):
        """
        Request the camera-processing loop to stop.
        """

        self.running = False

    # =========================================================
    # Frame processing
    # =========================================================

    def process_frame(self, frame):
        """
        Process a single camera frame.

        This follows the same GestureFlow processing pipeline
        previously used by the OpenCV application.
        """

        # -----------------------------------------------------
        # Mirror the camera feed.
        # -----------------------------------------------------

        frame = cv2.flip(
            frame,
            1,
        )

        self.timestamp_ms += 1

        results = self.hand_detector.find_hands(
            frame,
            self.timestamp_ms,
        )

        landmarks = None

        if results and results.hand_landmarks:
            landmarks = results.hand_landmarks[0]

        if landmarks:

            # -------------------------------------------------
            # Convert landmarks into HandData.
            # -------------------------------------------------

            hand = self.gesture_detector.get_hand(
                landmarks
            )

            if hand is None:
                return frame

            # -------------------------------------------------
            # Detect gesture.
            # -------------------------------------------------

            gesture = self.gesture_detector.detect_gesture(
                hand
            )

            is_scrolling = (
                self.gesture_detector.is_scroll_gesture_active(
                    hand
                )
            )

            # -------------------------------------------------
            # Move cursor unless the user is scrolling.
            # -------------------------------------------------

            if not is_scrolling:

                index_tip = landmarks[8]

                self.cursor_controller.move_cursor(
                    index_tip.x,
                    index_tip.y,
                )

            # -------------------------------------------------
            # Execute mouse action.
            # -------------------------------------------------

            self.handle_gesture(
                gesture
            )

            # -------------------------------------------------
            # Determine display gesture.
            # -------------------------------------------------

            display_gesture = (
                self.get_display_gesture(
                    gesture,
                    is_scrolling,
                )
            )

            # -------------------------------------------------
            # Draw landmarks.
            # -------------------------------------------------

            self.overlay.draw_landmarks(
                frame,
                [
                    (
                        landmark.x,
                        landmark.y,
                    )
                    for landmark in landmarks
                ],
            )

            # -------------------------------------------------
            # Draw status and gesture.
            # -------------------------------------------------

            self.overlay.draw_status(
                frame,
                "Hand detected",
            )

            self.overlay.draw_gesture(
                frame,
                display_gesture,
            )

            self.status_changed.emit(
                "Hand detected"
            )

            self.gesture_changed.emit(
                str(display_gesture)
            )

        else:

            # -------------------------------------------------
            # No hand detected.
            # -------------------------------------------------

            self.overlay.draw_status(
                frame,
                "No hand detected",
            )

            self.overlay.draw_gesture(
                frame,
                "NO HAND",
            )

            self.status_changed.emit(
                "No hand detected"
            )

            self.gesture_changed.emit(
                "NO HAND"
            )

            # -------------------------------------------------
            # Prevent cursor jumps after tracking is lost.
            # -------------------------------------------------

            self.cursor_controller.reset()

            # -------------------------------------------------
            # Never leave the mouse button held if tracking
            # disappears during a drag.
            # -------------------------------------------------

            if self.mouse_button_down:

                pyautogui.mouseUp()

                self.mouse_button_down = False

            self.gesture_detector.reset()

        return frame

    # =========================================================
    # Gesture display
    # =========================================================

    def get_display_gesture(
        self,
        gesture,
        is_scrolling,
    ):
        """
        Convert internal gesture state into display text.
        """

        display_gesture = gesture

        if is_scrolling:

            if self.gesture_detector.scroll_axis == "vertical":

                if self.gesture_detector.scroll_direction > 0:
                    display_gesture = "SCROLLING UP"

                elif self.gesture_detector.scroll_direction < 0:
                    display_gesture = "SCROLLING DOWN"

                else:
                    display_gesture = "SCROLL READY"

            elif self.gesture_detector.scroll_axis == "horizontal":

                if self.gesture_detector.scroll_direction > 0:
                    display_gesture = "SCROLLING RIGHT"

                elif self.gesture_detector.scroll_direction < 0:
                    display_gesture = "SCROLLING LEFT"

                else:
                    display_gesture = "SCROLL READY"

            else:

                display_gesture = "SCROLL READY"

        elif gesture is None:

            display_gesture = "MOVING"

        if self.mouse_button_down:
            display_gesture = "DRAGGING"

        return display_gesture

    # =========================================================
    # Mouse actions
    # =========================================================

    def handle_gesture(
        self,
        gesture,
    ):
        """
        Execute the mouse action associated with a gesture.
        """

        if gesture == "DOUBLE_CLICK":

            self.cursor_controller.double_click()

        elif gesture == "LEFT_CLICK":

            self.cursor_controller.left_click()

        elif gesture == "RIGHT_CLICK":

            self.cursor_controller.right_click()

        elif gesture == "DRAG_START":

            if not self.mouse_button_down:

                pyautogui.mouseDown()

                self.mouse_button_down = True

        elif gesture == "DRAG_END":

            if self.mouse_button_down:

                pyautogui.mouseUp()

                self.mouse_button_down = False

        elif isinstance(
            gesture,
            int,
        ) and not isinstance(
            gesture,
            bool,
        ):

            if gesture != 0:

                pyautogui.scroll(
                    gesture
                )

        elif gesture == "HORIZONTAL_SCROLL":

            horizontal_amount = (
                self.gesture_detector.horizontal_scroll_amount
            )

            if horizontal_amount != 0:

                pyautogui.hscroll(
                    horizontal_amount
                )

    # =========================================================
    # Cleanup
    # =========================================================

    def cleanup(self):
        """
        Release all camera, MediaPipe, and mouse resources.
        """

        # -----------------------------------------------------
        # Stop mouse dragging safely.
        # -----------------------------------------------------

        if self.mouse_button_down:

            pyautogui.mouseUp()

            self.mouse_button_down = False

        # -----------------------------------------------------
        # Release camera.
        # -----------------------------------------------------

        if self.cap is not None:

            self.cap.release()

            self.cap = None

        # -----------------------------------------------------
        # Release MediaPipe detector.
        # -----------------------------------------------------

        if self.hand_detector is not None:

            self.hand_detector.close()

            self.hand_detector = None

        # -----------------------------------------------------
        # Reset remaining components.
        # -----------------------------------------------------

        self.gesture_detector = None

        self.cursor_controller = None

        self.overlay = None
