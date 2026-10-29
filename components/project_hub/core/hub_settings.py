# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Preference manager for the Project Hub.
Features: Configures view modes (grid/list), sorting criteria, and startup behavior.
"""
from core.settings_manager import SettingsManager

class HubSettings:
    """Provides isolated access to Project Hub preferences backed by SettingsManager."""
    
    VIEW_GRID = "grid"
    VIEW_LIST = "list"
    
    SORT_MODIFIED_DESC = "modified_desc"
    SORT_NAME_ASC = "name_asc"
    SORT_SIZE_DESC = "size_desc"

    def __init__(self):
        self._settings = SettingsManager()

    def get_view_mode(self) -> str:
        return self._settings.get("hub_view_mode", self.VIEW_GRID)

    def set_view_mode(self, mode: str) -> None:
        if mode in (self.VIEW_GRID, self.VIEW_LIST):
            self._settings.set("hub_view_mode", mode)

    def get_sort_mode(self) -> str:
        return self._settings.get("hub_sort_by", self.SORT_MODIFIED_DESC)

    def set_sort_mode(self, sort_by: str) -> None:
        if sort_by in (self.SORT_MODIFIED_DESC, self.SORT_NAME_ASC, self.SORT_SIZE_DESC):
            self._settings.set("hub_sort_by", sort_by)

    def get_show_on_startup(self) -> bool:
        return bool(self._settings.get("show_hub_on_startup", True))

    def set_show_on_startup(self, show: bool) -> None:
        self._settings.set("show_hub_on_startup", bool(show))
