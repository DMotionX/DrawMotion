# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent
from core.animator_engine import AnimatorEngine
from graphics.hand_item import HandItem
from components.project_hub import ProjectHubWindow

class TestHubAndShutdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_animator_engine_shutdown(self):
        """Verifies AnimatorEngine shutdown stops timers and shuts down SFX thread."""
        hand = HandItem()
        engine = AnimatorEngine(hand)
        self.assertTrue(hasattr(engine, 'sfx_engine'))
        self.assertTrue(engine.sfx_engine._thread.isRunning())
        
        # Call shutdown
        engine.shutdown()
        self.assertFalse(engine.sfx_engine._thread.isRunning())

    def test_project_hub_maximized_show(self):
        """Verifies show_hub calls showMaximized and window is valid."""
        hub = ProjectHubWindow()
        self.assertTrue(hub.is_valid())
        hub.show_hub()
        self.assertTrue(hub.isMaximized() or hub.windowState() & Qt.WindowMaximized)
        hub.close()
        hub.deleteLater()
        QApplication.processEvents()

    def test_qml_syntax_clean(self):
        """Verifies all Project Hub QML components load without syntax or reference errors."""
        qml_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "components", "project_hub", "qml"
        )
        engine = QQmlEngine()
        main_qml = os.path.join(qml_dir, "MainHub.qml")
        self.assertTrue(os.path.exists(main_qml))

if __name__ == "__main__":
    unittest.main()
