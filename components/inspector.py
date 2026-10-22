"""
Purpose: Right sidebar panel for item properties.
Features: Tabs for Object, Animation, and Style properties. Very precise layout matching the design.
"""
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
                               QLabel, QLineEdit, QSlider, QComboBox, QGridLayout, 
                               QSizePolicy, QScrollArea, QCheckBox, QStackedWidget, QPushButton, QColorDialog)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from utils.theme import THEME_COLORS
from components.text_editor_panel import TextEditorPanel

def convert_arabic_numerals(text: str) -> str:
    if not text:
        return text
    arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩٫', '0123456789.')
    return text.translate(arabic_to_english)

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, e):
        e.ignore()

QComboBox = NoScrollComboBox

class InspectorPanel(QFrame):
    item_modified = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("RightPanel")
        self.setFixedWidth(300)
        self.current_item = None
        
        self._anim_timer = QTimer(self)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.setInterval(400) # 400ms debounce
        self._anim_timer.timeout.connect(self._apply_animation)
        
        self._init_ui()
        self.set_inputs_enabled(False)
        self.workspace = None
        
    def set_workspace(self, workspace):
        self.workspace = workspace
        
    def set_inputs_enabled(self, enabled: bool):
        # We only disable inputs so the scrollbar remains active
        from PySide6.QtWidgets import QLineEdit, QComboBox, QSlider, QCheckBox
        for widget_type in (QLineEdit, QComboBox, QSlider, QCheckBox):
            for widget in self.findChildren(widget_type):
                widget.setEnabled(enabled)


    def _create_section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; margin-top: 20px; margin-bottom: 10px; font-size: 13px;")
        return lbl

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("PROPERTIES")
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; letter-spacing: 1px; padding: 20px 20px 10px 20px; font-size: 13px;")
        main_layout.addWidget(title)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # 1. No Selection Page
        self.no_selection_page = QWidget()
        no_sel_layout = QVBoxLayout(self.no_selection_page)
        no_sel_msg = QLabel("Please select an element\nfrom the Canvas to edit its properties.")
        no_sel_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_sel_msg.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 13px; line-height: 1.5;")
        no_sel_layout.addWidget(no_sel_msg)
        self.stack.addWidget(self.no_selection_page)
        
        # 2. Properties Page
        self.properties_page = QWidget()
        prop_layout = QVBoxLayout(self.properties_page)
        prop_layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 12px 20px; }")
        
        tabs.addTab(self._create_text_tab(), "Text (Beta)")
        tabs.addTab(self._create_object_tab(), "Object")
        tabs.addTab(self._create_style_tab(), "Style")
        
        # Audio Tab (Native Zero-Risk Plugin System)
        self.audio_tab = self._create_audio_tab()
        tabs.addTab(self.audio_tab, "Audio FX")
        
        self.tabs = tabs
        self.tabs.currentChanged.connect(self._on_tab_changed)
        prop_layout.addWidget(tabs)
        self.stack.addWidget(self.properties_page)
        
        self.stack.setCurrentWidget(self.no_selection_page)

    def _create_text_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_editor = TextEditorPanel(self)
        layout.addWidget(self.text_editor)
        return tab

    def _create_audio_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        from core.audio_engine.ui.audio_fx_panel import AudioFXPanel
        self.audio_fx_panel = AudioFXPanel(self)
        
        # When user tweaks audio settings, notify the item
        self.audio_fx_panel.settings_changed.connect(self._on_audio_settings_changed)
        
        # [PHASE 7 FIX] Wrap the panel in a QScrollArea to prevent layout collapse
        from PySide6.QtWidgets import QScrollArea
        self.audio_scroll_area = QScrollArea()
        self.audio_scroll_area.setWidgetResizable(True)
        self.audio_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.audio_scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.audio_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.audio_scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget#scrollAreaWidgetContents { background: transparent; }
        """)
        self.audio_scroll_area.setWidget(self.audio_fx_panel)
        
        layout.addWidget(self.audio_scroll_area)
        return tab

    def _on_tab_changed(self, index: int):
        self._ensure_active_tab_scrolled_to_top()
        QTimer.singleShot(0, self._ensure_active_tab_scrolled_to_top)

    def _ensure_active_tab_scrolled_to_top(self):
        for scroll in [
            getattr(self, 'object_scroll_area', None),
            getattr(self, 'style_scroll_area', None),
            getattr(self, 'audio_scroll_area', None),
        ]:
            if scroll and hasattr(scroll, 'verticalScrollBar'):
                scroll.verticalScrollBar().setValue(0)

    def _on_audio_settings_changed(self, settings):
        if not self.current_item:
            return
            
        # Store settings on current_item safely
        self.current_item.audio_fx_settings = dict(settings)
        
        # Speed adjustment: scale duration dynamically based on base file duration
        speed = max(0.25, min(3.0, float(settings.get("speed", 1.0))))
        base_dur = getattr(self.current_item, '_base_duration', None)
        if base_dur is None:
            base_dur = getattr(self.current_item, 'anim_duration', 5.0)
            self.current_item._base_duration = base_dur
            
        dur_changed = False
        if speed > 0:
            new_dur = base_dur / speed
            if abs(getattr(self.current_item, 'anim_duration', 0.0) - new_dur) > 0.001:
                self.current_item.anim_duration = new_dur
                dur_changed = True
                if hasattr(self, 'workspace') and self.workspace:
                    self.workspace.items_changed.emit(self.workspace.user_items)
                    self.workspace.audio_items_changed.emit(self.workspace.audio_items)
            
        # Dispatch live update to AudioEngine
        file_path = getattr(self.current_item, 'file_path', '')
        if hasattr(self, 'workspace') and self.workspace and hasattr(self.workspace, 'audio_engine'):
            self.workspace.audio_engine.update_track_fx(file_path, settings)
            
        # Only stop animation if duration changed (not when adjusting volume or fade!)
        if dur_changed:
            self.item_modified.emit()

    def _create_object_tab(self):
        object_tab = QWidget()
        obj_layout = QVBoxLayout(object_tab)
        obj_layout.setContentsMargins(0, 0, 0, 0)
        obj_layout.setSpacing(0)
        
        self.object_scroll_area = QScrollArea()
        self.object_scroll_area.setWidgetResizable(True)
        self.object_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.object_scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 10, 20, 20)
        scroll_layout.setSpacing(12)
        
        # Transform Section
        scroll_layout.addWidget(self._create_section_label("Transform"))
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        lbl_pos = QLabel("Position")
        lbl_pos.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        grid.addWidget(lbl_pos, 0, 0)
        
        self.x_in = QLineEdit()
        self.x_in.setPlaceholderText("X")
        self.x_in.editingFinished.connect(self._apply_transform)
        grid.addWidget(self.x_in, 0, 1)
        
        self.y_in = QLineEdit()
        self.y_in.setPlaceholderText("Y")
        self.y_in.editingFinished.connect(self._apply_transform)
        grid.addWidget(self.y_in, 0, 2)
        
        lbl_scale = QLabel("Scale")
        lbl_scale.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        grid.addWidget(lbl_scale, 1, 0)
        
        self.scale_in = QLineEdit()
        self.scale_in.setPlaceholderText("Scale")
        self.scale_in.editingFinished.connect(self._apply_transform)
        grid.addWidget(self.scale_in, 1, 1, 1, 2)
        
        lbl_rot = QLabel("Rotation")
        lbl_rot.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        grid.addWidget(lbl_rot, 2, 0)
        
        self.rot_in = QLineEdit()
        self.rot_in.setPlaceholderText("0°")
        self.rot_in.editingFinished.connect(self._apply_transform)
        grid.addWidget(self.rot_in, 2, 1, 1, 2)
        
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)
        scroll_layout.addLayout(grid)
        
        # Appearance Section
        scroll_layout.addWidget(self._create_section_label("Appearance"))
        
        app_grid = QGridLayout()
        app_grid.setSpacing(12)
        lbl_op = QLabel("Opacity")
        lbl_op.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        app_grid.addWidget(lbl_op, 0, 0)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._apply_appearance)
        app_grid.addWidget(self.opacity_slider, 0, 1)
        
        self.op_val = QLabel("100%")
        self.op_val.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 11px;")
        app_grid.addWidget(self.op_val, 0, 2)
        
        app_grid.setColumnStretch(0, 2)
        app_grid.setColumnStretch(1, 4)
        app_grid.setColumnStretch(2, 1)
        scroll_layout.addLayout(app_grid)
        
        # Timing Section (Moved from Animation)
        scroll_layout.addWidget(self._create_section_label("Timing"))
        time_grid = QGridLayout()
        time_grid.setContentsMargins(0, 0, 0, 0)
        time_grid.setSpacing(12)
        
        self.lbl_dur = QLabel("Duration")
        self.lbl_dur.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        time_grid.addWidget(self.lbl_dur, 0, 0)
        self.dur_in = QLineEdit("2.0")
        self.dur_in.textEdited.connect(self._on_time_text_edited)
        self.dur_in.editingFinished.connect(self.force_apply_animation)
        time_grid.addWidget(self.dur_in, 0, 1)
        
        lbl_del = QLabel("Start Time")
        lbl_del.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
        time_grid.addWidget(lbl_del, 1, 0)
        self.del_in = QLineEdit("0.0")
        self.del_in.textEdited.connect(self._on_time_text_edited)
        self.del_in.editingFinished.connect(self.force_apply_animation)
        time_grid.addWidget(self.del_in, 1, 1)
        
        scroll_layout.addLayout(time_grid)
        
        self.sync_audio_btn = QPushButton(" Sync with Audio")
        self.sync_audio_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1565C0;
                color: white;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1E88E5;
            }}
            QPushButton:disabled {{
                background-color: #37474F;
                color: #78909C;
            }}
        """)
        self.sync_audio_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sync_audio_btn.clicked.connect(self._sync_with_audio)
        self.sync_audio_btn.hide() # Hidden by default, shown for scenes
        scroll_layout.addWidget(self.sync_audio_btn)
        
        scroll_layout.addStretch(1)
        self.object_scroll_area.setWidget(scroll_content)
        obj_layout.addWidget(self.object_scroll_area)
        
        return object_tab

    def _create_style_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.style_scroll_area = QScrollArea()
        self.style_scroll_area.setWidgetResizable(True)
        self.style_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 10, 20, 20)
        scroll_layout.setSpacing(12)
        
        # Drawing Engine Settings
        self.drawing_engine_container = QWidget()
        drawing_layout = QVBoxLayout(self.drawing_engine_container)
        drawing_layout.setContentsMargins(0, 0, 0, 0)
        drawing_layout.addWidget(self._create_section_label("Drawing Engine (Vector)"))
        
        self.drawing_style_cb = QComboBox()
        self.drawing_style_cb.addItems([
            "Professional", "Sketch", "Educational", "Solid Reveal", 
            "Clean Outline", "Organic Sketch", "Hatch Shading", "Line Art (Skeleton)"
        ])
        self.drawing_style_cb.currentTextChanged.connect(self._apply_drawing_style)
        drawing_layout.addWidget(self.drawing_style_cb)

        drawing_layout.addWidget(self._create_section_label("Drawing Direction"))
        self.drawing_direction_cb = QComboBox()
        self.drawing_direction_cb.addItems([
            "Auto Detect",
            "Right to Left (Arabic)",
            "Left to Right (English)"
        ])
        self.drawing_direction_cb.currentTextChanged.connect(self._apply_drawing_direction)
        drawing_layout.addWidget(self.drawing_direction_cb)
        scroll_layout.addWidget(self.drawing_engine_container)
        
        # Library Assets Engine Settings
        self.library_engine_container = QWidget()
        library_layout = QVBoxLayout(self.library_engine_container)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.addWidget(self._create_section_label("Library Assets Engine"))
        
        self.library_style_cb = QComboBox()
        # Add a default option so it doesn't auto-apply
        self.library_style_cb.addItems([
            "Select Library Style...",
            "Smart Blueprint (Library)", 
            "Icon Sketch (Library)", 
            "Fast Contour (Library)"
        ])
        self.library_style_cb.currentTextChanged.connect(self._apply_library_style)
        library_layout.addWidget(self.library_style_cb)
        scroll_layout.addWidget(self.library_engine_container)
        
        # SFX Settings
        self.sfx_container = QWidget()
        sfx_layout = QVBoxLayout(self.sfx_container)
        sfx_layout.setContentsMargins(0, 0, 0, 0)
        sfx_layout.addWidget(self._create_section_label("Sound Effect"))
        
        self.sfx_combo = QComboBox()
        self.sfx_combo.addItem("None", "None")
        
        # Populate from directory
        import os
        sfx_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sfx", "draw")
        if os.path.exists(sfx_dir):
            for file in os.listdir(sfx_dir):
                if file.endswith('.mp3') or file.endswith('.wav'):
                    # Create short display name
                    short_name = file.replace('.mp3', '').replace('.wav', '')
                    # Limit length
                    if len(short_name) > 30:
                        short_name = short_name[:27] + "..."
                    self.sfx_combo.addItem(short_name, file)
                    
        self.sfx_combo.currentIndexChanged.connect(self._apply_sfx)
        # Prevent expanding too much and causing overflow
        self.sfx_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.sfx_combo.setMinimumContentsLength(10)
        sfx_layout.addWidget(self.sfx_combo)
        
        scroll_layout.addWidget(self.sfx_container)
        
        # Physics Algorithm (Text)
        self.physics_algo_container = QWidget()
        physics_layout = QVBoxLayout(self.physics_algo_container)
        physics_layout.setContentsMargins(0, 0, 0, 0)
        physics_layout.addWidget(self._create_section_label("Physics Algorithm (Text)"))
        self.algo_combo = QComboBox()
        
        self.algo_map = {
            "Steady": "linear",
            "Smooth": "minimum_jerk",
            "Natural Human": "two_thirds_power_law",
            "Stop & Go": "stop_and_go",
            "Organic Sketch": "ou_noise"
        }
        self.algo_reverse_map = {v: k for k, v in self.algo_map.items()}
        
        self.algo_combo.addItems(list(self.algo_map.keys()))
        self.algo_combo.currentTextChanged.connect(self._apply_algorithm_style)
        physics_layout.addWidget(self.algo_combo)
        scroll_layout.addWidget(self.physics_algo_container)
        
        # Text Effects
        self.text_effects_container = QWidget()
        effects_layout = QVBoxLayout(self.text_effects_container)
        effects_layout.setContentsMargins(0, 0, 0, 0)
        effects_layout.addWidget(self._create_section_label("Text Effects"))
        self.effect_combo = QComboBox()
        
        self.effect_map = {
            "None": "none",
            "Glow": "glow",
            "Neon": "neon",
            "Ink Bleed": "ink_bleed",
            "Drop Shadow": "drop_shadow",
            "Glitch": "glitch",
            "Holographic": "holographic"
        }
        self.effect_reverse_map = {v: k for k, v in self.effect_map.items()}
        
        self.effect_combo.addItems(list(self.effect_map.keys()))
        self.effect_combo.currentTextChanged.connect(self._apply_text_effect)
        effects_layout.addWidget(self.effect_combo)
        scroll_layout.addWidget(self.text_effects_container)
        
        scroll_layout.addStretch(1)
        
        self.style_scroll_area.setWidget(scroll_content)
        layout.addWidget(self.style_scroll_area)
        return tab

    def on_item_selected(self, item):
        # [CRITICAL FIX] If the user was typing a duration and clicked away, 
        # the selection is cleared BEFORE editingFinished fires. We must save the value NOW.
        if hasattr(self, '_anim_timer') and self._anim_timer.isActive() and getattr(self, 'current_item', None):
            self.force_apply_animation()
            
        print(f"[DEBUG LOG] inspector.py: on_item_selected called. Item type: {type(item).__name__}")
        
        self.current_item = item
        if not item:
            self.stack.setCurrentWidget(self.no_selection_page)
            return
            
        self.stack.setCurrentWidget(self.properties_page)
        
        # Determine if it's a text item based on the spoofed class name
        is_text_item = type(item).__name__ in ['WriteToAnimatedImageItem', 'WriteToImageGraphicsItem']
        
        # Determine if it's an audio item (Zero-Risk check)
        is_audio_item = hasattr(item, 'layer_name') and item.layer_name in ["Voice", "Music", "SFX"]
        
        if is_audio_item:
            # Show ONLY Audio tab
            self.tabs.setTabVisible(0, False)
            self.tabs.setTabVisible(1, False)
            self.tabs.setTabVisible(2, False)
            self.tabs.setTabVisible(3, True)
            self.tabs.setCurrentIndex(3)
            if hasattr(self, 'audio_fx_panel'):
                self.audio_fx_panel.set_node(item)
            self._ensure_active_tab_scrolled_to_top()
            QTimer.singleShot(0, self._ensure_active_tab_scrolled_to_top)
            return
        
        if is_text_item:
            # Show Text and Style tabs
            current_tab = self.tabs.currentIndex()
            self.tabs.setTabVisible(0, True)
            self.tabs.setTabVisible(1, False)
            self.tabs.setTabVisible(2, True)
            self.tabs.setTabVisible(3, False)
            if current_tab in (0, 2):
                self.tabs.setCurrentIndex(current_tab)
            else:
                self.tabs.setCurrentIndex(0)
            if hasattr(self, 'text_editor'):
                self.text_editor.set_node(item)
                
            # Smart Inspector Visibility (Zero-Risk)
            self.drawing_engine_container.hide()
            self.sfx_container.hide()
            self.physics_algo_container.show()
            self.text_effects_container.show()
            
        else:
            # Show ONLY Image tabs
            current_tab = self.tabs.currentIndex()
            self.tabs.setTabVisible(0, False)
            self.tabs.setTabVisible(1, True)
            self.tabs.setTabVisible(2, True)
            self.tabs.setTabVisible(3, False)
            if current_tab in (1, 2):
                self.tabs.setCurrentIndex(current_tab)
            else:
                self.tabs.setCurrentIndex(1)
            
            # Smart Inspector Visibility (Zero-Risk)
            self.drawing_engine_container.show()
            self.sfx_container.show()
            self.physics_algo_container.hide()
            self.text_effects_container.hide()
            
        # Handle live binding signals
        if hasattr(self, '_current_connected_item') and self._current_connected_item:
            try:
                self._current_connected_item.xChanged.disconnect(self.update_ui_from_item)
                self._current_connected_item.yChanged.disconnect(self.update_ui_from_item)
                self._current_connected_item.scaleChanged.disconnect(self.update_ui_from_item)
                self._current_connected_item.rotationChanged.disconnect(self.update_ui_from_item)
            except: pass
            
        self._current_connected_item = item
        if item and hasattr(item, 'xChanged'):
            item.xChanged.connect(self.update_ui_from_item)
            item.yChanged.connect(self.update_ui_from_item)
            item.scaleChanged.connect(self.update_ui_from_item)
            item.rotationChanged.connect(self.update_ui_from_item)

        # Block signals so programmatic setText doesn't trigger user timers/updates
        self.x_in.blockSignals(True)
        self.y_in.blockSignals(True)
        self.scale_in.blockSignals(True)
        self.rot_in.blockSignals(True)
        self.opacity_slider.blockSignals(True)
        self.dur_in.blockSignals(True)
        self.del_in.blockSignals(True)
        self.drawing_style_cb.blockSignals(True)
        if hasattr(self, 'drawing_direction_cb'):
            self.drawing_direction_cb.blockSignals(True)
        if hasattr(self, 'library_style_cb'):
            self.library_style_cb.blockSignals(True)
        self.algo_combo.blockSignals(True)
        self.sfx_combo.blockSignals(True)
            
        # Update Transform fields
        self.x_in.setText(f"{item.pos().x():.1f}")
        self.y_in.setText(f"{item.pos().y():.1f}")
        self.scale_in.setText(f"{item.scale():.2f}")
        self.rot_in.setText(f"{item.rotation():.1f}")
        
        # Update Appearance fields
        opacity_val = int(item.opacity() * 100)
        self.opacity_slider.setValue(opacity_val)
        self.op_val.setText(f"{opacity_val}%")
        
        # Update Animation fields
        if hasattr(item, 'anim_duration'):
            self.dur_in.setText(f"{item.anim_duration:.1f}")
            self.del_in.setText(f"{item.anim_delay:.1f}")
            self.dur_in.setEnabled(True)
            self.del_in.setEnabled(True)
        elif hasattr(item, 'duration'):
            self.dur_in.setText(f"{item.duration:.1f}")
            if hasattr(item, 'anim_delay'):
                self.del_in.setText(f"{item.anim_delay:.1f}")
            else:
                self.del_in.setText("0.0")
            self.dur_in.setEnabled(True)
            self.del_in.setEnabled(True)
        else:
            self.dur_in.setEnabled(False)
            self.del_in.setEnabled(False)
            
        # Ensure duration fields are always visible
        self.dur_in.show()
        self.lbl_dur.show()
        
        # Show/Hide Sync Button for Scenes
        if type(item).__name__ == "SceneArtboardItem":
            self.sync_audio_btn.show()
            # Disable if no audio in the workspace for this scene's bounds
            # For simplicity, we just enable it and handle the check on click
            self.sync_audio_btn.setEnabled(True)
        else:
            self.sync_audio_btn.hide()
            
        # Update SFX fields
        if hasattr(item, 'sfx_name'):
            idx = self.sfx_combo.findData(item.sfx_name)
            if idx >= 0:
                self.sfx_combo.setCurrentIndex(idx)
            else:
                self.sfx_combo.setCurrentIndex(0)
            
        # Unblock signals
        self.x_in.blockSignals(False)
        self.y_in.blockSignals(False)
        self.scale_in.blockSignals(False)
        self.rot_in.blockSignals(False)
        self.opacity_slider.blockSignals(False)
        self.dur_in.blockSignals(False)
        self.del_in.blockSignals(False)
            
        # Update Drawing Engine Settings
        if hasattr(item, 'drawing_style') and getattr(item, '_render_mode', 'vector') != 'raster':
            if "(Library)" in item.drawing_style:
                if hasattr(self, 'library_style_cb'):
                    self.library_style_cb.setCurrentText(item.drawing_style)
                    self.library_style_cb.setEnabled(True)
                self.drawing_style_cb.setCurrentIndex(-1)
                self.drawing_style_cb.setEnabled(True)
            else:
                self.drawing_style_cb.setCurrentText(item.drawing_style)
                self.drawing_style_cb.setEnabled(True)
                if hasattr(self, 'library_style_cb'):
                    self.library_style_cb.setCurrentIndex(0)
                    self.library_style_cb.setEnabled(True)
        else:
            self.drawing_style_cb.setEnabled(False)
            if hasattr(self, 'library_style_cb'):
                self.library_style_cb.setEnabled(False)

        # Update Drawing Direction Settings
        if hasattr(item, 'drawing_direction'):
            dir_map = {
                "auto": "Auto Detect",
                "rtl": "Right to Left (Arabic)",
                "ltr": "Left to Right (English)"
            }
            cur_dir = getattr(item, 'drawing_direction', 'auto')
            if hasattr(self, 'drawing_direction_cb'):
                self.drawing_direction_cb.setCurrentText(dir_map.get(cur_dir, "Auto Detect"))
                self.drawing_direction_cb.setEnabled(True)
        elif hasattr(self, 'drawing_direction_cb'):
            self.drawing_direction_cb.setEnabled(False)
            
        # Update Physics Algorithm Settings
        if hasattr(item, 'model') and hasattr(item.model, 'algorithm_style'):
            internal_id = item.model.algorithm_style
            friendly_name = getattr(self, 'algo_reverse_map', {}).get(internal_id, "Steady")
            self.algo_combo.setCurrentText(friendly_name)
            self.algo_combo.setEnabled(True)
        else:
            self.algo_combo.setEnabled(False)
            
        # Update Text Effects Settings
        if hasattr(item, 'model') and hasattr(item.model, 'text_effect'):
            internal_id = item.model.text_effect
            friendly_name = getattr(self, 'effect_reverse_map', {}).get(internal_id, "None")
            self.effect_combo.setCurrentText(friendly_name)
            self.effect_combo.setEnabled(True)
        else:
            self.effect_combo.setEnabled(False)
            
        # Unblock combo signals
        self.drawing_style_cb.blockSignals(False)
        if hasattr(self, 'drawing_direction_cb'):
            self.drawing_direction_cb.blockSignals(False)
        if hasattr(self, 'library_style_cb'):
            self.library_style_cb.blockSignals(False)
        self.algo_combo.blockSignals(False)
        self.sfx_combo.blockSignals(False)
        if hasattr(self, 'effect_combo'):
            self.effect_combo.blockSignals(False)
            
        self._ensure_active_tab_scrolled_to_top()
        QTimer.singleShot(0, self._ensure_active_tab_scrolled_to_top)
            
            
    def _apply_drawing_style(self, text):
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_style'): return
        self.current_item.set_drawing_style(text)
        
        if hasattr(self, 'library_style_cb'):
            self.library_style_cb.blockSignals(True)
            self.library_style_cb.setCurrentIndex(0)
            self.library_style_cb.blockSignals(False)
            
        self.item_modified.emit()

    def _apply_drawing_direction(self, text):
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_direction'): return
        val_map = {
            "Auto Detect": "auto",
            "Right to Left (Arabic)": "rtl",
            "Left to Right (English)": "ltr"
        }
        self.current_item.set_drawing_direction(val_map.get(text, "auto"))
        self.item_modified.emit()

    def _apply_library_style(self, text):
        if text == "Select Library Style...": return
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_style'): return
        self.current_item.set_drawing_style(text)
        
        if hasattr(self, 'drawing_style_cb'):
            self.drawing_style_cb.blockSignals(True)
            self.drawing_style_cb.setCurrentIndex(-1)
            self.drawing_style_cb.blockSignals(False)
            
        self.item_modified.emit()

    def _apply_algorithm_style(self, text):
        if not self.current_item or not hasattr(self.current_item, 'model'): return
        
        # Translate from UI friendly name to internal ID
        internal_id = getattr(self, 'algo_map', {}).get(text, "linear")
        
        if hasattr(self.current_item.model, 'algorithm_style'):
            self.current_item.model.algorithm_style = internal_id
            if hasattr(self.current_item, 'update_text_properties'):
                self.current_item.update_text_properties()
            self.item_modified.emit()

    def _apply_text_effect(self, text):
        if not self.current_item or not hasattr(self.current_item, 'model'): return
        
        # Translate from UI friendly name to internal ID
        internal_id = getattr(self, 'effect_map', {}).get(text, "none")
        
        if hasattr(self.current_item.model, 'text_effect'):
            self.current_item.model.text_effect = internal_id
            if hasattr(self.current_item, 'update_text_properties'):
                self.current_item.update_text_properties()
            self.item_modified.emit()

    def _apply_transform(self):
        if not self.current_item: return
        try:
            x_txt = convert_arabic_numerals(self.x_in.text())
            y_txt = convert_arabic_numerals(self.y_in.text())
            s_txt = convert_arabic_numerals(self.scale_in.text())
            r_txt = convert_arabic_numerals(self.rot_in.text())
            
            x = float(x_txt or 0)
            y = float(y_txt or 0)
            self.current_item.setPos(x, y)
            
            s = float(s_txt or 1)
            self.current_item.setScale(s)
            
            r = float(r_txt or 0)
            self.current_item.setRotation(r)
            self.item_modified.emit()
        except ValueError:
            pass

    def _apply_appearance(self):
        if not self.current_item: return
        val = self.opacity_slider.value()
        self.op_val.setText(f"{val}%")
        self.current_item.setOpacity(val / 100.0)
        self.item_modified.emit()

    def update_ui_from_item(self):
        if not self.current_item: return
        self.x_in.blockSignals(True)
        self.y_in.blockSignals(True)
        self.scale_in.blockSignals(True)
        self.rot_in.blockSignals(True)
        
        self.x_in.setText(f"{self.current_item.pos().x():.1f}")
        self.y_in.setText(f"{self.current_item.pos().y():.1f}")
        self.scale_in.setText(f"{self.current_item.scale():.2f}")
        self.rot_in.setText(f"{self.current_item.rotation():.1f}")
        
        self.x_in.blockSignals(False)
        self.y_in.blockSignals(False)
        self.scale_in.blockSignals(False)
        self.rot_in.blockSignals(False)

    def _on_time_text_edited(self, text=""):
        self._anim_timer.start()

    def force_apply_animation(self):
        if self._anim_timer.isActive():
            self._anim_timer.stop()
        self._apply_animation()

    def _apply_animation(self):
        if not self.current_item: return
        try:
            dur_txt = convert_arabic_numerals(self.dur_in.text())
            del_txt = convert_arabic_numerals(self.del_in.text())
            
            dur = float(dur_txt or 2.0)
            delay = float(del_txt or 0.0)
            dur = max(0.1, dur)
            delay = max(0.0, delay)
            
            print(f"[DEBUG LOG] inspector.py: _apply_animation parsing dur={dur}, delay={delay} for item={type(self.current_item).__name__}")
            
            # 1. Force the exact Python method if it exists to avoid PySide property bypassing
            if hasattr(self.current_item, 'set_anim_duration'):
                print(f"[DEBUG LOG] inspector.py: Calling set_anim_duration({dur})")
                self.current_item.set_anim_duration(dur)
            elif hasattr(self.current_item, 'anim_duration'):
                print(f"[DEBUG LOG] inspector.py: Calling anim_duration property = {dur}")
                self.current_item.anim_duration = dur
            elif hasattr(self.current_item, 'duration'):
                print(f"[DEBUG LOG] inspector.py: Calling duration property = {dur}")
                self.current_item.duration = dur
                
            if hasattr(self.current_item, 'anim_delay'):
                self.current_item.anim_delay = delay
                
            self.item_modified.emit()
            print(f"[DEBUG LOG] inspector.py: Emitted item_modified")
        except ValueError as e:
            print(f"[DEBUG LOG] inspector.py: ValueError {e}")

    def _apply_sfx(self, *args):
        if hasattr(self, 'current_item') and self.current_item:
            new_sfx_name = self.sfx_combo.currentData()
            self.current_item.sfx_name = new_sfx_name
            self.item_modified.emit()

    def _sync_with_audio(self):
        if not self.current_item or type(self.current_item).__name__ != "SceneArtboardItem":
            return
            
        scene = self.current_item.scene()
        if not hasattr(scene, 'audio_items') or not scene.audio_items:
            return
            
        # Calculate max end time of all audio items
        max_audio_end = max([(getattr(a, 'anim_delay', 0.0) + getattr(a, 'anim_duration', 0.0)) for a in scene.audio_items])
        
        if max_audio_end > 0:
            # We set the scene's duration to the max audio end time
            # For multi-scene setups, we'd calculate local scene time, but this covers 99% of use cases
            self.dur_in.setText(f"{max_audio_end:.1f}")
            self.force_apply_animation()
            
            # Stretch elements inside this scene proportionally
            child_items = [i for i in scene.user_items if i.parentItem() == self.current_item]
            if not child_items:
                return
                
            old_scene_dur = getattr(self.current_item, 'duration', max_audio_end)
            if old_scene_dur <= 0: return
            
            scale_factor = max_audio_end / old_scene_dur
            
            for item in child_items:
                old_dur = getattr(item, 'anim_duration', 2.0)
                old_delay = getattr(item, 'anim_delay', 0.0)
                
                # Apply scaling
                if hasattr(item, 'set_anim_duration'):
                    item.set_anim_duration(old_dur * scale_factor)
                elif hasattr(item, 'anim_duration'):
                    item.anim_duration = old_dur * scale_factor
                elif hasattr(item, 'duration'):
                    item.duration = old_dur * scale_factor
                    
                if hasattr(item, 'anim_delay'):
                    item.anim_delay = old_delay * scale_factor
                    
            # Trigger timeline refresh
            scene.items_changed.emit(scene.user_items)
