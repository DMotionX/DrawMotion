# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later

import cv2
import numpy as np
import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from core.drawing_engine.algorithms.factory import AlgorithmFactory
from core.drawing_engine.algorithms.solid_reveal.algorithm import SolidRevealAlgorithm

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def make_test_multicomponent_qimage(w=1000, h=600):
    """
    Creates a synthetic multi-component image with two tall solid objects:
    - Component 1 (Left): x in [100, 400], y in [150, 500] (height=350px > 160px)
    - Component 2 (Right): x in [700, 950], y in [150, 450] (height=300px > 160px)
    On white canvas (255) with solid black ink (0).
    """
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    cv2.rectangle(canvas, (100, 150), (400, 500), (0, 0, 0), -1)
    cv2.rectangle(canvas, (700, 150), (950, 450), (0, 0, 0), -1)
    
    rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGBA)
    return QImage(rgba.data, w, h, w * 4, QImage.Format.Format_RGBA8888)

def test_solid_reveal_instantiation_and_fallback(qapp):
    algo = AlgorithmFactory.get_algorithm("Solid Reveal")
    assert isinstance(algo, SolidRevealAlgorithm)

    fallback_algo = AlgorithmFactory.get_algorithm("NonExistentStyleXYZ")
    assert isinstance(fallback_algo, SolidRevealAlgorithm)

def test_solid_reveal_transparent_image(qapp):
    algo = SolidRevealAlgorithm()
    transparent = QImage(200, 200, QImage.Format.Format_RGBA8888)
    transparent.fill(0)
    plan = algo.generate_plan(transparent, duration=5.0)
    assert plan == []

def test_solid_reveal_component_first_no_vertical_scan_slicing(qapp):
    """
    Verifies that tall objects (height > 160px) are drawn 100% completely as isolated components,
    permanently eliminating the horizontal slab vertical scan wipe (printer-like sweep).
    """
    qimg = make_test_multicomponent_qimage()
    algo = SolidRevealAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)
    assert len(plan) > 0

    strokes = [s for s in plan if s.get("type") == "stroke"]
    assert len(strokes) >= 2

    # In LTR, the left component (x in 100..400) must finish ALL its strokes
    # before the right component (x in 700..950) receives its first stroke.
    comp1_strokes = [s for s in strokes if s["points"][0].x() < 500]
    comp2_strokes = [s for s in strokes if s["points"][0].x() > 600]

    assert len(comp1_strokes) > 0, "Left component must have strokes"
    assert len(comp2_strokes) > 0, "Right component must have strokes"

    last_comp1_end = max(s["end_time"] for s in comp1_strokes)
    first_comp2_start = min(s["start_time"] for s in comp2_strokes)

    assert last_comp1_end <= first_comp2_start + 1e-4, (
        f"Component 1 must be completed (end={last_comp1_end:.2f}s) "
        f"before Component 2 starts (start={first_comp2_start:.2f}s)!"
    )

def test_solid_reveal_connected_wire_schematic_strict_piece_by_piece(qapp):
    """
    Verifies that when multiple objects are connected by a wire or cable (e.g. Laptop + Cable + Arduino + LED),
    they are NOT merged into one simultaneous drawing block. Each piece is drawn 100% completely before moving on!
    """
    w, h = 1200, 500
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    # Laptop on left (area > 8000)
    cv2.rectangle(canvas, (100, 100), (350, 400), (0, 0, 0), -1)
    # Cable touching laptop and touching arduino
    cv2.line(canvas, (350, 250), (600, 250), (0, 0, 0), 4)
    # Arduino on right (area > 8000)
    cv2.rectangle(canvas, (600, 100), (850, 400), (0, 0, 0), -1)
    rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGBA)
    qimg = QImage(rgba.data, w, h, w * 4, QImage.Format.Format_RGBA8888)

    algo = SolidRevealAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)
    strokes = [s for s in plan if s.get("type") == "stroke"]

    laptop_strokes = [s for s in strokes if s["points"][0].x() <= 360]
    arduino_strokes = [s for s in strokes if s["points"][0].x() >= 600]

    assert len(laptop_strokes) > 0, "Laptop must have strokes"
    assert len(arduino_strokes) > 0, "Arduino must have strokes"

    last_laptop_end = max(s["end_time"] for s in laptop_strokes)
    first_arduino_start = min(s["start_time"] for s in arduino_strokes)

    assert last_laptop_end <= first_arduino_start + 1e-4, (
        f"Laptop must be 100% completed (end={last_laptop_end:.2f}s) before Arduino starts (start={first_arduino_start:.2f}s)!"
    )

def test_solid_reveal_in_air_travel_flights(qapp):
    """
    Verifies that moving between disconnected objects emits explicit in-air travel flights
    with zero width and zero opacity, preventing phantom drag or line jumps.
    """
    qimg = make_test_multicomponent_qimage()
    algo = SolidRevealAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)

    travels = [s for s in plan if s.get("type") == "travel"]
    assert len(travels) > 0, "In-air travel flights must be emitted between components"

    for t in travels:
        assert t["width"] == 0.0, "In-air travels must have width=0.0"
        assert t["opacity"] == 0.0, "In-air travels must have opacity=0.0"
        assert len(t["points"]) == 2, "Travels must define origin and destination"

def test_solid_reveal_timeline_synchronization(qapp):
    """
    Verifies that the entire plan matches the requested duration with monotonic timestamps.
    """
    qimg = make_test_multicomponent_qimage()
    algo = SolidRevealAlgorithm()
    requested_duration = 10.0
    plan = algo.generate_plan(qimg, duration=requested_duration, rtl=False)

    assert len(plan) > 0
    assert plan[0]["start_time"] == pytest.approx(0.0, abs=1e-3)
    assert plan[-1]["end_time"] == pytest.approx(requested_duration, abs=1e-2)

    for i in range(1, len(plan)):
        assert plan[i]["start_time"] >= plan[i-1]["start_time"] - 1e-4
        assert plan[i]["end_time"] >= plan[i]["start_time"]
        assert plan[i]["duration"] > 0.0

def test_solid_reveal_direction_rtl_vs_ltr(qapp):
    """
    Verifies that in LTR mode the left component is drawn first, and in RTL mode the right component is drawn first.
    """
    qimg = make_test_multicomponent_qimage()
    algo = SolidRevealAlgorithm()

    plan_ltr = algo.generate_plan(qimg, duration=8.0, rtl=False)
    plan_rtl = algo.generate_plan(qimg, duration=8.0, rtl=True)

    first_ltr_stroke = next(s for s in plan_ltr if s.get("type") == "stroke")
    first_rtl_stroke = next(s for s in plan_rtl if s.get("type") == "stroke")

    assert first_ltr_stroke["points"][0].x() < 500, "LTR should start on left component"
    assert first_rtl_stroke["points"][0].x() > 600, "RTL should start on right component"

def test_solid_reveal_caching(qapp):
    """
    Verifies that repeated requests return cached deep copies without recomputation.
    """
    qimg = make_test_multicomponent_qimage()
    algo = SolidRevealAlgorithm()

    plan1 = algo.generate_plan(qimg, duration=6.0, rtl=False)
    plan2 = algo.generate_plan(qimg, duration=6.0, rtl=False)

    assert len(plan1) == len(plan2)
    assert plan1 is not plan2  # Deep copy verification
    assert plan1[0]["points"][0] == plan2[0]["points"][0]
