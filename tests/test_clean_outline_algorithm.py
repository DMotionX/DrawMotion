# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later

import cv2
import numpy as np
import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from core.drawing_engine.algorithms.factory import AlgorithmFactory
from core.drawing_engine.algorithms.clean_outline.algorithm import CleanOutlineAlgorithm

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def make_test_multicomponent_qimage(w=1000, h=600):
    """
    Creates a synthetic multi-component image with two tall solid objects:
    - Component 1 (Left): x in [100, 400], y in [150, 500]
    - Component 2 (Right): x in [700, 950], y in [150, 450]
    """
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    cv2.rectangle(canvas, (100, 150), (400, 500), (0, 0, 0), -1)
    cv2.rectangle(canvas, (700, 150), (950, 450), (0, 0, 0), -1)
    rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGBA)
    return QImage(rgba.data, w, h, w * 4, QImage.Format.Format_RGBA8888)

def make_connected_wire_qimage(w=1200, h=500):
    """
    Creates two standalone devices connected by a wire:
    - Laptop on left (area > 8000)
    - Thin cable touching both
    - Arduino on right (area > 8000)
    """
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)
    cv2.rectangle(canvas, (100, 100), (350, 400), (0, 0, 0), -1)
    cv2.line(canvas, (350, 250), (600, 250), (0, 0, 0), 4)
    cv2.rectangle(canvas, (600, 100), (850, 400), (0, 0, 0), -1)
    rgba = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGBA)
    return QImage(rgba.data, w, h, w * 4, QImage.Format.Format_RGBA8888)

def test_clean_outline_instantiation(qapp):
    algo = AlgorithmFactory.get_algorithm("Clean Outline")
    assert isinstance(algo, CleanOutlineAlgorithm)

def test_clean_outline_transparent_image(qapp):
    algo = CleanOutlineAlgorithm()
    transparent = QImage(200, 200, QImage.Format.Format_RGBA8888)
    transparent.fill(0)
    plan = algo.generate_plan(transparent, duration=5.0)
    assert plan == []

def test_clean_outline_piece_by_piece_strict_sequence(qapp):
    """
    Verifies that the left object finishes 100% completely before the hand
    lifts and moves to draw the right object.
    """
    qimg = make_test_multicomponent_qimage()
    algo = CleanOutlineAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)
    assert len(plan) > 0

    strokes = [s for s in plan if s.get("type") == "stroke"]
    assert len(strokes) >= 2

    comp1_strokes = [s for s in strokes if s["points"][0].x() < 500]
    comp2_strokes = [s for s in strokes if s["points"][0].x() > 600]

    assert len(comp1_strokes) > 0, "Component 1 must have strokes"
    assert len(comp2_strokes) > 0, "Component 2 must have strokes"

    comp1_end = max(s["end_time"] for s in comp1_strokes)
    comp2_start = min(s["start_time"] for s in comp2_strokes)

    assert comp1_end <= comp2_start + 1e-4, (
        f"Clean Outline: Component 1 must complete (end={comp1_end:.2f}s) "
        f"before Component 2 starts (start={comp2_start:.2f}s)!"
    )

def test_clean_outline_connected_wire_keeps_pieces_isolated(qapp):
    """
    Verifies that when two large devices are connected by a wire,
    they are drawn piece-by-piece rather than interleaved.
    """
    qimg = make_connected_wire_qimage()
    algo = CleanOutlineAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)
    strokes = [s for s in plan if s.get("type") == "stroke"]

    laptop_strokes = [s for s in strokes if s["points"][0].x() <= 360]
    arduino_strokes = [s for s in strokes if s["points"][0].x() >= 600]

    assert len(laptop_strokes) > 0, "Laptop must have strokes"
    assert len(arduino_strokes) > 0, "Arduino must have strokes"

    laptop_end = max(s["end_time"] for s in laptop_strokes)
    arduino_start = min(s["start_time"] for s in arduino_strokes)

    assert laptop_end <= arduino_start + 1e-4, (
        f"Clean Outline: Laptop must finish (end={laptop_end:.2f}s) "
        f"before Arduino starts (start={arduino_start:.2f}s)!"
    )

def test_clean_outline_in_air_travel_flights(qapp):
    """
    Verifies that clean in-air travel flights (width=0, opacity=0) occur between pieces.
    """
    qimg = make_test_multicomponent_qimage()
    algo = CleanOutlineAlgorithm()
    plan = algo.generate_plan(qimg, duration=8.0, rtl=False)

    travels = [s for s in plan if s.get("type") == "travel"]
    assert len(travels) > 0, "Clean outline must have in-air travel flights between pieces"
    for trav in travels:
        assert trav["width"] == 0.0
        assert trav["opacity"] == 0.0

def test_clean_outline_rtl_reading_progression(qapp):
    """
    Verifies that RTL mode draws from right to left (Component 2 before Component 1).
    """
    qimg = make_test_multicomponent_qimage()
    algo = CleanOutlineAlgorithm()
    plan_rtl = algo.generate_plan(qimg, duration=8.0, rtl=True)
    strokes_rtl = [s for s in plan_rtl if s.get("type") == "stroke"]

    comp1_strokes = [s for s in strokes_rtl if s["points"][0].x() < 500]
    comp2_strokes = [s for s in strokes_rtl if s["points"][0].x() > 600]

    comp2_end = max(s["end_time"] for s in comp2_strokes)
    comp1_start = min(s["start_time"] for s in comp1_strokes)

    assert comp2_end <= comp1_start + 1e-4, (
        f"RTL Clean Outline: Component 2 must complete (end={comp2_end:.2f}s) "
        f"before Component 1 starts (start={comp1_start:.2f}s)!"
    )

def test_clean_outline_exact_timeline_duration(qapp):
    """
    Verifies that total timeline starts at 0.0 and ends exactly at duration with zero drift.
    """
    qimg = make_test_multicomponent_qimage()
    algo = CleanOutlineAlgorithm()
    target_dur = 7.5
    plan = algo.generate_plan(qimg, duration=target_dur)

    assert len(plan) > 0
    assert abs(plan[0]["start_time"] - 0.0) < 1e-5
    assert abs(plan[-1]["end_time"] - target_dur) < 1e-4
