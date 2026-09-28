"""Dark glass visual system for the GestureFlow desktop utility."""


APP_STYLE = """
QMainWindow#mainWindow,
QDialog,
QWidget#controlPanel {
    background-color: #0b0f12;
    color: #f2f5f4;
}

QMainWindow#mainWindow {
    border: 1px solid rgba(255, 255, 255, 18);
}

QMainWindow#cameraPreviewWindow {
    background-color: #090d10;
}

QWidget {
    font-family: "Segoe UI";
    font-size: 13px;
    color: #f2f5f4;
}

QLabel {
    background: transparent;
}

QLabel#panelTitle {
    color: #f5f8f7;
    font-size: 24px;
    font-weight: 700;
}

QLabel#panelSubtitle,
QLabel#sectionLabel,
QLabel#statusTitle,
QLabel#dialogMessage {
    color: #879398;
}

QLabel#panelSubtitle {
    font-size: 13px;
}

QLabel#panelStatus {
    color: #73d6b0;
    font-size: 12px;
    font-weight: 600;
}

QFrame#cameraSection {
    background-color: rgba(255, 255, 255, 7);
    border: 1px solid rgba(255, 255, 255, 22);
    border-radius: 16px;
}

QLabel#cameraView {
    background-color: #10171b;
    color: #7f8e92;
    border: 1px solid rgba(255, 255, 255, 16);
    border-radius: 11px;
    font-size: 14px;
}

QFrame#statusSection {
    background-color: rgba(255, 255, 255, 9);
    border: 1px solid rgba(255, 255, 255, 18);
    border-radius: 12px;
}

QLabel#statusTitle,
QLabel#sectionLabel {
    font-size: 11px;
    font-weight: 600;
}

QLabel#statusValue {
    color: #a9b3b4;
    font-weight: 600;
}

QLabel#statusValue[state="active"] {
    color: #73d6b0;
}

QLabel#gestureValue {
    color: #f1f5f3;
    font-size: 19px;
    font-weight: 600;
}

QPushButton {
    min-height: 34px;
    border-radius: 10px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#primaryButton {
    background-color: #3a9f83;
    color: #ffffff;
    border: 1px solid #55b998;
}

QPushButton#primaryButton:hover {
    background-color: #48b393;
}

QPushButton#primaryButton:focus,
QPushButton#secondaryButton:focus,
QPushButton#textButton:focus {
    border: 1px solid #8be2c1;
}

QPushButton#secondaryButton {
    background-color: rgba(255, 255, 255, 12);
    color: #e6edeb;
    border: 1px solid rgba(255, 255, 255, 30);
}

QPushButton#secondaryButton:hover {
    background-color: rgba(255, 255, 255, 22);
}

QPushButton#textButton {
    background-color: transparent;
    color: #aab5b5;
    border: 1px solid transparent;
}

QPushButton#textButton:hover {
    color: #73d6b0;
}

QPushButton:disabled {
    background-color: rgba(255, 255, 255, 7);
    color: #627073;
    border-color: rgba(255, 255, 255, 12);
}

QLabel#dialogTitle {
    color: #f5f8f7;
    font-size: 19px;
    font-weight: 700;
}

QSlider::groove:horizontal {
    height: 4px;
    background: rgba(255, 255, 255, 22);
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #4aa98d;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 14px;
    margin: -5px 0;
    background: #dcefe8;
    border: 1px solid #73d6b0;
    border-radius: 7px;
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
