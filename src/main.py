import cv2

from hand_tracking.hand_detector import HandDetector
from gestures.gesture_detector import GestureDetector, HandData
from cursor.cursor_controller import CursorController


# MediaPipe hand landmark connections.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17),             # Palm
]


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    hand_detector = HandDetector()

    gesture_detector = GestureDetector(
        pinch_start_threshold=0.075,
        pinch_release_threshold=0.095,
        click_stable_frames=3,
        double_click_interval=0.1,
        right_click_cooldown=0.4,
    )

    cursor_controller = CursorController(
        smoothing=1,
        margin=0.1,
    )

    print("GestureFlow started.")
    print("Move your index finger to control the cursor.")
    print("Index + Thumb = Left Click.")
    print("Index + Thumb twice = Double Click.")
    print("Middle + Thumb = Right Click.")
    print("Press 'q' to quit.")

    # MediaPipe requires strictly increasing timestamps.
    timestamp_ms = 0

    while True:
        success, frame = camera.read()

        if not success:
            print("Error: Could not read frame.")
            break

        # Mirror the camera feed.
        frame = cv2.flip(frame, 1)

        # Increase timestamp for every frame.
        timestamp_ms += 1

        # Detect hand landmarks.
        results = hand_detector.find_hands(
            frame,
            timestamp_ms
        )

        gesture_name = "NO HAND"

        if results.hand_landmarks:

            for landmarks in results.hand_landmarks:

                # Create clean hand representation.
                hand = HandData(landmarks)

                # Get index fingertip.
                index_tip = hand.index_tip

                # Detect left-click or double-click.
                click_event = (
                    gesture_detector.detect_click_event(
                        landmarks
                    )
                )

                # Detect right click.
                right_click = (
                    gesture_detector.detect_right_click(
                        landmarks
                    )
                )

                # Get current gesture states.
                is_left_pinching = (
                    gesture_detector.previous_left_pinching
                )

                is_right_pinching = (
                    gesture_detector.previous_right_pinching
                )

                # Determine current gesture.
                if click_event == "DOUBLE_CLICK":

                    # The first click was already performed
                    # during the first pinch. This click is
                    # the second click of the double-click.
                    cursor_controller.left_click()

                    gesture_name = "DOUBLE CLICK"

                elif click_event == "LEFT_CLICK":

                    cursor_controller.left_click()

                    gesture_name = "LEFT CLICK"

                elif right_click:

                    cursor_controller.right_click()

                    gesture_name = "RIGHT CLICK"

                elif is_left_pinching:

                    gesture_name = "LEFT PINCH"

                elif is_right_pinching:

                    gesture_name = "RIGHT PINCH"

                else:

                    gesture_name = "MOVE"

                # Move cursor only when no click gesture
                # is currently active.
                if (
                    not is_left_pinching
                    and not is_right_pinching
                ):
                    cursor_controller.move_cursor(
                        index_tip.x,
                        index_tip.y
                    )

                # Convert normalized landmarks to pixel coordinates.
                points = []

                for landmark in landmarks:

                    x = int(
                        landmark.x * frame.shape[1]
                    )

                    y = int(
                        landmark.y * frame.shape[0]
                    )

                    points.append((x, y))

                # Draw hand connections.
                for start, end in HAND_CONNECTIONS:

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (0, 255, 0),
                        2,
                    )

                # Draw landmarks.
                for point in points:

                    cv2.circle(
                        frame,
                        point,
                        5,
                        (0, 255, 0),
                        -1,
                    )

                # Highlight index fingertip.
                cv2.circle(
                    frame,
                    points[8],
                    8,
                    (0, 0, 255),
                    -1,
                )

                # Highlight thumb fingertip.
                cv2.circle(
                    frame,
                    points[4],
                    8,
                    (255, 0, 0),
                    -1,
                )

                # Highlight middle fingertip.
                cv2.circle(
                    frame,
                    points[12],
                    8,
                    (255, 255, 0),
                    -1,
                )

        # Display current gesture.
        cv2.putText(
            frame,
            f"Gesture: {gesture_name}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2,
        )

        # Display left-click instruction.
        cv2.putText(
            frame,
            "Index + Thumb = Left Click",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Display double-click instruction.
        cv2.putText(
            frame,
            "Pinch Twice = Double Click",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Display right-click instruction.
        cv2.putText(
            frame,
            "Middle + Thumb = Right Click",
            (20, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Display quit instruction.
        cv2.putText(
            frame,
            "Q = Quit",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Display camera feed.
        cv2.imshow(
            "GestureFlow - Hand Tracking",
            frame
        )

        # Press Q to quit.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup.
    hand_detector.close()
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
