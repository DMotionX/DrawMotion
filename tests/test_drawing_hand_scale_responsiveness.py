import os
import sys
import unittest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

# Ensure offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = QApplication.instance() or QApplication(sys.argv)

from graphics.hand_item import HandItem
from graphics.animated_image_item import AnimatedImageItem
from graphics.animated_stroke_item import AnimatedStrokeItem
from core.animator_engine import AnimatorEngine
from core.settings_manager import SettingsManager
from components.write_to_image.hand_manager import WritingHandItem


class TestDrawingHandScaleResponsiveness(unittest.TestCase):
    def setUp(self):
        self.sm = SettingsManager()
        self.orig_hand_size = self.sm.get("hand_size", 2.0)
        self.orig_wh_size = self.sm.get("writing_hand_size", 1.0)
        self.sm.set("hand_size", 2.0)
        self.sm.set("writing_hand_size", 1.0)

        self.hand_item = HandItem()
        self.engine = AnimatorEngine(self.hand_item)

        # Create a test image item (with scale 0.33 as in typical imports)
        qimg = QImage(300, 300, QImage.Format.Format_ARGB32)
        qimg.fill(Qt.GlobalColor.green)
        self.image_item = AnimatedImageItem(QPixmap.fromImage(qimg))
        self.image_item.setScale(0.33)

    def tearDown(self):
        self.sm.set("hand_size", self.orig_hand_size)
        self.sm.set("writing_hand_size", self.orig_wh_size)

    def test_default_hand_size_is_2_0(self):
        """Verify that default hand_size is 2.0 and gives natural ~1.0 scale on 0.33 image."""
        self.assertEqual(self.sm.get("hand_size"), 2.0)
        computed_scale = self.engine._compute_drawing_hand_scale(self.image_item)
        # Should be closely centered around 0.99 - 1.0
        self.assertAlmostEqual(computed_scale, 1.0, delta=0.05)

    def test_hand_size_increases_linearly_and_visibly(self):
        """Verify increasing hand_size in settings noticeably increases the computed hand scale."""
        scale_at_2_0 = self.engine._compute_drawing_hand_scale(self.image_item)

        self.sm.set("hand_size", 3.0)
        scale_at_3_0 = self.engine._compute_drawing_hand_scale(self.image_item)

        # 3.0 is 1.5x of 2.0, so scale should increase by approximately 50%
        self.assertAlmostEqual(scale_at_3_0 / scale_at_2_0, 1.5, delta=0.05)
        self.assertGreater(scale_at_3_0, scale_at_2_0 * 1.4)

    def test_hand_size_decreases_cleanly(self):
        """Verify decreasing hand_size in settings noticeably decreases the computed hand scale."""
        scale_at_2_0 = self.engine._compute_drawing_hand_scale(self.image_item)

        self.sm.set("hand_size", 1.5)
        scale_at_1_5 = self.engine._compute_drawing_hand_scale(self.image_item)

        # 1.5 is 0.75x of 2.0
        self.assertAlmostEqual(scale_at_1_5 / scale_at_2_0, 0.75, delta=0.05)
        self.assertLess(scale_at_1_5, scale_at_2_0)

    def test_no_extreme_crushing_on_tiny_images(self):
        """Verify that an extremely small image (scale 0.05) does not crush the hand to zero."""
        tiny_item = AnimatedImageItem(QPixmap(50, 50))
        tiny_item.setScale(0.05)

        computed_scale = self.engine._compute_drawing_hand_scale(tiny_item)
        # Bounded factor ensures scale does not drop below 0.8
        self.assertGreaterEqual(computed_scale, 0.80)

    def test_live_setting_change_updates_visible_hand(self):
        """Verify HandItem updates its scale immediately when setting changes while visible."""
        self.hand_item.show()
        self.sm.set("hand_size", 2.0)
        self.assertAlmostEqual(self.hand_item.scale(), 1.0, delta=0.05)

        self.sm.set("hand_size", 3.0)
        self.assertAlmostEqual(self.hand_item.scale(), 1.5, delta=0.05)

    def test_hand_size_change_has_zero_effect_on_writing_hand(self):
        """Verify changing hand_size leaves WritingHandItem 100% untouched."""
        wh = WritingHandItem()
        orig_wh_scale = wh.scale()

        self.sm.set("hand_size", 10.0)
        self.assertEqual(wh.scale(), orig_wh_scale)


if __name__ == '__main__':
    unittest.main()
