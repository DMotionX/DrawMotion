import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QCheckBox, 
    QPushButton, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from utils.theme import THEME_COLORS

class AudioFXPanel(QWidget):
    """
    Zero-Risk Audio Properties Panel for manipulating audio tracks.
    """
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_audio_item = None
        self._init_ui()
        
    def _init_ui(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                margin-top: 1.5ex;
                background-color: rgba(0, 0, 0, 0.2);
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {THEME_COLORS['primary_green']};
                font-size: 11px;
                font-weight: bold;
                left: 10px;
            }}
            QSlider::groove:horizontal {{
                border-radius: 3px;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
            }}
            QSlider::sub-page:horizontal {{
                background: {THEME_COLORS['primary_green']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: #FFFFFF;
                border: 2px solid {THEME_COLORS['primary_green']};
            }}
            QCheckBox {{
                spacing: 8px;
                font-size: 12px;
                color: {THEME_COLORS['text_primary']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME_COLORS['primary_green']};
                border: 1px solid {THEME_COLORS['primary_green']};
                image: url(assets/icons/check.png); /* Fallback to green if missing */
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 0. Audio Output Device
        dev_group = QGroupBox("Audio Output Device")
        dev_layout = QVBoxLayout(dev_group)
        self.dev_combo = QComboBox()
        self.dev_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                color: #FFFFFF;
                padding: 5px 8px;
                font-size: 11px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: #1A211D;
                color: #FFFFFF;
                selection-background-color: {THEME_COLORS['primary_green']};
                selection-color: #FFFFFF;
            }}
        """)
        self._populate_devices()
        self.dev_combo.currentIndexChanged.connect(self._on_device_changed)
        dev_layout.addWidget(self.dev_combo)
        main_layout.addWidget(dev_group)
        
        # 1. Volume Booster
        vol_group = QGroupBox("Volume Booster (Native)")
        vol_layout = QVBoxLayout(vol_group)
        
        vol_header = QHBoxLayout()
        vol_lbl = QLabel("Level:")
        self.vol_val = QLabel("100% (Recommended)")
        self.vol_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        vol_header.addWidget(vol_lbl)
        vol_header.addStretch()
        vol_header.addWidget(self.vol_val)
        
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 300) # Up to 300% boost
        self.vol_slider.setValue(100)
        self.vol_slider.valueChanged.connect(self._on_vol_changed)
        
        vol_layout.addLayout(vol_header)
        vol_layout.addWidget(self.vol_slider)
        
        # 2. Noise Cancellation
        noise_group = QGroupBox("Noise Cancellation (AI Filter)")
        noise_layout = QVBoxLayout(noise_group)
        
        self.noise_checkbox = QCheckBox("Enable Background De-Noise")
        self.noise_checkbox.setChecked(False)
        self.noise_checkbox.toggled.connect(self._on_settings_changed)
        
        hint_lbl = QLabel("Hint: Removes static and room hum dynamically.")
        hint_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px;")
        
        noise_layout.addWidget(self.noise_checkbox)
        noise_layout.addWidget(hint_lbl)
        
        main_layout.addWidget(vol_group)
        main_layout.addWidget(noise_group)
        
        # 3. Auto Normalize
        norm_group = QGroupBox("Smart Auto-Normalize")
        norm_layout = QVBoxLayout(norm_group)
        
        self.norm_checkbox = QCheckBox("Enable Auto-Normalize (Studio Level)")
        self.norm_checkbox.setChecked(False)
        self.norm_checkbox.toggled.connect(self._on_settings_changed)
        
        norm_hint = QLabel("Hint: Automatically balances loud and quiet parts.")
        norm_hint.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px;")
        
        norm_layout.addWidget(self.norm_checkbox)
        norm_layout.addWidget(norm_hint)
        main_layout.addWidget(norm_group)
        
        # 4. Speed & Pitch
        speed_group = QGroupBox("Speed & Pitch")
        speed_layout = QVBoxLayout(speed_group)
        
        # Speed Slider
        speed_header = QHBoxLayout()
        speed_lbl = QLabel("Speed:")
        self.speed_val = QLabel("1.0x (Recommended)")
        self.speed_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        speed_header.addWidget(speed_lbl)
        speed_header.addStretch()
        speed_header.addWidget(self.speed_val)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200) # 0.5x to 2.0x
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        
        speed_layout.addLayout(speed_header)
        speed_layout.addWidget(self.speed_slider)
        
        # Pitch Checkbox (Simple approach)
        self.pitch_checkbox = QCheckBox("Deep Pitch Shift (Voice Masking)")
        self.pitch_checkbox.setChecked(False)
        self.pitch_checkbox.toggled.connect(self._on_settings_changed)
        
        speed_layout.addWidget(self.pitch_checkbox)
        main_layout.addWidget(speed_group)
        
        # 5. Fade In & Fade Out
        fade_group = QGroupBox("Smooth Transitions (Fade In/Out)")
        fade_layout = QVBoxLayout(fade_group)
        
        # Fade In
        fi_header = QHBoxLayout()
        fi_lbl = QLabel("Fade In (s):")
        self.fi_val = QLabel("0.0s")
        self.fi_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        fi_header.addWidget(fi_lbl)
        fi_header.addStretch()
        fi_header.addWidget(self.fi_val)
        
        self.fi_slider = QSlider(Qt.Orientation.Horizontal)
        self.fi_slider.setRange(0, 50) # 0 to 5 seconds (0.1 steps)
        self.fi_slider.setValue(0)
        self.fi_slider.valueChanged.connect(self._on_fade_changed)
        
        fade_layout.addLayout(fi_header)
        fade_layout.addWidget(self.fi_slider)
        
        # Fade Out
        fo_header = QHBoxLayout()
        fo_lbl = QLabel("Fade Out (s):")
        self.fo_val = QLabel("0.0s")
        self.fo_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        fo_header.addWidget(fo_lbl)
        fo_header.addStretch()
        fo_header.addWidget(self.fo_val)
        
        self.fo_slider = QSlider(Qt.Orientation.Horizontal)
        self.fo_slider.setRange(0, 50)
        self.fo_slider.setValue(0)
        self.fo_slider.valueChanged.connect(self._on_fade_changed)
        
        fade_layout.addLayout(fo_header)
        fade_layout.addWidget(self.fo_slider)
        main_layout.addWidget(fade_group)
        
        main_layout.addStretch()
        
    def _update_fade_labels(self):
        fi = self.fi_slider.value() / 10.0
        fo = self.fo_slider.value() / 10.0
        
        self.fi_val.setText(f"{fi:.1f}s")
        self.fo_val.setText(f"{fo:.1f}s")
        
        if fi > 0:
            self.fi_val.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: normal;")
        else:
            self.fi_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
            
        if fo > 0:
            self.fo_val.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: normal;")
        else:
            self.fo_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")

    def _on_fade_changed(self):
        self._update_fade_labels()
        self._on_settings_changed()

    def _update_vol_label(self, val):
        if val == 100:
            self.vol_val.setText("100% (Recommended)")
            self.vol_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        elif val > 100:
            self.vol_val.setText(f"{val}% (Export Boost)")
            self.vol_val.setStyleSheet("color: #FFB800; font-weight: bold;")
        else:
            self.vol_val.setText(f"{val}%")
            self.vol_val.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: normal;")
        
    def _on_vol_changed(self, val):
        self._update_vol_label(val)
        self._on_settings_changed()

    def _update_speed_label(self, val):
        mult = val / 100.0
        if val == 100:
            self.speed_val.setText("1.0x (Recommended)")
            self.speed_val.setStyleSheet(f"color: {THEME_COLORS['primary_green']}; font-weight: bold;")
        else:
            self.speed_val.setText(f"{mult}x")
            self.speed_val.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: normal;")
        
    def _on_speed_changed(self, val):
        self._update_speed_label(val)
        self._on_settings_changed()
        
    def _on_settings_changed(self):
        if self._current_audio_item:
            settings = {
                "volume": self.vol_slider.value(),
                "denoise": self.noise_checkbox.isChecked(),
                "normalize": self.norm_checkbox.isChecked(),
                "speed": self.speed_slider.value() / 100.0,
                "pitch": self.pitch_checkbox.isChecked(),
                "fade_in": self.fi_slider.value() / 10.0,
                "fade_out": self.fo_slider.value() / 10.0
            }
            # Save safely to item properties
            self._current_audio_item.audio_fx_settings = settings
            self.settings_changed.emit(settings)
            
    def set_node(self, item):
        """Bind UI to selected audio item safely."""
        self._current_audio_item = item
        if not item:
            return
            
        settings = getattr(item, 'audio_fx_settings', {"volume": 100, "denoise": False, "normalize": False, "speed": 1.0, "pitch": False, "fade_in": 0.0, "fade_out": 0.0})
        
        self.vol_slider.blockSignals(True)
        self.noise_checkbox.blockSignals(True)
        self.norm_checkbox.blockSignals(True)
        self.speed_slider.blockSignals(True)
        self.pitch_checkbox.blockSignals(True)
        self.fi_slider.blockSignals(True)
        self.fo_slider.blockSignals(True)
        
        self.vol_slider.setValue(settings.get("volume", 100))
        self.noise_checkbox.setChecked(settings.get("denoise", False))
        self.norm_checkbox.setChecked(settings.get("normalize", False))
        self.speed_slider.setValue(int(settings.get("speed", 1.0) * 100))
        self.pitch_checkbox.setChecked(settings.get("pitch", False))
        self.fi_slider.setValue(int(settings.get("fade_in", 0.0) * 10))
        self.fo_slider.setValue(int(settings.get("fade_out", 0.0) * 10))
        
        self._update_vol_label(settings.get("volume", 100))
        self._update_speed_label(int(settings.get("speed", 1.0) * 100))
        self._update_fade_labels()
        
        self.vol_slider.blockSignals(False)
        self.noise_checkbox.blockSignals(False)
        self.norm_checkbox.blockSignals(False)
        self.speed_slider.blockSignals(False)
        self.pitch_checkbox.blockSignals(False)
        self.fi_slider.blockSignals(False)
        self.fo_slider.blockSignals(False)
        
        self._populate_devices()

    def _populate_devices(self):
        from PySide6.QtMultimedia import QMediaDevices
        from core.settings_manager import SettingsManager
        devices = QMediaDevices.audioOutputs()
        saved_desc = SettingsManager().get("audio_output_device", "")
        
        self.dev_combo.blockSignals(True)
        self.dev_combo.clear()
        
        selected_idx = 0
        preferred_idx = -1
        for idx, dev in enumerate(devices):
            desc = dev.description()
            self.dev_combo.addItem(desc, desc)
            if saved_desc and desc == saved_desc:
                selected_idx = idx
            elif preferred_idx == -1 and any(k in desc.lower() for k in ["headphone", "earphone", "headset"]):
                preferred_idx = idx
                
        if not saved_desc and preferred_idx != -1:
            selected_idx = preferred_idx
            
        if self.dev_combo.count() > 0:
            self.dev_combo.setCurrentIndex(selected_idx)
            
        self.dev_combo.blockSignals(False)

    def _on_device_changed(self, idx):
        desc = self.dev_combo.currentData()
        if desc:
            from core.settings_manager import SettingsManager
            SettingsManager().set("audio_output_device", desc)
            parent_win = self.window()
            ws = getattr(parent_win, 'center_workspace', None)
            if ws and hasattr(ws, 'audio_engine'):
                ws.audio_engine.set_output_device(desc)
            if ws and hasattr(ws, 'animator_engine') and hasattr(ws.animator_engine, 'sfx_engine'):
                ws.animator_engine.sfx_engine.set_output_device(desc)
