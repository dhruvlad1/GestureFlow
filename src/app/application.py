"""
Main application controller for GestureFlow.

This module manages the complete GestureFlow runtime pipeline:

    Camera
        ↓
    Hand Detection
        ↓
    Gesture Detection
        ↓
    Cursor / Mouse Actions
        ↓
    Visualization

The module does not contain the application entry point.
That remains in main.py.
"""

import cv2
import pyautogui

from hand_tracking.hand_detector import HandDetector
from gestures.gesture_detector import GestureDetector
from cursor.cursor_controller import CursorController
from visualization.overlay import Overlay
from utils import config


class GestureFlowApp:
    """
    Controls the complete GestureFlow application lifecycle.
    """

    def __init__(self):
        """
        Initialize all GestureFlow components.
        """

        # -----------------------------------------------------
        # Initialize camera.
        # -----------------------------------------------------

        self.cap = cv2.VideoCapture(
            config.CAMERA_INDEX
        )

        # -----------------------------------------------------
        # Initialize application components.
        # -----------------------------------------------------

        self.hand_detector = HandDetector()

        self.gesture_detector = GestureDetector()

        self.cursor_controller = CursorController()

        self.overlay = Overlay()

        # -----------------------------------------------------
        # MediaPipe VIDEO mode requires timestamps to increase
        # monotonically for the lifetime of the detector.
        # -----------------------------------------------------

        self.timestamp_ms = 0

        # -----------------------------------------------------
        # Track whether the operating system mouse button
        # is currently being held for dragging.
        # -----------------------------------------------------

        self.mouse_button_down = False

    # =========================================================
    # Application startup
    # =========================================================

    def is_camera_open(self):
        """
        Return whether the configured camera was opened
        successfully.
        """

        return self.cap.isOpened()

    def print_startup_message(self):
        """
        Print GestureFlow controls and available gestures.
        """

        print()
        print("GestureFlow started.")
        print("Controls:")
        print("  Q = Quit")
        print("  R = Reset cursor smoothing")
        print()
        print("Gestures:")
        print("  Index + Thumb = Left Click")
        print("  Hold Index + Thumb = Drag")
        print("  Middle + Thumb = Right Click")
        print("  Ring + Thumb = Double Click")
        print("  Index + Middle + Up/Down = Vertical Scroll")
        print("  Index + Middle + Left/Right = Horizontal Scroll")
        print()

    # =========================================================
    # Gesture display
    # =========================================================

    def get_display_gesture(
        self,
        gesture,
        is_scrolling,
    ):
        """
        Convert the internal gesture state into human-readable
        text for the camera overlay.
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
        Execute the operating system mouse action associated
        with the detected gesture.
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

        elif isinstance(gesture, int) and not isinstance(
            gesture,
            bool,
        ):

            # Positive values scroll upward.
            # Negative values scroll downward.
            if gesture != 0:
                pyautogui.scroll(gesture)

        elif gesture == "HORIZONTAL_SCROLL":

            # -------------------------------------------------
            # PyAutoGUI uses hscroll() for horizontal scrolling.
            #
            # Positive values:
            #     Scroll right
            #
            # Negative values:
            #     Scroll left
            # -------------------------------------------------

            horizontal_amount = (
                self.gesture_detector.horizontal_scroll_amount
            )

            if horizontal_amount != 0:
                pyautogui.hscroll(
                    horizontal_amount
                )

    # =========================================================
    # Frame processing
    # =========================================================

    def process_frame(self, frame):
        """
        Process one camera frame.

        This includes:
        - hand detection
        - gesture detection
        - cursor movement
        - mouse actions
        - visualization
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
            # Convert MediaPipe landmarks into HandData.
            # -------------------------------------------------

            hand = self.gesture_detector.get_hand(
                landmarks
            )

            if hand is None:
                return frame

            # -------------------------------------------------
            # Detect gestures.
            # -------------------------------------------------

            gesture = self.gesture_detector.detect_gesture(
                hand
            )

            # -------------------------------------------------
            # Check whether the scroll gesture is currently
            # active.
            #
            # This is intentionally checked separately from
            # the returned scroll amount because continuous
            # scrolling may return 0 during a short interval
            # between scroll events.
            # -------------------------------------------------

            is_scrolling = (
                self.gesture_detector.is_scroll_gesture_active(
                    hand
                )
            )

            # -------------------------------------------------
            # Index fingertip controls cursor movement.
            #
            # Cursor movement is completely disabled while
            # Index + Middle are being used for scrolling.
            # -------------------------------------------------

            if not is_scrolling:

                index_tip = landmarks[8]

                self.cursor_controller.move_cursor(
                    index_tip.x,
                    index_tip.y,
                )

            # -------------------------------------------------
            # Perform mouse actions.
            # -------------------------------------------------

            self.handle_gesture(
                gesture
            )

            # -------------------------------------------------
            # Determine the gesture text shown on the camera
            # overlay.
            # -------------------------------------------------

            display_gesture = self.get_display_gesture(
                gesture,
                is_scrolling,
            )

            # -------------------------------------------------
            # Draw hand landmarks.
            # -------------------------------------------------

            self.overlay.draw_landmarks(
                frame,
                [
                    (landmark.x, landmark.y)
                    for landmark in landmarks
                ],
            )

            # -------------------------------------------------
            # Draw current gesture and tracking status.
            # -------------------------------------------------

            self.overlay.draw_gesture(
                frame,
                display_gesture,
            )

            self.overlay.draw_status(
                frame,
                "Hand detected",
            )

        else:

            # -------------------------------------------------
            # Display tracking status when no hand is detected.
            # -------------------------------------------------

            self.overlay.draw_status(
                frame,
                "No hand detected",
            )

            self.overlay.draw_gesture(
                frame,
                "NO HAND",
            )

            # Prevent a cursor jump when the hand disappears.
            self.cursor_controller.reset()

            # Never leave the mouse button held down
            # if tracking is lost during a drag.
            if self.mouse_button_down:
                pyautogui.mouseUp()
                self.mouse_button_down = False

            self.gesture_detector.reset()

        # -----------------------------------------------------
        # Display gesture controls.
        # -----------------------------------------------------

        cv2.putText(
            frame,
            "Index + Thumb = Left Click",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Hold Index + Thumb = Drag",
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Middle + Thumb = Right Click",
            (20, 195),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Ring + Thumb = Double Click",
            (20, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            "Index + Middle = Scroll",
            (20, 245),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # -----------------------------------------------------
        # Display keyboard controls at the bottom.
        # -----------------------------------------------------

        cv2.putText(
            frame,
            "Q = Quit | R = Reset",
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

        return frame

    # =========================================================
    # Main application loop
    # =========================================================

    def run(self):
        """
        Start the GestureFlow application loop.
        """

        if not self.is_camera_open():
            print("Could not open camera.")
            self.cleanup()
            return

        self.print_startup_message()

        # -----------------------------------------------------
        # Main loop.
        # -----------------------------------------------------

        while True:

            ret, frame = self.cap.read()

            if not ret:
                print("Failed to read camera frame.")
                break

            frame = self.process_frame(
                frame
            )

            cv2.imshow(
                config.WINDOW_TITLE,
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            # -------------------------------------------------
            # Quit.
            # -------------------------------------------------

            if key == ord("q"):
                break

            # -------------------------------------------------
            # Reset cursor smoothing.
            # -------------------------------------------------

            if key == ord("r"):
                self.cursor_controller.reset()

        self.cleanup()

    # =========================================================
    # Cleanup
    # =========================================================

    def cleanup(self):
        """
        Release all resources and safely terminate the
        application.
        """

        # -----------------------------------------------------
        # Never leave the mouse button held down.
        # -----------------------------------------------------

        if self.mouse_button_down:
            pyautogui.mouseUp()
            self.mouse_button_down = False

        # -----------------------------------------------------
        # Release camera and OpenCV resources.
        # -----------------------------------------------------

        if self.cap is not None:
            self.cap.release()

        cv2.destroyAllWindows()

        # -----------------------------------------------------
        # Release MediaPipe resources.
        # -----------------------------------------------------

        if self.hand_detector is not None:
            self.hand_detector.close()
