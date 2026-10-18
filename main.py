# Copyright (c) 2026 Mohamed Fadl & EASY SOFT TEAM
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Main entry point for the DrawMotion application.
Features: Initializes the Qt Application, applies the global theme, and sets up the main window structure (TopBar, LeftPanel, CenterWorkspace, RightPanel, BottomPanel).
Usage Summary: Run this file directly to start the application (python main.py).
"""
import sys
import os
import io
import traceback
import ctypes

# Install Native Crash Guard to eliminate silent crashes in standalone mode
def _install_native_crash_handler():
    def _crash_hook(exctype, value, tb):
        trace_str = "".join(traceback.format_exception(exctype, value, tb))
        try:
            from utils.paths import get_app_data_dir
            app_dir = get_app_data_dir()
            log_dir = os.path.join(app_dir, "Logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "crash_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                import datetime
                f.write(f"\n--- CRASH AT {datetime.datetime.now().isoformat()} ---\n")
                f.write(trace_str)
        except Exception:
            pass

        try:
            from core.diagnostics import StartupLifecycleTracker
            StartupLifecycleTracker.trace("FATAL_CRASH", f"{exctype.__name__}: {value}")
        except Exception:
            pass

        try:
            from utils.paths import get_app_data_dir
            msg = (
                f"DrawMotion encountered an unexpected error and needs to close.\n\n"
                f"Error: {exctype.__name__}: {value}\n\n"
                f"Diagnostic details have been saved to:\n"
                f"{os.path.join(get_app_data_dir(), 'Logs', 'crash_log.txt')}"
            )
            ctypes.windll.user32.MessageBoxW(0, msg, "DrawMotion - Critical Error", 0x10 | 0x10000)
        except Exception:
            pass
        
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = _crash_hook

_install_native_crash_handler()

# Permanent module-level references to prevent garbage collection from closing file descriptors
_qt_log_file = None
_crash_log_file = None
_QT_MSG_NAMES = {}

class _SafeLogStream:
    """Safe stream wrapper that writes to a persistent log file and flushes."""
    def __init__(self, target_file=None):
        self._target_file = target_file
    def write(self, s):
        try:
            if self._target_file and not self._target_file.closed:
                self._target_file.write(s)
                self._target_file.flush()
        except Exception:
            pass
    def flush(self):
        try:
            if self._target_file and not self._target_file.closed:
                self._target_file.flush()
        except Exception:
            pass

def _qt_message_handler(msg_type, context, msg):
    """Forensic Qt message handler. Captures qFatal/qCritical/qWarning directly to log and stderr."""
    try:
        import datetime
        t_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        type_name = _QT_MSG_NAMES.get(msg_type, f"TYPE_{msg_type}")
        ctx_info = ""
        if context:
            parts = []
            if getattr(context, "file", None):
                parts.append(str(context.file))
            if getattr(context, "line", 0):
                parts.append(str(context.line))
            if getattr(context, "function", None):
                parts.append(str(context.function))
            if parts:
                ctx_info = f" ({', '.join(parts)})"
        
        line = f"[{t_str}] [{type_name}]{ctx_info} {msg}\n"
        if _qt_log_file and not _qt_log_file.closed:
            _qt_log_file.write(line)
            _qt_log_file.flush()
        if sys.__stderr__:
            try:
                sys.__stderr__.write(line)
                sys.__stderr__.flush()
            except Exception:
                pass
    except Exception:
        pass

# Prevent silent crashes in PyInstaller/Nuitka --windowed mode where stdout/stderr are None
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Suppress Qt Multimedia FFmpeg debug logs
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.debug=false"

import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QFileDialog, QStackedWidget, QInputDialog, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from utils.theme import get_global_qss
from services.export_service import ExportService
from core.settings_manager import SettingsManager
from core.project_engine.project_manager import ProjectManager
from components.project_ui.projects_dialog import ProjectsDialog
from core.diagnostics import StartupLifecycleTracker

# Components
from components.toolbar import TopBar, WhiteInkMenuBar
from components.left_panel import LeftPanel
from components.canvas import CanvasWorkspace
from components.inspector import InspectorPanel
from components.timeline import TimelinePanel
from components.export_ui.export_dialog import ExportDialog

# Globally disable accidental mouse wheel scrolling on input widgets unless focused
from PySide6.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import QObject, QEvent, QCoreApplication

class GlobalWheelEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            try:
                if isinstance(obj, (QComboBox, QSpinBox, QDoubleSpinBox)):
                    if not obj.hasFocus():
                        event.ignore()
                        parent = obj.parent()
                        if parent:
                            QCoreApplication.sendEvent(parent, event)
                        return True
            except RuntimeError:
                pass # Object was already deleted in C++
        return super().eventFilter(obj, event)

# Globally prevent Arabic numerals in QLineEdits
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QLineEdit

class ArabicNumeralFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and isinstance(obj, QLineEdit):
            text = event.text()
            if text:
                arabic_to_english = str.maketrans('٠١٢٣٤٥٦٧٨٩٫', '0123456789.')
                translated = text.translate(arabic_to_english)
                if translated != text:
                    obj.insert(translated)
                    return True
        return super().eventFilter(obj, event)

class WhiteInkMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DrawMotion - Animation Studio (BETA)")
        self.resize(1280, 800)
        
        # Set window icon (ICO for Windows taskbar + title bar)
        _ico_path = os.path.join(os.path.dirname(__file__), "resources", "branding", "ICO", "DrawMotion.ico")
        if os.path.exists(_ico_path):
            self.setWindowIcon(QIcon(_ico_path))
        self.settings_manager = SettingsManager()
        
        from core.project_engine.project_manager import ProjectManager
        self.project_manager = ProjectManager(self)
        self.project_manager.project_error.connect(self._on_project_error)
        self.project_manager.recovery_found.connect(self._prompt_recovery)
        
        self.current_project_filepath = None
        self._init_ui()
        self._update_window_title()
        self._populate_recent_menu()
        
    def _update_window_title(self):
        if self.current_project_filepath and os.path.exists(self.current_project_filepath):
            filename = os.path.basename(self.current_project_filepath)
            self.setWindowTitle(f"DrawMotion Studio - {filename}")
        else:
            self.setWindowTitle("DrawMotion Animation Studio")
            
    def _prompt_recovery(self):
        from components.project_ui.widgets.recovery_dialog import CrashRecoveryDialog
        from PySide6.QtWidgets import QDialog
        
        dialog = CrashRecoveryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.project_manager.recover_crash()
        else:
            self.project_manager.discard_crash_recovery()
            
    def closeEvent(self, event):
        # 1. Gracefully terminate background update checker if running
        if hasattr(self, '_silent_updater') and self._silent_updater:
            try:
                if hasattr(self._silent_updater, 'shutdown'):
                    self._silent_updater.shutdown()
                elif self._silent_updater.isRunning():
                    self._silent_updater.quit()
                    self._silent_updater.wait(500)
            except Exception:
                pass

        # 2. Gracefully terminate thumbnail engine thread
        try:
            from core.thumbnail_engine import ThumbnailEngine
            if getattr(ThumbnailEngine, '_instance', None) is not None:
                ThumbnailEngine._instance.shutdown()
        except Exception:
            pass

        # 3. Gracefully terminate async engine tasks
        try:
            from core.async_engine.engine import AsyncEngine
            if getattr(AsyncEngine, '_instance', None) is not None:
                AsyncEngine._instance.shutdown()
        except Exception:
            pass

        # 4. Clean up the auto-save recovery file on normal graceful exit
        if hasattr(self, 'project_manager'):
            try:
                self.project_manager.cleanup_recovery()
            except Exception:
                pass
            
        # 5. Gracefully shutdown audio & SFX engines
        if hasattr(self, 'center_workspace'):
            ws = self.center_workspace
            if hasattr(ws, 'audio_engine'):
                try:
                    if hasattr(ws.audio_engine, 'shutdown'):
                        ws.audio_engine.shutdown()
                    elif hasattr(ws.audio_engine, 'destroy'):
                        ws.audio_engine.destroy()
                except Exception:
                    pass

            if hasattr(ws, 'animator_engine'):
                anim = ws.animator_engine
                try:
                    if hasattr(anim, 'stop'):
                        anim.stop()
                except Exception:
                    pass
                if hasattr(anim, 'sfx_engine'):
                    try:
                        if hasattr(anim.sfx_engine, 'shutdown'):
                            anim.sfx_engine.shutdown()
                        elif hasattr(anim.sfx_engine, 'destroy'):
                            anim.sfx_engine.destroy()
                    except Exception:
                        pass

        # 6. Stop media preview player in left panel
        if hasattr(self, 'left_panel') and hasattr(self.left_panel, 'player') and self.left_panel.player:
            try:
                self.left_panel.player.stop()
            except Exception:
                pass

        # 7. Gracefully terminate any running planner worker threads
        try:
            from graphics.animated_image_item import _ACTIVE_WORKER_THREADS
            for t in list(_ACTIVE_WORKER_THREADS):
                if t and t.isRunning():
                    t.quit()
                    t.wait(500)
            _ACTIVE_WORKER_THREADS.clear()
        except Exception:
            pass
                
        event.accept()


    def _init_ui(self):
        # Set generous default dimensions to prevent layout overflow
        self.resize(1280, 720)

        # 0. Setup Standard Menu Bar (Separation of Concerns)
        self.main_menu_bar = WhiteInkMenuBar(self)

        # Main Stacked Widget to hold Studio and Settings
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)
        
        # 1. Studio Widget (Main Interface)
        self.studio_widget = QWidget()
        main_layout = QVBoxLayout(self.studio_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        self.main_stack.addWidget(self.studio_widget)

        # Top Bar
        StartupLifecycleTracker.trace("UI_COMPONENT", "Creating TopBar...")
        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)

        # Middle Content (Left Panel + Canvas + Right Panel)
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(8)
        main_layout.addLayout(middle_layout, stretch=1)

        # Left Panel (Assets)
        StartupLifecycleTracker.trace("UI_COMPONENT", "Creating LeftPanel...")
        self.left_panel = LeftPanel()
        StartupLifecycleTracker.trace("UI_COMPONENT", "LeftPanel created successfully.")
        middle_layout.addWidget(self.left_panel)

        # Center Workspace (Canvas)
        StartupLifecycleTracker.trace("UI_COMPONENT", "Creating CanvasWorkspace...")
        self.center_workspace = CanvasWorkspace()
        middle_layout.addWidget(self.center_workspace, stretch=1)
        
        # Connect Mind Map Panel click to workspace (DISABLED - Phase 2.92)
        # getattr(self.left_panel, 'mind_map_panel', None) and self.left_panel.mind_map_panel.shape_clicked.connect(
        #     lambda shape: self.center_workspace.add_mind_map_node(
        #         shape, 
        #         self.center_workspace.view.viewport().rect().center()
        #     )
        # )

        # Right Panel (Inspector)
        StartupLifecycleTracker.trace("UI_COMPONENT", "Creating InspectorPanel...")
        self.right_panel = InspectorPanel()
        self.right_panel.set_workspace(self.center_workspace)
        middle_layout.addWidget(self.right_panel)

        # Bottom Panel (Timeline)
        StartupLifecycleTracker.trace("UI_COMPONENT", "Creating TimelinePanel...")
        self.bottom_panel = TimelinePanel()
        main_layout.addWidget(self.bottom_panel)

        self.bottom_panel.set_workspace(self.center_workspace)

        # Connect Signals
        def _update_play_state(is_playing):
            from utils.icons import get_icon
            if is_playing:
                self.top_bar.play_btn.setText("Stop")
                self.top_bar.play_btn.setIcon(get_icon("stop", "#FF5252"))
            else:
                self.top_bar.play_btn.setText("Play")
                self.top_bar.play_btn.setIcon(get_icon("play"))

        def on_play_clicked():
            # Clear focus from any active widget (like QLineEdit) to ensure editingFinished is processed
            focus_widget = QApplication.focusWidget()
            if focus_widget:
                focus_widget.clearFocus()
                
            engine = self.center_workspace.animator_engine
            if engine.timer.isActive():
                engine.stop()
                self.center_workspace.audio_engine.pause_all()
                _update_play_state(False)
            else:
                if not self.center_workspace.user_items:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self, 
                        "Playback Unavailable", 
                        "Please add at least one visual element (Image or Text) to the scene before starting the animation preview."
                    )
                    return
                self.center_workspace.play_animation()
                _update_play_state(True)
            
        self.top_bar.play_btn.clicked.connect(on_play_clicked)
        
        def on_animation_finished():
            _update_play_state(False)
            self.center_workspace.audio_engine.stop_all()
            
        self.center_workspace.animator_engine.finished.connect(on_animation_finished)
        self.top_bar.tool_selected.connect(self.center_workspace.set_tool_mode)
        self.center_workspace.tool_mode_changed.connect(self.top_bar.set_active_tool)
        
        self.top_bar.zoom_in.connect(self.center_workspace.zoom_in)
        self.top_bar.zoom_out.connect(self.center_workspace.zoom_out)
        self.top_bar.zoom_reset.connect(self.center_workspace.reset_zoom)
        self.center_workspace.zoom_changed.connect(self._on_zoom_changed)
        
        self.top_bar.undo_requested.connect(self.center_workspace.undo_stack.undo)
        self.top_bar.redo_requested.connect(self.center_workspace.undo_stack.redo)
        self.top_bar.export_btn.clicked.connect(self._start_export)
        
        # Connect Menu Bar Actions (Safe Wiring)
        self.main_menu_bar.exit_requested.connect(self.close)
        self.main_menu_bar.new_project_requested.connect(self._new_project_action)
        self.main_menu_bar.open_project_requested.connect(self._open_project_action)
        self.main_menu_bar.save_project_requested.connect(self._save_project_action)
        self.main_menu_bar.save_as_requested.connect(self._save_as_project_action)
        self.main_menu_bar.import_requested.connect(self._import_action)
        self.main_menu_bar.export_requested.connect(self._start_export)
        
        self.main_menu_bar.recent_menu.aboutToShow.connect(self._populate_recent_menu)
        
        self.main_menu_bar.undo_requested.connect(self.center_workspace.undo_stack.undo)
        self.main_menu_bar.redo_requested.connect(self.center_workspace.undo_stack.redo)
        
        # Clipboard connections
        self.main_menu_bar.cut_requested.connect(self._on_cut_requested)
        self.main_menu_bar.copy_requested.connect(self._on_copy_requested)
        self.main_menu_bar.paste_requested.connect(self.center_workspace.clipboard.paste)
        self.main_menu_bar.duplicate_requested.connect(self._on_duplicate_requested)
        
        # Note: Delete action can be wired if center_workspace has a delete selected function
        if hasattr(self.center_workspace, 'delete_selected_items'):
            self.main_menu_bar.delete_requested.connect(self.center_workspace.delete_selected_items)
            
        self.main_menu_bar.zoom_in_requested.connect(self.center_workspace.zoom_in)
        self.main_menu_bar.zoom_out_requested.connect(self.center_workspace.zoom_out)
        self.main_menu_bar.fit_canvas_requested.connect(self.center_workspace.fit_canvas)
        self.main_menu_bar.full_screen_requested.connect(self._toggle_full_screen)
        self.main_menu_bar.toggle_assets_requested.connect(self._toggle_assets_panel)
        self.main_menu_bar.toggle_properties_requested.connect(self._toggle_properties_panel)
        self.main_menu_bar.toggle_timeline_requested.connect(self._toggle_timeline_panel)
        self.main_menu_bar.reset_workspace_requested.connect(self._reset_workspace)
        
        # Temporary placeholder for upcoming features
        self.main_menu_bar.coming_soon_requested.connect(self._on_coming_soon_requested)
        
        # Connect Help Menu Actions
        self.main_menu_bar.user_guide_requested.connect(self._show_user_guide)
        self.main_menu_bar.whats_new_requested.connect(self._show_whats_new)
        self.main_menu_bar.shortcuts_requested.connect(self._show_shortcuts)
        self.main_menu_bar.report_problem_requested.connect(self._show_report_problem)
        self.main_menu_bar.legal_policies_requested.connect(self._show_legal_policies)
        self.main_menu_bar.about_requested.connect(self._show_about)
        
        # Connect Project Menu Actions
        self.main_menu_bar.project_settings_requested.connect(self._show_project_settings)
        self.main_menu_bar.project_info_requested.connect(self._show_project_info)
        
        # Connect Audio Menu Actions
        self.main_menu_bar.add_audio_requested.connect(self._add_audio_action)
        self.main_menu_bar.audio_settings_requested.connect(self._show_audio_settings)
        
        self.top_bar.aspect_ratio_changed.connect(self._on_top_bar_aspect_ratio_changed)
        
        self.center_workspace.item_selected.connect(self.right_panel.on_item_selected)
        
        self.center_workspace.item_loading_state_changed.connect(self._on_item_loading_state_changed)
        
        def on_item_modified():
            self.center_workspace.animator_engine.stop()
            _update_play_state(False)
            if hasattr(self.center_workspace, 'distribute_global_time'):
                self.center_workspace.distribute_global_time()
            else:
                self.center_workspace.items_changed.emit(self.center_workspace.user_items)
            
        self.right_panel.item_modified.connect(on_item_modified)
        
        self.center_workspace.items_changed.connect(self.left_panel.update_layers)
        self.center_workspace.audio_items_changed.connect(self.left_panel.update_audio_library)
        self.center_workspace.items_changed.connect(self.bottom_panel.update_timeline)
        self.center_workspace.animation_progress.connect(self.bottom_panel.set_playhead_progress)
        self.bottom_panel.delete_item_requested.connect(self.center_workspace.delete_timeline_item)
        self.bottom_panel.time_seek.connect(self.center_workspace.seek_animation)
        
        self.left_panel.add_scene_requested.connect(self.center_workspace.add_new_scene)
        self.left_panel.scene_deleted.connect(self.center_workspace.delete_scene)
        self.center_workspace.scene_added.connect(self.left_panel.add_scene_item)
        self.center_workspace.scene_deleted.connect(self.left_panel.remove_scene_item)
        self.left_panel.scene_selected.connect(self.center_workspace.focus_on_artboard)
        self.left_panel.asset_selected.connect(self.center_workspace.add_image_from_path)
        self.left_panel.image_uploaded.connect(self.center_workspace.add_image_from_path)
        self.left_panel.svg_selected.connect(self.center_workspace.add_svg_from_path)
        
        # Inject workspace reference into left_panel for artboard access
        self.left_panel.set_workspace(self.center_workspace)
        self.project_manager.set_workspace(self.center_workspace)

        # 2. Settings Page Widget
        from components.settings.settings_page import SettingsPage
        self.settings_page = SettingsPage()
        self.settings_page.set_project_manager(self.project_manager)
        self.main_stack.addWidget(self.settings_page)
        
        # Navigation connections
        self.top_bar.settings_btn.clicked.connect(self._show_settings_page)
        self.settings_page.back_requested.connect(self._show_studio_widget)

        # Populate initial scenes that were created before signals were connected
        for i in range(len(self.center_workspace.artboards)):
            self.left_panel.add_scene_item(i)

    def _on_project_error(self, error_msg):
        QMessageBox.critical(self, "Project Error", str(error_msg))

    def _on_zoom_changed(self, z):
        self.top_bar.zoom_label.setText("Fit" if z == 0 else f"{z}%")

    def _on_cut_requested(self):
        self._handle_clipboard_action("cut")

    def _on_copy_requested(self):
        self._handle_clipboard_action("copy")

    def _on_duplicate_requested(self):
        self._handle_clipboard_action("duplicate")

    def _toggle_assets_panel(self):
        self._toggle_panel(self.left_panel)

    def _toggle_properties_panel(self):
        self._toggle_panel(self.right_panel)

    def _toggle_timeline_panel(self):
        self._toggle_panel(self.bottom_panel)

    def _on_coming_soon_requested(self, name):
        QMessageBox.information(self, "Coming Soon", f"The '{name}' feature is scheduled for the next update!")

    def _on_top_bar_aspect_ratio_changed(self, w, h):
        for ab in self.center_workspace.artboards:
            ab._set_aspect_ratio(w, h)

    def _on_item_loading_state_changed(self, loading):
        self.right_panel.set_inputs_enabled(not loading)

    def _show_settings_page(self):
        self.main_stack.setCurrentWidget(self.settings_page)

    def _show_studio_widget(self):
        self.main_stack.setCurrentWidget(self.studio_widget)

    def _handle_clipboard_action(self, action: str):
        selected = self.center_workspace.scene.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        if action == "cut":
            self.center_workspace.clipboard.cut(item)
        elif action == "copy":
            self.center_workspace.clipboard.copy(item)
        elif action == "duplicate":
            self.center_workspace.clipboard.duplicate(item)

    def _new_project_action(self):
        reply = QMessageBox.question(
            self, "New Project",
            "Are you sure you want to create a new project? Unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.center_workspace.initialize_new_project()
            self.project_manager.workspace = self.center_workspace
            self.current_project_filepath = None
            if hasattr(self.project_manager, 'current_project_filepath'):
                self.project_manager.current_project_filepath = None
            self._update_window_title()
            QMessageBox.information(self, "New Project", "Workspace cleared for a new project.")

    def _add_to_recent_files(self, filepath: str):
        if not filepath:
            return
        norm_path = os.path.normpath(filepath)
        recent_files = self.settings_manager.get("recent_files", [])
        valid_files = [os.path.normpath(p) for p in recent_files if os.path.exists(p)]
        if norm_path in valid_files:
            valid_files.remove(norm_path)
        valid_files.insert(0, norm_path)
        valid_files = valid_files[:10] # Keep up to 10 recent projects
        self.settings_manager.set("recent_files", valid_files)
        self._populate_recent_menu()

    def _remove_from_recent_files(self, filepath: str):
        norm_path = os.path.normpath(filepath)
        recent_files = self.settings_manager.get("recent_files", [])
        valid_files = [os.path.normpath(p) for p in recent_files if os.path.normpath(p) != norm_path]
        self.settings_manager.set("recent_files", valid_files)
        self._populate_recent_menu()

    def _clear_recent_files(self):
        self.settings_manager.set("recent_files", [])
        self._populate_recent_menu()

    def _populate_recent_menu(self):
        menu = self.main_menu_bar.recent_menu
        menu.clear()
        
        recent_files = self.settings_manager.get("recent_files", [])
        valid_files = [os.path.normpath(p) for p in recent_files if os.path.exists(p)]
        if valid_files != recent_files:
            self.settings_manager.set("recent_files", valid_files)
            recent_files = valid_files
            
        if not recent_files:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            menu.addAction(action)
            return
            
        for idx, path in enumerate(recent_files):
            filename = os.path.basename(path)
            action = QAction(f"{idx + 1}.  {filename}", self)
            action.setToolTip(path)
            action.setStatusTip(path)
            action.setData(path)
            action.triggered.connect(self._on_recent_file_action_triggered)
            menu.addAction(action)

        menu.addSeparator()
        clear_action = QAction("Clear Recent Projects", self)
        clear_action.triggered.connect(self._clear_recent_files)
        menu.addAction(clear_action)

    def _on_recent_file_action_triggered(self):
        action = self.sender()
        if action and hasattr(action, 'data'):
            p = action.data()
            if p:
                self._open_recent_file(p)
                
    def _open_recent_file(self, filepath: str):
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "File Not Found", f"Project file no longer exists:\n{filepath}")
            self._remove_from_recent_files(filepath)
            return
        if self.project_manager.load_project_file(filepath):
            self.current_project_filepath = os.path.normpath(filepath)
            self._add_to_recent_files(filepath)
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{filepath}")

    def _import_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Asset", "", "Supported Files (*.png *.jpg *.jpeg *.svg *.mp3 *.wav)"
        )
        if not file_path: return
        
        ext = file_path.lower().split('.')[-1]
        if ext in ['png', 'jpg', 'jpeg']:
            self.center_workspace.add_image_from_path(file_path)
        elif ext == 'svg':
            self.center_workspace.add_svg_from_path(file_path)
        elif ext in ['mp3', 'wav']:
            # Call LeftPanel Audio library to handle it
            if hasattr(self.left_panel, 'audio_library') and hasattr(self.left_panel.audio_library, '_import_audio'):
                # We need to adapt since _import_audio usually takes no args and opens dialog
                # We will manually add it using AudioEngine directly
                self.center_workspace.audio_engine.add_track(file_path)
                self.center_workspace.audio_items_changed.emit(self.center_workspace.audio_items)
            else:
                QMessageBox.information(self, "Coming Soon", "Direct audio import will be mapped to the timeline in the next update!")

    def _open_project_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", self.project_manager.projects_dir, "DrawMotion Projects (*.wip)"
        )
        if file_path:
            if self.project_manager.load_project_file(file_path):
                self.current_project_filepath = os.path.normpath(file_path)
                self._add_to_recent_files(file_path)
                self._update_window_title()
                QMessageBox.information(self, "Success", "Project loaded successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to load project.")

    def _save_project_action(self):
        active_path = self.current_project_filepath or getattr(self.project_manager, 'current_project_filepath', None)
        if active_path and os.path.exists(os.path.dirname(active_path)):
            if self.project_manager.save_project_to_path(active_path):
                self.current_project_filepath = os.path.normpath(active_path)
                self._add_to_recent_files(active_path)
                self._update_window_title()
                QMessageBox.information(self, "Success", f"Project saved successfully!\n{os.path.basename(active_path)}")
                return
            else:
                QMessageBox.critical(self, "Error", f"Failed to save project:\n{active_path}")
                return

        # Fallback for unsaved / new projects: prompt via Save As
        self._save_as_project_action()

    def _save_as_project_action(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", self.project_manager.projects_dir, "DrawMotion Projects (*.wip)"
        )
        if file_path:
            if not file_path.lower().endswith(".wip"):
                file_path += ".wip"
            if self.project_manager.save_project_to_path(file_path):
                self.current_project_filepath = os.path.normpath(file_path)
                self._add_to_recent_files(file_path)
                self._update_window_title()
                QMessageBox.information(self, "Success", f"Project saved successfully to\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")

    def _toggle_full_screen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()
            
    def _toggle_panel(self, panel: QWidget):
        panel.setVisible(not panel.isVisible())
        
    def _reset_workspace(self):
        self.left_panel.setVisible(True)
        self.right_panel.setVisible(True)
        self.bottom_panel.setVisible(True)
        self.center_workspace.reset_zoom()
        
    def _show_user_guide(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://drawmotion-web.vercel.app/"))

    def _show_whats_new(self):
        from core.updater import CURRENT_VERSION
        from components.whats_new import WhatsNewDialog
        dlg = WhatsNewDialog(CURRENT_VERSION, self)
        dlg.exec()
        
    def _show_shortcuts(self):
        from components.help_dialogs import KeyboardShortcutsDialog
        dlg = KeyboardShortcutsDialog(self)
        dlg.exec()
        
    def _show_report_problem(self):
        from components.help_dialogs import ReportProblemDialog
        dlg = ReportProblemDialog(self)
        dlg.exec()
        
    def _show_legal_policies(self):
        from components.help_dialogs import LegalPoliciesDialog
        dlg = LegalPoliciesDialog(self)
        dlg.exec()

    def _show_about(self):
        from components.help_dialogs import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()
        
    def _show_project_settings(self):
        from components.project_dialogs import ProjectSettingsDialog
        dlg = ProjectSettingsDialog(self.center_workspace, self)
        dlg.exec()
        
    def _show_project_info(self):
        from components.project_dialogs import ProjectInfoDialog
        dlg = ProjectInfoDialog(self.center_workspace, self.project_manager, self)
        dlg.exec()
        
    def _add_audio_action(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Add Audio Track", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_path:
            if hasattr(self.center_workspace, 'audio_engine'):
                self.center_workspace.audio_engine.add_track(file_path)
                self.center_workspace.audio_items_changed.emit(self.center_workspace.audio_items)
            else:
                QMessageBox.critical(self, "Error", "Audio engine not found.")
                
    def _show_audio_settings(self):
        from components.audio_dialogs import AudioSettingsDialog
        dlg = AudioSettingsDialog(self, workspace=self.center_workspace)
        dlg.exec()
        
    def _start_export(self):
        # We use the new ExportDialog UI Prototype
        dialog = ExportDialog(
            self.center_workspace.scene, 
            self.center_workspace.animator_engine, 
            self.center_workspace.user_items, 
            self.center_workspace.audio_items,
            self
        )
        dialog.exec()

if __name__ == "__main__":
    import ctypes
    import sys
    import os
    import datetime
    import faulthandler
    from core.updater import CURRENT_VERSION
    from utils.paths import is_frozen_build, get_app_data_dir
    from core.diagnostics import StartupLifecycleTracker

    # ── 0. Forensic Signal Trapping & Message Routing ───────────────────────
    try:
        log_dir = os.path.join(get_app_data_dir(), "Logs")
        os.makedirs(log_dir, exist_ok=True)
        
        _qt_log_path = os.path.join(log_dir, "qt_messages.log")
        _crash_log_path = os.path.join(log_dir, "crash_faulthandler.log")
        
        _qt_log_file = open(_qt_log_path, "a", encoding="utf-8")
        _crash_log_file = open(_crash_log_path, "a", encoding="utf-8")
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        _qt_log_file.write(f"\n{'='*70}\n[QT_LOG_SESSION_START] {now_str} PID={os.getpid()}\n{'='*70}\n")
        _qt_log_file.flush()
        
        # Safe stream redirection for GUI subsystem (route stdout/stderr to log)
        if sys.stdout is None or isinstance(sys.stdout, io.StringIO):
            sys.stdout = _SafeLogStream(_qt_log_file)
        if sys.stderr is None or isinstance(sys.stderr, io.StringIO):
            sys.stderr = _SafeLogStream(_qt_log_file)
            
        # Enable faulthandler for Python/C signal trapping
        try:
            faulthandler.enable(file=_crash_log_file)
        except Exception:
            pass
            
        # Register Qt message handler before QApplication
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType
        _QT_MSG_NAMES[QtMsgType.QtDebugMsg] = "DEBUG"
        _QT_MSG_NAMES[QtMsgType.QtInfoMsg] = "INFO"
        _QT_MSG_NAMES[QtMsgType.QtWarningMsg] = "WARNING"
        _QT_MSG_NAMES[QtMsgType.QtCriticalMsg] = "CRITICAL"
        _QT_MSG_NAMES[QtMsgType.QtFatalMsg] = "FATAL"
        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass

    # ── 1. Startup Lifecycle Diagnostics Engine ─────────────────────────────
    StartupLifecycleTracker.initialize(version=CURRENT_VERSION)
    StartupLifecycleTracker.trace("BOOTSTRAP_START", f"PID={os.getpid()} Frozen={is_frozen_build()}")

    # ── 2. Single Instance Enforcer (Environment-Isolated Zero-Crash Mutex) ──
    # Development uses 'DrawMotion_Dev_Mutex' and Production uses 'DrawMotion_Prod_Mutex'
    # so they NEVER collide with or block each other.
    ERROR_ALREADY_EXISTS = 183
    mutex_name = "DrawMotion_Prod_Mutex" if is_frozen_build() else "DrawMotion_Dev_Mutex"
    StartupLifecycleTracker.trace("MUTEX_CHECK", f"Checking instance mutex: {mutex_name}")

    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        StartupLifecycleTracker.trace("MUTEX_BLOCKED", f"Another instance of {mutex_name} is already active.")
        from PySide6.QtWidgets import QApplication, QMessageBox
        temp_app = QApplication(sys.argv)
        env_label = "DrawMotion (Production)" if is_frozen_build() else "DrawMotion (Development)"
        QMessageBox.warning(None, "Application Already Running", f"{env_label} is already open!")
        sys.exit(0)

    StartupLifecycleTracker.trace("MUTEX_ACQUIRED", f"Mutex '{mutex_name}' acquired successfully.")
    # ────────────────────────────────────────────────────────────────────────

    # ── Windows Taskbar Fix ─────────────────────────────────────────────────
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DrawMotion.AnimationStudio.1.0"
        )
    except Exception:
        pass
    # ────────────────────────────────────────────────────────────────────────

    # Force application-wide locale to English to prevent Arabic/Indic numerals in QSpinBox
    from PySide6.QtCore import QLocale
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

    app = QApplication(sys.argv)
    StartupLifecycleTracker.trace("QT_APP_READY", "QApplication initialized.")

    from PySide6.QtGui import QImageReader
    from PySide6.QtCore import QCoreApplication
    StartupLifecycleTracker.trace("QT_LIB_PATHS", str(QCoreApplication.libraryPaths()))
    supported_formats = [bytes(fmt).decode('ascii', errors='ignore') for fmt in QImageReader.supportedImageFormats()]
    StartupLifecycleTracker.trace("QT_IMAGE_FORMATS", ", ".join(supported_formats))

    # ── 3. Boot Health Watchdog & Safe Recovery Check ─────────────────────────
    from core.recovery_engine import (
        record_boot_start, record_boot_success, record_boot_abort, is_recovery_required, SafeRecoveryDialog
    )
    
    needs_recovery, health_state = is_recovery_required(CURRENT_VERSION)
    if needs_recovery:
        StartupLifecycleTracker.trace("WATCHDOG_RECOVERY", f"Interventions triggered (attempts={health_state.get('boot_attempts', 0)})")
        rec_dlg = SafeRecoveryDialog(CURRENT_VERSION)
        code = rec_dlg.exec()
        if code == SafeRecoveryDialog.DialogCode.Accepted and rec_dlg.user_choice == "rollback":
            record_boot_abort()
            sys.exit(0)
        elif code == SafeRecoveryDialog.DialogCode.Accepted and rec_dlg.user_choice == "safemode":
            os.environ["DRAWMOTION_SAFE_MODE"] = "1"
        else:
            # Dismissed or continue: clear failure count and continue normal startup
            record_boot_success(CURRENT_VERSION)

    # Record boot start attempt
    record_boot_start(CURRENT_VERSION)
    StartupLifecycleTracker.trace("BOOT_ATTEMPT_RECORDED", "Watchdog marked starting.")
    # ────────────────────────────────────────────────────────────────────────
    
    # Initialize the Smart Error Tracker
    from core.error_handler.tracker import GlobalErrorTracker
    GlobalErrorTracker.initialize()
    
    arabic_filter = ArabicNumeralFilter()
    app.installEventFilter(arabic_filter)
    
    wheel_filter = GlobalWheelEventFilter()
    app.installEventFilter(wheel_filter)

    # Set app-level icon (shows in taskbar, alt+tab, title bar)
    _ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "branding", "ICO", "DrawMotion.ico")
    if os.path.exists(_ico_path):
        app.setWindowIcon(QIcon(_ico_path))

    # Apply global stylesheet
    app.setStyleSheet(get_global_qss())

    StartupLifecycleTracker.trace("UI_CREATING", "Instantiating WhiteInkMainWindow...")
    window = WhiteInkMainWindow()
    StartupLifecycleTracker.trace("UI_CREATED", "WhiteInkMainWindow created successfully.")

    window.showMaximized()
    StartupLifecycleTracker.trace("UI_DISPLAYED", "Main window rendered and maximized.")

    # Mark boot as successful immediately once the main window is rendered
    record_boot_success(CURRENT_VERSION)
    StartupLifecycleTracker.trace("BOOT_HEALTHY", "Startup completed cleanly with zero errors.")


    # --- Smart Updates & What's New ---
    from core.settings_manager import SettingsManager
    from core.updater import CURRENT_VERSION, UpdateCheckerThread
    import time
    from PySide6.QtCore import QTimer

    settings = SettingsManager()
    
    # 1. Check if we need to show What's New (first run after an update)
    last_run = settings.get("last_run_version", "")
    if last_run != CURRENT_VERSION:
        def show_whats_new():
            from components.whats_new import WhatsNewDialog
            dlg = WhatsNewDialog(CURRENT_VERSION, window)
            dlg.exec()
            settings.set("last_run_version", CURRENT_VERSION)
        
        # Show after UI has fully loaded
        QTimer.singleShot(500, show_whats_new)
        
    # 2. External Automatic Update Detection (Background check 2s after launch)
    def start_background_update_check():
        from core.update_engine.auto_notifier import SilentUpdateChecker

        def on_update_found(update_info):
            # Paradigm 2 (Use-While-Updating): Seamless background notification
            # Update top bar button indicator without blocking or freezing the main workspace
            window.top_bar.show_update_available(update_info)

        window._silent_updater = SilentUpdateChecker(window)
        window._silent_updater.update_found.connect(on_update_found)
        window._silent_updater.start()

    # Launch after 2 seconds to guarantee 0ms delay on initial UI startup
    QTimer.singleShot(2000, start_background_update_check)

    sys.exit(app.exec())
