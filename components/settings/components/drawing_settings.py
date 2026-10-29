from PySide6.QtWidgets import QComboBox, QSlider, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from .project_settings import SettingsSection
from components.write_to_image.hand_catalog import WritingHandCatalog

class DrawingSettings(SettingsSection):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("Drawing & Animation")
        card = self.begin_card("Drawing Preferences")

        # ── Unified Hand Style (replaces the old two-dropdown system) ─────────
        self.hand_style_combo = QComboBox()
        self.hand_style_combo.addItems([
            "Default Hand",   # default  → assets/hend_right.png
            "Left Hand",      # left     → assets/hand_lift.png
            "Young Man",      # young_man
            "Old Man",        # old_man
            "Woman",          # woman
            "No Hand",        # none
        ])

        _style_keys = ["default", "left", "young_man", "old_man", "woman", "none"]
        current_style = self.settings.get("hand_style", "default")

        # Migration: if old key default_hand_type was "none", honour it
        if current_style == "right":
            current_style = "default"

        idx = _style_keys.index(current_style) if current_style in _style_keys else 0
        self.hand_style_combo.setCurrentIndex(idx)

        def set_hand_style(i):
            self.settings.set("hand_style", _style_keys[i])

        self.hand_style_combo.currentIndexChanged.connect(set_hand_style)
        self.add_row(card, "Hand Style:", self.hand_style_combo)

        # ── Drawing Style ────────────────────────────────────────────────────
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Solid Reveal", "Clean Outline", "Sketch"])
        current_drawing = self.settings.get("default_drawing_style", "solid")
        idx2 = {"solid": 0, "clean": 1, "sketch": 2}.get(current_drawing, 0)
        self.style_combo.setCurrentIndex(idx2)

        def set_style(i):
            val = ["solid", "clean", "sketch"][i]
            self.settings.set("default_drawing_style", val)

        self.style_combo.currentIndexChanged.connect(set_style)
        self.add_row(card, "Default Drawing Style:", self.style_combo)

        # ── Ink Effect ───────────────────────────────────────────────────────
        self.ink_combo = QComboBox()
        self.ink_combo.addItems([
            "Glowing Dot",
            "Flying Particles",
            "None"
        ])
        
        _ink_keys = ["dot", "particles", "none"]
        current_ink = self.settings.get("ink_effect_type", "dot")
        idx3 = _ink_keys.index(current_ink) if current_ink in _ink_keys else 0
        self.ink_combo.setCurrentIndex(idx3)
        
        def set_ink_effect(i):
            self.settings.set("ink_effect_type", _ink_keys[i])
            
        self.ink_combo.currentIndexChanged.connect(set_ink_effect)
        self.add_row(card, "Ink Effect:", self.ink_combo)

        # ── Drawing Sound Volume ─────────────────────────────────────────────
        sfx_vol_container = QWidget()
        sfx_vol_layout = QHBoxLayout(sfx_vol_container)
        sfx_vol_layout.setContentsMargins(0, 0, 0, 0)
        sfx_vol_layout.setSpacing(12)
        
        self.sfx_slider = QSlider(Qt.Orientation.Horizontal)
        self.sfx_slider.setRange(0, 100)
        self.sfx_slider.setFixedWidth(220)
        curr_vol = int(self.settings.get("sfx_volume", 40))
        self.sfx_slider.setValue(curr_vol)
        
        self.sfx_val_lbl = QLabel(f"{curr_vol}%")
        self.sfx_val_lbl.setStyleSheet("color: #3CB371; font-weight: 600; min-width: 45px;")
        
        def on_sfx_vol_changed(val):
            self.settings.set("sfx_volume", val)
            self.sfx_val_lbl.setText(f"{val}%")
            
        self.sfx_slider.valueChanged.connect(on_sfx_vol_changed)
        sfx_vol_layout.addWidget(self.sfx_slider)
        sfx_vol_layout.addWidget(self.sfx_val_lbl)
        
        self.add_row(card, "Drawing Sound Volume:", sfx_vol_container)

        # ── Dedicated Handwriting Preferences Card (Write Engine) ───────────
        writing_card = self.begin_card("Handwriting Preferences (Write Engine)")

        # 1. Hand Direction (Right / Left)
        self.writing_hand_type_combo = QComboBox()
        self.writing_hand_type_combo.addItems(["Right Hand", "Left Hand"])
        _hand_type_keys = ["right", "left"]
        curr_ht = self.settings.get("writing_hand_type", "right")
        ht_idx = _hand_type_keys.index(curr_ht) if curr_ht in _hand_type_keys else 0
        self.writing_hand_type_combo.setCurrentIndex(ht_idx)

        # 2. Writing Pen Model & Style
        self.writing_style_combo = QComboBox()

        def refresh_writing_styles(hand_type_val: str):
            self.writing_style_combo.blockSignals(True)
            self.writing_style_combo.clear()
            available = WritingHandCatalog.get_available_styles(hand_type_val)
            for sid, sname in available:
                self.writing_style_combo.addItem(sname, sid)

            curr_sid = self.settings.get("writing_hand_style", "default")
            idx = self.writing_style_combo.findData(curr_sid)
            if idx < 0:
                idx = 0
            self.writing_style_combo.setCurrentIndex(idx)
            self.writing_style_combo.blockSignals(False)

        refresh_writing_styles(curr_ht)

        def on_writing_hand_type_changed(i: int):
            new_type = _hand_type_keys[i]
            self.settings.set("writing_hand_type", new_type)
            refresh_writing_styles(new_type)

        def on_writing_style_changed(i: int):
            new_sid = self.writing_style_combo.currentData()
            if new_sid:
                self.settings.set("writing_hand_style", new_sid)

        self.writing_hand_type_combo.currentIndexChanged.connect(on_writing_hand_type_changed)
        self.writing_style_combo.currentIndexChanged.connect(on_writing_style_changed)

        self.add_row(writing_card, "Writing Hand:", self.writing_hand_type_combo)
        self.add_row(writing_card, "Pen Model & Style:", self.writing_style_combo)

        # 3. Writing Hand Size Slider (0.5x to 2.0x)
        writing_size_container = QWidget()
        writing_size_layout = QHBoxLayout(writing_size_container)
        writing_size_layout.setContentsMargins(0, 0, 0, 0)
        writing_size_layout.setSpacing(12)

        self.writing_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.writing_size_slider.setRange(5, 20)  # 0.5x to 2.0x
        self.writing_size_slider.setFixedWidth(220)
        curr_size = float(self.settings.get("writing_hand_size", 1.0))
        self.writing_size_slider.setValue(int(round(curr_size * 10)))

        self.writing_size_lbl = QLabel(f"{curr_size:.1f}x")
        self.writing_size_lbl.setStyleSheet("color: #3CB371; font-weight: 600; min-width: 45px;")

        def on_writing_size_changed(val: int):
            fval = val / 10.0
            self.settings.set("writing_hand_size", fval)
            self.writing_size_lbl.setText(f"{fval:.1f}x")

        self.writing_size_slider.valueChanged.connect(on_writing_size_changed)
        writing_size_layout.addWidget(self.writing_size_slider)
        writing_size_layout.addWidget(self.writing_size_lbl)

        self.add_row(writing_card, "Writing Hand Size:", writing_size_container)

        # 4. Handwriting Kinematics Dynamics
        self.writing_algo_combo = QComboBox()
        algo_options = [
            ("Realistic Hybrid (Two-Thirds + Min-Jerk)", "realistic_hybrid"),
            ("Minimum-Jerk Velocity Envelope", "minimum_jerk"),
            ("Two-Thirds Power Law Curvature", "two_thirds_power_law"),
            ("Linear Uniform Timing", "linear"),
        ]
        for label, val in algo_options:
            self.writing_algo_combo.addItem(label, val)

        curr_algo = self.settings.get("writing_algorithm", "realistic_hybrid")
        algo_idx = self.writing_algo_combo.findData(curr_algo)
        if algo_idx < 0:
            algo_idx = 0
        self.writing_algo_combo.setCurrentIndex(algo_idx)

        def on_writing_algo_changed(i: int):
            algo_val = self.writing_algo_combo.currentData()
            if algo_val:
                self.settings.set("writing_algorithm", algo_val)

        self.writing_algo_combo.currentIndexChanged.connect(on_writing_algo_changed)
        self.add_row(writing_card, "Handwriting Dynamics:", self.writing_algo_combo)

        self.layout.addStretch()

