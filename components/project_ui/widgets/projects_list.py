"""
Projects List Widget — displays the list of projects with a search filter.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from utils.theme import THEME_COLORS
from .project_card import ProjectCard
from .empty_state import EmptyStateWidget

class ProjectsListWidget(QWidget):
    project_loaded = Signal(dict)

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.all_projects = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['divider']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_projects)
        layout.addWidget(self.search_input)

        # Scroll Area for the list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 8px; background: transparent; }
            QScrollBar::handle:vertical { background: #384A40; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(12)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)

    def load_projects(self):
        self.all_projects = self.project_manager.list_projects()
        # Sort by created_at descending (newest first)
        self.all_projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        self.filter_projects(self.search_input.text())

    def filter_projects(self, query: str):
        # Clear current list
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        q = query.lower().strip()
        filtered = [p for p in self.all_projects if q in p['name'].lower()]

        if not filtered:
            self.list_layout.addWidget(EmptyStateWidget())
        else:
            for proj in filtered:
                card = ProjectCard(proj, self.project_manager)
                card.project_loaded.connect(self.project_loaded.emit)
                card.project_deleted.connect(self.load_projects) # Reload on delete
                self.list_layout.addWidget(card)
