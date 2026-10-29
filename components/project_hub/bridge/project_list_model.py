# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Reactive list model exposing project archives to QML views.
Features: Standard QAbstractListModel implementation with named roles and atomic updates.
"""
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QByteArray, Property, Signal, Slot

class ProjectListModel(QAbstractListModel):
    """Exposes structured project data to QML ListView and GridView."""

    TitleRole = Qt.UserRole + 1
    PathRole = Qt.UserRole + 2
    ModifiedRole = Qt.UserRole + 3
    SizeRole = Qt.UserRole + 4
    ThumbnailRole = Qt.UserRole + 5
    SceneCountRole = Qt.UserRole + 6

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[dict] = []

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            self.TitleRole: QByteArray(b"title"),
            self.PathRole: QByteArray(b"path"),
            self.ModifiedRole: QByteArray(b"lastModified"),
            self.SizeRole: QByteArray(b"formattedSize"),
            self.ThumbnailRole: QByteArray(b"thumbnail"),
            self.SceneCountRole: QByteArray(b"sceneCount"),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._projects)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._projects)):
            return None

        project = self._projects[index.row()]
        if role == self.TitleRole:
            return project.get("title", "")
        elif role == self.PathRole:
            return project.get("path", "")
        elif role == self.ModifiedRole:
            return project.get("last_modified", "")
        elif role == self.SizeRole:
            return project.get("formatted_size", "")
        elif role == self.ThumbnailRole:
            return project.get("thumbnail", "")
        elif role == self.SceneCountRole:
            return project.get("scene_count", 1)
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._projects)

    def set_projects(self, projects: list[dict]) -> None:
        """Atomically replaces the project dataset and notifies QML views."""
        self.beginResetModel()
        self._projects = list(projects)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int, result="QVariantMap")
    def get(self, index: int) -> dict:
        """Allows direct index-based retrieval from QML."""
        if 0 <= index < len(self._projects):
            return self._projects[index]
        return {}

    def remove_by_path(self, filepath: str) -> None:
        """Removes a single item by path with animated row removal."""
        for idx, p in enumerate(self._projects):
            if p.get("path") == filepath:
                self.beginRemoveRows(QModelIndex(), idx, idx)
                self._projects.pop(idx)
                self.endRemoveRows()
                self.countChanged.emit()
                break
