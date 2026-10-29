"""
Purpose: Dedicated Disaster Recovery Dialog for DrawMotion.
Features:
- Pops up when Boot Health Watchdog detects repeated startup crashes.
- Provides 1-click rollback to the previous stable release.
- Provides Safe Mode launch option and instant crash log viewer.
Zero emojis, clean Qt dark styling, 100% resilient.
"""

import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from utils.theme import THEME_COLORS
from utils.icons import get_icon
from core.recovery_engine.watchdog import (
    get_previous_installer_info, launch_rollback_installer, save_boot_health, load_boot_health
)

class SafeRecoveryDialog(QDialog):
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.prev_version, self.prev_installer = get_previous_installer_info(current_version)
        self.user_choice = "cancel"

        self.setWindowTitle("DrawMotion - Startup Recovery Assistant")
        self.setFixedSize(580, 430)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #121815;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QFrame#card {{
                background-color: #18221D;
                border: 1px solid #26382F;
                border-radius: 8px;
            }}
            QLabel {{
                color: #D6DFDA;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("settings", THEME_COLORS['primary_green']).pixmap(36, 36))
        header_layout.addWidget(icon_lbl)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        main_title = QLabel("DrawMotion Startup Health")
        main_title.setStyleSheet("font-size: 17px; font-weight: bold; color: #FFFFFF;")
        title_layout.addWidget(main_title)

        sub_title = QLabel(f"DrawMotion v{self.current_version} detected consecutive startup interruptions.")
        sub_title.setStyleSheet("font-size: 12px; color: #8FA298;")
        title_layout.addWidget(sub_title)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Body Card
        body_card = QFrame()
        body_card.setObjectName("card")
        card_layout = QVBoxLayout(body_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        info_lbl = QLabel(
            "To safeguard your creative workspace and prevent repeated interruptions, "
            "you can launch DrawMotion normally, run in Safe Mode, or inspect diagnostic logs."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("font-size: 12px; line-height: 1.4; color: #CAD6D0;")
        card_layout.addWidget(info_lbl)

        # Options Container
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)

        # Primary Option: Continue Normal Launch
        self.continue_btn = QPushButton("Continue to DrawMotion (Normal Launch)")
        self.continue_btn.setIcon(get_icon("play", "#FFFFFF"))
        self.continue_btn.setIconSize(QSize(16, 16))
        self.continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 16px;
                border-radius: 6px;
                text-align: left;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['primary_green']}CC;
            }}
        """)
        self.continue_btn.clicked.connect(self._handle_try_again)
        options_layout.addWidget(self.continue_btn)

        # Option 2: Safe Mode
        self.safemode_btn = QPushButton("Launch in Safe Mode (Hardware Acceleration Disabled)")
        self.safemode_btn.setIcon(get_icon("settings", "#3FA36D"))
        self.safemode_btn.setIconSize(QSize(16, 16))
        self.safemode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.safemode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1F2E26;
                color: #E0EBE5;
                font-size: 12px;
                font-weight: 500;
                padding: 9px 16px;
                border-radius: 6px;
                text-align: left;
                border: 1px solid #2B4538;
            }}
            QPushButton:hover {{
                background-color: #273A30;
                border-color: {THEME_COLORS['primary_green']};
            }}
        """)
        self.safemode_btn.clicked.connect(self._handle_safemode)
        options_layout.addWidget(self.safemode_btn)

        # Option 3: Rollback to previous version (if available)
        if self.prev_version and self.prev_installer:
            self.rollback_btn = QPushButton(f"Rollback to Previous Version (v{self.prev_version})")
            self.rollback_btn.setIcon(get_icon("download", "#FFFFFF"))
            self.rollback_btn.setIconSize(QSize(16, 16))
            self.rollback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.rollback_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME_COLORS['orange_action']};
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 8px 16px;
                    border-radius: 6px;
                    text-align: left;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {THEME_COLORS['orange_hover']};
                }}
            """)
            self.rollback_btn.clicked.connect(self._handle_rollback)
            options_layout.addWidget(self.rollback_btn)

        # Option 4: View Crash Logs
        self.logs_btn = QPushButton("View Diagnostic Details")
        self.logs_btn.setIcon(get_icon("external_link", "#8FA298"))
        self.logs_btn.setIconSize(QSize(14, 14))
        self.logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logs_btn.setStyleSheet("""
            QPushButton {{
                background-color: #17211C;
                color: #8FA298;
                font-size: 12px;
                padding: 7px 16px;
                border-radius: 6px;
                text-align: left;
                border: 1px solid #24352C;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                border-color: #3B5446;
            }}
        """)
        self.logs_btn.clicked.connect(self._handle_view_logs)
        options_layout.addWidget(self.logs_btn)

        card_layout.addLayout(options_layout)
        layout.addWidget(body_card)

        # Bottom actions
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {{
                background-color: #1B2620;
                color: #C0CCC6;
                font-size: 12px;
                padding: 6px 18px;
                border-radius: 4px;
                border: 1px solid #2C3E34;
            }}
            QPushButton:hover {{
                background-color: #24352C;
                color: #FFFFFF;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)

    def reject(self):
        # Reset health counter on dismiss so user is never locked out
        self._handle_try_again()
        super().reject()

    def _handle_rollback(self):
        if self.prev_installer and os.path.exists(self.prev_installer):
            # Reset health counter so rolled back version starts clean
            state = load_boot_health()
            state["boot_attempts"] = 0
            save_boot_health(state)
            
            # Launch previous installer
            launch_rollback_installer(self.prev_installer)
            self.user_choice = "rollback"
            self.accept()
            sys.exit(0)

    def _handle_safemode(self):
        state = load_boot_health()
        state["boot_attempts"] = 0
        state["safe_mode"] = True
        save_boot_health(state)
        self.user_choice = "safemode"
        self.accept()

    def _handle_view_logs(self):
        try:
            from utils.paths import get_app_data_dir
            log_dir = os.path.join(get_app_data_dir(), "Logs")
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            try:
                import tempfile
                log_dir = os.path.join(tempfile.gettempdir(), "DrawMotion_Logs")
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                log_dir = os.path.expanduser("~")
            
        lifecycle_log = os.path.join(log_dir, "startup_lifecycle.log")
        crash_log = os.path.join(log_dir, "crash_log.txt")

        # Prioritize live lifecycle log so user sees immediate startup events, fallback to crash log or directory
        target_path = lifecycle_log if os.path.exists(lifecycle_log) else (crash_log if os.path.exists(crash_log) else log_dir)
        if os.path.exists(target_path):
            try:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(target_path)))
            except Exception:
                try:
                    if hasattr(os, 'startfile'):
                        os.startfile(target_path)
                except Exception:
                    pass

    def _handle_try_again(self):
        # Reset attempt count to allow clean attempt
        state = load_boot_health()
        state["boot_attempts"] = 0
        save_boot_health(state)
        self.user_choice = "retry"
        self.accept()
