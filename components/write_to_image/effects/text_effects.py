from PySide6.QtGui import QImage, QPainter, QColor, QRadialGradient, QBrush, QPainterPath
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap

def apply_glow_effect(img: QImage, color_hex: str) -> QImage:
    # Uses a QGraphicsDropShadowEffect to create a glow
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    item = QGraphicsPixmapItem(pixmap)
    
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(30)
    glow.setColor(QColor(color_hex))
    glow.setOffset(0, 0)
    item.setGraphicsEffect(glow)
    
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.end()
    
    # We must also draw the original text over the glow so it stays sharp
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawImage(0, 0, img)
    painter.end()
    
    return res

def apply_neon_effect(img: QImage, color_hex: str) -> QImage:
    # Multiple layered drop shadows for a intense neon look
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    # Base glow
    item1 = QGraphicsPixmapItem(pixmap)
    glow1 = QGraphicsDropShadowEffect()
    glow1.setBlurRadius(50)
    glow1.setColor(QColor(color_hex))
    glow1.setOffset(0, 0)
    item1.setGraphicsEffect(glow1)
    scene.addItem(item1)
    
    # Inner intense glow (white-ish)
    item2 = QGraphicsPixmapItem(pixmap)
    glow2 = QGraphicsDropShadowEffect()
    glow2.setBlurRadius(15)
    c2 = QColor(color_hex).lighter(150)
    glow2.setColor(c2)
    glow2.setOffset(0, 0)
    item2.setGraphicsEffect(glow2)
    scene.addItem(item2)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.end()
    
    return res

def apply_ink_bleed_effect(img: QImage) -> QImage:
    # A simple pseudo ink-bleed by slightly blurring and layering
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    item = QGraphicsPixmapItem(pixmap)
    bleed = QGraphicsDropShadowEffect()
    bleed.setBlurRadius(8)
    bleed.setColor(QColor(0, 0, 0, 150)) # Dark bleed
    bleed.setOffset(2, 2)
    item.setGraphicsEffect(bleed)
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.end()
    
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawImage(0, 0, img)
    painter.end()
    
    return res

def apply_drop_shadow_effect(img: QImage) -> QImage:
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    item = QGraphicsPixmapItem(pixmap)
    
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setColor(QColor(0, 0, 0, 180))
    shadow.setOffset(5, 5)
    item.setGraphicsEffect(shadow)
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.end()
    
    return res

def apply_glitch_effect(img: QImage) -> QImage:
    # Simulates a chromatic aberration / glitch effect by shifting red and blue channels
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setCompositionMode(QPainter.CompositionMode_Screen)
    
    # Red Shift
    painter.setOpacity(0.7)
    painter.drawImage(4, 0, img)
    # Blue Shift
    painter.drawImage(-4, 0, img)
    # Original
    painter.setOpacity(1.0)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawImage(0, 0, img)
    painter.end()
    
    return res

def apply_holographic_effect(img: QImage, color_hex: str) -> QImage:
    # A cyan/magenta glow with a slight transparency
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    item = QGraphicsPixmapItem(pixmap)
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(20)
    glow.setColor(QColor(0, 255, 255, 150)) # Cyan
    glow.setOffset(-3, 0)
    item.setGraphicsEffect(glow)
    scene.addItem(item)
    
    item2 = QGraphicsPixmapItem(pixmap)
    glow2 = QGraphicsDropShadowEffect()
    glow2.setBlurRadius(20)
    glow2.setColor(QColor(255, 0, 255, 150)) # Magenta
    glow2.setOffset(3, 0)
    item2.setGraphicsEffect(glow2)
    scene.addItem(item2)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.end()
    
    # Draw original text slightly transparent
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setOpacity(0.85)
    painter.drawImage(0, 0, img)
    painter.end()
    
    return res

def apply_text_effect(img: QImage, effect_type: str, color_hex: str) -> QImage:
    """
    Applies the specified effect to the rasterized QImage.
    """
    if effect_type == "glow":
        return apply_glow_effect(img, color_hex)
    elif effect_type == "neon":
        return apply_neon_effect(img, color_hex)
    elif effect_type == "ink_bleed":
        return apply_ink_bleed_effect(img)
    elif effect_type == "drop_shadow":
        return apply_drop_shadow_effect(img)
    elif effect_type == "glitch":
        return apply_glitch_effect(img)
    elif effect_type == "holographic":
        return apply_holographic_effect(img, color_hex)
    return img
