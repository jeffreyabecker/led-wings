"""G2 tests — core listable geometry primitives."""

import math

import pytest

from feathergen.geometry import (
    bbox,
    distance,
    point_at_arc,
    polyline_length,
    reflect_vertical,
    resample,
    rotate,
    sample_bezier,
    translate,
    unit_tangent_at_arc,
)


# --- distance / length -----------------------------------------------------


def test_distance_simple():
    assert distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)


def test_distance_zero():
    assert distance((1.0, 1.0), (1.0, 1.0)) == 0.0


def test_polyline_length_straight():
    pts = [(0.0, 0.0), (10.0, 0.0)]
    assert polyline_length(pts) == pytest.approx(10.0)


def test_polyline_length_polyline():
    pts = [(0.0, 0.0), (3.0, 4.0), (3.0, 9.0)]
    assert polyline_length(pts) == pytest.approx(5.0 + 5.0)


def test_polyline_length_single_point():
    assert polyline_length([(1.0, 2.0)]) == 0.0


def test_polyline_length_empty():
    assert polyline_length([]) == 0.0


# --- bbox -------------------------------------------------------------------


def test_bbox_basic():
    pts = [(1.0, -2.0), (5.0, 3.0), (-1.0, 0.5)]
    assert bbox(pts) == (-1.0, -2.0, 5.0, 3.0)


def test_bbox_single_point():
    assert bbox([(2.0, 3.0)]) == (2.0, 3.0, 2.0, 3.0)


def test_bbox_empty_raises():
    with pytest.raises(ValueError):
        bbox([])


# --- transforms -------------------------------------------------------------


def test_translate_moves_all_points():
    pts = [(0.0, 0.0), (1.0, 1.0)]
    assert translate(pts, 2.0, -1.0) == [(2.0, -1.0), (3.0, 0.0)]


def test_rotate_90_ccw():
    pts = [(1.0, 0.0)]
    out = rotate(pts, 90.0)
    assert out[0][0] == pytest.approx(0.0)
    assert out[0][1] == pytest.approx(1.0)


def test_rotate_about_origin_keeps_origin():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    out = rotate(pts, 45.0)
    assert out[0] == (0.0, 0.0)


def test_rotate_preserves_lengths():
    pts = [(0.0, 0.0), (3.0, 4.0), (1.0, 8.0)]
    out = rotate(pts, 33.0)
    assert polyline_length(out) == pytest.approx(polyline_length(pts))


def test_reflect_vertical_about_zero():
    pts = [(1.0, 2.0), (-3.0, 4.0)]
    assert reflect_vertical(pts) == [(-1.0, 2.0), (3.0, 4.0)]


def test_reflect_vertical_about_axis():
    pts = [(1.0, 2.0)]
    assert reflect_vertical(pts, axis_x=2.0) == [(3.0, 2.0)]


def test_reflect_vertical_is_involution():
    pts = [(1.0, 2.0), (5.0, -3.0)]
    assert reflect_vertical(reflect_vertical(pts)) == pts


# --- bézier ----------------------------------------------------------------


def test_bezier_quadratic_endpoints():
    ctrl = [(0.0, 0.0), (5.0, 10.0), (10.0, 0.0)]
    pts = sample_bezier(ctrl, 10)
    assert pts[0] == (0.0, 0.0)
    assert pts[-1] == (10.0, 0.0)
    assert len(pts) == 11


def test_bezier_quadratic_midpoint():
    # B(0.5) = (P0 + 2*P1 + P2) / 4 for a quadratic Bézier
    ctrl = [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0)]
    pts = sample_bezier(ctrl, 2)
    mid = pts[1]
    assert mid[0] == pytest.approx(2.5)
    assert mid[1] == pytest.approx(7.5)


def test_bezier_cubic_endpoints():
    ctrl = [(0.0, 0.0), (0.0, 5.0), (10.0, 5.0), (10.0, 10.0)]
    pts = sample_bezier(ctrl, 8)
    assert pts[0] == (0.0, 0.0)
    assert pts[-1] == (10.0, 10.0)
    assert len(pts) == 9


def test_bezier_bad_control_count():
    with pytest.raises(ValueError):
        sample_bezier([(0.0, 0.0), (1.0, 1.0)], 4)


# --- resample --------------------------------------------------------------


def test_resample_evenly_spaced_on_straight_line():
    pts = [(0.0, 0.0), (10.0, 0.0)]
    out = resample(pts, 2.0)
    assert out[0] == (0.0, 0.0)
    assert out[-1] == (10.0, 0.0)
    xs = [p[0] for p in out]
    assert xs == pytest.approx([0.0, 2.0, 4.0, 6.0, 8.0, 10.0])


def test_resample_across_vertices():
    # bent polyline: (0,0)->(3,0)->(3,4); spacing 2.5
    pts = [(0.0, 0.0), (3.0, 0.0), (3.0, 4.0)]
    out = resample(pts, 2.5)
    assert out[0] == (0.0, 0.0)
    assert out[-1] == (3.0, 4.0)
    # second point at 2.5 along first segment
    assert out[1][0] == pytest.approx(2.5)
    assert out[1][1] == pytest.approx(0.0)


def test_resample_spacing_larger_than_length():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    out = resample(pts, 5.0)
    assert out == [(0.0, 0.0), (1.0, 0.0)]


def test_resample_invalid_spacing():
    with pytest.raises(ValueError):
        resample([(0.0, 0.0), (1.0, 0.0)], 0.0)


def test_resample_single_point():
    assert resample([(3.0, 4.0)], 1.0) == [(3.0, 4.0)]


# --- point_at_arc / unit_tangent_at_arc ------------------------------------


def test_point_at_arc_start():
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
    assert point_at_arc(pts, 0.0) == (0.0, 0.0)


def test_point_at_arc_end():
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
    assert point_at_arc(pts, 15.0) == (10.0, 5.0)


def test_point_at_arc_mid_segment():
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
    assert point_at_arc(pts, 5.0) == (5.0, 0.0)


def test_point_at_arc_across_vertex():
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)]
    # 12 cm along: 10 on first segment + 2 up the second
    assert point_at_arc(pts, 12.0) == (10.0, 2.0)


def test_point_at_arc_clamps():
    pts = [(0.0, 0.0), (10.0, 0.0)]
    assert point_at_arc(pts, -5.0) == (0.0, 0.0)
    assert point_at_arc(pts, 999.0) == (10.0, 0.0)


def test_point_at_arc_empty_raises():
    with pytest.raises(ValueError):
        point_at_arc([], 1.0)


def test_unit_tangent_along_y():
    pts = [(0.0, 0.0), (0.0, 10.0)]
    tx, ty = unit_tangent_at_arc(pts, 5.0)
    assert (tx, ty) == (0.0, 1.0)


def test_unit_tangent_along_x():
    pts = [(0.0, 0.0), (10.0, 0.0)]
    tx, ty = unit_tangent_at_arc(pts, 5.0)
    assert (tx, ty) == (1.0, 0.0)


def test_unit_tangent_at_start():
    pts = [(0.0, 0.0), (0.0, 10.0)]
    assert unit_tangent_at_arc(pts, 0.0) == (0.0, 1.0)


def test_unit_tangent_at_end():
    pts = [(0.0, 0.0), (0.0, 10.0)]
    assert unit_tangent_at_arc(pts, 10.0) == (0.0, 1.0)


def test_unit_tangent_degenerate():
    assert unit_tangent_at_arc([(1.0, 1.0)], 0.0) == (0.0, 1.0)
