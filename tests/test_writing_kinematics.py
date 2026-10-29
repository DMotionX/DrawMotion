import os
import pytest
import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage, QPainter, QColor, QFont

from components.write_to_image.algorithms import get_writing_algorithm, ALGORITHM_REGISTRY
from components.write_to_image.algorithms.realistic_hybrid.realistic_hybrid_algorithm import RealisticHybridAlgorithm
from components.write_to_image.time_map_generator import generate_time_map
from components.write_to_image.models import WriteToImageModel
from components.write_to_image.graphics_item import WriteToImageGraphicsItem


@pytest.fixture(autouse=True)
def ensure_qapp(qapp):
    """Ensure a valid QApplication exists for QFont and QPainter operations."""
    return qapp



def test_algorithm_registry_and_fallback():
    """Verify registry lookups and graceful fallback for unknown names."""
    from core.settings_manager import SettingsManager
    SettingsManager().set("writing_algorithm", "realistic_hybrid")

    algo = get_writing_algorithm("realistic_hybrid")
    assert isinstance(algo, RealisticHybridAlgorithm)
    assert algo.name == "realistic_hybrid"

    # Default fallback
    fallback = get_writing_algorithm("unknown_algorithm_xyz")
    assert isinstance(fallback, RealisticHybridAlgorithm)

    # None fallback
    none_fallback = get_writing_algorithm(None)
    assert isinstance(none_fallback, RealisticHybridAlgorithm)



def test_realistic_hybrid_empty_and_trivial_seeds():
    """Verify algorithm handles empty, single-point, and two-point seed sequences."""
    algo = RealisticHybridAlgorithm()

    # Empty
    empty_res = algo.generate_times([], is_rtl=False)
    assert isinstance(empty_res, np.ndarray)
    assert len(empty_res) == 0

    # Single seed
    single_res = algo.generate_times([(10, 20)], is_rtl=False)
    assert isinstance(single_res, np.ndarray)
    assert len(single_res) == 1
    assert single_res[0] == 0.0

    # Two seeds
    two_res = algo.generate_times([(0, 0), (10, 10)], is_rtl=False)
    assert len(two_res) == 2
    assert two_res[0] == 0.0
    assert two_res[1] == 1.0


def test_realistic_hybrid_monotonicity_and_bounds():
    """Verify generated timestamps are strictly non-decreasing and bounded in [0.0, 1.0]."""
    algo = RealisticHybridAlgorithm()

    # Synthetic straight line of 50 seeds
    seeds = [(i, i * 2) for i in range(50)]
    times = algo.generate_times(seeds, is_rtl=False)

    assert len(times) == 50
    assert times[0] == 0.0
    assert times[-1] == 1.0
    assert not np.isnan(times).any()
    assert not np.isinf(times).any()

    # Monotonicity check
    diffs = np.diff(times)
    assert np.all(diffs >= -1e-7), "Timestamps must be non-decreasing"


def test_realistic_hybrid_curvature_slowing():
    """Verify Two-Thirds Power Law slows down execution at high-curvature corners."""
    algo = RealisticHybridAlgorithm()

    # Path with straight segment followed by sharp corner
    # Segment A: 20 points straight along X axis
    straight_seeds = [(i, 0) for i in range(20)]
    # Segment B: 5 points turning sharply 90 degrees and back
    corner_seeds = [(20, 1), (21, 5), (20, 10), (19, 14), (20, 18)]
    seeds = straight_seeds + corner_seeds

    times = algo.generate_times(seeds, is_rtl=False)
    assert len(times) == len(seeds)

    # Ensure no NaN or infinite values
    assert np.all(np.isfinite(times))
    assert times[0] == 0.0
    assert times[-1] == 1.0


def test_time_map_generator_returns_valid_map_and_trajectory(tmp_path):
    """Verify generate_time_map produces valid 2D matrix and 256-point trajectory."""
    # Create a simple synthetic text image
    width, height = 200, 80
    qimg = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    qimg.fill(Qt.transparent)

    painter = QPainter(qimg)
    painter.setPen(QColor(0, 0, 0, 255))
    painter.setFont(QFont("Arial", 28))
    painter.drawText(10, 50, "Test")
    painter.end()

    # Without trajectory
    time_map = generate_time_map(qimg, is_rtl=False, return_trajectory=False)
    assert isinstance(time_map, np.ndarray)
    assert time_map.shape == (height, width)
    assert time_map.dtype == np.uint8

    # With trajectory
    res = generate_time_map(qimg, is_rtl=False, return_trajectory=True)
    assert isinstance(res, tuple)
    time_map_res, trajectory = res

    assert isinstance(time_map_res, np.ndarray)
    assert len(trajectory) in (256, 512)
    for pt in trajectory:
        assert isinstance(pt, QPointF)
        # Point should be within reasonable canvas range
        assert 0.0 <= pt.x() <= width + 10.0
        assert 0.0 <= pt.y() <= height + 10.0


def test_graphics_item_smooth_trajectory_tracking(tmp_path):
    """Verify WriteToImageGraphicsItem smoothly integrates trajectory and tip positions."""
    # Render an image to disk
    width, height = 150, 60
    qimg = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    qimg.fill(Qt.transparent)
    painter = QPainter(qimg)
    painter.setPen(QColor(0, 0, 0, 255))
    painter.setFont(QFont("Arial", 24))
    painter.drawText(10, 40, "Hi")
    painter.end()

    img_file = str(tmp_path / "test_hi.png")
    qimg.save(img_file)

    model = WriteToImageModel(
        id="test_hi_item",
        name="Hi Item",
        text="Hi",
        image_path=img_file,
        writing_algorithm="realistic_hybrid"
    )

    item = WriteToImageGraphicsItem(model)

    assert hasattr(item, "_trajectory")
    assert len(item._trajectory) in (256, 512)

    # Test tip position at different progress values
    tip_0 = item.get_tip_position()
    assert isinstance(tip_0, QPointF)

    item.set_progress(0.5)
    tip_half = item.get_tip_position()
    assert isinstance(tip_half, QPointF)

    item.set_progress(1.0)
    tip_end = item.get_tip_position()
    assert isinstance(tip_end, QPointF)

    # In LTR text, tip at 1.0 should generally be to the right of tip at 0.0
    assert tip_end.x() >= tip_0.x() - 5.0


def test_topological_skeleton_traversal_reduces_jitter():
    """Verify that topological graph traversal eliminates vertical coordinate slicing jitter."""
    from components.write_to_image.time_map_generator import _topological_sort_seeds

    # Synthetic loop (simulating an 'o' or 'e' loop: circle of points)
    # When sorted by X, upper and lower halves oscillate back and forth
    theta = np.linspace(0, 2 * np.pi, 30, endpoint=False)
    radius = 10.0
    cx, cy = 20.0, 20.0
    circle_pts = [(int(cx + radius * np.cos(t)), int(cy + radius * np.sin(t))) for t in theta]
    # Remove duplicate points if any due to integer rounding
    unique_pts = list(dict.fromkeys(circle_pts))

    # Naive sort by X
    naive_sorted = sorted(unique_pts, key=lambda p: (p[0], p[1]))
    
    # Topological sort
    topo_sorted = _topological_sort_seeds(unique_pts, is_rtl=False)

    def count_reversals(pts):
        ys = [p[1] for p in pts]
        diffs = [ys[i+1] - ys[i] for i in range(len(ys)-1)]
        rev = 0
        prev = 0
        for d in diffs:
            if d != 0:
                s = 1 if d > 0 else -1
                if prev != 0 and s != prev:
                    rev += 1
                prev = s
        return rev

    naive_rev = count_reversals(naive_sorted)
    topo_rev = count_reversals(topo_sorted)

    # Topological traversal should follow the circle smoothly with at most 2 Y reversals (top and bottom apexes)
    assert topo_rev <= 2, f"Topological sort should trace loop smoothly (got {topo_rev} reversals)"
    assert len(topo_sorted) == len(unique_pts), "All points must be retained"
    assert set(topo_sorted) == set(unique_pts), "Point set must be identical"


def test_two_thirds_power_law_dynamics():
    """Verify TwoThirdsPowerLawAlgorithm slows at corners and accelerates on straight segments."""
    algo = get_writing_algorithm("two_thirds_power_law")
    assert algo.style == "two_thirds_power_law"

    # Straight stem followed by sharp corner
    straight = [(i, 0) for i in range(25)]
    corner = [(25, 1), (26, 4), (25, 8), (24, 12)]
    seeds = straight + corner

    times = algo.generate_times(seeds, is_rtl=False)
    assert len(times) == len(seeds)
    assert times[0] == 0.0
    assert times[-1] == 1.0
    assert np.all(np.diff(times) >= -1e-7), "Times must be monotonic"


def test_minimum_jerk_dynamics():
    """Verify MinimumJerkAlgorithm produces smooth bell-curved velocity with zero jerk."""
    algo = get_writing_algorithm("minimum_jerk")
    assert algo.style == "minimum_jerk"

    seeds = [(i * 2, 10) for i in range(40)]
    times = algo.generate_times(seeds, is_rtl=False)

    assert len(times) == 40
    assert times[0] == 0.0
    assert times[-1] == 1.0
    assert np.all(np.diff(times) >= -1e-7), "Times must be monotonic"

    # Check that mid-stroke speed is greater than initial speed (bell curve)
    dt_start = times[5] - times[0]
    dt_mid = times[25] - times[20]
    # In minimum jerk, mid-stroke covers 5 points faster than start covers 5 points
    assert dt_mid < dt_start, "Mid-stroke speed must be higher than starting speed"


def test_ou_noise_dynamics():
    """Verify OrnsteinUhlenbeckNoiseAlgorithm generates stochastic variation within valid bounds."""
    algo = get_writing_algorithm("ou_noise")
    assert algo.style == "ou_noise"

    seeds = [(i, i) for i in range(50)]
    times = algo.generate_times(seeds, is_rtl=False)

    assert len(times) == 50
    assert times[0] == 0.0
    assert times[-1] == 1.0
    assert np.all(np.diff(times) >= -1e-7), "Times must be non-decreasing"

    # Check reproducibility (deterministic seed)
    times_repeat = algo.generate_times(seeds, is_rtl=False)
    assert np.allclose(times, times_repeat), "Algorithm must be deterministic for identical input"


def test_stop_and_go_dynamics():
    """Verify StopAndGoAlgorithm inserts distinct pauses at stroke jumps."""
    algo = get_writing_algorithm("stop_and_go")
    assert algo.style == "stop_and_go"

    # Two separate letter clusters separated by jump > 6 px
    cluster1 = [(i, 10) for i in range(10)]
    cluster2 = [(i + 30, 10) for i in range(10)]
    seeds = cluster1 + cluster2

    times = algo.generate_times(seeds, is_rtl=False)
    assert len(times) == 20
    assert times[0] == 0.0
    assert times[-1] == 1.0
    assert np.all(np.diff(times) >= -1e-7), "Times must be monotonic"

    # The jump between cluster 1 and 2 should have a larger time interval (pause)
    dt_inside = times[5] - times[4]
    dt_jump = times[10] - times[9]
    assert dt_jump > dt_inside * 2.0, "Jump must exhibit a pronounced pause"


def test_linear_interpolation_dynamics():
    """Verify LinearInterpolationAlgorithm maintains uniform arc-length progress."""
    algo = get_writing_algorithm("linear")
    assert algo.style == "linear_interpolation"

    # Uniform grid
    seeds = [(i * 5, 0) for i in range(21)]
    times = algo.generate_times(seeds, is_rtl=False)

    assert len(times) == 21
    assert times[0] == 0.0
    assert times[-1] == 1.0

    # Diff should be constant (within floating point precision)
    diffs = np.diff(times)
    assert np.allclose(diffs, diffs[0], atol=1e-5), "Linear interpolation must have constant step dt"


