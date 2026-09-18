"""
GestureFlow application entry point.

The main application logic is handled by GestureFlowApp.
"""

from app.application import GestureFlowApp


def main():
    """
    Create and run the GestureFlow application.
    """

    app = GestureFlowApp()
    app.run()


if __name__ == "__main__":
    main()
