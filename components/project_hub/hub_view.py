# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Container widget and window hosting the QML Project Hub via QQuickWidget.
Features: Graceful fallback on graphics faults, dual-context update wiring, and main window coordination.
"""
import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QIcon, QColor

# Force Qt Quick Controls style to Basic to eliminate platform warnings
try:
    from PySide6.QtQuickControls2 import QQuickStyle
    QQuickStyle.setStyle("Basic")
except Exception:
    pass

from .core.hub_settings import HubSettings
from .core.thumbnail_cache import ThumbnailCache
from .core.project_scanner import ProjectScanner
from .bridge.project_list_model import ProjectListModel
from .bridge.update_bridge import UpdateBridge
from .bridge.hub_bridge import HubBridge

class ProjectHubWidget(QWidget):
    """Wraps QQuickWidget, bridges models, and manages QML lifecycle safely."""

    project_selected = Signal(str)
    new_project_requested = Signal(str)
    new_project_with_preset_requested = Signal(str, int, int)
    browse_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self._is_valid = False

        # 1. Initialize core services and models
        self.settings = HubSettings()
        self.thumb_cache = ThumbnailCache()
        self.scanner = ProjectScanner(self.thumb_cache)
        self.model = ProjectListModel(self)
        self.update_bridge = UpdateBridge(self)
        self.bridge = HubBridge(self.model, self.scanner, self.settings, self)

        # Connect bridge signals to host widget signals
        self.bridge.projectOpenRequested.connect(self.project_selected.emit)
        self.bridge.newProjectRequested.connect(self.new_project_requested.emit)
        self.bridge.newProjectWithPresetRequested.connect(self.new_project_with_preset_requested.emit)
        self.bridge.browseProjectRequested.connect(self.browse_requested.emit)
        self.bridge.closeHubRequested.connect(self.close_requested.emit)

        # 2. Setup QQuickWidget safely
        self.quick_widget = QQuickWidget(self)
        self.quick_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.quick_widget.setAttribute(Qt.WA_AlwaysStackOnTop, False)
        self.quick_widget.setClearColor(QColor("#0D110F"))

        # Explicitly configure QML engine import paths for standalone / frozen builds
        engine = self.quick_widget.engine()
        from utils.paths import resource_path
        qml_import_candidates = [
            resource_path("PySide6/qml"),
            resource_path("qml"),
            os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "PySide6", "qml"),
            os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "qml"),
        ]
        for import_dir in qml_import_candidates:
            if os.path.exists(import_dir):
                engine.addImportPath(import_dir)

        # Inject context properties
        context = self.quick_widget.rootContext()
        context.setContextProperty("hubBridge", self.bridge)
        context.setContextProperty("projectModel", self.model)
        context.setContextProperty("updateBridge", self.update_bridge)

        # Expose official DrawMotion branding icon
        logo_png = resource_path("resources/branding/PNG/DrawMotion_64x64.png")
        if not os.path.exists(logo_png):
            logo_png = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "resources", "branding", "PNG", "DrawMotion_64x64.png"
            )
        logo_url = QUrl.fromLocalFile(logo_png).toString() if os.path.exists(logo_png) else ""
        context.setContextProperty("appLogoUrl", logo_url)

        # Load QML root via multi-candidate resolution
        qml_candidates = [
            resource_path("components/project_hub/qml/MainHub.qml"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "qml", "MainHub.qml"),
            os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "components", "project_hub", "qml", "MainHub.qml"),
        ]
        qml_path = None
        for candidate in qml_candidates:
            if os.path.exists(candidate):
                qml_path = candidate
                break

        if qml_path and os.path.exists(qml_path):
            self.quick_widget.setSource(QUrl.fromLocalFile(qml_path))
            if self.quick_widget.status() != QQuickWidget.Status.Error:
                self._is_valid = True
                self.layout.addWidget(self.quick_widget)
            else:
                self._is_valid = False
                print("[ProjectHub] QML Load Errors:", [e.toString() for e in self.quick_widget.errors()])
        else:
            self._is_valid = False
            print("[ProjectHub] Warning: MainHub.qml could not be located in candidates:", qml_candidates)

        # Initial refresh
        self.bridge.refreshProjects()

        # Start non-intrusive background update check
        self.update_bridge.checkForUpdates()

    def is_valid(self) -> bool:
        """Returns True if QML initialized cleanly without OpenGL or syntax faults."""
        return self._is_valid

    def refresh(self) -> None:
        """Forces an explicit refresh of project listings."""
        if self._is_valid:
            self.bridge.refreshProjects()

    def cleanup(self) -> None:
        """Safely shuts down asynchronous workers and threads."""
        if hasattr(self, 'update_bridge') and self.update_bridge:
            self.update_bridge.shutdown()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)


class ProjectHubWindow(QMainWindow):
    """Standalone window for the Project Hub / Welcome Screen."""

    project_opened = Signal(str)
    new_project_created = Signal(str)
    new_project_with_preset_created = Signal(str, int, int)
    hub_closed = Signal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("DrawMotion - Projects Hub")
        self.resize(1080, 720)
        self.setMinimumSize(880, 560)

        # Set Window Icon
        _ico_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "resources", "branding", "ICO", "DrawMotion.ico"
        )
        if os.path.exists(_ico_path):
            self.setWindowIcon(QIcon(_ico_path))

        # Embed hub widget
        self.hub_widget = ProjectHubWidget(self)
        self.setCentralWidget(self.hub_widget)

        # Apply native Windows 10/11 dark title bar
        self._apply_dark_title_bar()

        # Wire signals
        self.hub_widget.project_selected.connect(self._on_project_selected)
        self.hub_widget.new_project_requested.connect(self._on_new_project_requested)
        self.hub_widget.new_project_with_preset_requested.connect(self._on_new_project_with_preset_requested)
        self.hub_widget.browse_requested.connect(self._on_browse_requested)
        self.hub_widget.close_requested.connect(self._on_close_requested)

        # Forward update installation to main window if available
        self.hub_widget.update_bridge.updateActionTriggered.connect(self._on_update_triggered)

    def _apply_dark_title_bar(self):
        """Applies Windows 10/11 immersive dark mode and charcoal caption color to title bar."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import c_int, byref, sizeof
            hwnd = int(self.winId())
            dark = c_int(1)
            # DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 11 & Windows 10 20H1+)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(dark), sizeof(dark))
            if res != 0:
                # DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 (Windows 10 1809 - 1909)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(dark), sizeof(dark))
            # DWMWA_CAPTION_COLOR (Windows 11 Build 22000+) - charcoal matching #0D110F
            cap_color = c_int(0x000F110D)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(cap_color), sizeof(cap_color))
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_dark_title_bar()

    def is_valid(self) -> bool:
        return self.hub_widget.is_valid()

    def _on_project_selected(self, filepath: str):
        self.hide()
        self.project_opened.emit(filepath)
        if self.main_window:
            self.main_window._open_recent_file(filepath)
            self.main_window.showMaximized()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _on_new_project_requested(self, name: str):
        if self.main_window:
            if hasattr(self.main_window, 'new_project_with_preset'):
                res = self.main_window.new_project_with_preset(1920, 1080)
                if res is False:
                    return
            else:
                self.main_window.new_project_action()
        self.hide()
        self.new_project_created.emit(name)
        if self.main_window:
            self.main_window.showMaximized()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _on_new_project_with_preset_requested(self, name: str, width: int, height: int):
        if self.main_window:
            if hasattr(self.main_window, 'new_project_with_preset'):
                res = self.main_window.new_project_with_preset(width, height)
                if res is False:
                    return
            else:
                self.main_window.new_project_action()
        self.hide()
        self.new_project_with_preset_created.emit(name, width, height)
        if self.main_window:
            self.main_window.showMaximized()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _on_browse_requested(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DrawMotion Project", "", "DrawMotion Projects (*.wip)"
        )
        if file_path:
            self._on_project_selected(file_path)

    def _on_close_requested(self):
        self.hide()
        self.hub_closed.emit()
        if self.main_window:
            self.main_window.showMaximized()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def closeEvent(self, event):
        if hasattr(self, 'hub_widget') and self.hub_widget:
            self.hub_widget.cleanup()
        if self.main_window:
            # Gracefully shut down background silent update checker thread before exit
            if hasattr(self.main_window, '_silent_updater') and self.main_window._silent_updater:
                try:
                    if hasattr(self.main_window._silent_updater, 'shutdown'):
                        self.main_window._silent_updater.shutdown()
                    elif self.main_window._silent_updater.isRunning():
                        self.main_window._silent_updater.quit()
                        self.main_window._silent_updater.wait(500)
                except Exception:
                    pass
            if hasattr(self.main_window, 'isVisible') and not self.main_window.isVisible():
                self.main_window.close()
                from PySide6.QtWidgets import QApplication
                QApplication.quit()
        super().closeEvent(event)

    def show_hub(self):
        """Refreshes and displays the hub maximized on the primary screen."""
        self.hub_widget.refresh()
        self.showMaximized()
        self._apply_dark_title_bar()
        self.raise_()
        self.activateWindow()

    def _on_update_triggered(self, update_info: dict):
        if self.main_window and hasattr(self.main_window, 'top_bar'):
            self.main_window.top_bar.show_update_available(update_info)
            from core.updater import UpdaterDialog
            dlg = UpdaterDialog(self)
            dlg.exec()
