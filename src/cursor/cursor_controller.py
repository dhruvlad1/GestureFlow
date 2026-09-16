import pyautogui


class CursorController:
    """
    Controls the operating system cursor using hand coordinates.
    """

    def __init__(
        self,
        smoothing=1,
        margin=0.1,
        screen_padding=5,
    ):
        """
        smoothing:
            Controls cursor responsiveness.
            1.0 = no smoothing / maximum responsiveness.

        margin:
            Percentage of the camera frame excluded from the
            movement area.

        screen_padding:
            Minimum number of pixels kept away from the screen
            edges to prevent PyAutoGUI fail-safe activation.
        """

        self.smoothing = smoothing
        self.margin = margin
        self.screen_padding = screen_padding

        self.screen_width, self.screen_height = (
            pyautogui.size()
        )

        self.previous_x = None
        self.previous_y = None

    def map_coordinates(self, x, y):
        """
        Convert normalized camera coordinates (0-1)
        into safe screen coordinates.
        """

        min_value = self.margin
        max_value = 1.0 - self.margin

        # Restrict camera coordinates to the control area.
        x = max(min_value, min(x, max_value))
        y = max(min_value, min(y, max_value))

        # Convert to 0-1 range.
        x = (
            (x - min_value)
            / (max_value - min_value)
        )

        y = (
            (y - min_value)
            / (max_value - min_value)
        )

        # Keep cursor away from exact screen corners.
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
        Apply exponential smoothing to cursor coordinates.
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
        hand coordinates.
        """

        screen_x, screen_y = self.map_coordinates(
            x,
            y
        )

        screen_x, screen_y = self.smooth_coordinates(
            screen_x,
            screen_y
        )

        pyautogui.moveTo(
            int(screen_x),
            int(screen_y),
            duration=0
        )

    def left_click(self):
        """
        Perform a left mouse click.
        """

        pyautogui.click()

    def right_click(self):
        """
        Perform a right mouse click.
        """

        pyautogui.rightClick()

    def reset(self):
        """
        Reset the smoothing state.
        """

        self.previous_x = None
        self.previous_y = None