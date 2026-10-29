# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Interactive, frameless, studio-grade reload/splash screen for DrawMotion.
Features: 0ms native Qt Widget startup, smooth capsule progress bar, live subsystem ticker, and seamless fade-out handoff.
"""
import os
import sys
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QGraphicsDropShadowEffect, QApplication
)
from components.splash.splash_theme import (
    SPLASH_DIMENSIONS, SPLASH_COLORS, get_splash_qss
)

class InteractiveSplashScreen(QWidget):
    """
    Studio-grade floating reload and splash screen.
    Guarantees instant (<50ms) visual response upon launching DrawMotion.
    """
    def __init__(self, version: str = "v1.7.13", parent=None):
        super().__init__(parent)
        self.version = version
        self._target_window = None

        # 1. Configure frameless, floating window attributes
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.SplashScreen | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Dimensions including padding for shadow
        w = SPLASH_DIMENSIONS["width"] + 48
        h = SPLASH_DIMENSIONS["height"] + 48
        self.resize(w, h)

        # 2. Setup layout with shadow margin
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(24, 24, 24, 24)
        outer_layout.setSpacing(0)

        # 3. Main Glassmorphic Studio Card
        self.card = QFrame(self)
        self.card.setObjectName("SplashCard")
        self.card.setStyleSheet(get_splash_qss())

        # Apply cinematic floating drop shadow
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(SPLASH_DIMENSIONS["shadow_blur"])
        shadow.setOffset(0, SPLASH_DIMENSIONS["shadow_offset_y"])
        shadow.setColor(QColor(0, 0, 0, 190))
        self.card.setGraphicsEffect(shadow)

        outer_layout.addWidget(self.card)

        # 4. Populate Card Content
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # --- Top Header: Logo + Title + Version Badge ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        # Brand Icon
        self.icon_label = QLabel(self.card)
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "resources", "branding", "PNG", "DrawMotion_64x64.png"
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                56, 56, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(pix)
        header_layout.addWidget(self.icon_label)

        # Title and Subtitle Block
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(2)
        
        self.title_label = QLabel("DRAWMOTION", self.card)
        self.title_label.setObjectName("SplashTitle")
        
        self.subtitle_label = QLabel("ANIMATION STUDIO", self.card)
        self.subtitle_label.setObjectName("SplashSubtitle")
        
        titles_layout.addWidget(self.title_label)
        titles_layout.addWidget(self.subtitle_label)
        header_layout.addLayout(titles_layout)

        header_layout.addStretch(1)

        # Version Pill Badge
        self.version_badge = QLabel(self.version, self.card)
        self.version_badge.setObjectName("VersionBadge")
        header_layout.addWidget(self.version_badge)

        card_layout.addLayout(header_layout)

        # Flexible spacing
        card_layout.addStretch(1)

        # --- Bottom Section: Status Ticker + Percentage + Capsule Progress Bar ---
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("Welcome to DrawMotion...", self.card)
        self.status_label.setObjectName("StatusLabel")
        status_row.addWidget(self.status_label)

        status_row.addStretch(1)

        self.percent_label = QLabel("0%", self.card)
        self.percent_label.setObjectName("PercentLabel")
        status_row.addWidget(self.percent_label)

        card_layout.addLayout(status_row)

        # Ultra-sleek capsule progress bar
        self.progress_bar = QProgressBar(self.card)
        self.progress_bar.setObjectName("CapsuleProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        card_layout.addWidget(self.progress_bar)

        # Center on primary screen immediately
        self._center_on_screen()

    def _center_on_screen(self):
        """Centers the splash screen on the active monitor geometry."""
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            geo = primary_screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def set_progress(self, value: int, message: str = None) -> None:
        """
        Updates progress bar percentage and live status message smoothly.
        Forces instant event processing to keep UI responsive throughout boot.
        """
        clamped = max(0, min(100, int(value)))
        self.progress_bar.setValue(clamped)
        self.percent_label.setText(f"{clamped}%")
        
        if message:
            self.status_label.setText(str(message))
            
        QApplication.processEvents()

    def finish_smoothly(self, target_window: QWidget = None) -> None:
        """
        Seamless transition: Displays the target window immediately in the background,
        keeps splash floating on top, and smoothly dissolves (fades out) over 250ms.
        """
        self._target_window = target_window
        self.set_progress(100, "Ready to create!")

        # Render target window immediately underneath the splash card
        if self._target_window is not None:
            try:
                if hasattr(self._target_window, "show_hub"):
                    self._target_window.show_hub()
                elif hasattr(self._target_window, "showMaximized"):
                    self._target_window.showMaximized()
                else:
                    self._target_window.show()
                # Ensure splash remains floating cleanly on top during its dissolve
                self.raise_()
            except Exception:
                pass

        # Smooth fade-out animation over the already-rendered target window
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self._fade_anim.start()

    def _on_fade_finished(self):
        """Finalizes transition and cleans up splash resources."""
        if self._target_window is not None:
            try:
                self._target_window.raise_()
                self._target_window.activateWindow()
            except Exception:
                pass
        self.close()
        self.deleteLater()
