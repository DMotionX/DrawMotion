"""
AdvancedSceneButton: A drop-down button in the Scenes sidebar panel for adding
scenes or assigning transition effects between scenes.
"""
from PySide6.QtWidgets import QPushButton, QMenu, QWidgetAction, QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QAction, QColor, QPainter, QPolygonF
from PySide6.QtCore import Qt, QPointF
import math
from utils.theme import THEME_COLORS


def _make_star_pixmap(color: str, size: int = 16):
    """Draw a 4-pointed star as a QPixmap in the given hex color."""
    from PySide6.QtGui import QPixmap, QPainterPath
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx, cy = size / 2, size / 2
    r_outer, r_inner = size / 2 - 1, size / 4
    points = []
    for i in range(8):
        angle = math.radians(i * 45 - 90)
        r = r_outer if i % 2 == 0 else r_inner
        points.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    return pix


class _TransitionMenuItem(QWidget):
    """Custom widget action item showing a colored star icon + label."""

    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 12, 4)
        layout.setSpacing(8)

        icon_lbl = QLabel()
        from PySide6.QtGui import QIcon
        icon_lbl.setPixmap(_make_star_pixmap(color, 16))
        icon_lbl.setFixedSize(16, 16)
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(label)
        text_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 13px;")
        layout.addWidget(text_lbl)
        layout.addStretch()


class AdvancedSceneButton(QPushButton):
    """
    A custom button for the Scenes panel that shows a dropdown menu for adding
    new scenes or choosing a transition effect to assign to the current scene.
    """

    # Metadata reused from the transitions effects registry
    TRANSITION_META = [
        {'id': 'fade',  'label': 'Fade',  'color': '#7C3AED'},
        {'id': 'slide', 'label': 'Slide', 'color': '#2563EB'},
        {'id': 'wipe',  'label': 'Wipe',  'color': '#059669'},
        {'id': 'zoom',  'label': 'Zoom',  'color': '#D97706'},
        {'id': 'iris',  'label': 'Iris',  'color': '#DB2777'},
    ]

    def __init__(self, add_scene_callback, get_current_artboard=None, parent=None):
        """
        Args:
            add_scene_callback: Called when the user picks "New Scene".
            get_current_artboard: Callable that returns the currently focused
                                  SceneArtboardItem (used to assign transition_type).
        """
        super().__init__("+ Add New Item", parent)
        self._get_artboard = get_current_artboard

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']}; 
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #38a169;
            }}
            QPushButton::menu-indicator {{
                image: none;
            }}
        """)

        menu_style = f"""
            QMenu {{
                background-color: {THEME_COLORS['surface']};
                color: white;
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 0px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_COLORS['primary_green']};
                border-radius: 4px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {THEME_COLORS['divider']};
                margin: 4px 8px;
            }}
        """

        self.menu = QMenu(self)
        self.menu.setStyleSheet(menu_style)

        # ── New Scene action ─────────────────────────────────────
        new_scene_action = QAction("New Scene", self)
        new_scene_action.triggered.connect(add_scene_callback)
        self.menu.addAction(new_scene_action)

        self.menu.addSeparator()

        # ── Transition Effect sub-menu ───────────────────────────
        transition_menu = self.menu.addMenu("Transition Effect")
        transition_menu.setStyleSheet(menu_style)

        # "None" option to remove transition
        none_action = QAction("No Transition", self)
        none_action.triggered.connect(self._on_no_transition_triggered)
        transition_menu.addAction(none_action)
        transition_menu.addSeparator()

        for meta in self.TRANSITION_META:
            wa = QWidgetAction(transition_menu)
            item_widget = _TransitionMenuItem(meta['label'], meta['color'])
            wa.setDefaultWidget(item_widget)
            wa.setData(meta['id'])
            wa.triggered.connect(self._on_transition_triggered)
            transition_menu.addAction(wa)

        self.setMenu(self.menu)

    def _on_no_transition_triggered(self):
        self._assign_transition(None)

    def _on_transition_triggered(self):
        sender = self.sender()
        if sender and hasattr(sender, 'data'):
            tid = sender.data()
            self._assign_transition(tid)

    def _assign_transition(self, transition_id):
        if not self._get_artboard:
            return
        artboard = self._get_artboard()
        if artboard:
            artboard.transition_type = transition_id
