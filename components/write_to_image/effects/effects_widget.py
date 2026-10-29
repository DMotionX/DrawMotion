"""
Text Effects Widget hosting the QML TextEffectsPicker via QQuickWidget with robust fallback.
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PySide6.QtCore import Signal, QUrl, Qt
from PySide6.QtQuickWidgets import QQuickWidget
from .effects_bridge import TextEffectsBridge
from .text_effects import AVAILABLE_EFFECTS


class TextEffectsWidget(QWidget):
    """
    Inspector container for Text Effects.
    Hosts QML TextEffectsPicker and exposes clean Python signals.
    """

    effect_changed = Signal(str)
    color_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.bridge = TextEffectsBridge(self)
        self.bridge.effectChanged.connect(self.effect_changed.emit)
        self.bridge.colorChanged.connect(self.color_changed.emit)

        # Attempt QML loading
        qml_path = os.path.join(os.path.dirname(__file__), "qml", "TextEffectsPicker.qml")
        self._qml_widget = None

        if os.path.exists(qml_path):
            try:
                self._qml_widget = QQuickWidget(self)
                self._qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
                self._qml_widget.setAttribute(Qt.WA_AlwaysStackOnTop)
                self._qml_widget.setClearColor(Qt.transparent)
                self._qml_widget.setMinimumHeight(180)
                self.setMinimumHeight(180)
                self._qml_widget.rootContext().setContextProperty("effectsBridge", self.bridge)
                self._qml_widget.setSource(QUrl.fromLocalFile(qml_path))
                self.layout.addWidget(self._qml_widget)
            except Exception:
                self._qml_widget = None

        if self._qml_widget is None or self._qml_widget.status() == QQuickWidget.Error:
            self.setMinimumHeight(0)
            # Fallback to standard PySide6 widgets
            if self._qml_widget:
                self.layout.removeWidget(self._qml_widget)
                self._qml_widget.deleteLater()
                self._qml_widget = None

            self._fallback_combo = QComboBox(self)
            for eff in AVAILABLE_EFFECTS:
                self._fallback_combo.addItem(eff["name"], eff["id"])
            self._fallback_combo.currentIndexChanged.connect(self._on_fallback_changed)
            self.layout.addWidget(self._fallback_combo)

    def _on_fallback_changed(self, idx: int):
        effect_id = self._fallback_combo.itemData(idx)
        self.bridge.setEffect(effect_id)

    def set_effect(self, effect_name: str):
        self.bridge.setEffect(effect_name)
        if hasattr(self, "_fallback_combo"):
            idx = self._fallback_combo.findData(effect_name)
            if idx >= 0:
                self._fallback_combo.setCurrentIndex(idx)

    def current_effect(self) -> str:
        return self.bridge.currentEffect
