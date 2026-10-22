from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel, QScrollArea
from PySide6.QtCore import Signal, Qt, QTimer

from .components.sidebar import SettingsSidebar
from .components.project_settings import ProjectSettings
from .components.export_settings import ExportSettings
from .components.general_settings import GeneralSettings
from .components.storage_settings import StorageSettings
from .components.update_settings import UpdateSettings
from .components.drawing_settings import DrawingSettings

class SettingsPage(QWidget):
    """
    Main Settings Page that holds the Sidebar and the StackedWidget of sections.
    """
    back_requested = Signal() # Emitted when 'Back to Studio' is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0E1512;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (Top Bar)
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(
            "background-color: #131C18; "
            "border-bottom: 1px solid #1E2E28;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        self.back_btn = QPushButton("  Back to Studio")
        from utils.icons import get_icon
        self.back_btn.setIcon(get_icon("undo", "white"))
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7A9E90;
                border: 1px solid #1E3028;
                padding: 8px 18px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover { background-color: #1A2E25; color: #D0D8D4; border-color: #2E8B57; }
        """)
        self.back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("DrawMotion Studio — Settings")
        title.setStyleSheet(
            "color: #D0D8D4; font-size: 17px; font-weight: 700; "
            "font-family: 'Segoe UI', Arial, sans-serif;"
        )
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E8B57;
                color: white;
                border: none;
                padding: 9px 26px;
                border-radius: 6px;
                font-weight: 700;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover { background-color: #38A169; }
            QPushButton:pressed { background-color: #276749; }
        """)
        self.save_btn.clicked.connect(self._on_save_clicked)
        
        header_layout.addWidget(self.back_btn)
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        
        # Body (Sidebar + Content)
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        
        self.sidebar = SettingsSidebar()
        
        # Scroll area wrapping all section content
        self.stacked_content = QStackedWidget()
        
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidget(self.stacked_content)
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #0E1512;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2E5040;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #2E8B57; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        
        # Add sections
        self.stacked_content.addWidget(ProjectSettings())
        
        self.drawing_settings = DrawingSettings()
        self.stacked_content.addWidget(self.drawing_settings)
        
        self.stacked_content.addWidget(ExportSettings())
        self.stacked_content.addWidget(GeneralSettings())
        
        self.storage_settings = StorageSettings()
        self.stacked_content.addWidget(self.storage_settings)
        
        self.stacked_content.addWidget(UpdateSettings())
        
        # Connect sidebar with auto-scroll reset to top
        self.sidebar.section_selected.connect(self._on_section_selected)
        
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.content_scroll, 1)  # Content takes all remaining space
        
        main_layout.addWidget(header)
        main_layout.addWidget(body, 1)

    def set_project_manager(self, pm):
        self.storage_settings.set_project_manager(pm)

    def _on_section_selected(self, index: int):
        self.stacked_content.setCurrentIndex(index)
        if hasattr(self, 'content_scroll') and self.content_scroll:
            self.content_scroll.verticalScrollBar().setValue(0)
            QTimer.singleShot(0, lambda: self.content_scroll.verticalScrollBar().setValue(0))

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'content_scroll') and self.content_scroll:
            self.content_scroll.verticalScrollBar().setValue(0)
            QTimer.singleShot(0, lambda: self.content_scroll.verticalScrollBar().setValue(0))

    def _on_save_clicked(self):
        from core.settings_manager import SettingsManager
        SettingsManager().save()
        
        # Elegant non-blocking button confirmation feedback
        self.save_btn.setText("✓ Settings Saved!")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 9px 26px;
                border-radius: 6px;
                font-weight: 700;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        def _restore_save_button():
            if hasattr(self, 'save_btn') and self.save_btn:
                self.save_btn.setText("Save Settings")
                self.save_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2E8B57;
                        color: white;
                        border: none;
                        padding: 9px 26px;
                        border-radius: 6px;
                        font-weight: 700;
                        font-size: 13px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QPushButton:hover { background-color: #38A169; }
                    QPushButton:pressed { background-color: #276749; }
                """)
                
        QTimer.singleShot(2000, _restore_save_button)
