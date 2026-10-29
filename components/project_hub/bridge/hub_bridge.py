# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Main controller bridge between Project Hub QML UI and DrawMotion core services.
Features: Dispatches project actions, controls sorting/filtering, and notifies the host window.
"""
import os
import subprocess
import sys
from PySide6.QtCore import QObject, Signal, Slot, Property
from ..core.project_scanner import ProjectScanner
from ..core.hub_settings import HubSettings
from .project_list_model import ProjectListModel

class HubBridge(QObject):
    """Exposes high-level project workflows and filtering actions to QML."""

    projectOpenRequested = Signal(str)
    newProjectRequested = Signal(str)
    newProjectWithPresetRequested = Signal(str, int, int)
    browseProjectRequested = Signal()
    closeHubRequested = Signal()
    stateChanged = Signal()

    def __init__(self, model: ProjectListModel, scanner: ProjectScanner = None, settings: HubSettings = None, parent=None):
        super().__init__(parent)
        self._model = model
        self._settings = settings or HubSettings()
        self._scanner = scanner or ProjectScanner()
        
        self._search_query = ""
        self._view_mode = self._settings.get_view_mode()
        self._sort_mode = self._settings.get_sort_mode()

    @Property(str, notify=stateChanged)
    def searchQuery(self) -> str:
        return self._search_query

    @Property(str, notify=stateChanged)
    def viewMode(self) -> str:
        return self._view_mode

    @Property(str, notify=stateChanged)
    def sortMode(self) -> str:
        return self._sort_mode

    @Property(int, notify=stateChanged)
    def projectCount(self) -> int:
        return self._model.count

    @Property(str, notify=stateChanged)
    def totalStorageFormatted(self) -> str:
        total_bytes = sum(p.get("size_bytes", 0) for p in self._model._projects)
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        else:
            return f"{total_bytes / (1024 * 1024):.1f} MB"

    @Slot(str)
    def setSearchQuery(self, query: str) -> None:
        self._search_query = query
        self.refreshProjects()

    @Slot(str)
    def setViewMode(self, mode: str) -> None:
        if mode in (HubSettings.VIEW_GRID, HubSettings.VIEW_LIST):
            self._view_mode = mode
            self._settings.set_view_mode(mode)
            self.stateChanged.emit()

    @Slot(str)
    def setSortMode(self, mode: str) -> None:
        self._sort_mode = mode
        self._settings.set_sort_mode(mode)
        self.refreshProjects()

    @Slot()
    def refreshProjects(self) -> None:
        """Scans filesystem and updates the reactive model."""
        projects = self._scanner.scan_all_projects(self._search_query, self._sort_mode)
        self._model.set_projects(projects)
        self.stateChanged.emit()

    @Slot(str)
    def openProject(self, path: str) -> None:
        """Requests opening an existing project."""
        norm = os.path.normpath(path)
        if os.path.exists(norm):
            self.projectOpenRequested.emit(norm)

    @Slot(str)
    def createNewProject(self, name: str = "") -> None:
        """Requests creating a new project."""
        self.newProjectRequested.emit(name.strip())

    @Slot(str, int, int)
    def createNewProjectWithPreset(self, name: str, width: int, height: int) -> None:
        """Requests creating a new project configured with canvas aspect ratio dimensions."""
        self.newProjectWithPresetRequested.emit(name.strip(), width, height)

    @Slot()
    def browseProject(self) -> None:
        """Requests triggering file dialog to open an external .wip project."""
        self.browseProjectRequested.emit()

    @Slot(str)
    def deleteProject(self, path: str) -> None:
        """Permanently deletes a project archive and updates the model."""
        self._scanner.delete_project_file(path)
        self._model.remove_by_path(path)
        self.stateChanged.emit()

    @Slot(str)
    def removeRecentProject(self, path: str) -> None:
        """Removes the project from recents without deleting the physical file."""
        self._scanner.remove_recent_entry(path)
        self._model.remove_by_path(path)
        self.stateChanged.emit()

    @Slot(str)
    def showInExplorer(self, path: str) -> None:
        """Opens native file explorer and highlights the project file."""
        norm = os.path.normpath(path)
        if os.path.exists(norm):
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{norm}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", norm])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(norm)])

    @Slot()
    def openProjectsDirectory(self) -> None:
        """Opens the default Projects directory in native file explorer."""
        proj_dir = self._scanner._get_default_projects_dir()
        os.makedirs(proj_dir, exist_ok=True)
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{os.path.normpath(proj_dir)}"')
        elif sys.platform == "darwin":
            subprocess.Popen(["open", proj_dir])
        else:
            subprocess.Popen(["xdg-open", proj_dir])

    @Slot()
    def closeHub(self) -> None:
        """Requests closing the Hub and focusing the Studio editor."""
        self.closeHubRequested.emit()
