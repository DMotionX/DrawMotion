import json
import os
from utils.paths import get_app_data_dir
from PySide6.QtCore import QObject, Signal

class SettingsManager(QObject):
    """
    Singleton Manager for all application settings.
    Saves to and loads from settings.json.
    Emits signals when settings change so the UI can update dynamically.
    """
    # Signals
    settings_changed = Signal(str, object) # key, new_value
    theme_changed = Signal(str)
    
    _instance = None
    
    DEFAULT_SETTINGS = {
        # Project Settings
        "canvas_size": "16:9",
        "default_scene_duration": 2.0,
        "auto_save_enabled": False,
        "auto_save_interval": 5, # minutes
        "default_project_path": os.path.normpath(os.path.expanduser("~/Documents/DrawMotion/Projects")),
        "default_export_path": os.path.normpath(os.path.expanduser("~/Documents/DrawMotion/Exports")),
        
        # Drawing & Animation
        "default_drawing_style": "solid",
        "hand_size": 2.0,
        "drag_hand_size": 2.2,
        
        # Export Settings
        "export_resolution": "1080p",
        "export_fps": 30,
        "export_format": "mp4",
        
        # General Settings
        "ui_theme": "default",
        "language": "en",
        
        # Updater Settings
        "last_update_check": 0.0,
        "last_run_version": "",
        
        # Hand Style — unified key
        # Values: 'default' | 'left' | 'young_man' | 'old_man' | 'woman' | 'none'
        "hand_style": "default",
        
        # Dedicated Writing Hand Settings
        "writing_hand_type": "right",
        "writing_hand_style": "default",
        "writing_hand_size": 1.0,
        "writing_algorithm": "realistic_hybrid",
        
        # Ink Effect — values: 'dot' | 'particles' | 'none'
        "ink_effect_type": "dot",
        
        # Drawing Sound Volume (Global 0-100)
        "sfx_volume": 40
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            QObject.__init__(cls._instance)
            cls._instance._init()
        return cls._instance
        
    def __init__(self):
        # Prevent Python's automatic __init__ call from triggering QObject.__init__ twice
        pass
        
    def _init(self):
        app_data_dir = get_app_data_dir()
        self.settings_file = os.path.join(app_data_dir, "settings.json")
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._settings.update(data)
                    # Migration: remove old split key and unify into hand_style
                    old_type = self._settings.pop("default_hand_type", None)
                    if old_type == "none" and self._settings.get("hand_style") == "default":
                        self._settings["hand_style"] = "none"
                    elif old_type == "left" and self._settings.get("hand_style") == "default":
                        self._settings["hand_style"] = "left"
                        
                    # Fix: If user has an old settings.json with empty paths, do not let them override the system defaults
                    if not self._settings.get("default_project_path"):
                        self._settings["default_project_path"] = self.DEFAULT_SETTINGS["default_project_path"]
                    if not self._settings.get("default_export_path"):
                        self._settings["default_export_path"] = self.DEFAULT_SETTINGS["default_export_path"]
            except Exception as e:
                print(f"[SettingsManager] Failed to load settings: {e}")

    def save(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"[SettingsManager] Failed to save settings: {e}")

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value):
        if key in self._settings and self._settings[key] == value:
            return # No change
            
        self._settings[key] = value
        self.save()
        self.settings_changed.emit(key, value)
        
        if key == "ui_theme":
            self.theme_changed.emit(value)
