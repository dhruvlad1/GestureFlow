"""
GestureFlow visualization and camera overlay.

This module is responsible only for drawing visual information
on the camera frame. It does not control the mouse or detect
gestures.
"""

import cv2


class Overlay:
    """
    Handles all visual information displayed on the camera frame.
    """

    def __init__(self):
        """
        Initialize the visualization overlay.
        """

        # -----------------------------------------------------
        # Default visualization settings.
        # -----------------------------------------------------

        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.font_scale = 0.7
        self.font_thickness = 2

        self.landmark_radius = 4
        self.connection_thickness = 2

    # =========================================================
    # Hand landmarks
    # =========================================================

    def draw_landmarks(self, frame, landmarks):
        """
        Draw hand landmarks and connections on the frame.

        landmarks should contain 21 normalized (x, y)
        coordinates from MediaPipe.
        """

        if not landmarks:
            return frame

        height, width = frame.shape[:2]

        # -----------------------------------------------------
        # Convert normalized coordinates into pixel coordinates.
        # -----------------------------------------------------

        points = []

        for x, y in landmarks:
            pixel_x = int(x * width)
            pixel_y = int(y * height)

            points.append(
                (pixel_x, pixel_y)
            )

        # -----------------------------------------------------
        # MediaPipe hand landmark connections.
        #
        # Each pair represents two connected landmarks.
        # -----------------------------------------------------

        connections = [
            # Thumb
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),

            # Index finger
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),

            # Middle finger
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),

            # Ring finger
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),

            # Pinky
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),

            # Palm
            (5, 9),
            (9, 13),
            (13, 17),
        ]

        # -----------------------------------------------------
        # Draw connections first so that landmarks appear
        # clearly on top of them.
        # -----------------------------------------------------

        for start_index, end_index in connections:
            if (
                start_index >= len(points)
                or end_index >= len(points)
            ):
                continue

            cv2.line(
                frame,
                points[start_index],
                points[end_index],
                (255, 255, 255),
                self.connection_thickness,
            )

        # -----------------------------------------------------
        # Draw each landmark.
        # -----------------------------------------------------

        for point in points:
            cv2.circle(
                frame,
                point,
                self.landmark_radius,
                (255, 255, 255),
                -1,
            )

        return frame

    # =========================================================
    # Status information
    # =========================================================

    def draw_status(self, frame, status):
        """
        Draw the current tracking/application status.
        """

        cv2.putText(
            frame,
            f"Status: {status}",
            (20, 35),
            self.font,
            self.font_scale,
            (255, 255, 255),
            self.font_thickness,
            cv2.LINE_AA,
        )

        return frame

    # =========================================================
    # Gesture information
    # =========================================================

    def draw_gesture(self, frame, gesture):
        """
        Draw the currently detected gesture.
        """

        cv2.putText(
            frame,
            f"Gesture: {gesture}",
            (20, 70),
            self.font,
            self.font_scale,
            (255, 255, 255),
            self.font_thickness,
            cv2.LINE_AA,
        )

        return frame

    # =========================================================
    # FPS information
    # =========================================================

    def draw_fps(self, frame, fps):
        """
        Draw the current frames-per-second value.
        """

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 105),
            self.font,
            self.font_scale,
            (255, 255, 255),
            self.font_thickness,
            cv2.LINE_AA,
        )

        return frame

    # =========================================================
    # Combined overlay
    # =========================================================

    def draw(
        self,
        frame,
        landmarks=None,
        gesture=None,
        status=None,
        fps=None,
    ):
        """
        Draw all available visualization information.

        Any parameter can be omitted when that information is
        not available.
        """

        if landmarks is not None:
            frame = self.draw_landmarks(
                frame,
                landmarks,
            )

        if status is not None:
            frame = self.draw_status(
                frame,
                status,
            )

        if gesture is not None:
            frame = self.draw_gesture(
                frame,
                gesture,
            )

        if fps is not None:
            frame = self.draw_fps(
                frame,
                fps,
            )

        return frame
