"""
app/main.py
============
Entry point for AI Sign Bridge desktop application.
Run from the project root: python app/main.py
"""

import sys
import os
import traceback

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from app.main_window import MainWindow
from app.paths import resource_path


def exception_hook(exc_type, exc_value, exc_tb):
    """Global exception handler — show a message box instead of silent crash."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        QMessageBox.critical(None, "AI Sign Bridge - Error",
            f"An unexpected error occurred:\n\n{msg[:1000]}")
    except Exception:
        pass
    sys.exit(1)


def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)

    # Set app-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Set app icon
    icon_path = resource_path("logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set app metadata
    app.setApplicationName("AI Sign Bridge")
    app.setOrganizationName("Hackathon")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
