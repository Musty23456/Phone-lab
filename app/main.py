"""
main.py

ALMUS PHONE LAB entry point. Sets up the QApplication, applies the dark
theme, and shows the main window. Designed to start successfully even
with no device connected and no adb/fastboot detected - all tool
lookups are defensive and surface friendly errors instead of crashing.
"""
from __future__ import annotations

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from app.ui.theme import load_stylesheet


def _install_global_exception_hook(app: QApplication):
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(message, file=sys.stderr)
        try:
            QMessageBox.critical(
                None,
                "ALMUS PHONE LAB - Unexpected Error",
                "An unexpected error occurred. The application will try to "
                "continue running.\n\nDetails:\n" + str(exc_value),
            )
        except Exception:
            pass

    sys.excepthook = handle_exception


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ALMUS PHONE LAB")
    app.setOrganizationName("ALMUS PRODUCTION")

    _install_global_exception_hook(app)

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
