import sys
import traceback
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

class GlobalErrorTracker:
    """
    A standalone smart engine to intercept unhandled exceptions
    across the entire application without modifying existing try/except blocks.
    Catches unexpected errors, prevents cascading loops, and displays a clean error dialog.
    """
    _is_displaying_error = False
    
    @classmethod
    def _exception_hook(cls, exc_type, exc_value, exc_traceback):
        # 1. Do not intercept keyboard interrupts or system exit — allow clean termination!
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 2. Always log to terminal via standard excepthook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

        # 3. Anti-storm re-entrancy guard:
        # If an error dialog is ALREADY open, suppress secondary modal popups!
        if cls._is_displaying_error:
            return

        cls._is_displaying_error = True
        try:
            # Format the traceback
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Show professional UI error
            error_msg = (
                f"An unexpected error occurred.\n\n"
                f"Error Type: {exc_type.__name__}\n"
                f"Details: {exc_value}\n\n"
                f"Please check the detailed text for the full traceback."
            )
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("DrawMotion System Error")
            msg_box.setText(error_msg)
            msg_box.setDetailedText(tb_str)
            # Use theme colors directly via stylesheet
            msg_box.setStyleSheet(
                "QMessageBox { background-color: #222A27; color: white; } "
                "QLabel { color: white; } "
                "QTextEdit { background-color: #111; color: #ff5555; } "
                "QPushButton { background-color: #F44336; color: white; padding: 5px 15px; border-radius: 4px; }"
            )
            msg_box.exec()
        except Exception as inner_err:
            print(f"[GlobalErrorTracker] Failed to display error dialog: {inner_err}", file=sys.stderr)
        finally:
            cls._is_displaying_error = False

    @classmethod
    def initialize(cls):
        """
        Activates the global error tracker. Call this once at application startup.
        """
        sys.excepthook = cls._exception_hook
