import os
import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                               QGridLayout, QToolButton, QLineEdit, QComboBox)
from PySide6.QtCore import Qt, QSize, Signal, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from utils.theme import THEME_COLORS

class TemplateLibraryWidget(QWidget):
    """
    Isolated UI component for the Educational Templates Library.
    Designed to not interfere with any existing shapes or components.
    """
    svg_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "library", "templates"))
        os.makedirs(self.templates_dir, exist_ok=True)
        
        self.all_assets = []
        self.asset_buttons = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(10)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("EDUCATIONAL TEMPLATES")
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; letter-spacing: 1px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        header.addLayout(title_layout)
        
        desc = QLabel("Drag & Drop to canvas")
        desc.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px;")
        header.addWidget(desc)
        layout.addLayout(header)
        
        # Filters and Search
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(8)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All Templates", 
            "Network Hardware",
            "Mobile & Wireless",
            "Cloud & IoT",
            "Logic Gates & Electronics",
            "Flowcharts & Processes",
            "Science & Math",
            "Mind Maps"
        ])
        self.category_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 6px;
                padding: 6px;
            }}
            QComboBox:focus {{ border: 1px solid {THEME_COLORS['primary_green']}; }}
        """)
        self.category_filter.currentTextChanged.connect(self.filter_assets)
        filter_layout.addWidget(self.category_filter)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search templates...")
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QLineEdit:focus {{ border: 1px solid {THEME_COLORS['primary_green']}; }}
        """)
        self.search_box.textChanged.connect(self.filter_assets)
        filter_layout.addWidget(self.search_box)
        layout.addLayout(filter_layout)
        
        # Grid Area
        self.grid_area = QScrollArea()
        self.grid_area.setWidgetResizable(True)
        self.grid_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.4);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.grid_content = QWidget()
        self.grid_content.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_content)
        self.grid_layout.setContentsMargins(0, 4, 0, 8)
        self.grid_layout.setSpacing(8)
        
        self._load_assets()
        
        self.grid_area.setWidget(self.grid_content)
        layout.addWidget(self.grid_area, stretch=1)
        
    def _load_assets(self):
        self.all_assets = []
        if os.path.exists(self.templates_dir):
            for root, _, files in os.walk(self.templates_dir):
                for filename in files:
                    if filename.lower().endswith('.svg'):
                        filepath = os.path.join(root, filename)
                        name = os.path.splitext(filename)[0]
                        # Extract category from folder name if it's inside a subfolder
                        folder_name = os.path.basename(root)
                        if folder_name != "templates":
                            category = folder_name.replace("_", " ")
                        else:
                            category = self._guess_category(name)
                            
                        self.all_assets.append({
                            'filepath': filepath,
                            'name': name,
                            'category': category
                        })
                    
        if not self.all_assets:
            empty_lbl = QLabel("No templates found.")
            empty_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_lbl, 0, 0)
            return

        for idx, asset in enumerate(self.all_assets):
            row, col = divmod(idx, 2)
            
            try:
                with open(asset['filepath'], 'r', encoding='utf-8') as f:
                    svg_str = f.read()
                svg_str = svg_str.replace('#111111', '#E0E0E0').replace('#1E1E1E', '#E0E0E0')
                
                renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
                pixmap = QPixmap(200, 200)
                pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                renderer.render(painter)
                painter.end()
                
                icon = QIcon(pixmap)
            except Exception:
                icon = QIcon(asset['filepath'])
            
            btn = QToolButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(60, 60))
            btn.setFixedSize(102, 102)
            btn.setToolTip(asset['name'].replace('_', ' ').title())
            
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: {THEME_COLORS['surface']};
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                }}
                QToolButton:hover {{
                    background: #2A3430;
                    border: 1px solid {THEME_COLORS['primary_green']};
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("filepath", asset['filepath'])
            btn.clicked.connect(self._on_asset_btn_clicked)
            
            self.grid_layout.addWidget(btn, row, col)
            self.asset_buttons.append((btn, asset))

    def _on_asset_btn_clicked(self):
        sender = self.sender()
        if sender:
            path = sender.property("filepath")
            if path:
                self.svg_selected.emit(path)

    def _guess_category(self, name: str) -> str:
        name = name.lower()
        if 'arduino' in name or 'microcontroller' in name:
            return "Embedded Systems"
        if 'mind_map' in name:
            return "Mind Maps"
        if 'laptop' in name or 'tech' in name:
            return "Technical & Programming"
        if 'vs' in name or 'comparison' in name:
            return "Comparisons"
        if 'process' in name or 'timeline' in name:
            return "Processes"
        return "All Templates"

    def filter_assets(self, _=None):
        search_query = self.search_box.text().lower().strip()
        cat_query = self.category_filter.currentText()
        
        # Clear layout safely without destroying buttons
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                if isinstance(w, QLabel):
                    w.deleteLater()
                else:
                    w.setParent(None)
        
        visible_assets = []
        for btn, asset in self.asset_buttons:
            # Smart search includes category and name
            text_to_search = f"{asset['name']} {asset['category']}".lower().replace('_', ' ')
            name_match = search_query in text_to_search
            cat_match = cat_query == "All Templates" or asset['category'] == cat_query
            
            if name_match and cat_match:
                visible_assets.append((btn, asset))
                btn.show()
            else:
                btn.hide()
                
        if not visible_assets:
            return
            
        current_row = 0
        
        if cat_query == "All Templates":
            # Group by category for section headers
            categories = {}
            for btn, asset in visible_assets:
                cat = asset['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(btn)
                
            for cat, btns in categories.items():
                lbl = QLabel(cat)
                lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-weight: bold; font-size: 11px; margin-top: 10px; margin-bottom: 2px;")
                self.grid_layout.addWidget(lbl, current_row, 0, 1, 2)
                current_row += 1
                
                for i, btn in enumerate(btns):
                    row_offset, col = divmod(i, 2)
                    self.grid_layout.addWidget(btn, current_row + row_offset, col)
                
                current_row += math.ceil(len(btns)/2)
        else:
            # Just add buttons normally
            for i, (btn, _) in enumerate(visible_assets):
                row_offset, col = divmod(i, 2)
                self.grid_layout.addWidget(btn, current_row + row_offset, col)
