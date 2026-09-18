from pathlib import Path

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from utils.config import (
    MAX_NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)


class HandDetector:
    """
    Handles MediaPipe hand landmark detection.
    """

    # CameraWorker mirrors frames before detection. The returned
    # MediaPipe label is therefore opposite the physical hand.
    INPUT_IS_MIRRORED = True

    def __init__(
        self,
        max_num_hands=MAX_NUM_HANDS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    ):
        # -----------------------------------------------------
        # Locate the project root.
        # -----------------------------------------------------

        project_root = Path(__file__).resolve().parents[2]

        model_path = (
            project_root
            / "models"
            / "hand_landmarker.task"
        )

        # -----------------------------------------------------
        # Configure MediaPipe model.
        # -----------------------------------------------------

        base_options = python.BaseOptions(
            model_asset_path=str(model_path)
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=(
                min_detection_confidence
            ),
            min_hand_presence_confidence=(
                min_tracking_confidence
            ),
            min_tracking_confidence=(
                min_tracking_confidence
            ),
        )

        # -----------------------------------------------------
        # Create the hand landmark detector.
        # -----------------------------------------------------

        self.detector = (
            vision.HandLandmarker.create_from_options(
                options
            )
        )

    def find_hands(self, frame, timestamp_ms):
        """
        Detect hands in a camera frame.

        timestamp_ms must increase monotonically because
        MediaPipe is running in VIDEO mode.
        """

        # -----------------------------------------------------
        # MediaPipe expects RGB images.
        # OpenCV captures frames in BGR format.
        # -----------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        # -----------------------------------------------------
        # Run MediaPipe video-mode detection.
        # -----------------------------------------------------

        results = self.detector.detect_for_video(
            mp_image,
            timestamp_ms,
        )

        return results

    @staticmethod
    def get_handedness_label(results, index):
        """Return MediaPipe's normalized label for one result hand."""

        return HandDetector.get_physical_handedness_label(
            results,
            index,
            input_is_mirrored=HandDetector.INPUT_IS_MIRRORED,
        )

    @staticmethod
    def get_physical_handedness_label(
        results,
        index,
        input_is_mirrored=True,
    ):
        """Resolve a MediaPipe label to the user's physical hand.

        MediaPipe labels are relative to the detected image. When
        processing the mirrored camera frame, physical labels must
        be swapped back to match the user's hands.
        """

        handedness = getattr(results, "handedness", None) or []

        if index >= len(handedness) or not handedness[index]:
            return None

        category = handedness[index][0]
        for value in (
            getattr(category, "category_name", None),
            getattr(category, "display_name", None),
        ):
            if not value:
                continue

            normalized = str(value).strip().casefold()

            if normalized == "left":
                label = "Left"
                break

            if normalized == "right":
                label = "Right"
                break

        else:
            return None

        if not input_is_mirrored:
            return label

        return "Right" if label == "Left" else "Left"

    def close(self):
        """
        Release the MediaPipe detector.
        """

        self.detector.close()
