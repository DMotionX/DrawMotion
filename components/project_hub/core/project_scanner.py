# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Discovers, inspects, and filters DrawMotion project files.
Features: Gathers recent and saved projects with atomic file checks, metadata parsing, and search filtering.
"""
import os
import time
import json
import zipfile
from datetime import datetime
from core.settings_manager import SettingsManager
from utils.paths import get_app_data_dir
from .thumbnail_cache import ThumbnailCache
from .hub_settings import HubSettings

class ProjectScanner:
    """Scans and formats local DrawMotion (.wip) project archives."""

    def __init__(self, thumbnail_cache: ThumbnailCache = None):
        self._settings = SettingsManager()
        self._thumb_cache = thumbnail_cache or ThumbnailCache()

    def _get_default_projects_dir(self) -> str:
        custom_path = self._settings.get("default_project_path", "")
        if custom_path and os.path.exists(custom_path):
            return custom_path
        return os.path.join(get_app_data_dir(), "Projects")

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _format_timestamp(self, timestamp: float) -> str:
        now = time.time()
        diff = max(0, now - timestamp)
        if diff < 60:
            return "Just now"
        elif diff < 3600:
            minutes = int(diff / 60)
            return f"{minutes} min{'s' if minutes > 1 else ''} ago"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff < 86400 * 7:
            days = int(diff / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%b %d, %Y")

    def _inspect_project_file(self, filepath: str) -> dict:
        """Inspects a single .wip project file safely."""
        norm_path = os.path.normpath(filepath)
        filename = os.path.basename(norm_path)
        base_name = os.path.splitext(filename)[0]

        try:
            stat = os.stat(norm_path)
            size_bytes = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            size_bytes = 0
            mtime = 0.0

        project_title = base_name
        scene_count = 1

        # Quick peek inside zip without extracting entire archive
        try:
            if zipfile.is_zipfile(norm_path):
                with zipfile.ZipFile(norm_path, "r") as zf:
                    if "project.json" in zf.namelist():
                        with zf.open("project.json") as pf:
                            p_data = json.loads(pf.read().decode("utf-8"))
                            p_title = p_data.get("name") or p_data.get("title")
                            if p_title:
                                project_title = p_title
                            artboards = p_data.get("artboards", [])
                            if artboards:
                                scene_count = len(artboards)
        except Exception:
            pass

        thumb_url = self._thumb_cache.get_thumbnail_url(norm_path, project_title)

        return {
            "title": project_title,
            "path": norm_path,
            "filename": filename,
            "mtime": mtime,
            "last_modified": self._format_timestamp(mtime),
            "size_bytes": size_bytes,
            "formatted_size": self._format_size(size_bytes),
            "thumbnail": thumb_url,
            "scene_count": scene_count,
        }

    def scan_all_projects(self, search_query: str = "", sort_by: str = HubSettings.SORT_MODIFIED_DESC) -> list[dict]:
        """Gathers all discoverable projects from recents and project directories."""
        discovered_paths = set()
        projects = []

        # 1. From recent files list
        recent_files = self._settings.get("recent_files", [])
        for p in recent_files:
            norm = os.path.normpath(p)
            if norm not in discovered_paths and os.path.isfile(norm) and norm.lower().endswith(".wip"):
                discovered_paths.add(norm)
                projects.append(self._inspect_project_file(norm))

        # 2. From default Projects directory
        proj_dir = self._get_default_projects_dir()
        if os.path.isdir(proj_dir):
            try:
                for entry in os.listdir(proj_dir):
                    if entry.lower().endswith(".wip"):
                        full_p = os.path.normpath(os.path.join(proj_dir, entry))
                        if full_p not in discovered_paths and os.path.isfile(full_p):
                            discovered_paths.add(full_p)
                            projects.append(self._inspect_project_file(full_p))
            except OSError:
                pass

        # 3. Apply search filter
        q = search_query.strip().lower()
        if q:
            projects = [
                p for p in projects
                if q in p["title"].lower() or q in p["filename"].lower()
            ]

        # 4. Apply sorting
        if sort_by == HubSettings.SORT_NAME_ASC:
            projects.sort(key=lambda x: x["title"].lower())
        elif sort_by == HubSettings.SORT_SIZE_DESC:
            projects.sort(key=lambda x: x["size_bytes"], reverse=True)
        else:  # SORT_MODIFIED_DESC default
            projects.sort(key=lambda x: x["mtime"], reverse=True)

        return projects

    def remove_recent_entry(self, filepath: str) -> None:
        """Removes a path from the recents list in SettingsManager."""
        norm_target = os.path.normpath(filepath)
        recent_files = self._settings.get("recent_files", [])
        updated = [p for p in recent_files if os.path.normpath(p) != norm_target]
        self._settings.set("recent_files", updated)

    def delete_project_file(self, filepath: str) -> bool:
        """Permanently deletes a project file and removes its recent reference."""
        self.remove_recent_entry(filepath)
        norm = os.path.normpath(filepath)
        if os.path.exists(norm):
            try:
                os.remove(norm)
                return True
            except OSError:
                return False
        return True
