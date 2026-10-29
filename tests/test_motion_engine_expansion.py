# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QPixmap

from core.motion_engine.motion_solver import MotionSolver
from core.motion_engine.motion_engine import MotionEngine
from core.audio_engine.sfx_engine import SFXSyncEngine
from graphics.animated_stroke_item import AnimatedStrokeItem
from graphics.animated_image_item import AnimatedImageItem
from components.write_to_image.graphics_item import WriteToImageGraphicsItem
from components.write_to_image.models import WriteToImageModel
from core.drawing_engine.raster_engine.raster_item import AnimatedRasterItem
from models.item_models import BaseItemModel

class TestMotionEngineExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_eight_way_directional_matrix(self):
        """Verifies entry starting points are properly positioned outside artboard for all 8 directions."""
        artboard = QRectF(0, 0, 1920, 1080)
        item_rect = QRectF(0, 0, 200, 150)
        target = QPointF(500, 400)
        
        directions = ["left", "right", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"]
        for d in directions:
            start_pos = MotionSolver.compute_entry_start_pos(d, artboard, item_rect, target, 1.0)
            self.assertIsInstance(start_pos, QPointF)
            if "left" in d:
                self.assertLess(start_pos.x(), artboard.left())
            if "right" in d:
                self.assertGreater(start_pos.x(), artboard.right())
            if "top" in d:
                self.assertLess(start_pos.y(), artboard.top())
            if "bottom" in d:
                self.assertGreater(start_pos.y(), artboard.bottom())

    def test_all_eight_motion_styles_solve_without_error(self):
        """Verifies all 8 styles evaluate cleanly at start, midpoint, and completion."""
        artboard = QRectF(0, 0, 1920, 1080)
        item_rect = QRectF(0, 0, 200, 150)
        target = QPointF(600, 400)
        styles = [
            "hand_drag", "hand_push", "slide", "gravity_drop", 
            "elastic_pop", "flip_3d", "cinematic_zoom", "arc_glide"
        ]
        
        for style in styles:
            # Test at start
            sol_start = MotionSolver.solve_frame(
                time_in_item=0.0, motion_duration=1.5, motion_style=style,
                direction="left", easing="smooth", target_pos=target,
                item_rect=item_rect, item_scale=1.0, artboard_rect=artboard
            )
            self.assertIn("item_pos", sol_start)
            self.assertIn("item_scale_mult", sol_start)
            self.assertIn("item_opacity", sol_start)
            self.assertIn("sfx_hint", sol_start)
            
            # Test at midpoint
            sol_mid = MotionSolver.solve_frame(
                time_in_item=0.75, motion_duration=1.5, motion_style=style,
                direction="left", easing="smooth", target_pos=target,
                item_rect=item_rect, item_scale=1.0, artboard_rect=artboard
            )
            self.assertIn("item_pos", sol_mid)
            
            # Test at completion (zero drift: item_pos must match target_pos exactly)
            sol_end = MotionSolver.solve_frame(
                time_in_item=2.0, motion_duration=1.5, motion_style=style,
                direction="left", easing="smooth", target_pos=target,
                item_rect=item_rect, item_scale=1.0, artboard_rect=artboard
            )
            self.assertEqual(sol_end["item_pos"], target)
            self.assertAlmostEqual(sol_end["item_scale_mult"], 1.0, places=2)
            self.assertAlmostEqual(sol_end["item_opacity"], 1.0, places=2)

    def test_six_easing_curves_evaluation(self):
        """Verifies that all 6 easing functions compute monotonic or valid boundary transitions."""
        easings = ["smooth", "back", "bounce", "elastic", "exponential", "linear"]
        for name in easings:
            fn = MotionSolver.get_easing_function(name)
            self.assertTrue(callable(fn))
            val_0 = fn(0.0)
            val_1 = fn(1.0)
            self.assertAlmostEqual(val_0, 0.0, places=3)
            self.assertAlmostEqual(val_1, 1.0, places=3)

    def test_sfx_hints_generation(self):
        """Verifies that styles generate proper sfx_hint values during motion."""
        artboard = QRectF(0, 0, 1920, 1080)
        item_rect = QRectF(0, 0, 200, 150)
        target = QPointF(500, 300)
        
        # Test whoosh hint early in hand_drag
        sol_early = MotionSolver.solve_frame(
            time_in_item=0.1, motion_duration=1.5, motion_style="hand_drag",
            direction="left", easing="smooth", target_pos=target,
            item_rect=item_rect, item_scale=1.0, artboard_rect=artboard
        )
        self.assertEqual(sol_early["sfx_hint"], "whoosh")
        
        # Test impact hint on settle
        sol_settle = MotionSolver.solve_frame(
            time_in_item=1.35, motion_duration=1.5, motion_style="hand_drag",
            direction="left", easing="smooth", target_pos=target,
            item_rect=item_rect, item_scale=1.0, artboard_rect=artboard
        )
        self.assertEqual(sol_settle["sfx_hint"], "impact")

    def test_universal_stroke_item_motion_serialization(self):
        """Verifies AnimatedStrokeItem carries entrance_mode and motion_settings through to_dict and from_dict."""
        path = QPainterPath()
        path.addRect(0, 0, 100, 100)
        stroke = AnimatedStrokeItem(path)
        stroke.entrance_mode = "motion"
        stroke.motion_settings = {
            "style": "gravity_drop",
            "direction": "top",
            "duration": 2.2,
            "easing": "bounce",
            "sfx": "thud"
        }
        stroke.setPos(250, 350)
        stroke.setScale(1.5)
        
        serialized = stroke.to_dict()
        self.assertEqual(serialized["entrance_mode"], "motion")
        self.assertEqual(serialized["motion_settings"]["style"], "gravity_drop")
        self.assertEqual(serialized["motion_settings"]["sfx"], "thud")
        
        # Deserialize
        restored = AnimatedStrokeItem.from_dict(serialized)
        self.assertEqual(restored.entrance_mode, "motion")
        self.assertEqual(restored.motion_settings["style"], "gravity_drop")
        self.assertEqual(restored.motion_settings["sfx"], "thud")
        self.assertEqual(restored.pos().x(), 250)
        self.assertEqual(restored.pos().y(), 350)
        self.assertEqual(restored.scale(), 1.5)

    def test_universal_write_to_image_motion_serialization(self):
        """Verifies WriteToImageGraphicsItem carries entrance_mode and motion_settings through serialization."""
        model = WriteToImageModel(id="test_wti_1", name="Motion Text", text="Hello Motion")
        item = WriteToImageGraphicsItem(model)
        item.entrance_mode = "motion"
        item.motion_settings = {
            "style": "elastic_pop",
            "direction": "left",
            "duration": 1.8,
            "easing": "elastic",
            "sfx": "pop"
        }
        item.setPos(400, 200)
        item.setScale(1.25)
        
        serialized = item.to_dict()
        self.assertEqual(serialized["entrance_mode"], "motion")
        self.assertEqual(serialized["motion_settings"]["style"], "elastic_pop")
        self.assertEqual(serialized["motion_settings"]["sfx"], "pop")
        
        restored = WriteToImageGraphicsItem.from_dict(serialized)
        self.assertEqual(restored.entrance_mode, "motion")
        self.assertEqual(restored.motion_settings["style"], "elastic_pop")
        self.assertEqual(restored.motion_settings["sfx"], "pop")
        self.assertEqual(restored.pos().x(), 400)
        self.assertEqual(restored.pos().y(), 200)

    def test_universal_raster_item_motion_serialization(self):
        """Verifies AnimatedRasterItem carries entrance_mode and motion_settings through serialization."""
        pixmap = QPixmap(100, 100)
        pixmap.fill()
        item = AnimatedRasterItem(pixmap)
        item.entrance_mode = "motion"
        item.motion_settings = {
            "style": "cinematic_zoom",
            "direction": "left",
            "duration": 2.0,
            "easing": "back",
            "sfx": "whoosh"
        }
        item.setPos(150, 250)
        item.setScale(1.1)
        
        serialized = item.to_dict()
        self.assertEqual(serialized["entrance_mode"], "motion")
        self.assertEqual(serialized["motion_settings"]["style"], "cinematic_zoom")
        self.assertEqual(serialized["motion_settings"]["sfx"], "whoosh")
        
        restored = AnimatedRasterItem.from_dict(serialized)
        self.assertEqual(restored.entrance_mode, "motion")
        self.assertEqual(restored.motion_settings["style"], "cinematic_zoom")
        self.assertEqual(restored.motion_settings["sfx"], "whoosh")
        self.assertEqual(restored.pos().x(), 150)
        self.assertEqual(restored.pos().y(), 250)

    def test_motion_sfx_audio_assets_exist(self):
        """Verifies that all 3 motion procedural WAV assets exist on disk in assets/sfx/motion."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        motion_dir = os.path.join(base_dir, "assets", "sfx", "motion")
        
        whoosh_file = os.path.join(motion_dir, "whoosh.wav")
        thud_file = os.path.join(motion_dir, "thud.wav")
        pop_file = os.path.join(motion_dir, "pop.wav")
        
        self.assertTrue(os.path.exists(whoosh_file), f"Missing {whoosh_file}")
        self.assertTrue(os.path.exists(thud_file), f"Missing {thud_file}")
        self.assertTrue(os.path.exists(pop_file), f"Missing {pop_file}")
        self.assertGreater(os.path.getsize(whoosh_file), 1000)
        self.assertGreater(os.path.getsize(thud_file), 1000)
        self.assertGreater(os.path.getsize(pop_file), 1000)

    def test_motion_engine_zero_drift_reset(self):
        """Verifies MotionEngine.capture_target_transform and reset_item restores original transform with zero drift."""
        path = QPainterPath()
        path.addEllipse(0, 0, 80, 80)
        stroke = AnimatedStrokeItem(path)
        stroke.setPos(450.0, 320.0)
        stroke.setScale(1.8)
        stroke.setRotation(45.0)
        stroke.setOpacity(0.85)
        
        MotionEngine.capture_target_transform(stroke)
        
        # Apply an active mid-flight motion frame
        artboard = QRectF(0, 0, 1920, 1080)
        MotionEngine.apply_motion_frame(
            item=stroke, hand_item=None, time_sec=0.4,
            start_time=0.0, action_duration=1.5, artboard_rect=artboard
        )
        
        # Verify item was displaced during flight
        self.assertNotEqual(stroke.pos(), QPointF(450.0, 320.0))
        
        # Reset item
        MotionEngine.reset_item(stroke)
        
        # Verify complete zero drift restoration
        self.assertEqual(stroke.pos(), QPointF(450.0, 320.0))
        self.assertAlmostEqual(stroke.scale(), 1.8, places=3)
        self.assertAlmostEqual(stroke.rotation(), 45.0, places=3)
        self.assertAlmostEqual(stroke.opacity(), 0.85, places=3)

if __name__ == "__main__":
    unittest.main()
