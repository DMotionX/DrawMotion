"""
Purpose: Left sidebar panel for asset management.
Features: Custom vertical tabs for Assets, Scenes, Layers, Music, Uploads.
"""
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                               QLineEdit, QListWidget, QListWidgetItem, QToolButton, 
                               QStackedWidget, QPushButton, QSlider, QScrollArea, QGridLayout, QFileDialog)
from PySide6.QtCore import Qt, QSize, Signal, QUrl, QEvent, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from utils.paths import get_app_data_dir
import os
import shutil
from services.db_service import DBService

DISABLE_ANIM = os.environ.get("DM_NO_ANIM", "0") == "1"
DISABLE_TAB0 = os.environ.get("DM_NO_TAB0", "0") == "1"

class AnimatedReloadButton(QToolButton):
    """
    Interactive, high-aesthetic Reload button with smooth 360-degree rotation animation.
    Designed to fit seamlessly in panel headers without crowding button rows.
    """
    def __init__(self, parent=None, icon_name="reload", size=24, icon_size=14):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Reload & Refresh Assets")
        self._angle = 0.0
        self._is_hovered = False
        self._icon_size = icon_size
        
        self._icon_normal = get_icon(icon_name, THEME_COLORS['text_secondary'])
        self._icon_hover = get_icon(icon_name, THEME_COLORS['primary_green'])
        
        if not DISABLE_ANIM:
            self._anim = QPropertyAnimation(self, b"rotation")
            self._anim.setDuration(450)
            self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self._anim.finished.connect(self._reset_rotation)
        else:
            self._anim = None

    def get_rotation(self):
        return self._angle

    def set_rotation(self, angle):
        self._angle = angle
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    def trigger_spin(self):
        if not self._anim:
            return
        if self._anim.state() == QPropertyAnimation.State.Running:
            return
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(360.0)
        self._anim.start()

    def _reset_rotation(self):
        self._angle = 0.0
        self.update()

    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Micro-interactive background and subtle emerald border
        if self.isDown():
            painter.setBrush(QColor("#1A2821"))
            painter.setPen(QColor(THEME_COLORS.get('green_hover', '#38A169')))
        elif self._is_hovered:
            painter.setBrush(QColor("#24352D"))
            painter.setPen(QColor(THEME_COLORS['primary_green']))
        else:
            painter.setBrush(QColor(THEME_COLORS['surface']))
            painter.setPen(QColor(255, 255, 255, 20))
        
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        
        # Draw vector icon rotated around center
        icon = self._icon_hover if self._is_hovered else self._icon_normal
        pix = icon.pixmap(self._icon_size, self._icon_size)
        
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        painter.drawPixmap(-self._icon_size / 2.0, -self._icon_size / 2.0, pix)
        painter.restore()
        painter.end()

class HoverIconButton(QPushButton):
    def __init__(self, text, icon_normal, icon_hover, parent=None):
        super().__init__(text, parent)
        self.icon_normal = icon_normal
        self.icon_hover = icon_hover
        self.setIcon(self.icon_normal)

    def enterEvent(self, event):
        self.setIcon(self.icon_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.icon_normal)
        super().leaveEvent(event)

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout

class FolderNameDialog(QDialog):
    def __init__(self, parent=None, title="Folder Name", text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(f"background-color: {THEME_COLORS['bg_main']}; color: {THEME_COLORS['text_primary']};")
        self.setFixedSize(300, 130)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Enter folder name:")
        layout.addWidget(label)
        
        self.input_field = QLineEdit(text)
        self.input_field.setStyleSheet(f"background-color: {THEME_COLORS['surface']}; color: {THEME_COLORS['text_primary']}; border: 1px solid {THEME_COLORS['border']}; border-radius: 4px; padding: 6px;")
        
        # FIX RTL BUG: AlignRight prevents the cursor from jumping wildly when mixing Arabic/Numbers
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.input_field)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(f"background-color: {THEME_COLORS['primary_green']}; color: white; padding: 6px 16px; border-radius: 4px; font-weight: bold;")
        ok_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"background-color: {THEME_COLORS['surface']}; color: white; padding: 6px 16px; border-radius: 4px; font-weight: bold;")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def get_text(self):
        return self.input_field.text().strip()

class LeftPanel(QFrame):
    add_scene_requested = Signal()
    scene_selected = Signal(int)
    scene_deleted = Signal(int)
    asset_selected = Signal(str)
    image_uploaded = Signal(str)
    svg_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("LeftPanel")
        self.setFixedWidth(320)
        self.db_service = DBService()
        self._workspace = None   # Injected by main.py after construction
        self._init_ui()

    def set_workspace(self, workspace):
        """Called by main.py to inject workspace reference so we can read the current artboard."""
        self._workspace = workspace

    def _get_current_artboard(self):
        """Return the currently focused artboard item from workspace."""
        if self._workspace and self._workspace.artboards:
            idx = self._workspace.current_scene_index
            if 0 <= idx < len(self._workspace.artboards):
                return self._workspace.artboards[idx]
        return None

    def eventFilter(self, obj, event):
        """Nuitka-safe event filter replacing lambda-based mousePressEvent overrides."""
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                folder_name = obj.property("folder_name")
                if folder_name is not None:
                    self._enter_folder(folder_name)
                    return True

                filepath = obj.property("filepath")
                if filepath is not None:
                    self.image_uploaded.emit(filepath)
                    return True

                audio_item = obj.property("audio_item")
                if audio_item is not None:
                    self._on_card_clicked(audio_item)
                    return True

                if hasattr(self, '_scene_cards'):
                    for idx, (h_item, sc_card) in enumerate(self._scene_cards):
                        if sc_card is obj:
                            self._select_scene_card(idx)
                            return True

        return super().eventFilter(obj, event)

    def _on_sidebar_btn_clicked(self):
        sender = self.sender()
        if sender:
            idx = sender.property("tab_index")
            if idx is not None:
                self._switch_tab(idx)

    def _on_folder_card_custom_context_menu(self, pos):
        card = self.sender()
        if card:
            f_name = card.property("folder_name")
            if f_name:
                self._show_folder_context_menu(card, pos, f_name)

    def _on_asset_card_custom_context_menu(self, pos):
        card = self.sender()
        if card:
            filepath = card.property("filepath")
            if filepath:
                self._show_asset_context_menu(card, pos, filepath)

    def _on_delete_scene_btn_clicked(self):
        btn = self.sender()
        if btn:
            item = btn.property("hidden_item")
            if item:
                self._on_scene_delete_clicked(item)

    def _on_delete_audio_btn_clicked(self):
        btn = self.sender()
        if btn:
            item = btn.property("audio_item")
            if item is not None:
                self._delete_audio_node(item)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Leftmost Sidebar (Custom Tabs)
        sidebar_container = QFrame()
        sidebar_container.setFixedWidth(70)
        sidebar_container.setStyleSheet(f"background-color: {THEME_COLORS['bg_secondary']}; border-right: 1px solid {THEME_COLORS['border']}; border-radius: 8px 0 0 8px;")
        
        sidebar_container_layout = QVBoxLayout(sidebar_container)
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_container_layout.setSpacing(0)
        
        # Transparent Scroll Area to prevent squishing (Hidden Overflow-Y)
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Hidden scrollbar
        sidebar_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        sidebar = QWidget()
        sidebar.setStyleSheet("background: transparent;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(10)
        
        self.tabs_group = []
        
        def create_sidebar_btn(text, icon_name, index):
            btn = QToolButton()
            btn.setProperty("tab_index", index)
            btn.setText(text)
            btn.setIcon(get_icon(icon_name))
            btn.setIconSize(QSize(22, 22))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setFixedSize(70, 75) # Fixed size to completely prevent squishing
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QToolButton {{ 
                    color: {THEME_COLORS['text_secondary']}; 
                    border: none; 
                    font-size: 10px; 
                    padding-top: 10px;
                    padding-bottom: 5px;
                }}
                QToolButton:checked {{ 
                    color: {THEME_COLORS['primary_green']}; 
                    background-color: {THEME_COLORS['panel']}; 
                    border-left: 3px solid {THEME_COLORS['primary_green']}; 
                }}
                QToolButton:hover {{ 
                    color: {THEME_COLORS['text_primary']}; 
                }}
            """)
            btn.setProperty("tab_index", index)
            btn.clicked.connect(self._on_sidebar_btn_clicked)
            self.tabs_group.append(btn)
            return btn
            
        sidebar_layout.addWidget(create_sidebar_btn("Assets", "folder", 0))
        sidebar_layout.addWidget(create_sidebar_btn("Scenes", "image", 1))
        # sidebar_layout.addWidget(create_sidebar_btn("Layers", "layers", 2)) # Hidden
        sidebar_layout.addWidget(create_sidebar_btn("Music", "music", 3))
        sidebar_layout.addWidget(create_sidebar_btn("Shapes", "shape", 4))
        sidebar_layout.addWidget(create_sidebar_btn("Templates", "templates", 5))
        # sidebar_layout.addWidget(create_sidebar_btn("Mind Map", "shape", 6))
        sidebar_layout.addStretch()
        
        sidebar_scroll.setWidget(sidebar)
        sidebar_container_layout.addWidget(sidebar_scroll)
        
        layout.addWidget(sidebar_container)
        
        # Content Area (Lazy-Loaded Component Stack)
        self.content_stack = QStackedWidget()
        self._tab_cache = {}
        self._tab_factories = {
            0: self._create_assets_tab,
            1: self._create_scenes_tab,
            2: self._create_layers_tab,
            3: self._create_music_tab,
            4: self._create_shapes_tab,
            5: self._create_templates_tab,
        }
        
        # Populate with lightweight transparent placeholders (instant startup)
        for _ in range(6):
            placeholder = QWidget()
            placeholder.setStyleSheet("background: transparent;")
            self.content_stack.addWidget(placeholder)
            
        layout.addWidget(self.content_stack, stretch=1)
        self._switch_tab(0)

    def _ensure_tab_loaded(self, index: int):
        """Ensures the tab at index is constructed on-demand, with self-healing fallback."""
        if index in self._tab_cache:
            return self._tab_cache[index]

        if index in self._tab_factories:
            try:
                from core.diagnostics import StartupLifecycleTracker
                StartupLifecycleTracker.trace("LEFT_PANEL", f"Loading tab {index} on demand...")
            except Exception:
                pass

            if index == 0 and DISABLE_TAB0:
                try:
                    from core.diagnostics import StartupLifecycleTracker
                    StartupLifecycleTracker.trace("LEFT_PANEL_BYPASS", "Tab 0 creation bypassed by DM_NO_TAB0=1")
                except Exception:
                    pass
                placeholder = QWidget()
                placeholder.setStyleSheet("background: transparent;")
                self._tab_cache[index] = placeholder
                old_w = self.content_stack.widget(index)
                if old_w is not None and old_w is not placeholder:
                    self.content_stack.removeWidget(old_w)
                    old_w.deleteLater()
                self.content_stack.insertWidget(index, placeholder)
                return placeholder

            try:
                widget = self._tab_factories[index]()
                self._tab_cache[index] = widget
                try:
                    from core.diagnostics import StartupLifecycleTracker
                    StartupLifecycleTracker.trace("LEFT_PANEL", f"Tab {index} constructed successfully.")
                except Exception:
                    pass

                # Replace placeholder at this slot
                old_w = self.content_stack.widget(index)
                if old_w is not None and old_w is not widget:
                    self.content_stack.removeWidget(old_w)
                    old_w.deleteLater()
                self.content_stack.insertWidget(index, widget)
                return widget
            except Exception as e:
                try:
                    from core.diagnostics import StartupLifecycleTracker
                    StartupLifecycleTracker.trace("LEFT_PANEL_ERR", f"Tab {index} load failed: {e}")
                except Exception:
                    pass

                fallback = self._create_fallback_card(index, str(e))
                old_w = self.content_stack.widget(index)
                if old_w is not None:
                    self.content_stack.removeWidget(old_w)
                    old_w.deleteLater()
                self.content_stack.insertWidget(index, fallback)
                return fallback
        return None

    def _reload_tab(self, index: int):
        """Force reloads a tab on user request with clean teardown."""
        if index in self._tab_cache:
            old_widget = self._tab_cache.pop(index)
            try:
                self.content_stack.removeWidget(old_widget)
                old_widget.deleteLater()
            except Exception:
                pass

        placeholder = QWidget()
        placeholder.setStyleSheet("background: transparent;")
        self.content_stack.insertWidget(index, placeholder)
        self._ensure_tab_loaded(index)
        self.content_stack.setCurrentIndex(index)

    def _create_fallback_card(self, index: int, error_msg: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['surface']};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                margin: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 24, 16, 24)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("reload", THEME_COLORS['primary_green']).pixmap(QSize(32, 32)))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_lbl)

        title = QLabel("Component Suspended")
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; font-size: 13px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        desc = QLabel("This module encountered a delay and was paused silently to protect studio stability.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(desc)

        reload_btn = QPushButton(" Reload Component")
        reload_btn.setIcon(get_icon("reload", "white"))
        reload_btn.setIconSize(QSize(15, 15))
        reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 7px 14px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['green_hover']};
            }}
        """)
        reload_btn.clicked.connect(lambda: self._reload_tab(index))
        card_layout.addWidget(reload_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return card

    def _switch_tab(self, index):
        for btn in self.tabs_group:
            btn.setChecked(btn.property("tab_index") == index)
        self._ensure_tab_loaded(index)
        self.content_stack.setCurrentIndex(index)
        if index == 0 and not getattr(self, '_assets_loaded', False):
            self._assets_loaded = True
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self._refresh_assets_grid)

    def _create_header(self, title_text, reload_callback=None):
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch()
        if reload_callback:
            reload_btn = AnimatedReloadButton(self)
            def on_reload_clicked():
                reload_btn.trigger_spin()
                reload_callback()
            reload_btn.clicked.connect(on_reload_clicked)
            header.addWidget(reload_btn)
        return header

    def _render_svg_pixmap(self, name: str, color: str, size: int = 36) -> QPixmap:
        """Render high-resolution vector icon with antialiasing onto a transparent QPixmap."""
        from utils.icons import SVG_ICONS
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPainter, QColor
        from PySide6.QtCore import QByteArray
        if name not in SVG_ICONS:
            return QPixmap()
        svg_str = SVG_ICONS[name].replace('stroke="currentColor"', f'stroke="{color}"')
        renderer = QSvgRenderer(QByteArray(svg_str.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _create_assets_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(10)
        
        # Header with interactive rotating reload action on far right
        layout.addLayout(self._create_header("ASSETS", reload_callback=self._refresh_assets_grid))
        
        # Breadcrumb and New Folder Row (Uncrowded, full width)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(6)
        
        self.breadcrumb_btn = QPushButton("Assets")
        self.breadcrumb_btn.setStyleSheet(f"background: transparent; color: {THEME_COLORS['text_secondary']}; font-weight: bold; border: none; text-align: left;")
        self.breadcrumb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.breadcrumb_btn.clicked.connect(self._go_home_folder)
        
        back_btn = QToolButton()
        back_btn.setText("<")
        back_btn.setToolTip("Go Back")
        back_btn.clicked.connect(self._go_back_folder)
        back_btn.setStyleSheet(f"background: transparent; color: {THEME_COLORS['text_primary']}; font-weight: bold; font-size: 14px;")
        
        self.back_btn = back_btn
        self.back_btn.hide() # Hidden at root
        
        top_bar.addWidget(self.back_btn)
        top_bar.addWidget(self.breadcrumb_btn)
        top_bar.addStretch()
        
        new_folder_btn = QToolButton()
        new_folder_btn.setIcon(get_icon("folder", THEME_COLORS['primary_green']))
        new_folder_btn.setIconSize(QSize(14, 14))
        new_folder_btn.setText(" New Folder")
        new_folder_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        new_folder_btn.setToolTip("Create New Folder")
        new_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_folder_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {THEME_COLORS['surface']};
                color: #D2DAD5;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            QToolButton:hover {{
                background-color: #24352D;
                border-color: {THEME_COLORS['primary_green']};
                color: #FFFFFF;
            }}
        """)
        new_folder_btn.clicked.connect(self._create_new_folder)
        
        top_bar.addWidget(new_folder_btn)
        layout.addLayout(top_bar)
        
        # Upload Button
        upload_btn = QPushButton("Upload New File")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['orange_action']}; 
                color: white; 
                padding: 8px 12px; 
                font-weight: bold;
                font-size: 11.5px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #F57C00;
            }}
        """)
        upload_btn.clicked.connect(self._handle_upload)
        layout.addWidget(upload_btn)
        
        # Search Box
        self.asset_search_input = QLineEdit()
        self.asset_search_input.setPlaceholderText("Search assets...")
        self.asset_search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_COLORS['surface']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
        """)
        self.asset_search_input.textChanged.connect(self._on_asset_search_changed)
        layout.addWidget(self.asset_search_input)
        
        # Grid Area for thumbnails with sleek custom scrollbar
        grid_area = QScrollArea()
        grid_area.setWidgetResizable(True)
        grid_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid_area.setStyleSheet(f"""
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
        
        grid_content = QWidget()
        grid_content.setStyleSheet("background: transparent;")
        grid_content.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.assets_grid_layout = QGridLayout(grid_content)
        self.assets_grid_layout.setContentsMargins(0, 4, 0, 8)
        self.assets_grid_layout.setSpacing(8)
        self.assets_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Fixed column constraints ensuring items start from the left and never center in empty space
        self.assets_grid_layout.setColumnMinimumWidth(0, 102)
        self.assets_grid_layout.setColumnMinimumWidth(1, 102)
        self.assets_grid_layout.setColumnStretch(0, 0)
        self.assets_grid_layout.setColumnStretch(1, 0)
        self.assets_grid_layout.setColumnStretch(2, 1)
        
        self.current_asset_folder = ""
        self.asset_search_query = ""
        self._assets_loaded = False
        
        grid_area.setWidget(grid_content)
        layout.addWidget(grid_area, stretch=1)
        
        return tab

    def _on_asset_search_changed(self, text: str):
        self.asset_search_query = text.strip().lower()
        self._refresh_assets_grid()

    def _go_home_folder(self):
        self.current_asset_folder = ""
        self._refresh_assets_grid()

    def _go_back_folder(self):
        if getattr(self, 'current_asset_folder', ""):
            # Go up one level
            parts = self.current_asset_folder.replace('\\', '/').rstrip('/').split('/')
            if len(parts) > 1:
                self.current_asset_folder = '/'.join(parts[:-1])
            else:
                self.current_asset_folder = ""
            self._refresh_assets_grid()

    def _enter_folder(self, folder_name):
        if getattr(self, 'current_asset_folder', ""):
            self.current_asset_folder += f"/{folder_name}"
        else:
            self.current_asset_folder = folder_name
        self._refresh_assets_grid()

    def _create_new_folder(self):
        dialog = FolderNameDialog(self, "New Folder", "")
        if dialog.exec_():
            folder_name = dialog.get_text()
            if folder_name:
                from core.security_engine import SecurityEngine
                if not SecurityEngine.get_instance().is_safe_input(folder_name):
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Security Alert", "The folder name contains invalid or potentially harmful characters.")
                    return
                    
                user_library_path = os.path.join(get_app_data_dir(), "assets", "library")
                target_path = os.path.join(user_library_path, getattr(self, 'current_asset_folder', ""), folder_name)
                try:
                    os.makedirs(target_path, exist_ok=True)
                    self._refresh_assets_grid()
                except Exception as e:
                    print(f"Failed to create folder: {e}")
        
    def _create_shapes_tab(self):
        from asset_library.ui.library_widget import SVGLibraryWidget
        tab = SVGLibraryWidget()
        tab.svg_selected.connect(self.svg_selected.emit)
        return tab

    def _create_templates_tab(self):
        from asset_library.ui.template_library_widget import TemplateLibraryWidget
        tab = TemplateLibraryWidget()
        tab.svg_selected.connect(self.svg_selected.emit)
        return tab
        
    def _refresh_assets_grid(self):
        while self.assets_grid_layout.count():
            child = self.assets_grid_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
                
        user_library_path = os.path.join(get_app_data_dir(), "assets", "library")
        current_full_path = os.path.join(user_library_path, getattr(self, 'current_asset_folder', ""))
        os.makedirs(current_full_path, exist_ok=True)
        
        # Update breadcrumb
        if getattr(self, 'breadcrumb_btn', None):
            if not getattr(self, 'current_asset_folder', ""):
                self.breadcrumb_btn.setText("Assets")
                self.breadcrumb_btn.setStyleSheet(f"background: transparent; color: {THEME_COLORS['text_secondary']}; font-weight: bold; border: none; text-align: left;")
                self.back_btn.hide()
            else:
                display_path = self.current_asset_folder.replace('\\', '/').replace('/', ' > ')
                self.breadcrumb_btn.setText(f"Assets > {display_path}")
                self.breadcrumb_btn.setStyleSheet(f"background: transparent; color: {THEME_COLORS['text_primary']}; font-weight: bold; border: none; text-align: left;")
                self.back_btn.show()

        items = []
        
        # 1. Folders in current path
        try:
            for item_name in os.listdir(current_full_path):
                item_path = os.path.join(current_full_path, item_name)
                if os.path.isdir(item_path):
                    items.append({'type': 'folder', 'name': item_name})
        except Exception:
            pass

        # 2. Shipped assets (ONLY AT ROOT)
        if not getattr(self, 'current_asset_folder', ""):
            try:
                from utils.paths import resource_path
                shipped_library_path = resource_path(os.path.join("assets", "library"))
            except ImportError:
                shipped_library_path = os.path.join("assets", "library")
                
            if os.path.exists(shipped_library_path):
                for root, _, files in os.walk(shipped_library_path):
                    for filename in files:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                            items.append({'type': 'file', 'filepath': os.path.join(root, filename)})
        
        # 3. Files in current user path
        try:
            for item_name in os.listdir(current_full_path):
                item_path = os.path.join(current_full_path, item_name)
                if os.path.isfile(item_path) and item_name.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    items.append({'type': 'file', 'filepath': item_path})
        except Exception:
            pass

        # Filter by search query if present
        search_query = getattr(self, 'asset_search_query', "")
        if search_query:
            filtered_items = []
            for item in items:
                name_to_check = item['name'] if item['type'] == 'folder' else os.path.basename(item['filepath'])
                if search_query in name_to_check.lower():
                    filtered_items.append(item)
            items = filtered_items

        if not items:
            empty_lbl = QLabel("No assets found" if search_query else "Folder is empty")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px; padding: 24px;")
            self.assets_grid_layout.addWidget(empty_lbl, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
            return
            
        for idx, item_data in enumerate(items):
            row, col = divmod(idx, 2)
            
            if item_data['type'] == 'folder':
                folder_card = QFrame()
                folder_card.setFixedSize(102, 122)
                folder_card.setCursor(Qt.CursorShape.PointingHandCursor)
                folder_card.setObjectName("folder_card")
                folder_card.setStyleSheet(f"""
                    QFrame#folder_card {{
                        background-color: {THEME_COLORS['surface']};
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 8px;
                    }}
                    QFrame#folder_card:hover {{
                        background-color: #24352D;
                        border: 1px solid {THEME_COLORS['primary_green']};
                    }}
                """)
                
                folder_layout = QVBoxLayout(folder_card)
                folder_layout.setContentsMargins(6, 10, 6, 8)
                folder_layout.setSpacing(6)
                folder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Dedicated inner box for folder icon (guarantees icon is never clipped)
                icon_container = QFrame()
                icon_container.setFixedSize(88, 68)
                icon_container.setObjectName("folder_icon_box")
                icon_container.setStyleSheet("""
                    QFrame#folder_icon_box {
                        background-color: #1A201D;
                        border: 1px solid rgba(255, 255, 255, 0.04);
                        border-radius: 6px;
                    }
                """)
                icon_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                
                icon_inner_layout = QVBoxLayout(icon_container)
                icon_inner_layout.setContentsMargins(0, 0, 0, 0)
                icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                icon_lbl = QLabel()
                icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_lbl.setStyleSheet("background: transparent; border: none;")
                icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                icon_pix = self._render_svg_pixmap("folder", THEME_COLORS['primary_green'], 38)
                icon_lbl.setPixmap(icon_pix)
                icon_inner_layout.addWidget(icon_lbl)
                
                folder_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Folder Name Label
                name_lbl = QLabel()
                name_lbl.setFixedHeight(22)
                name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                font_metrics = name_lbl.fontMetrics()
                elided_name = font_metrics.elidedText(item_data['name'], Qt.TextElideMode.ElideMiddle, 86)
                name_lbl.setText(elided_name)
                name_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {THEME_COLORS['text_primary']};
                        font-size: 11px;
                        font-weight: 600;
                        background: transparent;
                        border: none;
                    }}
                """)
                name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                folder_layout.addWidget(name_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
                
                folder_card.setToolTip(f"Folder: {item_data['name']}\nClick to open")
                folder_card.setProperty("folder_name", item_data['name'])
                folder_card.installEventFilter(self)
                folder_card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                folder_card.customContextMenuRequested.connect(self._on_folder_card_custom_context_menu)
                self.assets_grid_layout.addWidget(folder_card, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            else:
                filepath = item_data['filepath']
                filename = os.path.basename(filepath)
                
                # Card Frame Container
                card = QFrame()
                card.setFixedSize(102, 122)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setObjectName("asset_card")
                card.setStyleSheet(f"""
                    QFrame#asset_card {{
                        background-color: {THEME_COLORS['surface']};
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 8px;
                    }}
                    QFrame#asset_card:hover {{
                        background-color: #24352D;
                        border: 1px solid {THEME_COLORS['primary_green']};
                    }}
                """)
                
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(6, 10, 6, 8)
                card_layout.setSpacing(6)
                card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Dedicated inner preview box with rounded corners and recessed background
                preview_container = QFrame()
                preview_container.setFixedSize(88, 68)
                preview_container.setObjectName("asset_preview")
                preview_container.setStyleSheet("""
                    QFrame#asset_preview {{
                        background-color: #1A201D;
                        border: 1px solid rgba(255, 255, 255, 0.04);
                        border-radius: 6px;
                    }}
                """)
                preview_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                
                preview_inner_layout = QVBoxLayout(preview_container)
                preview_inner_layout.setContentsMargins(3, 3, 3, 3)
                preview_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                thumb_lbl = QLabel()
                thumb_lbl.setFixedSize(80, 60)
                thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_lbl.setStyleSheet("background: transparent; border: none;")
                thumb_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                
                # Placeholder image icon while loading
                default_icon_pix = self._render_svg_pixmap("image", THEME_COLORS['text_secondary'], 28)
                thumb_lbl.setPixmap(default_icon_pix)
                preview_inner_layout.addWidget(thumb_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
                
                card_layout.addWidget(preview_container, alignment=Qt.AlignmentFlag.AlignCenter)
                
                # Title Label (File name from computer)
                title_lbl = QLabel()
                title_lbl.setFixedHeight(22)
                title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                font_metrics = title_lbl.fontMetrics()
                elided_title = font_metrics.elidedText(filename, Qt.TextElideMode.ElideMiddle, 86)
                title_lbl.setText(elided_title)
                title_lbl.setStyleSheet(f"""
                    QLabel {{
                        color: {THEME_COLORS['text_secondary']};
                        font-size: 10.5px;
                        font-weight: 500;
                        background: transparent;
                        border: none;
                    }}
                """)
                title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                card_layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
                
                tooltip_text = f"{filename}\nPath: {filepath}"
                card.setToolTip(tooltip_text)
                
                # Click handlers: clicking card inserts the image
                card.setProperty("filepath", filepath)
                card.installEventFilter(self)
                
                # Context menu on right click
                card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                card.customContextMenuRequested.connect(self._on_asset_card_custom_context_menu)
                
                # Decoupled Asynchronous Thumbnail Loading
                def create_thumbnail_callback(target_label):
                    def on_thumbnail_ready(icon):
                        if not icon or icon.isNull():
                            return
                        try:
                            import shiboken6
                            if not shiboken6.isValid(target_label):
                                return
                            pixmap = icon.pixmap(QSize(78, 58))
                            if not pixmap.isNull():
                                target_label.setPixmap(pixmap)
                        except Exception:
                            pass
                    return on_thumbnail_ready
                            
                from core.thumbnail_engine import ThumbnailEngine
                ThumbnailEngine.get_instance().request_thumbnail(filepath, create_thumbnail_callback(thumb_lbl))
                
                self.assets_grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Enforce column dimensions and bottom stretch to anchor cards to the left
        self.assets_grid_layout.setColumnMinimumWidth(0, 102)
        self.assets_grid_layout.setColumnMinimumWidth(1, 102)
        self.assets_grid_layout.setColumnStretch(0, 0)
        self.assets_grid_layout.setColumnStretch(1, 0)
        self.assets_grid_layout.setColumnStretch(2, 1)
        self.assets_grid_layout.setRowStretch(len(items) // 2 + 1, 1)

    def _show_folder_context_menu(self, btn, pos, folder_name):
        from PySide6.QtWidgets import QMenu, QInputDialog, QMessageBox
        import shutil
        import platform
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #2E8B57; }")
        
        rename_action = menu.addAction("Rename Folder")
        menu.addSeparator()
        
        open_action = menu.addAction("Open in Explorer")
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Folder")
        
        user_library_path = os.path.join(get_app_data_dir(), "assets", "library")
        current_full_path = os.path.join(user_library_path, getattr(self, 'current_asset_folder', ""))
        folder_path = os.path.join(current_full_path, folder_name)
        
        action = menu.exec_(btn.mapToGlobal(pos))
        
        if action == rename_action:
            dialog = FolderNameDialog(self, "Rename Folder", folder_name)
            if dialog.exec_():
                new_name = dialog.get_text()
                if new_name and new_name != folder_name:
                    from core.security_engine import SecurityEngine
                    if not SecurityEngine.get_instance().is_safe_input(new_name):
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.warning(self, "Security Alert", "The folder name contains invalid or potentially harmful characters.")
                        return
                        
                    new_path = os.path.join(current_full_path, new_name)
                    try:
                        os.rename(folder_path, new_path)
                        self._refresh_assets_grid()
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not rename folder:\n{e}")
                    
        elif action == delete_action:
            reply = QMessageBox.question(self, "Confirm Delete", 
                                         f"Are you sure you want to delete the folder '{folder_name}' and ALL its contents?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    shutil.rmtree(folder_path)
                    self._refresh_assets_grid()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not delete folder:\n{e}")
                    
        elif action == open_action:
            try:
                if platform.system() == "Windows":
                    os.startfile(folder_path)
                elif platform.system() == "Darwin":
                    import subprocess
                    subprocess.Popen(["open", folder_path])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", folder_path])
            except Exception as e:
                print(f"Error opening folder: {e}")

    def _show_asset_context_menu(self, btn, pos, file_path):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #F44336; }")
        
        # Move To Submenu
        move_menu = menu.addMenu("Move to Folder...")
        move_menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #2E8B57; }")
        
        user_library_path = os.path.join(get_app_data_dir(), "assets", "library")
        os.makedirs(user_library_path, exist_ok=True)
        
        folders = ["/ (Root)"]
        for root, dirs, _ in os.walk(user_library_path):
            for d in dirs:
                rel_path = os.path.relpath(os.path.join(root, d), user_library_path)
                folders.append(rel_path.replace('\\', '/'))
        
        def make_move_handler(dest_rel):
            def handler():
                try:
                    if dest_rel == "/ (Root)":
                        dest_dir = user_library_path
                    else:
                        dest_dir = os.path.join(user_library_path, dest_rel)
                    
                    filename = os.path.basename(file_path)
                    dest_file = os.path.join(dest_dir, filename)
                    
                    if os.path.exists(dest_file) and os.path.samefile(file_path, dest_file):
                        return
                        
                    import shutil
                    # To prevent overwriting, add suffix if exists
                    counter = 1
                    base, ext = os.path.splitext(filename)
                    while os.path.exists(dest_file):
                        dest_file = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                        counter += 1
                    
                    shutil.move(file_path, dest_file)
                    self._refresh_assets_grid()
                except Exception as e:
                    print(f"Error moving file: {e}")
            return handler
            
        for f in folders:
            action = move_menu.addAction(f)
            action.triggered.connect(make_move_handler(f))
            
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Asset")
        
        action = menu.exec_(btn.mapToGlobal(pos))
        if action == delete_action:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                self._refresh_assets_grid()
            except Exception as e:
                print(f"Error deleting file: {e}")

    def _create_mind_map_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)

        # Header row with BETA badge
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)
        header_inner = self._create_header("Mind Maps")
        header_row.addLayout(header_inner)

        from PySide6.QtWidgets import QLabel
        beta_badge = QLabel("BETA")
        beta_badge.setStyleSheet(
            "background-color: #2E8B57; color: #FFFFFF; "
            "font-size: 8px; font-weight: bold; letter-spacing: 0.8px; "
            "border-radius: 4px; padding: 2px 5px;"
        )
        from PySide6.QtCore import Qt as _Qt
        beta_badge.setAlignment(_Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(beta_badge)
        header_row.addStretch()

        layout.addLayout(header_row)

        from components.mind_map_builder.ui_panel import MindMapPanel
        self.mind_map_panel = MindMapPanel()
        layout.addWidget(self.mind_map_panel)

        return container


    def _create_scenes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)
        
        layout.addLayout(self._create_header("SCENES"))
        
        from advanced_features.components.scene_dropdown import AdvancedSceneButton
        add_btn = AdvancedSceneButton(
            add_scene_callback=self.add_scene_requested.emit,
            get_current_artboard=self._get_current_artboard,
        )
        self._add_btn = add_btn
        layout.addWidget(add_btn)

        # Scenes are rendered as custom cards inside a scroll area
        self._scenes_scroll = QScrollArea()
        self._scenes_scroll.setWidgetResizable(True)
        self._scenes_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scenes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scenes_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._scenes_container = QWidget()
        self._scenes_container.setStyleSheet("background: transparent;")
        self._scenes_layout = QVBoxLayout(self._scenes_container)
        self._scenes_layout.setContentsMargins(0, 0, 0, 0)
        self._scenes_layout.setSpacing(6)
        self._scenes_layout.addStretch()

        self._scenes_scroll.setWidget(self._scenes_container)
        layout.addWidget(self._scenes_scroll, stretch=1)

        # Keep a parallel QListWidget hidden for signal compatibility (currentRowChanged)
        self.scenes_list = QListWidget()
        self.scenes_list.setVisible(False)
        self.scenes_list.currentRowChanged.connect(self.scene_selected.emit)
        layout.addWidget(self.scenes_list)

        # Track card widgets: list of (QListWidgetItem, card_frame)
        self._scene_cards: list = []

        return tab

    def _select_scene_card(self, index: int):
        """Visually select a scene card and sync the hidden list."""
        for i, (_, card) in enumerate(self._scene_cards):
            if i == index:
                card.setProperty("selected", True)
            else:
                card.setProperty("selected", False)
            card.style().unpolish(card)
            card.style().polish(card)
        self.scenes_list.setCurrentRow(index)

    def add_scene_item(self, index: int):
        self._ensure_tab_loaded(1)
        if not hasattr(self, 'scenes_list') or self.scenes_list is None:
            return

        # Add a hidden QListWidgetItem to keep signal compatibility
        hidden_item = QListWidgetItem()
        hidden_item.setData(Qt.ItemDataRole.UserRole, index)
        self.scenes_list.addItem(hidden_item)

        # --- Build the card ---
        card = QFrame()
        card.setProperty("selected", False)
        card.setFixedHeight(54)
        card.setStyleSheet(f"""
            QFrame[selected="false"] {{
                background-color: {THEME_COLORS['surface']};
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
            }}
            QFrame[selected="false"]:hover {{
                border: 1px solid rgba(255,255,255,0.12);
                background-color: #2A3430;
            }}
            QFrame[selected="true"] {{
                background-color: #1D2E25;
                border-radius: 8px;
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 0, 10, 0)
        card_layout.setSpacing(10)

        # Scene number badge
        badge = QFrame()
        badge.setFixedSize(28, 28)
        badge.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['primary_green']};
                border-radius: 6px;
                border: none;
            }}
        """)
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_num = QLabel(str(index + 1))
        badge_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_num.setStyleSheet("color: white; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        badge_layout.addWidget(badge_num)
        card_layout.addWidget(badge)

        # Scene label
        label = QLabel(f"Scene {index + 1}")
        label.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: 600; font-size: 13px; background: transparent; border: none;")
        card_layout.addWidget(label, 1)

        # Delete button
        delete_btn = QToolButton()
        delete_btn.setText("x")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFixedSize(22, 22)
        delete_btn.setStyleSheet(f"""
            QToolButton {{
                color: {THEME_COLORS['text_secondary']};
                border: none;
                background: transparent;
                font-size: 13px;
                font-weight: bold;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                color: #ff5252;
                background: rgba(255, 82, 82, 0.1);
            }}
        """)
        delete_btn.setProperty("hidden_item", hidden_item)
        delete_btn.clicked.connect(self._on_delete_scene_btn_clicked)
        card_layout.addWidget(delete_btn)

        # Click anywhere on the card to select
        card.installEventFilter(self)

        # Insert before the trailing stretch
        insert_pos = self._scenes_layout.count() - 1
        self._scenes_layout.insertWidget(insert_pos, card)

        self._scene_cards.append((hidden_item, card))
        self._select_scene_card(len(self._scene_cards) - 1)

    def _on_scene_delete_clicked(self, item):
        row = self.scenes_list.row(item)
        if row != -1:
            self.scene_deleted.emit(row)

    def remove_scene_item(self, row: int):
        if 0 <= row < self.scenes_list.count():
            self.scenes_list.takeItem(row)

            # Remove card widget
            if row < len(self._scene_cards):
                _, card = self._scene_cards.pop(row)
                self._scenes_layout.removeWidget(card)
                card.deleteLater()

            # Re-number remaining badges
            for i, (_, c) in enumerate(self._scene_cards):
                badge_lbl = c.findChild(QLabel)
                if badge_lbl:
                    badge_lbl.setText(str(i + 1))
                labels = c.findChildren(QLabel)
                for lbl in labels:
                    if lbl.text().startswith("Scene "):
                        lbl.setText(f"Scene {i + 1}")

            if self._scene_cards:
                new_row = max(0, row - 1)
                self._select_scene_card(new_row)

    def _create_layers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)
        
        layout.addLayout(self._create_header("LAYERS"))
        
        self.layers_list = QListWidget()
        self.layers_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ padding: 12px; color: {THEME_COLORS['text_secondary']}; border-radius: 6px; margin-bottom: 5px; background: {THEME_COLORS['bg_main']}; }}
            QListWidget::item:hover {{ color: {THEME_COLORS['text_primary']}; }}
            QListWidget::item:selected {{ border: 1px solid {THEME_COLORS['primary_green']}; color: {THEME_COLORS['primary_green']}; font-weight: bold; }}
        """)
        
        # Enable drag and drop to reorder
        self.layers_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Start empty
            
        layout.addWidget(self.layers_list, stretch=1)
        return tab
        
    def update_layers(self, items):
        self._ensure_tab_loaded(2)
        if not hasattr(self, 'layers_list') or self.layers_list is None:
            return
        self.layers_list.clear()
        for idx, item in enumerate(items):
            # Try to get a meaningful name
            name = f"Item {idx + 1}"
            if hasattr(item, 'property') and item.property("layer_name"):
                name = item.property("layer_name")
                
            list_item = QListWidgetItem(f"{name}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.layers_list.addItem(list_item)

    def _create_music_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)
        
        layout.addLayout(self._create_header("AUDIO LIBRARY"))
        
        try:
            self.player = QMediaPlayer(self)
            self.audio_output = QAudioOutput(self)
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(1.0)
        except Exception as e:
            print(f"Warning: Audio player initialization deferred or failed: {e}")
            self.player = None
            self.audio_output = None
        
        # Upload & Record Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        # Upload Button
        add_btn = QPushButton("+ Upload")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['surface']}; 
                color: {THEME_COLORS['primary_green']};
                border-radius: 6px;
                padding: 9px;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['primary_green']};
                color: {THEME_COLORS['bg_main']};
            }}
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._upload_audio_to_library)
        btn_layout.addWidget(add_btn)
        
        # Record Button
        icon_red = get_icon("mic", "#F44336")
        icon_white = get_icon("mic", "white")
        rec_btn = HoverIconButton(" Record", icon_red, icon_white)
        
        rec_btn.setIconSize(QSize(16, 16))
        rec_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['surface']}; 
                color: #F44336;
                border-radius: 6px;
                padding: 9px;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #F44336;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #F44336;
                color: white;
            }}
        """)
        rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rec_btn.clicked.connect(self._open_voice_recorder)
        btn_layout.addWidget(rec_btn)
        
        layout.addLayout(btn_layout)
        
        # Scrollable audio list container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self._audio_list_container = QWidget()
        self._audio_list_container.setStyleSheet("background: transparent;")
        self._audio_list_layout = QVBoxLayout(self._audio_list_container)
        self._audio_list_layout.setContentsMargins(0, 0, 0, 0)
        self._audio_list_layout.setSpacing(4)
        self._audio_list_layout.addStretch()
        
        scroll_area.setWidget(self._audio_list_container)
        layout.addWidget(scroll_area, stretch=1)
        
        return tab

    def _audio_section_header(self, label: str, color: str) -> QWidget:
        """Creates a section header for Voice / SFX / Music groups."""
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 8, 0, 2)
        hl.setSpacing(8)
        
        bar = QFrame()
        bar.setFixedSize(3, 14)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 1px; border: none;")
        
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: transparent; border: none; letter-spacing: 1px;")
        
        hl.addWidget(bar)
        hl.addWidget(lbl)
        hl.addStretch()
        return w

    def _audio_card(self, item, filename: str, layer_color: str) -> QWidget:
        """Creates a single audio file card with a colored bar, filename, and delete button."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['surface']};
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.06);
            }}
            QFrame:hover {{
                border: 1px solid rgba(255,255,255,0.12);
            }}
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 10, 0)
        card_layout.setSpacing(0)
        
        # Colored left bar (replaces emoji)
        side_bar = QFrame()
        side_bar.setFixedWidth(4)
        side_bar.setStyleSheet(f"background-color: {layer_color}; border-radius: 3px 0 0 3px; border: none;")
        card_layout.addWidget(side_bar)
        
        card_layout.addSpacing(10)
        
        # File name label
        name_lbl = QLabel(filename)
        name_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 11px; background: transparent; border: none;")
        name_lbl.setToolTip(f"{item.layer_name}: {filename}")
        name_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        name_lbl.setProperty("audio_item", item)
        name_lbl.installEventFilter(self)
        card_layout.addWidget(name_lbl, 1)
        
        # Delete button
        del_btn = QToolButton()
        del_btn.setText("x")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setFixedSize(22, 22)
        del_btn.setStyleSheet(f"""
            QToolButton {{
                color: {THEME_COLORS['text_secondary']};
                border: none;
                background: transparent;
                font-size: 13px;
                font-weight: bold;
                border-radius: 3px;
            }}
            QToolButton:hover {{
                color: #ff5252;
                background: rgba(255, 82, 82, 0.1);
            }}
        """)
        del_btn.setProperty("audio_item", item)
        del_btn.clicked.connect(self._on_delete_audio_btn_clicked)
        card_layout.addWidget(del_btn)
        
        return card
        
    def _upload_audio_to_library(self):
        if not self._workspace:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            self._workspace.add_audio_node(file_path, "Music")
            
    def update_audio_library(self, audio_items):
        self._ensure_tab_loaded(3)
        if not hasattr(self, '_audio_list_layout') or self._audio_list_layout is None:
            return

        # Clear old cards from the layout (keep stretch at end)
        while self._audio_list_layout.count() > 1:
            item = self._audio_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Layer config: (label, color)
        layers = [
            ("Voice", "VOICE", "#1565C0"),
            ("SFX",   "SFX",   "#6A1B9A"),
            ("Music", "MUSIC", "#2D6A4F"),
        ]
        
        for layer_key, layer_label, layer_color in layers:
            items_in_layer = [i for i in audio_items if i.layer_name == layer_key]
            if not items_in_layer:
                continue
            
            # Section header
            header = self._audio_section_header(layer_label, layer_color)
            self._audio_list_layout.insertWidget(
                self._audio_list_layout.count() - 1, header
            )
            
            # Cards
            for item in items_in_layer:
                filename = os.path.basename(item.file_path)
                card = self._audio_card(item, filename, layer_color)
                card.setFixedHeight(38)
                self._audio_list_layout.insertWidget(
                    self._audio_list_layout.count() - 1, card
                )

    def _on_card_clicked(self, node):
        self._ensure_tab_loaded(3)
        if hasattr(self, 'player') and self.player and node and node.file_path:
            self.player.setSource(QUrl.fromLocalFile(node.file_path))
            self.player.play()
            
    def _delete_audio_node(self, node):
        self._ensure_tab_loaded(3)
        if self._workspace:
            if hasattr(self, 'player') and self.player and self.player.source() == QUrl.fromLocalFile(node.file_path):
                self.player.stop()
            self._workspace.remove_audio_node(node)
            
    def _on_audio_clicked(self, list_item):
        self._ensure_tab_loaded(3)
        node = list_item.data(Qt.ItemDataRole.UserRole)
        if hasattr(self, 'player') and self.player and node and node.file_path:
            self.player.setSource(QUrl.fromLocalFile(node.file_path))
            self.player.play()

    def _handle_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            library_path = os.path.join(get_app_data_dir(), "assets", "library")
            if getattr(self, 'current_asset_folder', ""):
                library_path = os.path.join(library_path, self.current_asset_folder)
            os.makedirs(library_path, exist_ok=True)
            filename = os.path.basename(file_path)
            dest_path = os.path.join(library_path, filename)
            
            # Avoid copying if it's the exact same file path
            is_same_file = False
            if os.path.exists(dest_path):
                is_same_file = os.path.samefile(file_path, dest_path)
            
            if not is_same_file:
                # Ensure filename is unique if it exists
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path) and not os.path.samefile(file_path, dest_path):
                    dest_path = os.path.join(library_path, f"{base}_{counter}{ext}")
                    counter += 1
                
                # Check again in case it matched an existing file during the loop
                if not os.path.exists(dest_path) or not os.path.samefile(file_path, dest_path):
                    shutil.copy2(file_path, dest_path)
            
            # Refresh grid and emit signal so workspace uses the new file
            self._refresh_assets_grid()
            self.image_uploaded.emit(dest_path)

    def _open_voice_recorder(self):
        from core.voice_recorder.manager import VoiceRecorderManager
        from core.voice_recorder.components.record_dialog import VoiceRecorderDialog
        
        # Instantiate manager permanently to avoid Garbage Collection killing the timer
        if not hasattr(self, '_voice_manager'):
            self._voice_manager = VoiceRecorderManager()
            
            def handle_recording_finished(filepath):
                if self._workspace:
                    # Add to UI layer
                    self._workspace.add_audio_node(filepath, "Voice")
                    # Connect to AudioEngine to actually play it with the video
                    if hasattr(self._workspace, 'audio_engine'):
                        self._workspace.audio_engine.add_track(filepath, 0.0)
                        
            self._voice_manager.recording_finished.connect(handle_recording_finished)
        
        dialog = VoiceRecorderDialog(self._voice_manager, self.window())
        dialog.exec()
