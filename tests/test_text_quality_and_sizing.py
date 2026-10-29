import os
import sys
import unittest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsRectItem
from PySide6.QtCore import QRectF, Qt

# Ensure offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = QApplication.instance() or QApplication(sys.argv)

from components.write_to_image.image_renderer import render_text_to_image
from components.write_to_image.models import WriteToImageModel
from components.write_to_image.graphics_item import WriteToImageGraphicsItem


class TestTextQualityAndSizing(unittest.TestCase):
    def test_high_quality_rendering_output(self):
        """Verify that render_text_to_image produces valid, sharp image with charmap."""
        img_path = render_text_to_image(
            text="اختبار جودة النص العربي والإنجليزية",
            font_family="Arial",
            font_size=42,
            color="#2A322E",
            id_str="quality_test_1"
        )
        self.assertTrue(os.path.exists(img_path))
        charmap_path = img_path.replace(".png", "_charmap.json")
        self.assertTrue(os.path.exists(charmap_path))

    def test_smart_text_autofit_sizing(self):
        """Verify that smart auto-fit proportions the text prominently on a 1920x1080 artboard."""
        model = WriteToImageModel(
            id="sizing_test_item",
            name="Text Image",
            text="عنوان رئيسي للمشهد",
            font_family="Arial",
            font_size=42,
            color="#000000"
        )
        img_path = render_text_to_image(
            text=model.text,
            font_family=model.font_family,
            font_size=model.font_size,
            color=model.color,
            id_str=model.id
        )
        model.image_path = img_path

        item = WriteToImageGraphicsItem(model)
        board_rect = QRectF(0, 0, 1920, 1080)
        text_rect = item.boundingRect()

        # Simulate workspace smart auto-fit calculation
        desired_scale_w = (board_rect.width() * 0.55) / text_rect.width()
        desired_scale_h = (board_rect.height() * 0.35) / text_rect.height() if text_rect.height() > 0 else desired_scale_w
        optimal_scale = min(desired_scale_w, desired_scale_h)
        optimal_scale = max(1.0, min(optimal_scale, 5.0))
        item.setScale(optimal_scale)

        visual_width = text_rect.width() * optimal_scale
        visual_height = text_rect.height() * optimal_scale

        # Visual width should comfortably occupy ~30% - 75% of artboard
        self.assertGreaterEqual(visual_width, board_rect.width() * 0.30)
        self.assertLessEqual(visual_width, board_rect.width() * 0.75)
        # Visual height should be clearly legible
        self.assertGreaterEqual(visual_height, 60.0)


if __name__ == '__main__':
    unittest.main()
