from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt, QObject

class MenuSignalBridge(QObject):
    """
    Dedicated QObject bridge for application menu actions.
    Isolates Qt signals from native QMenuBar widget class to prevent
    Shiboken MetaObject collision and memory access violations during compilation.
    Zero emojis, 100% backward-compatible.
    """
    # --- Signals for File Menu ---
    projects_hub_requested = Signal()
    new_project_requested = Signal()
    open_project_requested = Signal()
    save_project_requested = Signal()
    save_as_requested = Signal()
    import_requested = Signal()
    export_requested = Signal()
    exit_requested = Signal()

    # --- Signals for Edit Menu ---
    undo_requested = Signal()
    redo_requested = Signal()
    cut_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()
    duplicate_requested = Signal()
    delete_requested = Signal()

    # --- Signals for View Menu ---
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    fit_canvas_requested = Signal()
    full_screen_requested = Signal()
    toggle_assets_requested = Signal()
    toggle_properties_requested = Signal()
    toggle_timeline_requested = Signal()
    reset_workspace_requested = Signal()

    # --- Signals for Project Menu ---
    project_settings_requested = Signal()
    project_info_requested = Signal()

    # --- Signals for Audio Menu ---
    add_audio_requested = Signal()
    audio_settings_requested = Signal()

    # --- Signals for Help Menu ---
    user_guide_requested = Signal()
    whats_new_requested = Signal()
    shortcuts_requested = Signal()
    report_problem_requested = Signal()
    legal_policies_requested = Signal()
    about_requested = Signal()

    # --- Signals for Future/Placeholder Actions ---
    coming_soon_requested = Signal(str)


class WhiteInkMenuBar(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        if hasattr(parent, 'menuBar'):
            self.menu_bar = parent.menuBar()
        else:
            self.menu_bar = QMenuBar(parent)
            
        # Dedicated signal bridge
        self.bridge = MenuSignalBridge(self)

        # Expose all signals directly on WhiteInkMenuBar for 100% backward compatibility
        self.projects_hub_requested = self.bridge.projects_hub_requested
        self.new_project_requested = self.bridge.new_project_requested
        self.open_project_requested = self.bridge.open_project_requested
        self.save_project_requested = self.bridge.save_project_requested
        self.save_as_requested = self.bridge.save_as_requested
        self.import_requested = self.bridge.import_requested
        self.export_requested = self.bridge.export_requested
        self.exit_requested = self.bridge.exit_requested

        self.undo_requested = self.bridge.undo_requested
        self.redo_requested = self.bridge.redo_requested
        self.cut_requested = self.bridge.cut_requested
        self.copy_requested = self.bridge.copy_requested
        self.paste_requested = self.bridge.paste_requested
        self.duplicate_requested = self.bridge.duplicate_requested
        self.delete_requested = self.bridge.delete_requested

        self.zoom_in_requested = self.bridge.zoom_in_requested
        self.zoom_out_requested = self.bridge.zoom_out_requested
        self.fit_canvas_requested = self.bridge.fit_canvas_requested
        self.full_screen_requested = self.bridge.full_screen_requested
        self.toggle_assets_requested = self.bridge.toggle_assets_requested
        self.toggle_properties_requested = self.bridge.toggle_properties_requested
        self.toggle_timeline_requested = self.bridge.toggle_timeline_requested
        self.reset_workspace_requested = self.bridge.reset_workspace_requested

        self.project_settings_requested = self.bridge.project_settings_requested
        self.project_info_requested = self.bridge.project_info_requested

        self.add_audio_requested = self.bridge.add_audio_requested
        self.audio_settings_requested = self.bridge.audio_settings_requested

        self.user_guide_requested = self.bridge.user_guide_requested
        self.whats_new_requested = self.bridge.whats_new_requested
        self.shortcuts_requested = self.bridge.shortcuts_requested
        self.report_problem_requested = self.bridge.report_problem_requested
        self.legal_policies_requested = self.bridge.legal_policies_requested
        self.about_requested = self.bridge.about_requested
        self.coming_soon_requested = self.bridge.coming_soon_requested

        # Apply styling to match DrawMotion dark theme with premium spacing
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #1A211D;
                color: #FFFFFF;
                border-bottom: 1px solid #2A322E;
                font-size: 13px;
                padding: 4px 6px;
            }
            QMenuBar::item {
                spacing: 6px;
                padding: 6px 14px;
                background: transparent;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #2E8B57;
            }
            QMenuBar::item:pressed {
                background-color: #1E663B;
            }
            QMenu {
                background-color: #222A27;
                color: #FFFFFF;
                border: 1px solid #2A322E;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 30px 8px 24px;
            }
            QMenu::item:selected {
                background-color: #2E8B57;
            }
            QMenu::separator {
                height: 1px;
                background: #2A322E;
                margin: 4px 0px;
            }
        """)

        self._build_file_menu()
        self._build_edit_menu()
        self._build_view_menu()
        self._build_project_menu()
        self._build_audio_menu()
        self._build_help_menu()

    def addMenu(self, title: str) -> QMenu:
        return self.menu_bar.addMenu(title)

    def _add_action(self, menu: QMenu, name: str, shortcut: str = None, signal = None):
        action = QAction(name, self.main_window or self)
        if shortcut:
            action.setShortcut(shortcut)
        
        if signal:
            action.triggered.connect(signal.emit)
        else:
            action.setData(name)
            action.triggered.connect(self._on_placeholder_action_triggered)
            
        menu.addAction(action)
        return action

    def _on_placeholder_action_triggered(self):
        sender = self.sender()
        name = sender.data() if sender and hasattr(sender, "data") else "Feature"
        self.coming_soon_requested.emit(str(name))

    def _build_file_menu(self):
        file_menu = self.addMenu("&File")

        self._add_action(file_menu, "Projects Hub...", "Ctrl+H", self.projects_hub_requested)
        file_menu.addSeparator()
        self._add_action(file_menu, "New Project", "Ctrl+N", self.new_project_requested)
        self._add_action(file_menu, "Open Project", "Ctrl+O", self.open_project_requested)
        
        self.recent_menu = file_menu.addMenu("Open Recent")
        
        # Add a placeholder
        recent_action = QAction("No recent files", self.main_window or self)
        recent_action.setEnabled(False)
        self.recent_menu.addAction(recent_action)

        file_menu.addSeparator()

        self._add_action(file_menu, "Save", "Ctrl+S", self.save_project_requested)
        self._add_action(file_menu, "Save As", "Ctrl+Shift+S", self.save_as_requested)
        
        file_menu.addSeparator()
        
        self._add_action(file_menu, "Import", "Ctrl+I", self.import_requested)
        
        export_menu = file_menu.addMenu("Export")
        export_video = QAction("Export to Video", self.main_window or self)
        export_video.triggered.connect(self.export_requested.emit)
        export_menu.addAction(export_video)

        file_menu.addSeparator()

        self._add_action(file_menu, "Exit", "Alt+F4", self.exit_requested)

    def _build_edit_menu(self):
        edit_menu = self.addMenu("&Edit")

        self._add_action(edit_menu, "Undo", "Ctrl+Z", self.undo_requested)
        self._add_action(edit_menu, "Redo", "Ctrl+Y", self.redo_requested)
        
        edit_menu.addSeparator()
        
        self._add_action(edit_menu, "Cut", "Ctrl+X", self.cut_requested)
        self._add_action(edit_menu, "Copy", "Ctrl+C", self.copy_requested)
        self._add_action(edit_menu, "Paste", "Ctrl+V", self.paste_requested)
        self._add_action(edit_menu, "Duplicate", "Ctrl+D", self.duplicate_requested)
        
        edit_menu.addSeparator()
        
        self._add_action(edit_menu, "Delete", "Del", self.delete_requested)

    def _build_view_menu(self):
        view_menu = self.addMenu("&View")

        self._add_action(view_menu, "Zoom In", "Ctrl++", self.zoom_in_requested)
        self._add_action(view_menu, "Zoom Out", "Ctrl+-", self.zoom_out_requested)
        self._add_action(view_menu, "Fit Canvas", "Ctrl+0", self.fit_canvas_requested)
        self._add_action(view_menu, "Full Screen", "F11", self.full_screen_requested)
        
        view_menu.addSeparator()
        
        self._add_action(view_menu, "Show Assets Panel", "", self.toggle_assets_requested)
        self._add_action(view_menu, "Show Properties Panel", "", self.toggle_properties_requested)
        self._add_action(view_menu, "Show Timeline", "", self.toggle_timeline_requested)
        
        view_menu.addSeparator()
        
        self._add_action(view_menu, "Reset Workspace", "", self.reset_workspace_requested)

    def _build_project_menu(self):
        proj_menu = self.addMenu("&Project")

        self._add_action(proj_menu, "Project Settings", "", self.project_settings_requested)
        
        proj_menu.addSeparator()
        
        self._add_action(proj_menu, "Project Information", "", self.project_info_requested)

    def _build_audio_menu(self):
        audio_menu = self.addMenu("&Audio")

        self._add_action(audio_menu, "Add Voice", "", self.add_audio_requested)
        
        audio_menu.addSeparator()
        
        self._add_action(audio_menu, "Audio Settings", "", self.audio_settings_requested)

    def _build_help_menu(self):
        help_menu = self.addMenu("&Help")

        self._add_action(help_menu, "User Guide", "F1", self.user_guide_requested)
        self._add_action(help_menu, "Keyboard Shortcuts", "", self.shortcuts_requested)
        self._add_action(help_menu, "What's New", "", self.whats_new_requested)
        self._add_action(help_menu, "Report a Problem", "", self.report_problem_requested)
        self._add_action(help_menu, "Legal Policies & Privacy", "", self.legal_policies_requested)
        
        help_menu.addSeparator()
        
        self._add_action(help_menu, "About DrawMotion", "", self.about_requested)
