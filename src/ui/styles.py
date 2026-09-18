"""
Global stylesheet for the GestureFlow desktop application.

Keeping the stylesheet in one module makes it easier to maintain
the visual design as the application grows.
"""


# =============================================================
# Application Theme
# =============================================================

APP_STYLE = """
QMainWindow {
    background-color: #f5f7fa;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 14px;
    color: #202124;
}

QLabel {
    background: transparent;
}

QFrame {
    background-color: #ffffff;
    border: 1px solid #e1e5ea;
    border-radius: 10px;
}

QPushButton {
    background-color: #202124;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #303134;
}

QPushButton:pressed {
    background-color: #171717;
}

QPushButton:disabled {
    background-color: #d9dde2;
    color: #888888;
}
"""


def get_app_style():
    """
    Return the global GestureFlow application stylesheet.
    """

    return APP_STYLE
