"""
Purpose: Right sidebar panel for item properties.
Features: Tabs for Object, Animation, and Style properties. Very precise layout matching the design.
"""
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
                               QLabel, QLineEdit, QSlider, QComboBox, QGridLayout, 
                               QSizePolicy, QScrollArea, QCheckBox, QStackedWidget, QPushButton, QColorDialog)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
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
        e.accept()

QComboBox = NoScrollComboBox

class InspectorScrollArea(QScrollArea):
    """
    Custom QScrollArea that prevents focus transitions from violently hijacking
    and auto-scrolling the inspector viewport.
    """
    def focusNextPrevChild(self, next):
        return False

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusAboutToChange):
            return True
        return super().eventFilter(obj, event)

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
        # We only disable inputs so the scrollbar remains active, while preserving scroll position
        active_scrolls = [
            getattr(self, 'object_scroll_area', None),
            getattr(self, 'style_scroll_area', None),
            getattr(self, 'audio_scroll_area', None),
        ]
        saved_positions = {s: s.verticalScrollBar().value() for s in active_scrolls if s and hasattr(s, 'verticalScrollBar')}

        from PySide6.QtWidgets import QLineEdit, QComboBox, QSlider, QCheckBox
        for widget_type in (QLineEdit, QComboBox, QSlider, QCheckBox):
            for widget in self.findChildren(widget_type):
                widget.setEnabled(enabled)

        for s, pos in saved_positions.items():
            if s and hasattr(s, 'verticalScrollBar'):
                s.verticalScrollBar().setValue(pos)


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
        
        # [PHASE 7 FIX] Wrap the panel in an InspectorScrollArea to prevent layout collapse
        self.audio_scroll_area = InspectorScrollArea()
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
        
        self.object_scroll_area = InspectorScrollArea()
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
        
        self.style_scroll_area = InspectorScrollArea()
        self.style_scroll_area.setWidgetResizable(True)
        self.style_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 10, 20, 20)
        scroll_layout.setSpacing(12)
        
        # Entrance Animation Mode (Draw vs Motion)
        self.entrance_mode_container = QWidget()
        entrance_layout = QVBoxLayout(self.entrance_mode_container)
        entrance_layout.setContentsMargins(0, 0, 0, 0)
        entrance_layout.addWidget(self._create_section_label("Entrance Animation Mode"))
        
        self.entrance_mode_cb = QComboBox()
        self.entrance_mode_cb.addItem("Draw with Pen", "draw")
        self.entrance_mode_cb.addItem("Hand Placement & Motion (Beta)", "motion")
        self.entrance_mode_cb.currentIndexChanged.connect(self._apply_entrance_mode)
        entrance_layout.addWidget(self.entrance_mode_cb)
        scroll_layout.addWidget(self.entrance_mode_container)

        # Motion Engine Settings Container
        self.motion_engine_container = QWidget()
        motion_layout = QVBoxLayout(self.motion_engine_container)
        motion_layout.setContentsMargins(0, 0, 0, 0)
        motion_layout.setSpacing(10)
        
        motion_layout.addWidget(self._create_section_label("Motion Style"))
        self.motion_style_cb = QComboBox()
        self.motion_style_cb.addItem("Hand Drag & Place", "hand_drag")
        self.motion_style_cb.addItem("Hand Push & Slide", "hand_push")
        self.motion_style_cb.addItem("Directional Slide-In", "slide")
        self.motion_style_cb.addItem("Gravity Drop & Bounce", "gravity_drop")
        self.motion_style_cb.addItem("Elastic Pop & Scale", "elastic_pop")
        self.motion_style_cb.addItem("3D Flip Card", "flip_3d")
        self.motion_style_cb.addItem("Cinematic Zoom", "cinematic_zoom")
        self.motion_style_cb.addItem("Arc Glide", "arc_glide")
        self.motion_style_cb.currentIndexChanged.connect(self._apply_motion_settings)
        motion_layout.addWidget(self.motion_style_cb)
        
        self.motion_dir_lbl = self._create_section_label("Entrance Direction")
        motion_layout.addWidget(self.motion_dir_lbl)
        self.motion_dir_cb = QComboBox()
        self.motion_dir_cb.addItem("From Left", "left")
        self.motion_dir_cb.addItem("From Right", "right")
        self.motion_dir_cb.addItem("From Top", "top")
        self.motion_dir_cb.addItem("From Bottom", "bottom")
        self.motion_dir_cb.addItem("From Top-Left", "top_left")
        self.motion_dir_cb.addItem("From Top-Right", "top_right")
        self.motion_dir_cb.addItem("From Bottom-Left", "bottom_left")
        self.motion_dir_cb.addItem("From Bottom-Right", "bottom_right")
        self.motion_dir_cb.currentIndexChanged.connect(self._apply_motion_settings)
        motion_layout.addWidget(self.motion_dir_cb)
        
        motion_layout.addWidget(self._create_section_label("Motion Easing"))
        self.motion_easing_cb = QComboBox()
        self.motion_easing_cb.addItem("Smooth (Hermite)", "smooth")
        self.motion_easing_cb.addItem("Back (Overshoot)", "back")
        self.motion_easing_cb.addItem("Bounce (Physical)", "bounce")
        self.motion_easing_cb.addItem("Elastic (Spring)", "elastic")
        self.motion_easing_cb.addItem("Exponential", "exponential")
        self.motion_easing_cb.addItem("Linear", "linear")
        self.motion_easing_cb.currentIndexChanged.connect(self._apply_motion_settings)
        motion_layout.addWidget(self.motion_easing_cb)

        motion_layout.addWidget(self._create_section_label("Motion Speed / Duration"))
        dur_box = QHBoxLayout()
        self.motion_dur_slider = QSlider(Qt.Orientation.Horizontal)
        self.motion_dur_slider.setRange(5, 40)
        self.motion_dur_slider.setValue(15)
        self.motion_dur_slider.valueChanged.connect(self._apply_motion_settings)
        dur_box.addWidget(self.motion_dur_slider)
        
        self.motion_dur_lbl = QLabel("1.5s")
        self.motion_dur_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 11px; min-width: 35px;")
        dur_box.addWidget(self.motion_dur_lbl)
        motion_layout.addLayout(dur_box)

        # Motion Sound FX (Air Whoosh / Wood Drop Thud / Pop)
        motion_layout.addWidget(self._create_section_label("Motion Sound Effect"))
        self.motion_sfx_cb = QComboBox()
        self.motion_sfx_cb.addItem("None (Silent)", "none")
        self.motion_sfx_cb.addItem("Air Whoosh", "whoosh")
        self.motion_sfx_cb.addItem("Wood Drop Thud", "thud")
        self.motion_sfx_cb.addItem("Pop Bubble", "pop")
        self.motion_sfx_cb.currentIndexChanged.connect(self._apply_motion_settings)
        motion_layout.addWidget(self.motion_sfx_cb)

        # Quick Test Button
        self.test_motion_btn = QPushButton("▶  Test Motion Preview")
        self.test_motion_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A241F;
                color: #3FA36D;
                border: 1px solid #2E8B57;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background-color: #24352B;
                color: #56C98B;
                border: 1px solid #3FA36D;
            }
            QPushButton:pressed {
                background-color: #16241C;
            }
        """)
        self.test_motion_btn.clicked.connect(self._test_motion_preview)
        motion_layout.addWidget(self.test_motion_btn)
        
        self.motion_engine_container.hide()
        scroll_layout.addWidget(self.motion_engine_container)

        # Drawing Engine Settings
        self.drawing_engine_container = QWidget()
        drawing_layout = QVBoxLayout(self.drawing_engine_container)
        drawing_layout.setContentsMargins(0, 0, 0, 0)
        drawing_layout.addWidget(self._create_section_label("Drawing Engine (Vector)"))
        
        self.drawing_style_cb = QComboBox()
        self.drawing_style_cb.addItems([
            "Professional", "Sketch", "Educational", "Solid Reveal", 
            "Clean Outline", "Organic Sketch", "Hatch Shading", "Line Art (Skeleton)",
            "Blueprint Drafting", "Engraving Hatch", "Ribbon Flow"
        ])
        self.drawing_style_cb.currentTextChanged.connect(self._apply_drawing_style)
        drawing_layout.addWidget(self.drawing_style_cb)

        drawing_layout.addWidget(self._create_section_label("Drawing Direction"))
        self.drawing_direction_cb = QComboBox()
        self.drawing_direction_cb.addItems([
            "Auto Detect",
            "Right to Left (RTL)",
            "Left to Right (LTR)"
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
        effects_layout.setSpacing(6)
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
        
        # Dedicated Handwriting Pen (Write Engine)
        self.handwriting_pen_container = QWidget()
        hw_layout = QVBoxLayout(self.handwriting_pen_container)
        hw_layout.setContentsMargins(0, 0, 0, 0)
        hw_layout.setSpacing(10)

        hw_layout.addWidget(self._create_section_label("Handwriting Hand"))
        self.hw_hand_combo = QComboBox()
        self.hw_hand_combo.addItem("Right Hand", "right")
        self.hw_hand_combo.addItem("Left Hand", "left")
        self.hw_hand_combo.currentIndexChanged.connect(self._on_hw_hand_type_changed)
        hw_layout.addWidget(self.hw_hand_combo)

        hw_layout.addWidget(self._create_section_label("Pen Model & Style"))
        self.hw_style_combo = QComboBox()
        self.hw_style_combo.currentIndexChanged.connect(self._on_hw_style_changed)
        hw_layout.addWidget(self.hw_style_combo)

        hw_layout.addWidget(self._create_section_label("Writing Hand Size"))
        hw_size_layout = QHBoxLayout()
        self.hw_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.hw_size_slider.setRange(5, 20)  # 0.5x to 2.0x
        self.hw_size_slider.setValue(10)
        self.hw_size_slider.valueChanged.connect(self._on_hw_size_changed)

        self.hw_size_lbl = QLabel("1.0x")
        self.hw_size_lbl.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold; min-width: 40px;")
        hw_size_layout.addWidget(self.hw_size_slider)
        hw_size_layout.addWidget(self.hw_size_lbl)
        hw_layout.addLayout(hw_size_layout)

        scroll_layout.addWidget(self.handwriting_pen_container)
        
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
            if hasattr(self, 'handwriting_pen_container'):
                self.hw_hand_combo.setEnabled(False)
                self.hw_style_combo.setEnabled(False)
                self.hw_size_slider.setEnabled(False)
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
            self.entrance_mode_container.hide()
            self.motion_engine_container.hide()
            self.drawing_engine_container.hide()
            if hasattr(self, 'library_engine_container'):
                self.library_engine_container.hide()
            self.sfx_container.hide()
            self.physics_algo_container.show()
            self.text_effects_container.show()
            if hasattr(self, 'handwriting_pen_container'):
                self.handwriting_pen_container.show()
                self.hw_hand_combo.setEnabled(True)
                self.hw_style_combo.setEnabled(True)
                self.hw_size_slider.setEnabled(True)
            
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
            self.sfx_container.show()
            self.physics_algo_container.hide()
            self.text_effects_container.hide()
            if hasattr(self, 'handwriting_pen_container'):
                self.handwriting_pen_container.hide()
                self.hw_hand_combo.setEnabled(False)
                self.hw_style_combo.setEnabled(False)
                self.hw_size_slider.setEnabled(False)

            has_entrance = hasattr(item, 'entrance_mode') or hasattr(item, 'motion_settings')
            if has_entrance:
                self.entrance_mode_container.show()
                cur_mode = getattr(item, 'entrance_mode', 'draw')
                if cur_mode == 'motion':
                    self.drawing_engine_container.hide()
                    if hasattr(self, 'library_engine_container'):
                        self.library_engine_container.hide()
                    self.motion_engine_container.show()
                else:
                    self.drawing_engine_container.show()
                    if hasattr(self, 'library_engine_container'):
                        self.library_engine_container.show()
                    self.motion_engine_container.hide()
            else:
                self.entrance_mode_container.hide()
                self.motion_engine_container.hide()
                self.drawing_engine_container.show()
            
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
        self.entrance_mode_cb.blockSignals(True)
        self.motion_style_cb.blockSignals(True)
        self.motion_dir_cb.blockSignals(True)
        self.motion_easing_cb.blockSignals(True)
        self.motion_dur_slider.blockSignals(True)
        self.motion_sfx_cb.blockSignals(True)
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
                "rtl": "Right to Left (RTL)",
                "ltr": "Left to Right (LTR)"
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
            
        # Update Handwriting Pen Settings
        if is_text_item and hasattr(self, 'handwriting_pen_container'):
            self.hw_hand_combo.setEnabled(True)
            self.hw_style_combo.setEnabled(True)
            self.hw_size_slider.setEnabled(True)
            self._update_hw_pen_ui_from_item(item)
        elif hasattr(self, 'handwriting_pen_container'):
            self.hw_hand_combo.setEnabled(False)
            self.hw_style_combo.setEnabled(False)
            self.hw_size_slider.setEnabled(False)
            
        # Update Entrance & Motion fields
        if hasattr(item, 'entrance_mode'):
            idx = self.entrance_mode_cb.findData(item.entrance_mode)
            if idx >= 0:
                self.entrance_mode_cb.setCurrentIndex(idx)
            else:
                self.entrance_mode_cb.setCurrentIndex(0)
                
        if hasattr(item, 'motion_settings'):
            m_settings = getattr(item, 'motion_settings', {}) or {}
            m_style = m_settings.get("style", "hand_drag")
            m_dir = m_settings.get("direction", "left")
            m_easing = m_settings.get("easing", "smooth")
            m_dur = float(m_settings.get("duration", 1.5))
            m_sfx = m_settings.get("sfx", "none")
            
            idx = self.motion_style_cb.findData(m_style)
            if idx >= 0: self.motion_style_cb.setCurrentIndex(idx)
            
            idx = self.motion_dir_cb.findData(m_dir)
            if idx >= 0: self.motion_dir_cb.setCurrentIndex(idx)
            
            idx = self.motion_easing_cb.findData(m_easing)
            if idx >= 0: self.motion_easing_cb.setCurrentIndex(idx)

            idx = self.motion_sfx_cb.findData(m_sfx)
            if idx >= 0: self.motion_sfx_cb.setCurrentIndex(idx)
            
            slider_val = int(round(m_dur * 10))
            self.motion_dur_slider.setValue(max(5, min(40, slider_val)))
            self.motion_dur_lbl.setText(f"{m_dur:.1f}s")
            self.motion_dir_cb.setEnabled(m_style not in ("elastic_pop", "flip_3d", "gravity_drop"))

        # Unblock combo signals
        self.entrance_mode_cb.blockSignals(False)
        self.motion_style_cb.blockSignals(False)
        self.motion_dir_cb.blockSignals(False)
        self.motion_easing_cb.blockSignals(False)
        self.motion_dur_slider.blockSignals(False)
        self.motion_sfx_cb.blockSignals(False)
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
            
    def _apply_entrance_mode(self, index):
        if not self.current_item: return
        mode = self.entrance_mode_cb.currentData() or "draw"
        self.current_item.entrance_mode = mode
        
        if mode == "motion":
            self.drawing_engine_container.hide()
            if hasattr(self, 'library_engine_container'):
                self.library_engine_container.hide()
            self.motion_engine_container.show()
            style = self.motion_style_cb.currentData() or "hand_drag"
            self.motion_dir_cb.setEnabled(style not in ("elastic_pop", "flip_3d", "gravity_drop"))
        else:
            self.drawing_engine_container.show()
            if hasattr(self, 'library_engine_container'):
                self.library_engine_container.show()
            self.motion_engine_container.hide()
            
        self.item_modified.emit()

    def _apply_motion_settings(self, *args):
        if not self.current_item: return
        style = self.motion_style_cb.currentData() or "hand_drag"
        direction = self.motion_dir_cb.currentData() or "left"
        easing = self.motion_easing_cb.currentData() or "smooth"
        sfx = self.motion_sfx_cb.currentData() or "none"
        dur_sec = round(self.motion_dur_slider.value() / 10.0, 1)
        self.motion_dur_lbl.setText(f"{dur_sec}s")
        
        self.motion_dir_cb.setEnabled(style not in ("elastic_pop", "flip_3d", "gravity_drop"))
        
        self.current_item.motion_settings = {
            "style": style,
            "direction": direction,
            "duration": dur_sec,
            "easing": easing,
            "sfx": sfx
        }
        self.item_modified.emit()

    def _test_motion_preview(self):
        if not self.current_item:
            return
        if self.workspace and hasattr(self.workspace, "preview_item_motion"):
            self.workspace.preview_item_motion(self.current_item)
            
            
    def _apply_drawing_style(self, text):
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_style'): return
        if getattr(self.current_item, 'drawing_style', None) == text:
            return
        cur_scroll = self.style_scroll_area.verticalScrollBar().value() if hasattr(self, 'style_scroll_area') and self.style_scroll_area else 0
        self.current_item.set_drawing_style(text)
        
        if hasattr(self, 'library_style_cb'):
            self.library_style_cb.blockSignals(True)
            self.library_style_cb.setCurrentIndex(0)
            self.library_style_cb.blockSignals(False)
            
        self.item_modified.emit()
        if hasattr(self, 'style_scroll_area') and self.style_scroll_area:
            self.style_scroll_area.verticalScrollBar().setValue(cur_scroll)

    def _apply_drawing_direction(self, text):
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_direction'): return
        val_map = {
            "Auto Detect": "auto",
            "Right to Left (RTL)": "rtl",
            "Left to Right (LTR)": "ltr"
        }
        new_dir = val_map.get(text, "auto")
        if getattr(self.current_item, 'drawing_direction', None) == new_dir:
            return
        cur_scroll = self.style_scroll_area.verticalScrollBar().value() if hasattr(self, 'style_scroll_area') and self.style_scroll_area else 0
        self.current_item.set_drawing_direction(new_dir)
        self.item_modified.emit()
        if hasattr(self, 'style_scroll_area') and self.style_scroll_area:
            self.style_scroll_area.verticalScrollBar().setValue(cur_scroll)

    def _apply_library_style(self, text):
        if text == "Select Library Style...": return
        if not self.current_item or not hasattr(self.current_item, 'set_drawing_style'): return
        cur_scroll = self.style_scroll_area.verticalScrollBar().value() if hasattr(self, 'style_scroll_area') and self.style_scroll_area else 0
        self.current_item.set_drawing_style(text)
        
        if hasattr(self, 'drawing_style_cb'):
            self.drawing_style_cb.blockSignals(True)
            self.drawing_style_cb.setCurrentIndex(-1)
            self.drawing_style_cb.blockSignals(False)
            
        self.item_modified.emit()
        if hasattr(self, 'style_scroll_area') and self.style_scroll_area:
            self.style_scroll_area.verticalScrollBar().setValue(cur_scroll)

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
            if self.current_item.model.text_effect != internal_id:
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
            
            # Sync target transform for motion engine
            self.current_item._motion_target_pos = QPointF(x, y)
            self.current_item._motion_target_scale = float(s)
            self.current_item._motion_target_rotation = float(r)
            
            self.item_modified.emit()
        except ValueError:
            pass

    def _apply_appearance(self):
        if not self.current_item: return
        val = self.opacity_slider.value()
        self.op_val.setText(f"{val}%")
        self.current_item.setOpacity(val / 100.0)
        self.current_item._motion_target_opacity = val / 100.0
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

    def _refresh_hw_styles_combo(self, hand_type: str, selected_sid: str = None):
        from components.write_to_image.hand_catalog import WritingHandCatalog
        self.hw_style_combo.blockSignals(True)
        self.hw_style_combo.clear()
        styles = WritingHandCatalog.get_available_styles(hand_type)
        for sid, name in styles:
            self.hw_style_combo.addItem(name, sid)
        
        if selected_sid:
            idx = self.hw_style_combo.findData(selected_sid)
            if idx >= 0:
                self.hw_style_combo.setCurrentIndex(idx)
        self.hw_style_combo.blockSignals(False)

    def _update_hw_pen_ui_from_item(self, item):
        from core.settings_manager import SettingsManager
        self.hw_hand_combo.setEnabled(True)
        self.hw_style_combo.setEnabled(True)
        self.hw_size_slider.setEnabled(True)
        sm = SettingsManager()
        model = getattr(item, 'model', None)

        ht = getattr(model, 'writing_hand_type', None) or sm.get("writing_hand_type", "right")
        sid = getattr(model, 'writing_hand_style', None) or sm.get("writing_hand_style", "default")
        sz = getattr(model, 'writing_hand_size', None)
        if sz is None:
            sz = float(sm.get("writing_hand_size", 1.0))
        else:
            sz = float(sz)

        self.hw_hand_combo.blockSignals(True)
        ht_idx = self.hw_hand_combo.findData(ht)
        if ht_idx >= 0:
            self.hw_hand_combo.setCurrentIndex(ht_idx)
        self.hw_hand_combo.blockSignals(False)

        self._refresh_hw_styles_combo(ht, selected_sid=sid)

        self.hw_size_slider.blockSignals(True)
        slider_val = int(round(sz * 10))
        slider_val = max(5, min(slider_val, 20))
        self.hw_size_slider.setValue(slider_val)
        self.hw_size_lbl.setText(f"{sz:.1f}x")
        self.hw_size_slider.blockSignals(False)

    def _on_hw_hand_type_changed(self, index):
        from core.settings_manager import SettingsManager
        new_ht = self.hw_hand_combo.currentData()
        if not new_ht: return
        SettingsManager().set("writing_hand_type", new_ht)
        self._refresh_hw_styles_combo(new_ht)
        if self.current_item and hasattr(self.current_item, 'model'):
            self.current_item.model.writing_hand_type = new_ht
            cur_sid = self.hw_style_combo.currentData() or "default"
            self.current_item.model.writing_hand_style = cur_sid
            self.item_modified.emit()

    def _on_hw_style_changed(self, index):
        from core.settings_manager import SettingsManager
        new_sid = self.hw_style_combo.currentData()
        if not new_sid: return
        SettingsManager().set("writing_hand_style", new_sid)
        if self.current_item and hasattr(self.current_item, 'model'):
            self.current_item.model.writing_hand_style = new_sid
            self.item_modified.emit()

    def _on_hw_size_changed(self, value):
        from core.settings_manager import SettingsManager
        fval = value / 10.0
        self.hw_size_lbl.setText(f"{fval:.1f}x")
        SettingsManager().set("writing_hand_size", fval)
        if self.current_item and hasattr(self.current_item, 'model'):
            self.current_item.model.writing_hand_size = fval
            self.item_modified.emit()
