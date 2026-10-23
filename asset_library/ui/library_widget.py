from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QToolButton, QLineEdit
from PySide6.QtCore import Qt, QSize, Signal, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from asset_library.core.asset_loader import AssetLoader
from utils.theme import THEME_COLORS
import os

class SVGLibraryWidget(QWidget):
    """
    Isolated UI component for the SVG Asset Library sidebar.
    """
    svg_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.asset_loader = AssetLoader()
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
        title = QLabel("SVG SHAPES")
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; letter-spacing: 1px;")
        title_layout.addWidget(title)
        
        beta_badge_inner = QLabel("BETA")
        beta_badge_inner.setStyleSheet(f"background-color: {THEME_COLORS.get('orange_action', '#FF9800')}; color: white; font-size: 9px; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        title_layout.addWidget(beta_badge_inner)
        title_layout.addStretch()
        header.addLayout(title_layout)
        
        desc = QLabel("Drag & Drop or Click to add")
        desc.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px;")
        header.addWidget(desc)
        layout.addLayout(header)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search shapes...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_assets)
        header_layout.addWidget(self.search_input)
        
        # Import button
        self.import_btn = QToolButton()
        self.import_btn.setToolTip("Import SVG")
        self.import_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            QToolButton:hover {{
                background-color: {THEME_COLORS['green_hover']};
            }}
        """)
        from utils.icons import SVG_ICONS
        renderer = QSvgRenderer(QByteArray(SVG_ICONS['import'].encode('utf-8')))
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.import_btn.setIcon(QIcon(pixmap))
        self.import_btn.setIconSize(QSize(20, 20))
        self.import_btn.clicked.connect(self.import_svg)
        header_layout.addWidget(self.import_btn)
        
        layout.addLayout(header_layout)
        
        # Grid Area
        self.grid_area = QScrollArea()
        self.grid_area.setWidgetResizable(True)
        self.grid_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Custom sleek transparent scrollbar styling
        self.grid_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 0px;
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
        self.grid_layout.setSpacing(8)
        
        self._load_assets()
        
        self.grid_area.setWidget(self.grid_content)
        layout.addWidget(self.grid_area, stretch=1)
        
    def _load_assets(self):
        self.all_assets = self.asset_loader.get_all_assets()
        
        if not self.all_assets:
            empty_lbl = QLabel("No SVG assets found.")
            empty_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']};")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_lbl, 0, 0)
            return

        for idx, asset in enumerate(self.all_assets):
            row, col = divmod(idx, 2)
            
            # Read SVG and replace dark colors with white for the UI thumbnail
            try:
                with open(asset['filepath'], 'r', encoding='utf-8') as f:
                    svg_str = f.read()
                import re
                svg_str = re.sub(r'(?i)(#000000|#000\b|black|#111111|#1E1E1E)', '#E0E0E0', svg_str)
                
                renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
                pixmap = QPixmap(200, 200)
                pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(pixmap)
                # Enable antialiasing for better icon quality
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                renderer.render(painter)
                painter.end()
                
                icon = QIcon(pixmap)
            except Exception:
                icon = QIcon(asset['filepath'])
            
            btn = QToolButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(44, 44))
            btn.setFixedSize(102, 102)
            btn.setText(asset['name'].capitalize())
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setToolTip(f"{asset['name'].capitalize()}\n{asset['filepath']}")
            
            # Premium styling
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: {THEME_COLORS['surface']};
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    color: {THEME_COLORS['text_secondary']};
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 2px;
                }}
                QToolButton:hover {{
                    background: #2A3430;
                    border: 1px solid {THEME_COLORS['primary_green']};
                    color: #FFFFFF;
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("filepath", asset['filepath'])
            btn.clicked.connect(self._on_asset_btn_clicked)
            
            self.grid_layout.addWidget(btn, row, col)
            self.asset_buttons.append((btn, asset['name'].lower()))

    def _on_asset_btn_clicked(self):
        sender = self.sender()
        if sender:
            path = sender.property("filepath")
            if path:
                self.svg_selected.emit(path)

    def filter_assets(self, text):
        query = text.lower().strip()
        visible_count = 0
        
        for btn, name in self.asset_buttons:
            if query in name:
                btn.show()
                # Reposition the visible ones
                row, col = divmod(visible_count, 2)
                self.grid_layout.addWidget(btn, row, col)
                visible_count += 1
            else:
                btn.hide()

    def import_svg(self):
        from PySide6.QtWidgets import QFileDialog
        import shutil
        import os
        
        filepath, _ = QFileDialog.getOpenFileName(self, "Import SVG File", "", "SVG Files (*.svg)")
        if not filepath:
            return
            
        # Copy to AppData
        filename = os.path.basename(filepath)
        from utils.paths import get_app_data_dir
        appdata_dir = os.path.join(get_app_data_dir(), 'assets', 'svg')
        os.makedirs(appdata_dir, exist_ok=True)
        
        target_path = os.path.join(appdata_dir, filename)
        shutil.copy2(filepath, target_path)
        
        # Reload assets
        self.all_assets = self.loader.load_assets()
        self._load_assets()
