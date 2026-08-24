"""G3 tests — compute_rachis."""

import json
from pathlib import Path

import pytest

from feathergen.geometry import distance, polyline_length
from feathergen.rachis import (
    DEFAULT_LED_PITCH_CM,
    CURVATURE_BOW_FRACTION,
    Rachis,
    compute_rachis,
    max_lateral_offset,
)

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)


# --- basic construction -----------------------------------------------------


def test_rachis_returns_rachis():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med-high"})
    assert isinstance(r, Rachis)
    assert r.total == 75.0
    assert r.curvature == "med-high"


def test_rachis_polyline_base_to_tip():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med-high"})
    assert r.polyline[0] == (0.0, 0.0)
    assert r.polyline[-1][0] == pytest.approx(0.0)
    assert r.polyline[-1][1] == pytest.approx(75.0)


def test_rachis_length_equals_total_within_tolerance():
    # Bowed arc is slightly longer than the chord (total); allow 1 %.
    for curvature in CURVATURE_BOW_FRACTION:
        r = compute_rachis({"total_cm": 75.0, "curvature": curvature})
        assert r.length == pytest.approx(75.0, rel=0.01)


def test_straight_endpoint_to_endpoint_equals_total():
    r = compute_rachis({"total_cm": 75.0, "curvature": "straight"})
    assert distance(r.polyline[0], r.polyline[-1]) == pytest.approx(75.0)


def test_straight_has_no_bend():
    r = compute_rachis({"total_cm": 75.0, "curvature": "straight"})
    assert max_lateral_offset(r) == pytest.approx(0.0, abs=1e-9)


def test_curvature_changes_max_lateral_offset():
    low = compute_rachis({"total_cm": 75.0, "curvature": "low"})
    high = compute_rachis({"total_cm": 75.0, "curvature": "high"})
    assert max_lateral_offset(low) < max_lateral_offset(high)


def test_curvature_ordering():
    offsets = {
        c: max_lateral_offset(compute_rachis({"total_cm": 75.0, "curvature": c}))
        for c in ("low", "med-low", "med", "med-high", "high")
    }
    assert offsets["low"] < offsets["med-low"] < offsets["med"] < offsets["med-high"] < offsets["high"]


def test_bow_cm_scales_with_total():
    r1 = compute_rachis({"total_cm": 50.0, "curvature": "high"})
    r2 = compute_rachis({"total_cm": 100.0, "curvature": "high"})
    assert r2.bow_cm == pytest.approx(2.0 * r1.bow_cm)


# --- bend points ------------------------------------------------------------


def test_bend_points_start_at_base():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med"})
    assert r.bend_points[0] == (0.0, 0.0)


def test_bend_points_end_at_tip():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med"})
    assert distance(r.bend_points[-1], (0.0, 75.0)) == pytest.approx(0.0, abs=1e-6)


def _dist_point_segment(p, a, b):
    """Distance from point p to segment a-b."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return distance(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    return distance(p, (ax + t * dx, ay + t * dy))


def test_bend_points_fall_on_rachis():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med-high"})
    for bp in r.bend_points:
        # the bend point must lie on some segment of the rachis polyline
        d = min(_dist_point_segment(bp, a, b) for a, b in zip(r.polyline, r.polyline[1:]))
        assert d < 1e-6


def test_bend_points_evenly_spaced():
    r = compute_rachis({"total_cm": 75.0, "curvature": "straight"})
    gaps = [
        distance(a, b)
        for a, b in zip(r.bend_points, r.bend_points[1:])
    ]
    # every gap except the final (short) one is the LED pitch
    assert gaps[:-1] == pytest.approx([DEFAULT_LED_PITCH_CM] * (len(gaps) - 1))


def test_bend_pitch_custom():
    r = compute_rachis({"total_cm": 75.0, "curvature": "straight"}, bend_pitch=5.0)
    gaps = [distance(a, b) for a, b in zip(r.bend_points, r.bend_points[1:])]
    assert gaps[:-1] == pytest.approx([5.0] * (len(gaps) - 1))


def test_bend_point_count_reasonable():
    r = compute_rachis({"total_cm": 75.0, "curvature": "med"})
    # ~75 cm / 1.04 cm pitch => ~73 gaps, 74 points
    assert 70 <= len(r.bend_points) <= 78


# --- errors -----------------------------------------------------------------


def test_unknown_curvature_raises():
    with pytest.raises(ValueError, match="unknown curvature"):
        compute_rachis({"total_cm": 75.0, "curvature": "extreme"})


def test_invalid_total_raises():
    with pytest.raises(ValueError, match="total_cm"):
        compute_rachis({"total_cm": 0.0, "curvature": "low"})


def test_invalid_bend_pitch_raises():
    with pytest.raises(ValueError, match="bend_pitch"):
        compute_rachis({"total_cm": 75.0, "curvature": "low"}, bend_pitch=0.0)


def test_missing_keys_raises():
    with pytest.raises(KeyError):
        compute_rachis({"curvature": "low"})


# --- data set sweep ---------------------------------------------------------


def test_all_feathers_compute():
    # every feathers.json row must produce a rachis with valid length
    for f in FEATHERS["feathers"]:
        r = compute_rachis(f)
        assert r.length == pytest.approx(f["total_cm"], rel=0.01)
        assert len(r.bend_points) >= 2


def test_p4_row():
    row = next(f for f in FEATHERS["feathers"] if f["id"] == "P4")
    r = compute_rachis(row)
    assert r.total == 75.0
    assert r.curvature == "med-high"
    assert polyline_length(r.polyline) == pytest.approx(75.0, rel=0.01)
