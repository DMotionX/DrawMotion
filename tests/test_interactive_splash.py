# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
from PySide6.QtWidgets import QApplication, QWidget
from components.splash import InteractiveSplashScreen

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def test_interactive_splash_initialization(qapp):
    splash = InteractiveSplashScreen(version="v1.7.13")
    assert splash is not None
    assert splash.version == "v1.7.13"
    assert splash.title_label.text() == "DRAWMOTION"
    assert splash.subtitle_label.text() == "ANIMATION STUDIO"
    assert splash.version_badge.text() == "v1.7.13"
    assert splash.progress_bar.value() == 0
    splash.close()

def test_interactive_splash_progress_updates(qapp):
    splash = InteractiveSplashScreen(version="v1.7.13")
    splash.show()
    
    splash.set_progress(25, "Verifying health...")
    assert splash.progress_bar.value() == 25
    assert splash.percent_label.text() == "25%"
    assert splash.status_label.text() == "Verifying health..."

    splash.set_progress(75, "Loading studio...")
    assert splash.progress_bar.value() == 75
    assert splash.percent_label.text() == "75%"
    assert splash.status_label.text() == "Loading studio..."

    # Test clamping
    splash.set_progress(150, "Capped")
    assert splash.progress_bar.value() == 100

    splash.set_progress(-20, "Floor")
    assert splash.progress_bar.value() == 0
    splash.close()

def test_interactive_splash_finish_smoothly(qapp, qtbot):
    dummy_window = QWidget()
    splash = InteractiveSplashScreen(version="v1.7.13")
    splash.show()

    splash.finish_smoothly(dummy_window)
    # Wait for the 250ms animation and deletion to complete
    qtbot.wait(350)
    assert dummy_window.isVisible()
    dummy_window.close()
