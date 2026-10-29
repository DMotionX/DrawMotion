from PySide6.QtGui import QImage, QPainter, QColor, QRadialGradient, QBrush, QPainterPath
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap

def _create_tinted_image(src: QImage, color: QColor) -> QImage:
    """Creates a tinted clone of src preserving its exact alpha mask."""
    tinted = QImage(src.size(), QImage.Format.Format_ARGB32_Premultiplied)
    tinted.fill(Qt.GlobalColor.transparent)
    p = QPainter(tinted)
    p.drawImage(0, 0, src)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(tinted.rect(), color)
    p.end()
    return tinted


def apply_glow_effect(img: QImage, color_hex: str) -> QImage:
    """Soft, radiant outer luminescence that preserves 100% crisp foreground text."""
    base_color = QColor(color_hex)
    if base_color.lightnessF() < 0.25:
        glow_color = QColor("#00B4D8")
    else:
        glow_color = QColor(base_color)
    glow_color.setAlpha(150)

    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    item = QGraphicsPixmapItem(pixmap)
    
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(20)
    glow.setColor(glow_color)
    glow.setOffset(0, 0)
    item.setGraphicsEffect(glow)
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    
    # Always composite the original text on top with 100% opacity for tack-sharp letterforms
    painter.drawImage(0, 0, img)
    painter.end()
    return res


def apply_neon_effect(img: QImage, color_hex: str) -> QImage:
    """Dual-pass neon glow: soft aura + focused halo, compositing sharp text on top."""
    base_color = QColor(color_hex)
    if base_color.lightnessF() < 0.25:
        neon_color = QColor("#00F0FF")
    else:
        neon_color = QColor(base_color)

    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    # Pass 1: Soft outer aura
    item1 = QGraphicsPixmapItem(pixmap)
    glow1 = QGraphicsDropShadowEffect()
    glow1.setBlurRadius(24)
    c1 = QColor(neon_color)
    c1.setAlpha(130)
    glow1.setColor(c1)
    glow1.setOffset(0, 0)
    item1.setGraphicsEffect(glow1)
    scene.addItem(item1)
    
    # Pass 2: Focused inner neon core
    item2 = QGraphicsPixmapItem(pixmap)
    glow2 = QGraphicsDropShadowEffect()
    glow2.setBlurRadius(8)
    c2 = QColor(neon_color).lighter(120)
    c2.setAlpha(180)
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
    
    # Composite original crisp text on top to eliminate eye-straining blur or washout
    painter.drawImage(0, 0, img)
    painter.end()
    return res


def apply_ink_bleed_effect(img: QImage) -> QImage:
    """Realistic paper ink absorption & subtle bleed."""
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    item = QGraphicsPixmapItem(pixmap)
    bleed = QGraphicsDropShadowEffect()
    bleed.setBlurRadius(6)
    bleed.setColor(QColor(0, 0, 0, 130))
    bleed.setOffset(1, 1)
    item.setGraphicsEffect(bleed)
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    
    painter.drawImage(0, 0, img)
    painter.end()
    return res


def apply_drop_shadow_effect(img: QImage) -> QImage:
    """Soft directional drop shadow."""
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    item = QGraphicsPixmapItem(pixmap)
    
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(14)
    shadow.setColor(QColor(0, 0, 0, 160))
    shadow.setOffset(4, 4)
    item.setGraphicsEffect(shadow)
    scene.addItem(item)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    painter.drawImage(0, 0, img)
    painter.end()
    return res


def apply_glitch_effect(img: QImage) -> QImage:
    """True RGB chromatic aberration with cyan/magenta channel offsets and sharp center."""
    cyan_fringe = _create_tinted_image(img, QColor(0, 230, 255, 180))
    magenta_fringe = _create_tinted_image(img, QColor(255, 30, 80, 180))
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # Cyan shifted left, Magenta shifted right
    painter.drawImage(-3, 0, cyan_fringe)
    painter.drawImage(3, 0, magenta_fringe)
    # Original text centered on top
    painter.drawImage(0, 0, img)
    painter.end()
    return res


def apply_holographic_effect(img: QImage, color_hex: str) -> QImage:
    """Dual cyan and magenta chromatic radiance with crisp foreground text."""
    scene = QGraphicsScene()
    pixmap = QPixmap.fromImage(img)
    
    item1 = QGraphicsPixmapItem(pixmap)
    glow1 = QGraphicsDropShadowEffect()
    glow1.setBlurRadius(16)
    glow1.setColor(QColor(0, 255, 255, 140))
    glow1.setOffset(-2, 0)
    item1.setGraphicsEffect(glow1)
    scene.addItem(item1)
    
    item2 = QGraphicsPixmapItem(pixmap)
    glow2 = QGraphicsDropShadowEffect()
    glow2.setBlurRadius(16)
    glow2.setColor(QColor(255, 0, 255, 140))
    glow2.setOffset(2, 0)
    item2.setGraphicsEffect(glow2)
    scene.addItem(item2)
    
    res = QImage(img.size(), QImage.Format.Format_ARGB32_Premultiplied)
    res.fill(Qt.GlobalColor.transparent)
    painter = QPainter(res)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    scene.render(painter)
    
    # Draw original text with crisp definition
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


AVAILABLE_EFFECTS = [
    {"id": "none", "name": "None", "description": "Original clean render"},
    {"id": "glow", "name": "Glow", "description": "Soft radiant outer luminescence"},
    {"id": "neon", "name": "Neon", "description": "High-intensity double-pass neon glow"},
    {"id": "ink_bleed", "name": "Ink Bleed", "description": "Realistic paper ink absorption & slight bleed"},
    {"id": "drop_shadow", "name": "Drop Shadow", "description": "Soft cinematic directional shadow"},
    {"id": "glitch", "name": "Glitch", "description": "Chromatic RGB aberration offset"},
    {"id": "holographic", "name": "Holographic", "description": "Dual cyan and magenta chromatic radiance"},
]

