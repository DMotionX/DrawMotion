# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import cv2
import numpy as np
import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from core.drawing_engine.algorithms.factory import AlgorithmFactory
from core.drawing_engine.algorithms.hatch_shading.smart_education_generator import generate_smart_educational_paths

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def make_test_schematic_qimage(w=1000, h=600):
    """Creates a synthetic multi-component schematic with Arduino, Sensor, and connecting wires on white background."""
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    # Component 1: Arduino on the left (x: 100..400, y: 150..500)
    cv2.rectangle(canvas, (100, 150), (400, 500), (0, 0, 0), 3)
    cv2.rectangle(canvas, (200, 250), (300, 380), (0, 0, 0), -1) # MCU chip
    cv2.rectangle(canvas, (120, 160), (380, 180), (0, 0, 0), -1) # Header pins

    # Component 2: Sensor on the right (x: 700..950, y: 150..350)
    cv2.rectangle(canvas, (700, 150), (950, 350), (0, 0, 0), 3)
    cv2.circle(canvas, (825, 250), 40, (0, 0, 0), 3)

    # Connecting wire between Arduino and Sensor
    cv2.line(canvas, (380, 170), (550, 170), (0, 0, 0), 2)
    cv2.line(canvas, (550, 170), (550, 220), (0, 0, 0), 2)
    cv2.line(canvas, (550, 220), (700, 220), (0, 0, 0), 2)

    rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGBA)
    return QImage(rgba.data, w, h, w * 4, QImage.Format.Format_RGBA8888)

def test_educational_algorithm_instantiation(qapp):
    algo = AlgorithmFactory.get_algorithm("Educational")
    assert algo is not None

def test_educational_module_decomposition(qapp):
    """Verifies that the generator decomposes multi-object schematics into distinct modules rather than slicing horizontally."""
    qimg = make_test_schematic_qimage()
    algo = AlgorithmFactory.get_algorithm("Educational")
    mask = algo._get_ink_mask(qimg)

    modules = generate_smart_educational_paths(mask, scale=1.0, rtl=False)
    assert len(modules) >= 2, f"Expected at least 2 distinct modules + wires, got {len(modules)}"

    # Find main body modules (excluding the final wires)
    body_modules = [m for m in modules if not m.get("is_wires", False)]
    assert len(body_modules) >= 2, "Expected at least 2 main body modules (Arduino and Sensor)"

    # Check that Arduino and Sensor modules have distinct horizontal centers
    centers_x = [m["centroid"][0] for m in body_modules]
    assert max(centers_x) - min(centers_x) > 200, "Modules should have well-separated horizontal centers"

def test_educational_plan_generation_timing_and_travels(qapp):
    """Verifies plan generation, steady reveal timing, and in-air travel flights between modules."""
    qimg = make_test_schematic_qimage()
    algo = AlgorithmFactory.get_algorithm("Educational")
    
    duration = 6.0
    plan = algo.generate_plan(qimg, duration=duration, rtl=False)
    assert len(plan) > 0, "Plan should contain timed segments"

    # Verify timing monotonicity and bounds
    for i in range(len(plan)):
        assert plan[i]["start_time"] >= 0.0
        assert plan[i]["end_time"] <= duration + 0.05
        assert plan[i]["duration"] > 0.0
        if i > 0:
            assert plan[i]["start_time"] >= plan[i-1]["start_time"] - 1e-4

    # Verify in-air travel flights exist
    travel_segments = [seg for seg in plan if seg.get("type") == "travel"]
    assert len(travel_segments) > 0, "Educational flow must include prominent in-air travel flights"
    for trav in travel_segments:
        assert trav["width"] == 0.0
        assert trav["opacity"] == 0.0

def test_educational_direction_rtl_vs_ltr(qapp):
    """Verifies that in LTR the left component is drawn first, and in RTL the right component is drawn first."""
    qimg = make_test_schematic_qimage()
    algo = AlgorithmFactory.get_algorithm("Educational")

    plan_ltr = algo.generate_plan(qimg, duration=6.0, rtl=False)
    plan_rtl = algo.generate_plan(qimg, duration=6.0, rtl=True)

    # First stroke start X in LTR vs RTL
    first_stroke_ltr = next(s for s in plan_ltr if s.get("type") == "stroke")
    first_stroke_rtl = next(s for s in plan_rtl if s.get("type") == "stroke")

    ltr_start_x = first_stroke_ltr["points"][0].x()
    rtl_start_x = first_stroke_rtl["points"][0].x()

    assert ltr_start_x < 500, f"LTR should start on left Arduino, got x={ltr_start_x}"
    assert rtl_start_x > 600, f"RTL should start on right Sensor, got x={rtl_start_x}"
