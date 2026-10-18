import sys
import traceback
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

class GlobalErrorTracker:
    """
    A standalone smart engine to intercept unhandled exceptions
    across the entire application without modifying existing try/except blocks.
    It catches the error and displays a professional QMessageBox instead of failing silently.
    """
    
    @staticmethod
    def _exception_hook(exc_type, exc_value, exc_traceback):
        # Format the traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Log to terminal (standard behavior)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        # Show professional UI error
        error_msg = f"An unexpected error occurred.\n\nError Type: {exc_type.__name__}\nDetails: {exc_value}\n\nPlease check the detailed text for the full traceback."
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("DrawMotion System Error")
        msg_box.setText(error_msg)
        msg_box.setDetailedText(tb_str)
        # Use theme colors directly via stylesheet
        msg_box.setStyleSheet("QMessageBox { background-color: #222A27; color: white; } "
                              "QLabel { color: white; } "
                              "QTextEdit { background-color: #111; color: #ff5555; } "
                              "QPushButton { background-color: #F44336; color: white; padding: 5px 15px; border-radius: 4px; }")
        msg_box.exec()

    @classmethod
    def initialize(cls):
        """
        Activates the global error tracker. Call this once at application startup.
        """
        sys.excepthook = cls._exception_hook
