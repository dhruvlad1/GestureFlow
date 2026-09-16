import cv2

from hand_tracking.hand_detector import HandDetector


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

    detector = HandDetector()

    print("GestureFlow started. Press 'q' to quit.")

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
        results = detector.find_hands(frame, timestamp_ms)

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:

                # Get index fingertip landmark.
                index_tip = hand_landmarks[8]

                # Print normalized coordinates.
                print(
                    f"Index Tip -> "
                    f"x: {index_tip.x:.3f}, "
                    f"y: {index_tip.y:.3f}"
                )

                # Convert normalized landmarks to pixel coordinates.
                points = []

                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])

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

        cv2.imshow("GestureFlow - Hand Tracking", frame)

        # Press Q to quit.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    detector.close()
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()