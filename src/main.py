"""GestureFlow Qt application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    """
    Create and run the GestureFlow desktop utility.
    """

    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(False)

    window = MainWindow(application)
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
