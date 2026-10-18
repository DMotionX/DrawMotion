"""
Projects Dialog — Aggregator for the project management UI.
Now modularized using components from the `widgets` package.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS

from .widgets.project_header import ProjectHeader
from .widgets.projects_list import ProjectsListWidget


class ProjectsDialog(QDialog):
    """
    Main dialog window for managing projects.
    Integrates the Header (Open File) and the List (Search + Cards).
    """
    def __init__(self, project_manager, workspace, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.workspace = workspace
        
        self.setWindowTitle("My Projects")
        self.setFixedSize(540, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME_COLORS['bg_main']};
                color: {THEME_COLORS['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Widget (Title & Open File Button)
        self.header = ProjectHeader(self)
        self.header.open_file_requested.connect(self._on_external_file_loaded)
        self.header.new_project_requested.connect(self._on_new_project)
        layout.addWidget(self.header)

        # List Widget (Search & Project Cards)
        self.list_widget = ProjectsListWidget(self.project_manager, self)
        self.list_widget.project_loaded.connect(self._on_internal_project_loaded)
        layout.addWidget(self.list_widget, 1) # Takes remaining vertical space
        
        # Initial load
        self.list_widget.load_projects()


    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_internal_project_loaded(self, proj_data: dict):
        """ Triggered when 'Load' is clicked on a ProjectCard. """
        self._load_with_confirmation(proj_data['path'], proj_data['name'])

    def _on_external_file_loaded(self, file_path: str):
        """ Triggered when 'Open File...' selects an external .wip file. """
        import os
        name = os.path.basename(file_path).replace('.wip', '')
        self._load_with_confirmation(file_path, name)

    def _on_new_project(self):
        """ Clears everything and starts a fresh project. """
        confirm = QMessageBox.question(
            self, "New Project", 
            "Starting a new project will clear your current workspace.\nUnsaved changes will be lost.\n\nContinue?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.workspace.initialize_new_project()
            self.project_manager.cleanup_recovery() # Ensure no false crashes
            self.accept()
            
    def _load_with_confirmation(self, path: str, name: str):
        """ Replaces current workspace if user confirms. """
        confirm = QMessageBox.question(
            self, "Load Project", 
            "Loading a project will replace your current workspace.\nUnsaved changes will be lost.\n\nContinue?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if self.project_manager.load_project_file(path):
                self.accept()
                QMessageBox.information(self, "Success", f"Project '{name}' loaded successfully.")
