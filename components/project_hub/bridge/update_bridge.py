# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Bridges the core updater thread with the QML Project Hub interface.
Features: Non-blocking asynchronous update checks, state notification, and seamless dispatch.
"""
from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from core.updater import CURRENT_VERSION, UpdateCheckerThread

class UpdateBridge(QObject):
    """Exposes update state and controls to QML without blocking the UI thread."""

    updateStateChanged = Signal()
    updateActionTriggered = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_version = CURRENT_VERSION
        self._latest_version = ""
        self._changelog = ""
        self._has_update = False
        self._is_checking = False
        self._update_data = {}
        self._checker_thread = None

    @Property(str, notify=updateStateChanged)
    def currentVersion(self) -> str:
        return self._current_version

    @Property(str, notify=updateStateChanged)
    def latestVersion(self) -> str:
        return self._latest_version

    @Property(str, notify=updateStateChanged)
    def changelog(self) -> str:
        return self._changelog

    @Property(bool, notify=updateStateChanged)
    def hasUpdate(self) -> bool:
        return self._has_update

    @Property(bool, notify=updateStateChanged)
    def isChecking(self) -> bool:
        return self._is_checking

    @Slot()
    def checkForUpdates(self) -> None:
        """Launches a safe background update check."""
        if self._is_checking:
            return

        self._is_checking = True
        self.updateStateChanged.emit()

        self._checker_thread = UpdateCheckerThread(self)
        self._checker_thread.update_available.connect(self._on_update_available)
        self._checker_thread.no_update.connect(self._on_no_update)
        self._checker_thread.error.connect(self._on_update_error)
        self._checker_thread.start()

    def _on_update_available(self, data: dict) -> None:
        self._is_checking = False
        self._update_data = data
        self._latest_version = data.get("version", "")
        self._changelog = data.get("changelog", "")
        self._has_update = True
        self.updateStateChanged.emit()

    def _on_no_update(self) -> None:
        self._is_checking = False
        self._has_update = False
        self.updateStateChanged.emit()

    def _on_update_error(self, err: str) -> None:
        self._is_checking = False
        self.updateStateChanged.emit()

    @Slot()
    def dismissUpdate(self) -> None:
        """Dismisses the update notification banner for this session."""
        self._has_update = False
        self.updateStateChanged.emit()

    @Slot()
    def triggerUpdate(self) -> None:
        """Emits signal to main window to launch the official updater dialog or process."""
        self.updateActionTriggered.emit(self._update_data)

    @Slot()
    def openChangelog(self) -> None:
        """Opens project releases page in default web browser."""
        url = "https://github.com/DMotionX/DrawMotion/releases"
        QDesktopServices.openUrl(QUrl(url))

    def shutdown(self) -> None:
        """Safely terminates active checker thread to prevent process aborts on exit."""
        if self._checker_thread:
            try:
                self._checker_thread.shutdown()
            except Exception:
                pass
