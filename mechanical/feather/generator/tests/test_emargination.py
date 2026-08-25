"""G6 tests — emargination."""

import json
from pathlib import Path

import pytest

from feathergen.emargination import apply_emargination
from feathergen.geometry import distance, is_simple_polygon
from feathergen.rachis import compute_rachis
from feathergen.vane import Vane, compute_vane, vane_width_at

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)


def row(feather_id):
    return next(f for f in FEATHERS["feathers"] if f["id"] == feather_id)


def build(feather_id, **kw):
    r = row(feather_id)
    return compute_vane(r, compute_rachis(r), **kw)


def build_emarg(feather_id, **kw):
    return apply_emargination(build(feather_id), **kw)


# --- absent by default ------------------------------------------------------


def test_false_leaves_outline_unchanged():
    v = build("P4")
    v2 = apply_emargination(v, emargination=False)
    assert v2.outline == v.outline
    assert v2.outer_rail == v.outer_rail


# --- present when true ------------------------------------------------------


def test_true_changes_outline():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True)
    assert v2.outline != v.outline


def test_true_changes_only_outer_rail():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True)
    assert v2.outer_rail != v.outer_rail
    assert v2.inner_rail == v.inner_rail


# --- notch on the outer vane near the tip -----------------------------------


def _dist_point_polyline(p, pts):
    """Min distance from point p to a polyline (nearest segment)."""
    def _seg(q, r):
        ax, ay = q
        bx, by = r
        dx, dy = bx - ax, by - ay
        ll = dx * dx + dy * dy
        if ll == 0:
            return distance(p, q)
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / ll))
        return distance(p, (ax + t * dx, ay + t * dy))
    return min(_seg(a, b) for a, b in zip(pts, pts[1:]))


def _notch_outer_points(v2, fid="P4"):
    """The Bézier points that form the notch (points not on the original rail)."""
    orig = compute_vane(row(fid), compute_rachis(row(fid))).outer_rail
    return [p for p in v2.outer_rail if p not in orig]


def test_notch_narrows_outer_vane():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True)
    # the deepest notch point is closer to the inner rail than the plain vane
    # width at the notch midpoint
    w_plain = vane_width_at(0.78, v)
    w_notched = min(_dist_point_polyline(p, v2.inner_rail) for p in _notch_outer_points(v2, "P4"))
    assert w_notched < w_plain


def test_notch_is_near_tip_not_at_base():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True)
    # width near the base is unaffected
    assert vane_width_at(0.2, v2) == pytest.approx(vane_width_at(0.2, v), rel=1e-6)


def test_notch_outer_side_inward():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True)
    d_plain = vane_width_at(0.78, v)
    d_notched = min(_dist_point_polyline(p, v2.inner_rail) for p in _notch_outer_points(v2, "P4"))
    assert d_notched < d_plain


# --- single closed loop -----------------------------------------------------


def test_outline_closed():
    v2 = build_emarg("P4")
    assert v2.outline[0] == v2.outline[-1]


def test_outline_simple_no_fragmentation():
    for fid in ("P1", "P2", "P3", "P4", "P5"):
        v2 = build_emarg(fid)
        assert is_simple_polygon(v2.outline), f"{fid} self-intersects"


# --- knobs / errors ---------------------------------------------------------


def test_custom_span():
    v = build("P4")
    v2 = apply_emargination(v, emargination=True, span=(0.7, 0.9))
    assert v2.outline != v.outline


def test_custom_depth():
    v = build("P4")
    shallow = apply_emargination(v, emargination=True, depth=0.2)
    deep = apply_emargination(v, emargination=True, depth=0.6)
    # deeper notch pulls the outer rail farther inward → narrower vane
    w_shallow = min(_dist_point_polyline(p, shallow.inner_rail) for p in _notch_outer_points(shallow, "P4"))
    w_deep = min(_dist_point_polyline(p, deep.inner_rail) for p in _notch_outer_points(deep, "P4"))
    assert w_deep < w_shallow


def test_bad_span_raises():
    v = build("P4")
    with pytest.raises(ValueError, match="span"):
        apply_emargination(v, emargination=True, span=(0.9, 0.5))


def test_bad_depth_raises():
    v = build("P4")
    with pytest.raises(ValueError, match="depth"):
        apply_emargination(v, emargination=True, depth=1.5)


# --- data set sweep ---------------------------------------------------------


def test_emarginated_feathers_only():
    # P1-P5 have emargination=true in feathers.json; nothing else
    em = [f["id"] for f in FEATHERS["feathers"] if f["emargination"]]
    assert em == ["P1", "P2", "P3", "P4", "P5"]


def test_sweep_true_feathers_stay_simple():
    for f in FEATHERS["feathers"]:
        if f["emargination"]:
            v2 = build_emarg(f["id"])
            assert v2.outline[0] == v2.outline[-1]
            assert is_simple_polygon(v2.outline), f"{f['id']} self-intersects"


def test_sweep_false_feathers_unchanged():
    # applying the flag with emargination=False never changes an outline
    for f in FEATHERS["feathers"]:
        if not f["emargination"]:
            v = build(f["id"])
            assert apply_emargination(v, emargination=False).outline == v.outline


def test_returns_vane():
    assert isinstance(build_emarg("P4"), Vane)
