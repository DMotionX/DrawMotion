import os
import sys
import unittest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

# Ensure offscreen Qt platform only when needed on headless Linux
if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = QApplication.instance() or QApplication(sys.argv)

from graphics.animated_image_item import AnimatedImageItem
from graphics.hand_item import HandItem
from core.animator_engine import AnimatorEngine


class TestImageTransitHandHiding(unittest.TestCase):
    def setUp(self):
        self.scene = QGraphicsScene()
        self.hand_item = HandItem()
        self.scene.addItem(self.hand_item)
        self.engine = AnimatorEngine(self.hand_item)

        # Create 2 dummy images
        img1 = QImage(100, 100, QImage.Format.Format_ARGB32)
        img1.fill(Qt.GlobalColor.blue)
        self.item1 = AnimatedImageItem(QPixmap.fromImage(img1))
        self.item1.anim_duration = 2.0
        self.item1.setPos(50, 50)

        img2 = QImage(100, 100, QImage.Format.Format_ARGB32)
        img2.fill(Qt.GlobalColor.red)
        self.item2 = AnimatedImageItem(QPixmap.fromImage(img2))
        self.item2.anim_duration = 2.0
        self.item2.setPos(400, 400)

        self.scene.addItem(self.item1)
        self.scene.addItem(self.item2)

    def test_hand_strictly_hidden_during_image_to_image_transit(self):
        """Verify that during move-hand between two images, the hand item is hidden."""
        self.engine.sync_queue([self.item1, self.item2])
        self.assertGreater(len(self.engine.schedule), 2)
        
        # Schedule: [draw item1, move-hand, draw item2]
        move_action = self.engine.schedule[1]
        self.assertEqual(move_action['type'], 'move-hand')

        # Seek to middle of transition between image 1 and image 2
        transit_mid = (move_action['start'] + move_action['end']) / 2.0
        self.engine.seek(transit_mid, show_hand_when_stopped=True)

        self.assertFalse(
            self.hand_item.isVisible(),
            "HandItem MUST be hidden during transit between images to prevent awkward shrinking/gliding."
        )


if __name__ == '__main__':
    unittest.main()
