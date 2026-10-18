from PySide6.QtWidgets import QComboBox, QSlider, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from .project_settings import SettingsSection

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

        self.layout.addStretch()
