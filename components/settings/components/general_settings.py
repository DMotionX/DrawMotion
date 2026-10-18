from PySide6.QtWidgets import QComboBox, QLabel
from .project_settings import SettingsSection


class GeneralSettings(SettingsSection):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Card 1: Appearance ────────────────────────────────────────────────
        card1 = self.begin_card("Appearance")

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default Theme", "Light Mode (Coming Soon)", "Dark Mode (Coming Soon)"])
        current_theme = self.settings.get("ui_theme", "default")
        self.theme_combo.setCurrentIndex({"default": 0, "light": 1, "dark": 2}.get(current_theme, 0))

        def set_theme(idx):
            self.settings.set("ui_theme", ["default", "light", "dark"][idx])

        self.theme_combo.currentIndexChanged.connect(set_theme)
        self.add_row(card1, "UI Theme:", self.theme_combo)

        # ── Card 2: Language ──────────────────────────────────────────────────
        card2 = self.begin_card("Language")

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English (US)", "العربية (Coming Soon)"])
        self.lang_combo.setCurrentIndex(0)

        def on_lang_change(idx):
            if idx == 1:
                self.lang_combo.setCurrentIndex(0)
            else:
                self.settings.set("language", "en")

        self.lang_combo.currentIndexChanged.connect(on_lang_change)
        self.add_row(card2, "Language:", self.lang_combo)

        note = QLabel("* More language support will be available in a future update.")
        note.setStyleSheet("color: #4A6055; font-size: 11px; margin-top: 4px;")
        card2.addWidget(note)
        
        # ── Card 3: Performance (Beta) ────────────────────────────────────────
        card3 = self.begin_card("Performance")
        
        from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QFrame
        from PySide6.QtCore import Qt
        
        # Container for the row to give it some padding and nice hover feel
        perf_container = QFrame()
        perf_container.setStyleSheet("background-color: transparent;")
        
        row_layout = QHBoxLayout(perf_container)
        row_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Title and Description
        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        
        title_lbl = QLabel("Hardware Acceleration (GPU)")
        title_lbl.setStyleSheet("color: #E2E8F0; font-size: 15px; font-weight: 700; background: transparent;")
        
        desc_lbl = QLabel("Offload heavy rendering to your graphics card for extremely smooth timeline playback and transitions.\nNote: Requires a dedicated graphics card. A restart is required after changing this setting.")
        desc_lbl.setStyleSheet("color: #7A9E90; font-size: 13px; background: transparent;")
        desc_lbl.setWordWrap(True)
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)
        
        row_layout.addLayout(text_layout)
        row_layout.addStretch()
        
        # Right side: Styled Checkbox (Toggle-like)
        self.gpu_cb = QCheckBox("Enable (Beta)")
        self.gpu_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gpu_cb.setStyleSheet("""
            QCheckBox { color: #E2A03F; font-size: 14px; font-weight: bold; background: transparent; padding-right: 10px; }
            QCheckBox::indicator { width: 24px; height: 24px; border-radius: 6px; border: 2px solid #2E5040; background-color: #111D18; }
            QCheckBox::indicator:checked { background-color: #38A169; border-color: #38A169; }
            QCheckBox::indicator:hover { border-color: #3CB371; }
        """)
        
        is_gpu = self.settings.get("use_gpu_acceleration", False)
        self.gpu_cb.setChecked(is_gpu)
        
        def on_gpu_changed(state):
            is_enabled = bool(state)
            self.settings.set("use_gpu_acceleration", is_enabled)
            if hasattr(self, 'gpu_status_lbl'):
                if not is_enabled:
                    self.gpu_status_lbl.setText("Disabled (Safe Mode)")
                    self.gpu_status_lbl.setStyleSheet("color: #718096; font-size: 12px; margin-left: 10px; font-weight: bold;")
                else:
                    self.gpu_status_lbl.setText("Active (Hardware Accelerated)")
                    self.gpu_status_lbl.setStyleSheet("color: #48BB78; font-size: 12px; margin-left: 10px; font-weight: bold;")
                
        self.gpu_cb.stateChanged.connect(on_gpu_changed)
        row_layout.addWidget(self.gpu_cb)
        
        # Add FPS Checkbox
        self.fps_cb = QCheckBox("Show FPS")
        self.fps_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fps_cb.setStyleSheet("""
            QCheckBox { color: #A0AEC0; font-size: 13px; font-weight: bold; background: transparent; padding-right: 10px; margin-left: 10px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #4A5568; background-color: #1A202C; }
            QCheckBox::indicator:checked { background-color: #48BB78; border-color: #48BB78; }
            QCheckBox::indicator:hover { border-color: #A0AEC0; }
        """)
        
        is_fps = self.settings.get("show_fps", False)
        self.fps_cb.setChecked(is_fps)
        self.fps_cb.stateChanged.connect(self._on_fps_changed)
        row_layout.addWidget(self.fps_cb)
        
        card3.addWidget(perf_container)
        
        # Tools row
        from PySide6.QtWidgets import QPushButton, QMessageBox
        from PySide6.QtOpenGLWidgets import QOpenGLWidget
        from PySide6.QtGui import QOpenGLContext

        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(10, 0, 10, 10)
        
        check_btn = QPushButton("Check GPU Compatibility")
        check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        check_btn.setStyleSheet("""
            QPushButton { background-color: #2D3748; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; border: 1px solid #4A5568; }
            QPushButton:hover { background-color: #4A5568; }
        """)
        
        test_btn = QPushButton("Test Smoothness (Benchmark)")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet("""
            QPushButton { background-color: #2C7A7B; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; border: 1px solid #319795; }
            QPushButton:hover { background-color: #319795; }
        """)
        
        self.gpu_status_lbl = QLabel("")
        
        is_gpu_enabled = self.settings.get("use_gpu_acceleration", False)
        if is_gpu_enabled:
            self.gpu_status_lbl.setText("Active (Hardware Accelerated)")
            self.gpu_status_lbl.setStyleSheet("color: #48BB78; font-size: 12px; margin-left: 10px; font-weight: bold;")
        else:
            self.gpu_status_lbl.setText("Disabled (Safe Mode)")
            self.gpu_status_lbl.setStyleSheet("color: #718096; font-size: 12px; margin-left: 10px; font-weight: bold;")
        
        tools_layout.addWidget(check_btn)
        tools_layout.addWidget(test_btn)
        tools_layout.addWidget(self.gpu_status_lbl)
        tools_layout.addStretch()
        
        card3.addLayout(tools_layout)
        
        def run_gpu_check():
            from core.gpu_engine.hardware_detector import GPUHardwareDetector
            
            best_gpu = GPUHardwareDetector.detect_best_gpu()
            is_supported = GPUHardwareDetector.is_gpu_supported(best_gpu)
            
            if is_supported:
                self.gpu_status_lbl.setText(f"Active: {best_gpu}")
                self.gpu_status_lbl.setStyleSheet("color: #48BB78; font-size: 12px; margin-left: 10px; font-weight: bold;")
                self.gpu_cb.setChecked(True)
            else:
                self.gpu_status_lbl.setText("Unsupported or missing GPU.")
                self.gpu_status_lbl.setStyleSheet("color: #F56565; font-size: 12px; margin-left: 10px; font-weight: bold;")
                self.gpu_cb.setChecked(False)
                QMessageBox.warning(self, "Compatibility Check", "Sorry, your graphics card does not support hardware acceleration. The application will continue running in Safe Mode (CPU) to ensure stability.")
                
        def run_benchmark():
            from core.gpu_engine.benchmark_tool import BenchmarkTool
            dlg = BenchmarkTool(self)
            dlg.exec()
            
        check_btn.clicked.connect(run_gpu_check)
        test_btn.clicked.connect(run_benchmark)

        self._main_layout.addStretch()

    def _on_fps_changed(self, state):
        self.settings.set("show_fps", bool(state))
