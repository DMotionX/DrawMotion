# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Visual design tokens and QSS styles for the DrawMotion interactive splash screen.
Features: Studio-grade dark gradient, rounded capsule progress bar, drop shadow parameters.
"""

SPLASH_DIMENSIONS = {
    "width": 540,
    "height": 310,
    "border_radius": 16,
    "shadow_blur": 36,
    "shadow_offset_y": 10,
}

SPLASH_COLORS = {
    "card_bg_start": "#161C19",
    "card_bg_end": "#0E1210",
    "card_border": "rgba(46, 139, 87, 0.35)",
    "shadow": "rgba(0, 0, 0, 180)",
    "title": "#FFFFFF",
    "subtitle": "#4EBA80",
    "version_badge_bg": "rgba(46, 139, 87, 0.2)",
    "version_badge_border": "rgba(78, 186, 128, 0.4)",
    "version_badge_text": "#7EE5AE",
    "track_bg": "#1C2420",
    "bar_gradient_start": "#2E8B57",
    "bar_gradient_end": "#4EBA80",
    "status_text": "#9BA39F",
    "percentage_text": "#5AA87C",
}

def get_splash_qss() -> str:
    return f"""
    QFrame#SplashCard {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {SPLASH_COLORS['card_bg_start']}, stop:1 {SPLASH_COLORS['card_bg_end']});
        border: 1px solid {SPLASH_COLORS['card_border']};
        border-radius: {SPLASH_DIMENSIONS['border_radius']}px;
    }}
    QLabel#SplashTitle {{
        color: {SPLASH_COLORS['title']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#SplashSubtitle {{
        color: {SPLASH_COLORS['subtitle']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 3px;
    }}
    QLabel#VersionBadge {{
        background-color: {SPLASH_COLORS['version_badge_bg']};
        border: 1px solid {SPLASH_COLORS['version_badge_border']};
        color: {SPLASH_COLORS['version_badge_text']};
        font-family: 'Segoe UI', 'Inter', monospace;
        font-size: 10px;
        font-weight: 600;
        border-radius: 9px;
        padding: 2px 8px;
    }}
    QLabel#StatusLabel {{
        color: {SPLASH_COLORS['status_text']};
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 11px;
    }}
    QLabel#PercentLabel {{
        color: {SPLASH_COLORS['percentage_text']};
        font-family: 'Segoe UI', 'Inter', monospace;
        font-size: 11px;
        font-weight: 600;
    }}
    QProgressBar#CapsuleProgressBar {{
        background-color: {SPLASH_COLORS['track_bg']};
        border: none;
        border-radius: 3px;
        min-height: 5px;
        max-height: 5px;
        text-align: right;
    }}
    QProgressBar#CapsuleProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {SPLASH_COLORS['bar_gradient_start']}, stop:1 {SPLASH_COLORS['bar_gradient_end']});
        border-radius: 3px;
    }}
    """
