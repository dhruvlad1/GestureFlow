"""
Central configuration for GestureFlow.

All user-adjustable application parameters are kept here so that
the rest of the application does not need to contain hard-coded
configuration values.
"""


# =============================================================
# Camera / Hand Tracking Configuration
# =============================================================

# Number of hands that MediaPipe should track.
MAX_NUM_HANDS = 2

# Minimum confidence required to initially detect a hand.
MIN_DETECTION_CONFIDENCE = 0.7

# Minimum confidence required to continue tracking a hand.
MIN_TRACKING_CONFIDENCE = 0.7


# =============================================================
# Gesture Detection Configuration
# =============================================================

# Distance below which a finger + thumb combination is considered
# to have started pinching.
PINCH_START_THRESHOLD = 0.075

# Distance above which a pinch is considered released.
#
# This is intentionally larger than the start threshold to provide
# hysteresis and prevent rapid gesture flickering.
PINCH_RELEASE_THRESHOLD = 0.095

# Minimum joint angle required to consider a finger extended.
FINGER_EXTENSION_ANGLE = 160

# Number of consecutive frames required to confirm a click gesture.
CLICK_STABLE_FRAMES = 3

# Minimum time between left and double-click actions.
CLICK_COOLDOWN = 0.25

# Minimum time between consecutive right clicks.
RIGHT_CLICK_COOLDOWN = 0.4

# Time for which Index + Thumb must be held before dragging starts.
DRAG_HOLD_DURATION = 0.5


# =============================================================
# Scrolling Configuration
# =============================================================

# Minimum movement required before scrolling direction is selected.
SCROLL_THRESHOLD = 0.015

# Amount of scrolling generated for each scroll event.
SCROLL_SPEED = 60

# Minimum movement required to select or change the scroll
# direction.
SCROLL_DIRECTION_CHANGE_THRESHOLD = 0.012

# Ratio required for one axis to dominate diagonal movement.
SCROLL_AXIS_DOMINANCE = 1.25

# Time interval between continuous scroll events.
#
# 0.02 seconds = maximum of approximately 50 events per second.
SCROLL_UPDATE_INTERVAL = 0.02


# =============================================================
# Cursor Configuration
# =============================================================

# Cursor smoothing factor.
#
# 1.0 = maximum responsiveness.
# Lower values provide more smoothing.
CURSOR_SMOOTHING = 1.0

# Usable horizontal MediaPipe coordinate range.
CAMERA_MIN_X = 0.10
CAMERA_MAX_X = 0.90

# Usable vertical MediaPipe coordinate range.
CAMERA_MIN_Y = 0.10
CAMERA_MAX_Y = 0.90

# Safety distance between the cursor and the physical screen edges.
SCREEN_PADDING = 5


# =============================================================
# Application Configuration
# =============================================================

# Window title used by the current OpenCV application.
WINDOW_TITLE = "GestureFlow"

# Camera device index.
#
# 0 = default webcam.
CAMERA_INDEX = 0
