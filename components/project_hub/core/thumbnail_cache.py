# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Fast thumbnail generation and caching for project cards in the Hub.
Features: Extracts embedded drawings from .wip files or generates sleek studio-grade placeholders.
"""
import os
import json
import hashlib
import zipfile
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPen, QLinearGradient
from PySide6.QtCore import Qt, QRectF, QUrl
from utils.paths import get_app_data_dir

class ThumbnailCache:
    """Manages on-disk caching of project thumbnails with high-fidelity artwork extraction."""

    def __init__(self):
        self.cache_dir = os.path.join(get_app_data_dir(), "Cache", "HubThumbnails")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, filepath: str) -> str:
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            mtime = 0.0
        unique_str = f"{os.path.normpath(filepath)}:{mtime}"
        file_hash = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"thumb_{file_hash}.png")

    def get_thumbnail_url(self, filepath: str, title: str = "") -> str:
        """Returns a valid file URL string suitable for QML Image sources."""
        if not filepath or not os.path.exists(filepath):
            return ""

        cache_path = self._get_cache_path(filepath)
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return QUrl.fromLocalFile(cache_path).toString()

        generated = False
        try:
            if zipfile.is_zipfile(filepath):
                with zipfile.ZipFile(filepath, "r") as zf:
                    names = zf.namelist()

                    # 1. Look for explicit cover/thumbnail
                    for explicit in ("thumbnail.png", "assets" + "/thumbnail.png", "cover.png"):
                        if explicit in names:
                            with zf.open(explicit) as src, open(cache_path, "wb") as dst:
                                dst.write(src.read())
                            generated = True
                            break

                    # 2. Extract artwork image from project items or library
                    if not generated and "project.json" in names:
                        try:
                            p_data = json.loads(zf.read("project.json").decode("utf-8"))
                            src_image = None
                            assets_dir = os.path.join(get_app_data_dir(), "assets")

                            for item in p_data.get("items", []):
                                ip = item.get("image_path") or item.get("svg_filepath")
                                if not ip:
                                    continue

                                # Check inside zip
                                if ip in names:
                                    raw = zf.read(ip)
                                    loaded = QImage.fromData(raw)
                                    if not loaded.isNull():
                                        src_image = loaded
                                        break

                                # Check absolute disk path
                                if os.path.exists(ip):
                                    loaded = QImage(ip)
                                    if not loaded.isNull():
                                        src_image = loaded
                                        break

                                # Search by basename inside DrawMotion assets library
                                base_name = os.path.basename(ip)
                                if os.path.isdir(assets_dir):
                                    for root, _, files in os.walk(assets_dir):
                                        if base_name in files:
                                            candidate_path = os.path.join(root, base_name)
                                            loaded = QImage(candidate_path)
                                            if not loaded.isNull():
                                                src_image = loaded
                                                break
                                    if src_image:
                                        break

                            # Fallback: scan zip assets/ folder for any image
                            if not src_image:
                                for name in names:
                                    if name.startswith("assets/") and name.lower().endswith((".png", ".jpg", ".jpeg")):
                                        raw = zf.read(name)
                                        loaded = QImage.fromData(raw)
                                        if not loaded.isNull():
                                            src_image = loaded
                                            break

                            if src_image and not src_image.isNull():
                                self._render_artwork_thumbnail(src_image, cache_path)
                                generated = True
                        except Exception:
                            generated = False
        except Exception:
            generated = False

        if not generated or not os.path.exists(cache_path):
            self._generate_placeholder(cache_path, title or os.path.basename(filepath))

        return QUrl.fromLocalFile(cache_path).toString()

    def _render_artwork_thumbnail(self, src_img: QImage, target_path: str) -> None:
        """Renders project artwork scaled crisply on a whiteboard studio canvas."""
        w, h = 360, 202
        canvas = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        canvas.fill(QColor("#FAFAF8"))  # Whiteboard canvas tone

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Scale and center the artwork with margin
        scaled = src_img.scaled(w - 24, h - 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        dest_x = (w - scaled.width()) // 2
        dest_y = (h - scaled.height()) // 2

        painter.drawImage(dest_x, dest_y, scaled)

        # Subtle vignette border to give physical whiteboard depth
        painter.setPen(QPen(QColor(0, 0, 0, 25), 1.0))
        painter.drawRect(0, 0, w - 1, h - 1)
        painter.end()

        canvas.save(target_path, "PNG")

    def _generate_placeholder(self, target_path: str, title: str) -> None:
        """Draws a modern studio placeholder thumbnail when no cover is present."""
        w, h = 360, 202
        img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor("#1E2421"))
        gradient.setColorAt(1.0, QColor("#121614"))
        painter.fillRect(0, 0, w, h, gradient)

        painter.setPen(QPen(QColor("#2A322E"), 1.0))
        painter.drawRect(0, 0, w - 1, h - 1)

        center_x = w / 2.0
        center_y = h / 2.0 - 15.0

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#222A27"))
        painter.drawRoundedRect(QRectF(center_x - 32, center_y - 32, 64, 64), 14, 14)

        painter.setPen(QPen(QColor("#2E8B57"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(center_x - 32, center_y - 32, 64, 64), 14, 14)

        initial = (title.strip()[:1] if title.strip() else "D").upper()
        font = QFont("Segoe UI", 22, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#2E8B57"))
        painter.drawText(QRectF(center_x - 32, center_y - 32, 64, 64), Qt.AlignCenter, initial)

        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor("#A6ABA8"))
        painter.drawText(QRectF(10, h - 36, w - 20, 24), Qt.AlignCenter, "DrawMotion Project")

        painter.end()
        img.save(target_path, "PNG")
