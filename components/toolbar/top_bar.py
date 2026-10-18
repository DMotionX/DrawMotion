"""
Purpose: Top toolbar component for the UI.
Features: Contains tool selection (Select, Hand, Pen, etc.) with icons, undo/redo, and export.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QToolButton, QLabel, QSpacerItem, QSizePolicy, QButtonGroup, QVBoxLayout
from PySide6.QtCore import Qt, QSize, Signal, QEvent
from PySide6.QtGui import QIcon, QAction
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from core.settings_manager import SettingsManager

class TopBar(QFrame):
    tool_selected = Signal(str)
    zoom_in = Signal()
    zoom_out = Signal()
    zoom_reset = Signal()
    undo_requested = Signal()
    redo_requested = Signal()
    save_requested = Signal()
    record_requested = Signal()
    aspect_ratio_changed = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(70) # Restored height for a sleeker look
        self._init_ui()

    def _create_tool_button(self, text, icon_name, checkable=False, checked=False):
        btn = QToolButton()
        btn.setText(text)
        btn.setIcon(get_icon(icon_name))
        btn.setIconSize(QSize(20, 20))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        # Removed fixed size, using minimum size to allow flexible layout
        btn.setMinimumSize(44, 48)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        # Ensure tool buttons inherit correct styling
        btn.setStyleSheet("""
            QToolButton { font-size: 10px; padding: 2px; background: transparent; border: none; }
            QToolButton:checked { color: #2E8B57; background-color: #222A27; border-radius: 6px; }
            QToolButton:hover { background-color: #2A322E; border-radius: 6px; }
        """)
        
        if checkable:
            btn.setCheckable(True)
            btn.setChecked(checked)
        return btn

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6) # Reduced spacing to fit everything

        # Logo / Brand
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(8)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        import os
        from PySide6.QtGui import QPixmap
        from utils.paths import resource_path
        logo_icon = QLabel()
        logo_icon.setStyleSheet("background: transparent;")
        
        _logo_path = resource_path("resources/branding/PNG/DrawMotion_64x64.png")
        if os.path.exists(_logo_path):
            _pix = QPixmap(_logo_path).scaled(
                32, 32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_icon.setPixmap(_pix)
        else:
            logo_icon.setPixmap(get_icon("shape", THEME_COLORS['primary_green']).pixmap(24, 24))
        
        logo_layout.addWidget(logo_icon)
        
        logo_text = QLabel("DrawMotion")
        logo_text.setStyleSheet(
            f"color: {THEME_COLORS['text_primary']}; font-weight: bold; "
            f"font-size: 14px; background: transparent; letter-spacing: 0.5px;"
        )
        logo_layout.addWidget(logo_text)
        layout.addLayout(logo_layout)
        
        # Tools Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.VLine)
        div1.setStyleSheet(f"color: {THEME_COLORS['divider']};")
        layout.addWidget(div1)

        # Tools Group
        self.tool_group = QButtonGroup(self)
        # [FROZEN: CWE] Hide Text button from UI
        tools = [
            ("Select", "select"),
            ("Text", "text")
        ]
        for id_counter, (name, icon) in enumerate(tools):
            btn = self._create_tool_button(name, icon, checkable=True, checked=(name=="Select"))
            mapped_name = name
            if name == "Text": mapped_name = "WriteToImage"
            elif name == "Mind Map": mapped_name = "MindMap"
            btn.setProperty("toolName", mapped_name)
            self.tool_group.addButton(btn, id_counter)
            if name == "Text":
                # [PHASE 3 FIX]: Elegant Overlay BETA Badge
                wrapper = QFrame()
                wrapper.setStyleSheet("background: transparent; border: none;")
                wrapper.setFixedSize(60, 60) # Ensure enough space
                
                # Center the button in the wrapper
                btn.setParent(wrapper)
                btn.move(10, 10)
                
                # Elegant overlay badge
                beta_label = QLabel("BETA", wrapper)
                beta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                beta_label.setStyleSheet("""
                    background-color: #E53935;
                    color: white;
                    font-size: 8px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                    border-radius: 4px;
                    padding: 2px 4px;
                """)
                beta_label.adjustSize()
                # Position top right overlapping the button
                beta_label.move(wrapper.width() - beta_label.width() - 5, 2)
                
                layout.addWidget(wrapper)
            else:
                layout.addWidget(btn)
            
        self.tool_group.buttonClicked.connect(self._on_tool_clicked)

        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.VLine)
        div2.setStyleSheet(f"color: {THEME_COLORS['divider']};")
        layout.addWidget(div2)

        # Actions Group
        undo_btn = self._create_tool_button("Undo", "undo")
        undo_btn.clicked.connect(self.undo_requested.emit)
        layout.addWidget(undo_btn)
        
        redo_btn = self._create_tool_button("Redo", "redo")
        redo_btn.clicked.connect(self.redo_requested.emit)
        layout.addWidget(redo_btn)
        
        self.play_btn = self._create_tool_button("Play", "play")
        layout.addWidget(self.play_btn)
        # Spacer to push the rest to the right
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Zoom Controls
        zoom_frame = QFrame()
        zoom_frame.setStyleSheet(f"background-color: {THEME_COLORS['bg_main']}; border-radius: 6px;")
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(4, 2, 4, 2)
        zoom_layout.setSpacing(2)
        
        zoom_minus = QToolButton()
        zoom_minus.setText("-")
        zoom_minus.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 14px; border: none;")
        zoom_minus.setFixedSize(24, 24)
        zoom_minus.clicked.connect(self.zoom_out.emit)
        zoom_layout.addWidget(zoom_minus)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; font-size: 11px; background: transparent;")
        self.zoom_label.setFixedWidth(40)
        # Clicking the label resets zoom — uses eventFilter instead of lambda to be Nuitka-safe
        self.zoom_label.installEventFilter(self)
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_plus = QToolButton()
        zoom_plus.setText("+")
        zoom_plus.setStyleSheet("background: transparent; color: white; font-weight: bold; font-size: 14px; border: none;")
        zoom_plus.setFixedSize(24, 24)
        zoom_plus.clicked.connect(self.zoom_in.emit)
        zoom_layout.addWidget(zoom_plus)
        
        layout.addWidget(zoom_frame)

        layout.addSpacing(16)
        
        # Screen Size / Aspect Ratio Combo
        from PySide6.QtWidgets import QComboBox
        self.ratio_cb = QComboBox()
        self.ratio_cb.addItems(["YouTube (16:9)", "Instagram (1:1)", "TikTok (9:16)", "Standard (4:3)"])
        self.ratio_cb.setStyleSheet(f"background-color: {THEME_COLORS['surface']}; color: {THEME_COLORS['text_primary']}; border: 1px solid {THEME_COLORS['divider']}; border-radius: 4px; padding: 4px;")
        
        # Load from Settings
        settings = SettingsManager()
        saved_ratio = settings.get("canvas_size", "16:9")
        ratio_map = {"16:9": 0, "1:1": 1, "9:16": 2, "4:3": 3}
        if saved_ratio in ratio_map:
            self.ratio_cb.setCurrentIndex(ratio_map[saved_ratio])
            
        self.ratio_cb.currentIndexChanged.connect(self._on_ratio_changed)
        layout.addWidget(self.ratio_cb)

        # Update Button (Hidden by default, shown if update found)
        self.update_btn = QToolButton()
        self.update_btn.setText(" Update")
        self.update_btn.setIcon(get_icon("update", THEME_COLORS['primary_green']))
        self.update_btn.setIconSize(QSize(16, 16))
        self.update_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {THEME_COLORS['primary_green']}40;
                color: {THEME_COLORS['primary_green']};
                border: 1px solid {THEME_COLORS['primary_green']};
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {THEME_COLORS['primary_green']};
                color: {THEME_COLORS['bg_main']};
            }}
        """)
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self.update_btn)
        
        layout.addSpacing(16)

        # Settings
        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(get_icon("settings"))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.settings_btn)
        
        layout.addSpacing(8)

        # Projects and Save buttons were moved to the new MenuBar for better separation of concerns

        # Export Button
        self.export_btn = QToolButton()
        self.export_btn.setText(" Export ")
        self.export_btn.setIcon(get_icon("upload", "white"))
        self.export_btn.setIconSize(QSize(16, 16))
        self.export_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.export_btn.setObjectName("ExportButton")
        self.export_btn.setFixedSize(110, 36)
        layout.addWidget(self.export_btn)

    def set_export_progress(self, current, total):
        pass # Implemented in UI controller

    def eventFilter(self, obj, event):
        """Nuitka-safe event filter replacing lambda-based mousePressEvent overrides."""
        if obj is self.zoom_label and event.type() == QEvent.Type.MouseButtonPress:
            self.zoom_reset.emit()
            return True
        return super().eventFilter(obj, event)

    def _on_tool_clicked(self, button):
        tool_name = button.property("toolName")
        if tool_name:
            self.tool_selected.emit(tool_name)
            
    def set_active_tool(self, tool_name: str):
        # Update the button state programmatically without emitting tool_selected again
        for btn in self.tool_group.buttons():
            if btn.property("toolName") == tool_name or btn.property("toolName") == (tool_name if tool_name != "Select" else "Select"):
                if not btn.isChecked():
                    btn.setChecked(True)
                break

    def _on_ratio_changed(self, index):
        ratios = [
            (1920, 1080, "16:9"), # YouTube
            (1080, 1080, "1:1"), # Instagram
            (1080, 1920, "9:16"), # TikTok
            (1024, 768, "4:3")   # Standard
        ]
        if 0 <= index < len(ratios):
            w, h, ratio_str = ratios[index]
            self.aspect_ratio_changed.emit(w, h)
            # Save to SettingsManager
            SettingsManager().set("canvas_size", ratio_str)

    def show_update_available(self, version_info):
        self._latest_version_info = version_info
        v_tag = version_info.get("version", "")
        if v_tag:
            self.update_btn.setText(f" Update v{v_tag}")
        self.update_btn.setVisible(True)

    def _on_update_clicked(self):
        if hasattr(self, '_latest_version_info'):
            from core.update_engine.ui import FastUpdateDialog
            if not hasattr(self, '_update_dialog') or self._update_dialog is None:
                self._update_dialog = FastUpdateDialog(self._latest_version_info)
            self._update_dialog.show()
            self._update_dialog.raise_()
            self._update_dialog.activateWindow()
