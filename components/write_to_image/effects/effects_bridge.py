"""
Bridge between PySide6 Python layer and QML Text Effects visual components.
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from .text_effects import AVAILABLE_EFFECTS


class TextEffectsBridge(QObject):
    """
    Exposes reactive properties and slots to QML for interactive text effects preview.
    """

    effectChanged = Signal(str)
    colorChanged = Signal(str)
    intensityChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_effect = "none"
        self._current_color = "#3498db"
        self._current_intensity = 1.0

    @Property(str, notify=effectChanged)
    def currentEffect(self) -> str:
        return self._current_effect

    @Property(str, notify=colorChanged)
    def currentColor(self) -> str:
        return self._current_color

    @Property(float, notify=intensityChanged)
    def currentIntensity(self) -> float:
        return self._current_intensity

    @Slot(str)
    def setEffect(self, effect_name: str):
        if self._current_effect != effect_name:
            self._current_effect = effect_name
            self.effectChanged.emit(effect_name)

    @Slot(str)
    def setColor(self, hex_color: str):
        if self._current_color != hex_color:
            self._current_color = hex_color
            self.colorChanged.emit(hex_color)

    @Slot(float)
    def setIntensity(self, value: float):
        clamped = max(0.0, min(2.0, float(value)))
        if abs(self._current_intensity - clamped) > 1e-4:
            self._current_intensity = clamped
            self.intensityChanged.emit(clamped)

    @Slot(result=list)
    def getAvailableEffects(self) -> list:
        return list(AVAILABLE_EFFECTS)
