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


def _setup_logging():
    """Ensure a valid stdout/stderr in the frozen windowed app.
    The redirect_stdio runtime hook already does this, but if it was
    skipped (e.g. running unpackaged) this is a safe fallback."""
    if not getattr(sys, 'frozen', False):
        return
    if hasattr(sys.stdout, "write") and hasattr(sys.stdout, "flush"):
        return
    try:
        log_dir = os.path.dirname(sys.executable)
        log_path = os.path.join(log_dir, "ai_sign_bridge.log")
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except Exception:
        pass


def exception_hook(exc_type, exc_value, exc_tb):
    """Global exception handler — log to file and show a message box instead of silent crash."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        if hasattr(sys.stdout, "write"):
            sys.stdout.write(f"FATAL: {msg}\n")
    except Exception:
        pass
    try:
        QMessageBox.critical(None, "AI Sign Bridge - Error",
            f"An unexpected error occurred:\n\n{msg[:1000]}")
    except Exception:
        pass
    sys.exit(1)


def main():
    _setup_logging()
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)

    # Set app-wide font (rounded clay look, Segoe UI fallback)
    font = QFont("Fredoka", 10)
    font.setFamilies(["Fredoka", "Baloo 2", "Nunito", "Quicksand", "Segoe UI", "sans-serif"])
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
