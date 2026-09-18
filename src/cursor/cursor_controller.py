import pyautogui


class CursorController:
    """
    Controls the operating system cursor using hand coordinates.
    """

    def __init__(
        self,
        smoothing=1.0,
        camera_min_x=0.10,
        camera_max_x=0.90,
        camera_min_y=0.10,
        camera_max_y=0.90,
        screen_padding=5,
    ):
        """
        smoothing:
            1.0 = maximum responsiveness.
            Lower values provide more smoothing.

        camera_min_x / camera_max_x:
            Usable horizontal hand movement range.

        camera_min_y / camera_max_y:
            Usable vertical hand movement range.

        screen_padding:
            Small safety distance from the screen edges.
        """

        self.smoothing = smoothing

        self.camera_min_x = camera_min_x
        self.camera_max_x = camera_max_x

        self.camera_min_y = camera_min_y
        self.camera_max_y = camera_max_y

        self.screen_padding = screen_padding

        self.screen_width, self.screen_height = pyautogui.size()

        self.previous_x = None
        self.previous_y = None

    def map_coordinates(self, x, y):
        """
        Map the usable MediaPipe coordinate range directly
        across the usable screen area.
        """

        # Clamp camera coordinates to the usable range.
        x = max(
            self.camera_min_x,
            min(x, self.camera_max_x),
        )

        y = max(
            self.camera_min_y,
            min(y, self.camera_max_y),
        )

        # Convert camera X to 0-1.
        x = (
            (x - self.camera_min_x)
            / (self.camera_max_x - self.camera_min_x)
        )

        # Convert camera Y to 0-1.
        y = (
            (y - self.camera_min_y)
            / (self.camera_max_y - self.camera_min_y)
        )

        # Map to the usable screen area.
        min_screen_x = self.screen_padding
        max_screen_x = (
            self.screen_width
            - self.screen_padding
            - 1
        )

        min_screen_y = self.screen_padding
        max_screen_y = (
            self.screen_height
            - self.screen_padding
            - 1
        )

        screen_x = (
            min_screen_x
            + x * (max_screen_x - min_screen_x)
        )

        screen_y = (
            min_screen_y
            + y * (max_screen_y - min_screen_y)
        )

        return screen_x, screen_y

    def smooth_coordinates(self, x, y):
        """
        Apply exponential smoothing to screen coordinates.
        """

        if self.previous_x is None:
            self.previous_x = x
            self.previous_y = y
        else:
            self.previous_x = (
                self.previous_x * (1 - self.smoothing)
                + x * self.smoothing
            )

            self.previous_y = (
                self.previous_y * (1 - self.smoothing)
                + y * self.smoothing
            )

        return self.previous_x, self.previous_y

    def move_cursor(self, x, y):
        """
        Move the operating system cursor using normalized
        MediaPipe hand coordinates.
        """

        screen_x, screen_y = self.map_coordinates(x, y)

        screen_x, screen_y = self.smooth_coordinates(
            screen_x,
            screen_y,
        )

        pyautogui.moveTo(
            int(screen_x),
            int(screen_y),
            duration=0,
        )

    def left_click(self):
        """Perform a left mouse click."""

        pyautogui.click()

    def right_click(self):
        """Perform a right mouse click."""

        pyautogui.rightClick()

    def double_click(self):
        """Perform a double mouse click."""

        pyautogui.doubleClick()

    def reset(self):
        """Reset the cursor smoothing state."""

        self.previous_x = None
        self.previous_y = None
