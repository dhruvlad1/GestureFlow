"""Global stylesheet for the GestureFlow desktop utility."""


APP_STYLE = """
QMainWindow#mainWindow,
QDialog,
QWidget#controlPanel {
    background-color: rgba(25, 34, 42, 238);
    color: #eef4f5;
}

QMainWindow#cameraPreviewWindow {
    background-color: #10191f;
}

QLabel#cameraView {
    background-color: #10191f;
    color: #9eafb5;
    border: none;
    font-size: 14px;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 13px;
    color: #eef4f5;
}

QLabel {
    background: transparent;
}

QLabel#panelTitle {
    color: #f5f8f8;
    font-size: 21px;
    font-weight: 700;
}

QLabel#panelSubtitle,
QLabel#sectionLabel,
QLabel#statusTitle,
QLabel#dialogMessage {
    color: #9eafb5;
}

QLabel#panelSubtitle {
    font-size: 12px;
}

QLabel#panelStatus {
    color: #71d0bd;
    font-size: 12px;
    font-weight: 600;
}

QFrame#statusSection {
    background-color: rgba(255, 255, 255, 18);
    border: 1px solid rgba(255, 255, 255, 28);
    border-radius: 10px;
}

QFrame#panelDivider {
    background-color: rgba(255, 255, 255, 32);
    border: none;
}

QLabel#statusValue {
    color: #aab9bd;
    font-weight: 600;
}

QLabel#statusValue[state="active"] {
    color: #71d0bd;
}

QLabel#gestureValue {
    color: #f1f6f5;
    font-size: 24px;
    font-weight: 600;
}

QPushButton {
    min-height: 34px;
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#primaryButton {
    background-color: #2d9d8c;
    color: #ffffff;
    border: 1px solid #49b5a4;
}

QPushButton#primaryButton:hover {
    background-color: #3aaf9e;
}

QPushButton#secondaryButton {
    background-color: rgba(255, 255, 255, 18);
    color: #e8f0ef;
    border: 1px solid rgba(255, 255, 255, 48);
}

QPushButton#secondaryButton:hover {
    background-color: rgba(255, 255, 255, 30);
}

QPushButton#textButton {
    background-color: transparent;
    color: #9eafb5;
    border: none;
}

QPushButton#textButton:hover {
    color: #71d0bd;
}

QPushButton:disabled {
    background-color: rgba(255, 255, 255, 10);
    color: #627279;
    border-color: rgba(255, 255, 255, 18);
}

QLabel#dialogTitle {
    color: #f5f8f8;
    font-size: 18px;
    font-weight: 700;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 55);
    border-radius: 4px;
}
"""


def get_app_style():
    """Return the GestureFlow application stylesheet."""

    return APP_STYLE
