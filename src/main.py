import cv2
import pyautogui

from hand_tracking.hand_detector import HandDetector
from gestures.gesture_detector import GestureDetector
from cursor.cursor_controller import CursorController


def main():

    # ---------------------------------------------------------
    # Initialize camera.
    # ---------------------------------------------------------

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Could not open camera.")
        return

    # ---------------------------------------------------------
    # Initialize hand detector.
    # ---------------------------------------------------------

    hand_detector = HandDetector(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    # ---------------------------------------------------------
    # Initialize gesture detector.
    # ---------------------------------------------------------

    gesture_detector = GestureDetector(
        pinch_start_threshold=0.075,
        pinch_release_threshold=0.095,
        click_stable_frames=3,
        right_click_cooldown=0.4,
        drag_hold_duration=0.5,
        scroll_threshold=0.015,
        scroll_speed=60,
        scroll_direction_change_threshold=0.012,
    )

    # ---------------------------------------------------------
    # Initialize cursor controller.
    # ---------------------------------------------------------

    cursor_controller = CursorController(
        smoothing=1.0,
        camera_min_x=0.10,
        camera_max_x=0.90,
        camera_min_y=0.10,
        camera_max_y=0.90,
        screen_padding=5,
    )

    # MediaPipe VIDEO mode requires timestamps to increase
    # monotonically for the lifetime of the detector.
    timestamp_ms = 0

    # Track whether the operating system mouse button
    # is currently being held for dragging.
    mouse_button_down = False

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

    # ---------------------------------------------------------
    # Main loop.
    # ---------------------------------------------------------

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Failed to read camera frame.")
            break

        # Mirror the camera feed.
        frame = cv2.flip(frame, 1)

        timestamp_ms += 1

        results = hand_detector.find_hands(
            frame,
            timestamp_ms,
        )

        landmarks = None

        if results and results.hand_landmarks:
            landmarks = results.hand_landmarks[0]

        if landmarks:

            # -------------------------------------------------
            # Convert MediaPipe landmarks into HandData.
            # -------------------------------------------------

            hand = gesture_detector.get_hand(
                landmarks
            )

            if hand is None:
                continue

            # -------------------------------------------------
            # Detect gestures.
            # -------------------------------------------------

            gesture = gesture_detector.detect_gesture(
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
                gesture_detector.is_scroll_gesture_active(
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

                cursor_controller.move_cursor(
                    index_tip.x,
                    index_tip.y,
                )

            # -------------------------------------------------
            # Perform mouse actions.
            # -------------------------------------------------

            if gesture == "DOUBLE_CLICK":

                cursor_controller.double_click()

            elif gesture == "LEFT_CLICK":

                cursor_controller.left_click()

            elif gesture == "RIGHT_CLICK":

                cursor_controller.right_click()

            elif gesture == "DRAG_START":

                if not mouse_button_down:
                    pyautogui.mouseDown()
                    mouse_button_down = True

            elif gesture == "DRAG_END":

                if mouse_button_down:
                    pyautogui.mouseUp()
                    mouse_button_down = False

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
                    gesture_detector.horizontal_scroll_amount
                )

                if horizontal_amount != 0:
                    pyautogui.hscroll(
                        horizontal_amount
                    )

            # -------------------------------------------------
            # Draw fingertips.
            # -------------------------------------------------

            height, width = frame.shape[:2]

            index_tip_x = int(
                landmarks[8].x * width
            )

            index_tip_y = int(
                landmarks[8].y * height
            )

            middle_tip_x = int(
                landmarks[12].x * width
            )

            middle_tip_y = int(
                landmarks[12].y * height
            )

            ring_tip_x = int(
                landmarks[16].x * width
            )

            ring_tip_y = int(
                landmarks[16].y * height
            )

            cv2.circle(
                frame,
                (index_tip_x, index_tip_y),
                8,
                (0, 255, 0),
                -1,
            )

            cv2.circle(
                frame,
                (middle_tip_x, middle_tip_y),
                8,
                (255, 0, 0),
                -1,
            )

            cv2.circle(
                frame,
                (ring_tip_x, ring_tip_y),
                8,
                (0, 255, 255),
                -1,
            )

            # -------------------------------------------------
            # Display current gesture.
            # -------------------------------------------------

            display_gesture = gesture

            if is_scrolling:

                if gesture_detector.scroll_axis == "vertical":

                    if gesture_detector.scroll_direction > 0:
                        display_gesture = "SCROLLING UP"

                    elif gesture_detector.scroll_direction < 0:
                        display_gesture = "SCROLLING DOWN"

                    else:
                        display_gesture = "SCROLL READY"

                elif gesture_detector.scroll_axis == "horizontal":

                    if gesture_detector.scroll_direction > 0:
                        display_gesture = "SCROLLING RIGHT"

                    elif gesture_detector.scroll_direction < 0:
                        display_gesture = "SCROLLING LEFT"

                    else:
                        display_gesture = "SCROLL READY"

                else:

                    display_gesture = "SCROLL READY"

            elif gesture is None:

                display_gesture = "MOVING"

            if mouse_button_down:
                display_gesture = "DRAGGING"

            cv2.putText(
                frame,
                f"Gesture: {display_gesture}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        else:

            cv2.putText(
                frame,
                "No hand detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            # Prevent a cursor jump when the hand disappears.
            cursor_controller.reset()

            # Never leave the mouse button held down
            # if tracking is lost during a drag.
            if mouse_button_down:
                pyautogui.mouseUp()
                mouse_button_down = False

            gesture_detector.reset()

        # -----------------------------------------------------
        # Display gesture controls.
        # -----------------------------------------------------

        cv2.putText(
            frame,
            "Index + Thumb = Left Click",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "Hold Index + Thumb = Drag",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "Middle + Thumb = Right Click",
            (20, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "Ring + Thumb = Double Click",
            (20, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "Index + Middle = Scroll",
            (20, 175),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            "Q = Quit",
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        cv2.imshow(
            "GestureFlow",
            frame,
        )

        key = cv2.waitKey(1) & 0xFF

        # -----------------------------------------------------
        # Quit.
        # -----------------------------------------------------

        if key == ord("q"):
            break

        # -----------------------------------------------------
        # Reset cursor smoothing.
        # -----------------------------------------------------

        if key == ord("r"):
            cursor_controller.reset()

    # ---------------------------------------------------------
    # Cleanup.
    # ---------------------------------------------------------

    if mouse_button_down:
        pyautogui.mouseUp()

    cap.release()
    cv2.destroyAllWindows()
    hand_detector.close()


if __name__ == "__main__":
    main()
