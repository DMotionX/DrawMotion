from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QHBoxLayout, QMessageBox, QFrame, QApplication,
    QTabWidget, QTextBrowser, QWidget
)
from PySide6.QtCore import Qt, QUrl, QSize, QTimer
from PySide6.QtGui import QDesktopServices, QFont, QPixmap, QImage
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from core.updater import CURRENT_VERSION
import os
import platform
import datetime
import urllib.parse

class KeyboardShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #1A211D; color: #FFFFFF; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QTableWidget {
                background-color: #222A27;
                color: #FFFFFF;
                gridline-color: #2A322E;
                border: 1px solid #2A322E;
            }
            QHeaderView::section {
                background-color: #2A322E;
                color: #FFFFFF;
                padding: 4px;
                border: none;
            }
            QPushButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #3CB371; }
        """)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("DrawMotion Shortcuts")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.table = QTableWidget(12, 2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        shortcuts = [
            ("New Project", "Ctrl+N"),
            ("Open Project", "Ctrl+O"),
            ("Save Project", "Ctrl+S"),
            ("Save As", "Ctrl+Shift+S"),
            ("Import Asset", "Ctrl+I"),
            ("Undo", "Ctrl+Z"),
            ("Redo", "Ctrl+Y"),
            ("Delete Selected", "Del"),
            ("Zoom In", "Ctrl++"),
            ("Zoom Out", "Ctrl+-"),
            ("Fit Canvas", "Ctrl+0"),
            ("Full Screen", "F11")
        ]
        
        for row, (action, shortcut) in enumerate(shortcuts):
            self.table.setItem(row, 0, QTableWidgetItem(action))
            self.table.setItem(row, 1, QTableWidgetItem(shortcut))
            
        layout.addWidget(self.table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

class FeedbackSuccessDialog(QDialog):
    """
    Interactive confirmation dialog displayed when a bug report or feedback
    has been dispatched via email or copied to clipboard.
    Professional dark theme, vector SVG green checkmark, zero emojis.
    """
    def __init__(self, parent=None, title_text="Feedback Dispatched Successfully", message_text=""):
        super().__init__(parent)
        self.setWindowTitle(title_text)
        self.setFixedSize(460, 210)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #121815;
                color: #FFFFFF;
                border: 1px solid #23352B;
                border-radius: 10px;
            }
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
            }
            QPushButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                border: 1px solid #3CB371;
                border-radius: 6px;
                padding: 7px 24px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #369D63;
                border-color: #4BD488;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        # Header with vector green checkmark
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Render check_circle SVG cleanly
        from utils.icons import SVG_ICONS
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPainter, QColor
        from PySide6.QtCore import QByteArray
        if "check_circle" in SVG_ICONS:
            svg_str = SVG_ICONS["check_circle"].replace('stroke="currentColor"', 'stroke="#2E8B57"')
            renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
            pixmap = QPixmap(36, 36)
            pixmap.fill(QColor("transparent"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
            painter.end()
            icon_lbl.setPixmap(pixmap)

        header_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        main_title = QLabel(title_text)
        main_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        main_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        title_col.addWidget(main_title)

        sub_msg = QLabel(message_text)
        sub_msg.setWordWrap(True)
        sub_msg.setStyleSheet("color: #9AB0A4; font-size: 11.5px; line-height: 1.4;")
        title_col.addWidget(sub_msg)
        header_row.addLayout(title_col, stretch=1)

        layout.addLayout(header_row)
        layout.addStretch()

        # Action Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("Got it")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

class ReportProblemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report a Problem")
        self.setFixedSize(540, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #121614;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                background: transparent;
                border: none;
            }
            QTextEdit {
                background-color: #192420;
                color: #E0E8E4;
                border: 1px solid #283C32;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                selection-background-color: #2E8B57;
            }
            QTextEdit:focus {
                border-color: #3FA36D;
            }
            QPushButton {
                background-color: #23342C;
                color: #E0E8E4;
                border: 1px solid #2F453A;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2D4439;
                border-color: #3FA36D;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #161D1A;
                border-color: #202925;
                color: #55625B;
            }
            #primary_btn {
                background-color: #2E8B57;
                border: 1px solid #3CB371;
                color: #FFFFFF;
                font-weight: 600;
            }
            #primary_btn:hover {
                background-color: #369D63;
                border-color: #4BD488;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title_lbl = QLabel("Report an Issue or Feedback")
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        subtitle_lbl = QLabel("Send diagnostics directly to the development team. All data remains strictly local.")
        subtitle_lbl.setStyleSheet("color: #8A9C93; font-size: 12px;")
        
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        layout.addLayout(header_layout)

        # Description Label
        desc_lbl = QLabel("Issue Description:")
        desc_lbl.setStyleSheet("color: #CFD9D3; font-size: 12px; font-weight: 600;")
        layout.addWidget(desc_lbl)

        # Description TextEdit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Describe the steps to reproduce the issue, unexpected behavior, or what you were doing when it occurred...")
        self.text_edit.setFixedHeight(115)
        layout.addWidget(self.text_edit)

        # Screenshot Card Container
        screenshot_card = QFrame()
        screenshot_card.setStyleSheet("""
            QFrame#screenshot_card {
                background-color: #16201B;
                border: 1px solid #23352B;
                border-radius: 8px;
            }
        """)
        screenshot_card.setObjectName("screenshot_card")
        card_layout = QVBoxLayout(screenshot_card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        card_title = QLabel("Diagnostic Screenshot")
        card_title.setStyleSheet("color: #CFD9D3; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        card_layout.addWidget(card_title)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(12)

        # Thumbnail Box
        self.preview_box = QFrame()
        self.preview_box.setFixedSize(110, 74)
        self.preview_box.setStyleSheet("""
            QFrame {
                background-color: #101613;
                border: 1px dashed #2B3D33;
                border-radius: 6px;
            }
        """)
        box_layout = QVBoxLayout(self.preview_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        self.screenshot_preview = QLabel("No Image")
        self.screenshot_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_preview.setStyleSheet("color: #60736A; font-size: 11px; background: transparent; border: none;")
        box_layout.addWidget(self.screenshot_preview)
        preview_row.addWidget(self.preview_box)

        # Buttons beside preview in two clean rows to prevent truncation
        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(6)

        actions_row_1 = QHBoxLayout()
        actions_row_1.setSpacing(8)

        self.capture_btn = QPushButton("Capture Screen")
        self.capture_btn.setIcon(get_icon("camera", THEME_COLORS['primary_green']))
        self.capture_btn.setIconSize(QSize(15, 15))
        self.capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.capture_btn.setFixedHeight(30)
        self.capture_btn.clicked.connect(self._take_screenshot)
        actions_row_1.addWidget(self.capture_btn)

        self.browse_btn = QPushButton("Browse Image...")
        self.browse_btn.setIcon(get_icon("image", "#A4B5AC"))
        self.browse_btn.setIconSize(QSize(14, 14))
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setFixedHeight(30)
        self.browse_btn.clicked.connect(self._browse_image)
        actions_row_1.addWidget(self.browse_btn)

        buttons_col.addLayout(actions_row_1)

        actions_row_2 = QHBoxLayout()
        actions_row_2.setSpacing(8)

        self.copy_btn = QPushButton("Copy Image")
        self.copy_btn.setIcon(get_icon("copy", "#A4B5AC"))
        self.copy_btn.setIconSize(QSize(14, 14))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedHeight(30)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_screenshot)
        actions_row_2.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setFixedHeight(30)
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._clear_screenshot)
        actions_row_2.addWidget(self.clear_btn)

        buttons_col.addLayout(actions_row_2)

        self.screenshot_status = QLabel("Capture runs asynchronously without freezing the interface.")
        self.screenshot_status.setStyleSheet("color: #7A8C82; font-size: 11px; background: transparent; border: none;")
        buttons_col.addWidget(self.screenshot_status)

        preview_row.addLayout(buttons_col)
        card_layout.addLayout(preview_row)
        layout.addWidget(screenshot_card)

        # Bottom Button Bar (Official Email & Copy Report - 100% Closed-Source Direct Support)
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(cancel_btn)

        btn_bar.addStretch()

        self.copy_report_btn = QPushButton("Copy Report")
        self.copy_report_btn.setIcon(get_icon("copy", "#A4B5AC"))
        self.copy_report_btn.setIconSize(QSize(14, 14))
        self.copy_report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_report_btn.setFixedHeight(36)
        self.copy_report_btn.clicked.connect(self._copy_full_report)
        btn_bar.addWidget(self.copy_report_btn)

        self.send_btn = QPushButton("Send via Email")
        self.send_btn.setObjectName("primary_btn")
        self.send_btn.setIcon(get_icon("send", "#FFFFFF"))
        self.send_btn.setIconSize(QSize(15, 15))
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFixedHeight(36)
        self.send_btn.clicked.connect(self._send_email)
        btn_bar.addWidget(self.send_btn)

        layout.addLayout(btn_bar)

        self.screenshot_path = None

    def _take_screenshot(self):
        # Asynchronously hide dialog and capture screen to prevent GUI freeze
        self.hide()
        QTimer.singleShot(60, self._perform_capture)

    def _perform_capture(self):
        from utils.paths import get_app_data_dir

        main_window = self.parent()
        if main_window:
            pixmap = main_window.grab()
        else:
            app = QApplication.instance()
            active_win = app.activeWindow() if app else None
            pixmap = active_win.grab() if active_win else QPixmap()

        if not pixmap.isNull():
            # Save into isolated cache directory
            cache_dir = os.path.join(get_app_data_dir(), "Cache", "BugReports")
            os.makedirs(cache_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.screenshot_path = os.path.join(cache_dir, f"report_{ts}.png")
            pixmap.save(self.screenshot_path, "PNG")

            # Copy to clipboard automatically for convenient pasting
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setPixmap(pixmap)

            # Update preview thumbnail
            thumb = pixmap.scaled(self.preview_box.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.screenshot_preview.setPixmap(thumb)
            self.screenshot_status.setText("Screenshot captured and copied to clipboard.")
            self.screenshot_status.setStyleSheet("color: #3FA36D; font-size: 11px; background: transparent; border: none;")
            self.copy_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
        else:
            self.screenshot_status.setText("Could not capture screenshot.")
            self.screenshot_status.setStyleSheet("color: #E57373; font-size: 11px; background: transparent; border: none;")

        self.show()
        self.raise_()
        self.activateWindow()

    def _browse_image(self):
        from PySide6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Screenshot or Diagnostic Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if filepath and os.path.exists(filepath):
            self.screenshot_path = filepath
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                thumb = pixmap.scaled(self.preview_box.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.screenshot_preview.setPixmap(thumb)
                self.screenshot_status.setText(f"Attached: {os.path.basename(filepath)}")
                self.screenshot_status.setStyleSheet("color: #3FA36D; font-size: 11px; background: transparent; border: none;")
                self.copy_btn.setEnabled(True)
                self.clear_btn.setEnabled(True)

    def _copy_screenshot(self):
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            pixmap = QPixmap(self.screenshot_path)
            if not pixmap.isNull():
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setPixmap(pixmap)
                self.screenshot_status.setText("Copied to clipboard (press Ctrl+V to paste).")
                self.screenshot_status.setStyleSheet("color: #3FA36D; font-size: 11px; background: transparent; border: none;")

    def _clear_screenshot(self):
        self.screenshot_path = None
        self.screenshot_preview.clear()
        self.screenshot_preview.setText("No Image")
        self.screenshot_status.setText("No screenshot attached.")
        self.screenshot_status.setStyleSheet("color: #7A8C82; font-size: 11px; background: transparent; border: none;")
        self.copy_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)

    def _send_email(self):
        problem_text = self.text_edit.toPlainText().strip()
        if not problem_text:
            QMessageBox.warning(self, "Details Required", "Please describe the problem before sending.")
            return

        subject = urllib.parse.quote(f"[DrawMotion Bug Report] User Feedback")
        body_content = (
            f"=== DRAWMOTION BUG REPORT ===\n\n"
            f"App Version: DrawMotion Studio v{CURRENT_VERSION}\n"
            f"Platform: {platform.system()} {platform.release()} ({platform.architecture()[0]})\n"
            f"Support Contact: easysoft.dv2team@gmail.com\n\n"
            f"=== ISSUE DESCRIPTION ===\n"
            f"{problem_text}\n\n"
        )
        if self.screenshot_path:
            body_content += (
                f"=== ATTACHMENT INFO ===\n"
                f"Screenshot was captured and copied to your clipboard.\n"
                f"Local cache path: {self.screenshot_path}\n"
                f"(Please paste image via Ctrl+V or attach it from the path above)\n"
            )

        # Backup copy to clipboard so user never loses their report
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(body_content)

        body = urllib.parse.quote(body_content)
        mailto_url = f"mailto:easysoft.dv2team@gmail.com?subject={subject}&body={body}"
        QDesktopServices.openUrl(QUrl(mailto_url))
        
        parent_win = self.parent()
        self.accept()

        success_dlg = FeedbackSuccessDialog(
            parent_win,
            title_text="Feedback Dispatched Successfully",
            message_text=(
                "Your diagnostic report has been opened in your default email client addressed to easysoft.dv2team@gmail.com.\n\n"
                "All diagnostic details have also been safely copied to your clipboard."
            )
        )
        success_dlg.exec()

    def _copy_full_report(self):
        problem_text = self.text_edit.toPlainText().strip()
        if not problem_text:
            QMessageBox.warning(self, "Details Required", "Please describe the problem before copying.")
            return

        body_content = (
            f"=== DRAWMOTION BUG REPORT ===\n\n"
            f"App Version: DrawMotion Studio v{CURRENT_VERSION}\n"
            f"Platform: {platform.system()} {platform.release()} ({platform.architecture()[0]})\n"
            f"Support Contact: easysoft.dv2team@gmail.com\n\n"
            f"=== ISSUE DESCRIPTION ===\n"
            f"{problem_text}\n\n"
        )
        if self.screenshot_path:
            body_content += (
                f"=== ATTACHMENT INFO ===\n"
                f"Screenshot cached at: {self.screenshot_path}\n"
            )

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(body_content)

        success_dlg = FeedbackSuccessDialog(
            self,
            title_text="Report Copied Successfully",
            message_text=(
                "All diagnostic details and issue steps have been copied to your clipboard.\n\n"
                "You can paste them directly into an email to easysoft.dv2team@gmail.com."
            )
        )
        success_dlg.exec()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About DrawMotion")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog { background-color: #1A211D; color: #FFFFFF; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QPushButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #3CB371; }
            a { color: #2E8B57; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Load High-Res PNG Logo
        logo_label = QLabel()
        png_path = os.path.join(os.path.dirname(__file__), "..", "resources", "branding", "PNG", "DrawMotion_256x256.png")
        if os.path.exists(png_path):
            pixmap = QPixmap(png_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        title = QLabel("DrawMotion Animation Studio")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        from core.updater import CURRENT_VERSION
        version = QLabel(f"Version: {CURRENT_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        desc = QLabel("The Ultimate Whiteboard Animation Software.\nBuilt with PySide6.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        link = QLabel('<a href="https://drawmotion-web.vercel.app/">drawmotion-web.vercel.app</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setOpenExternalLinks(True)
        layout.addWidget(link)
        
        layout.addStretch()
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        policies_btn = QPushButton("Legal & Privacy")
        policies_btn.setIcon(get_icon("shield", "#FFFFFF"))
        policies_btn.setIconSize(QSize(14, 14))
        policies_btn.setStyleSheet("""
            QPushButton {
                background-color: #213329;
                color: #C8D6CF;
                border: 1px solid #2F4D3C;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2A4335;
                color: #FFFFFF;
                border-color: #3FA36D;
            }
        """)
        policies_btn.clicked.connect(self._open_policies)
        btn_row.addWidget(policies_btn)
        
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        
        layout.addLayout(btn_row)

    def _open_policies(self):
        dlg = LegalPoliciesDialog(self)
        dlg.exec()


class LegalPoliciesDialog(QDialog):
    """
    Professional in-app dialog displaying the DrawMotion End-User License
    Agreement (EULA), Privacy Policy, and Third-Party Open Source Notices.
    Zero emojis, high-contrast dark theme, native Markdown rendering,
    100% offline-capable, and completely isolated from external file editors.
    """
    def __init__(self, parent=None, initial_tab=0):
        super().__init__(parent)
        self.setWindowTitle("DrawMotion - Legal Policies & Privacy")
        self.setWindowIcon(get_icon("shield", THEME_COLORS['primary_green']))
        self.resize(740, 560)
        self.setMinimumSize(640, 460)
        self.setModal(True)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #121815;
                color: #FFFFFF;
            }}
            QTabWidget::pane {{
                border: 1px solid #23352B;
                background-color: #151D18;
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: #121815;
                color: #8E9F96;
                padding: 9px 18px;
                font-size: 12px;
                font-weight: 600;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                border: 1px solid transparent;
            }}
            QTabBar::tab:selected {{
                background-color: #151D18;
                color: #3FA36D;
                border: 1px solid #23352B;
                border-bottom: 1px solid #151D18;
            }}
            QTabBar::tab:hover:!selected {{
                color: #FFFFFF;
                background-color: #18231D;
            }}
            QTextBrowser {{
                background-color: #151D18;
                color: #D6DFDA;
                border: none;
                padding: 16px 18px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }}
            QScrollBar:vertical {{
                background: #151D18;
                width: 7px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #253A2E;
                min-height: 24px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #365543;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)
        
        # ── Header ───────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        shield_icon = QLabel()
        shield_icon.setPixmap(get_icon("shield", THEME_COLORS['primary_green']).pixmap(28, 28))
        shield_icon.setFixedSize(32, 32)
        header_layout.addWidget(shield_icon)
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        title_lbl = QLabel("DrawMotion Legal Policies & Privacy")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        subtitle_lbl = QLabel("Commercial Rights • Zero Telemetry • 100% Local-First Engine")
        subtitle_lbl.setStyleSheet("font-size: 11px; color: #7F9489;")
        header_text_layout.addWidget(title_lbl)
        header_text_layout.addWidget(subtitle_lbl)
        header_layout.addLayout(header_text_layout)
        
        header_layout.addStretch()
        
        badge_lbl = QLabel(f"v{CURRENT_VERSION} • Free & Open Source (GNU GPLv3)")
        badge_lbl.setStyleSheet("""
            background-color: #17261F;
            border: 1px solid #274234;
            border-radius: 4px;
            padding: 4px 10px;
            color: #3FA36D;
            font-size: 11px;
            font-weight: 600;
        """)
        header_layout.addWidget(badge_lbl)
        layout.addLayout(header_layout)
        
        # ── Tabbed Browsers ───────────────────────────────────────────────────
        self.tabs = QTabWidget()
        
        eula_browser = self._create_browser(self._get_eula_markdown())
        self.tabs.addTab(eula_browser, "End-User License (EULA)")
        
        privacy_browser = self._create_browser(self._get_privacy_markdown())
        self.tabs.addTab(privacy_browser, "Privacy Policy (Local-First)")
        
        third_party_browser = self._create_browser(self._get_third_party_markdown())
        self.tabs.addTab(third_party_browser, "Open Source & LGPLv3")
        
        if 0 <= initial_tab < self.tabs.count():
            self.tabs.setCurrentIndex(initial_tab)
            
        layout.addWidget(self.tabs)
        
        # ── Footer ───────────────────────────────────────────────────────────
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        
        credit_lbl = QLabel("DrawMotion Team • Founded by Mohamed Fadl • easysoft.dv2team@gmail.com")
        credit_lbl.setStyleSheet("color: #647B70; font-size: 11px;")
        footer_layout.addWidget(credit_lbl)
        
        footer_layout.addStretch()
        
        web_btn = QPushButton("Official Website")
        web_btn.setIcon(get_icon("globe", "#A0AFA7"))
        web_btn.setIconSize(QSize(14, 14))
        web_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        web_btn.setStyleSheet("""
            QPushButton {
                background-color: #16201A;
                border: 1px solid #273A30;
                border-radius: 6px;
                color: #C0CDC6;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #1D2C24;
                border-color: #3FA36D;
                color: #FFFFFF;
            }
        """)
        web_btn.clicked.connect(self._open_web_url)
        footer_layout.addWidget(web_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                border: none;
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['green_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)

    def _open_web_url(self):
        QDesktopServices.openUrl(QUrl("https://drawmotion-web.vercel.app/"))

    def _create_browser(self, content: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setReadOnly(True)
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(content)
        return browser

    def _get_eula_markdown(self) -> str:
        return (
            "### 1. 100% Free for Personal, Educational, and Commercial Production\n"
            "DrawMotion is provided completely free of charge. You are granted a non-exclusive, "
            "worldwide license to use the software for personal projects, academic research, and commercial creative production.\n\n"
            "### 2. You Own Your Output (Full Monetization Rights)\n"
            "**All videos, animations, illustrations, and exported media you produce with DrawMotion belong 100% to you.**\n"
            "- You are completely free to monetize your creations on YouTube, TikTok, Facebook, social media, commercial advertising, or client freelance contracts.\n"
            "- **Zero Royalties:** You do not owe any licensing fees, royalties, or revenue share to DrawMotion Team.\n"
            "- Attribution is appreciated but never mandatory for commercial works.\n\n"
            "### 3. Free & Open-Source Software (GNU GPLv3)\n"
            "DrawMotion is licensed under the **GNU General Public License v3.0 (GPLv3)**.\n"
            "- You are free to inspect, fork, modify, and contribute to DrawMotion's source code: https://github.com/DMotionX/DrawMotion\n"
            "- Any derivative works or modifications you distribute must also be published under GPLv3.\n"
            "- **No Selling or Renting:** You may not repackage DrawMotion into adware bundles, malware wrappers, or deceptive commercial installers.\n"
            "- **No Unauthorized Cloud Hosting:** You may not offer DrawMotion as a paid SaaS subscription without explicit written permission from the author.\n\n"
            "### 4. LGPLv3 Qt Carve-Out\n"
            "In compliance with the GNU Lesser General Public License (LGPLv3) governing Qt 6 and PySide6, you retain the right to modify or replace the dynamically linked Qt/PySide6 shared libraries with your own compatible versions.\n\n"
            "**Open-Source LGPL Exception:**\n"
            "In compliance with the GNU Lesser General Public License (LGPLv3) governing Qt 6 and PySide6, you retain the right to modify or replace the dynamically linked Qt/PySide6 shared libraries (.dll, .pyd) with your own compatible versions.\n\n"
            "### 5. Code Signing & Antivirus Transparency\n"
            "DrawMotion binaries are signed with a private self-signed certificate under DrawMotion Team rather than an expensive commercial certificate authority. Every release is verified through automated scanning tooling and VirusTotal prior to distribution.\n\n"
            "### 6. Experimental Beta Status & Disclaimer of Warranty\n"
            "DrawMotion is in an active Beta Development Phase. Users are advised to maintain regular backups of project files.\n"
            "THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE AUTHOR (MOHAMED FADL) AND DRAWMOTION TEAM MAKE NO REPRESENTATION OR WARRANTY THAT THE SOFTWARE WILL OPERATE UNINTERRUPTED, ERROR-FREE, OR SECURE."
        )

    def _get_privacy_markdown(self) -> str:
        return (
            "### 1. Core Philosophy: Strict Local-First Architecture\n"
            "Your creative work, privacy, and sovereignty are paramount. DrawMotion is engineered from the ground up on a strict **Local-First** architecture.\n\n"
            "### 2. Zero Data Harvesting & Zero Telemetry\n"
            "- We do **NOT** collect, harvest, monitor, sell, or profile your personal information, device data, or creative projects.\n"
            "- There are **no** background analytics, trackers, behavioral telemetry, or user fingerprinting scripts embedded in the software.\n\n"
            "### 3. 100% Offline Capable\n"
            "DrawMotion functions fully without an active internet connection:\n"
            "- All project files (.dm), vector drawing paths, timeline configurations, imported assets (images, audio, fonts), and rendered video animations are processed and stored strictly on your local disk.\n"
            "- We have zero access to your projects or assets.\n\n"
            "### 4. Network Communication (Updates Only)\n"
            "The only automated network communication performed by DrawMotion occurs during software update checks:\n"
            "- When checking for updates, DrawMotion makes a secure HTTPS GET request to our official release servers (GitHub API / hosting endpoint) to retrieve the latest version tag and release changelog.\n"
            "- Standard hosting providers automatically process technical routing metadata (including incoming IP addresses, HTTP User-Agent strings, and application version headers) as required for operational routing, uptime reliability, and DDoS mitigation.\n"
            "- We do not link this network metadata to your personal identity, nor do we retain, sell, or disclose it for marketing or advertising purposes.\n\n"
            "### 5. Support Communications\n"
            "If you voluntarily contact us via email ([easysoft.dv2team@gmail.com](mailto:easysoft.dv2team@gmail.com)) or send diagnostic reports, we receive only the technical details you choose to share. This information is used strictly and exclusively to diagnose bugs and provide technical assistance."
        )

    def _get_third_party_markdown(self) -> str:
        return (
            "### 1. Third-Party Open-Source Notices\n"
            "DrawMotion gratefully utilizes high-quality open-source frameworks and libraries:\n\n"
            "- **Qt 6 & PySide6:**\n"
            "  Licensed under the GNU Lesser General Public License v3 (LGPLv3). Source code for Qt is available at [https://code.qt.io](https://code.qt.io). PySide6 is dynamically linked as standalone shared libraries.\n\n"
            "- **FFmpeg:**\n"
            "  Licensed under LGPL/GPL. Used as an isolated binary for high-speed media encoding and audio synchronization pipelines.\n\n"
            "- **NumPy & SciPy:**\n"
            "  Licensed under the BSD License. Used for high-performance mathematical array processing and curve interpolation.\n\n"
            "- **OpenCV (opencv-contrib-python):**\n"
            "  Licensed under the Apache 2.0 License. Used for computer vision algorithms and image transformation.\n\n"
            "- **Hershey Fonts:**\n"
            "  Stroke-based vector fonts for handwriting animations.\n\n"
            "- **Python Runtime:**\n"
            "  Distributed under the Python Software Foundation (PSF) License.\n\n"
            "### 2. Anti-Monopoly Software Initiative\n"
            "DrawMotion operates entirely as an independent initiative by Mohamed Fadl to challenge digital software monopolies by making professional animation tools freely accessible to every creator worldwide."
        )

