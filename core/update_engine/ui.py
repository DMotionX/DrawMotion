import sys
import os
import subprocess
import tempfile
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QProgressBar, QTextBrowser
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QDesktopServices
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from .parallel_downloader import DownloadWorker
from core.updater import CURRENT_VERSION

class FastUpdateDialog(QDialog):
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("DrawMotion - Update Available")
        self.setWindowIcon(get_icon("update", THEME_COLORS['primary_green']))
        self.setFixedSize(560, 520)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME_COLORS['bg_main']};
                color: {THEME_COLORS['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        
        # Header
        title_lbl = QLabel(f"Version {self.update_info.get('version', '')} is available! (Current: {CURRENT_VERSION})")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {THEME_COLORS['primary_green']};")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title_lbl)
        
        subtitle_lbl = QLabel("What's New in this Release:")
        subtitle_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {THEME_COLORS['text_secondary']};")
        layout.addWidget(subtitle_lbl)
        
        # Changelog Browser with internal vertical scrolling and Markdown support
        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setReadOnly(True)
        self.changelog_browser.setOpenExternalLinks(True)
        changelog_text = self.update_info.get("changelog", "Enhancements, performance optimizations, and stability fixes.")
        self.changelog_browser.setMarkdown(changelog_text)
        self.changelog_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['divider']};
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {THEME_COLORS['bg_main']};
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {THEME_COLORS['divider']};
                min-height: 25px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {THEME_COLORS['primary_green']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
        """)
        layout.addWidget(self.changelog_browser, stretch=1)
        
        # Live Stats Label (Hidden initially)
        self.stats_lbl = QLabel("")
        self.stats_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 12px; font-weight: 500;")
        self.stats_lbl.setVisible(False)
        layout.addWidget(self.stats_lbl)

        # Progress Bar (Hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {THEME_COLORS['divider']};
                border-radius: 6px;
                text-align: center;
                background-color: {THEME_COLORS['surface']};
                color: white;
                font-weight: bold;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME_COLORS['primary_green']};
                border-radius: 5px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Browser / IDM external download button
        self.browser_btn = QPushButton("Browser / IDM Download")
        self.browser_btn.setIcon(get_icon("external_link", THEME_COLORS['text_secondary']))
        self.browser_btn.setIconSize(QSize(14, 14))
        self.browser_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browser_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME_COLORS['divider']};
                padding: 8px 14px;
                border-radius: 6px;
                color: {THEME_COLORS['text_secondary']};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['surface']};
                color: #FFFFFF;
                border-color: {THEME_COLORS['primary_green']};
            }}
        """)
        self.browser_btn.clicked.connect(self._open_in_browser)
        btn_layout.addWidget(self.browser_btn)

        btn_layout.addStretch()

        self.skip_btn = QPushButton("Not Now")
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME_COLORS['divider']};
                padding: 8px 18px;
                border-radius: 6px;
                color: {THEME_COLORS['text_secondary']};
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['surface']};
                color: white;
                border-color: {THEME_COLORS['text_secondary']};
            }}
        """)
        self.skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.skip_btn)
        
        self.update_btn = QPushButton("Update Now (8 Streams)")
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['orange_action']};
                color: white;
                font-weight: bold;
                padding: 8px 22px;
                border-radius: 6px;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['orange_hover']};
            }}
            QPushButton:disabled {{
                background-color: {THEME_COLORS['divider']};
                color: {THEME_COLORS['text_secondary']};
            }}
        """)
        self.update_btn.clicked.connect(self._start_fast_download)
        btn_layout.addWidget(self.update_btn)
        
        layout.addLayout(btn_layout)
        self.worker = None

    def _get_target_url(self) -> str:
        url = self.update_info.get("url")
        if not url:
            for asset in self.update_info.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    url = asset.get("browser_download_url")
                    break
        return url or ""

    def _open_in_browser(self):
        url = self._get_target_url()
        if url:
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "Download Error", "Direct download URL is not available.")

    def _start_fast_download(self):
        url = self._get_target_url()
        if not url:
            QMessageBox.warning(self, "Download Error", "No suitable executable found in the latest release.")
            return
            
        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.browser_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.stats_lbl.setVisible(True)
        self.stats_lbl.setText("Connecting 8 concurrent streams to CDN...")
        
        temp_path = os.path.join(tempfile.gettempdir(), f"DrawMotion_Update_v{self.update_info.get('version', 'latest')}.exe")
        
        # 8 concurrent streams for maximum speed
        self.worker = DownloadWorker(url, temp_path, chunks=8)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.stats.connect(self._on_download_stats)
        self.worker.finished.connect(self._on_download_finished)
        self.worker.error.connect(self._on_download_error)
        self.worker.start()

    def _on_download_stats(self, downloaded, total, speed_bytes_s, eta_seconds):
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        speed_mb_s = speed_bytes_s / (1024 * 1024)
        
        if eta_seconds > 60:
            eta_str = f"{eta_seconds // 60}m {eta_seconds % 60}s"
        else:
            eta_str = f"{eta_seconds}s"
            
        self.stats_lbl.setText(
            f"Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB  •  Speed: {speed_mb_s:.2f} MB/s  •  ETA: {eta_str}"
        )
        
    def _on_download_finished(self, filepath):
        # Register installer in local recovery vault for rollback protection
        run_path = filepath
        try:
            from core.recovery_engine.watchdog import register_installer_in_vault
            vault_path = register_installer_in_vault(filepath, str(self.update_info.get('version', '')))
            if vault_path and os.path.exists(vault_path):
                run_path = vault_path
        except Exception:
            pass

        self.stats_lbl.setText("Download completed successfully!")
        
        reply = QMessageBox.question(
            self,
            "Update Ready to Install",
            f"DrawMotion v{self.update_info.get('version', '')} was downloaded successfully in the background.\n\n"
            "Would you like to restart DrawMotion and apply the update now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                subprocess.Popen([run_path, "/VERYSILENT", "/SP-", "/SUPPRESSMSGBOXES", "/RESTARTAPP"])
                sys.exit(0)
            except Exception as e:
                QMessageBox.critical(self, "Installation Error", f"Could not launch installer: {e}")
                self.accept()
        else:
            self.stats_lbl.setText("Update cached in local vault. You may restart whenever you are ready.")
            self.accept()
            
    def _on_download_error(self, err_msg):
        QMessageBox.critical(self, "Download Failed", f"An error occurred during download: {err_msg}")
        self.update_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.browser_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.stats_lbl.setVisible(False)
        if self.worker:
            self.worker.cancel()
