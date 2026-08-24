"""G5 tests — tip styles."""

import json
from pathlib import Path

import pytest

from feathergen.geometry import is_simple_polygon
from feathergen.rachis import compute_rachis
from feathergen.tips import (
    TIP_RADIUS_FRACTION,
    TIP_STYLES,
    apply_tip,
    tip_cap_width,
    tip_radius,
)
from feathergen.vane import compute_vane

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)


def row(feather_id):
    return next(f for f in FEATHERS["feathers"] if f["id"] == feather_id)


def build(feather_id, tip, **kw):
    r = row(feather_id)
    v = compute_vane(r, compute_rachis(r), **kw)
    return apply_tip(v, tip)


def build_pointed(feather_id, **kw):
    r = row(feather_id)
    return compute_vane(r, compute_rachis(r), **kw)


def cap_width(vane):
    # vane length = outline y-extent (base y=0..tip y=total) minus quill
    ys = [p[1] for p in vane.outline]
    total = max(ys)
    vane_cm = total - vane.quill_cm
    return tip_cap_width(vane, vane_cm)


# --- styles are distinct ----------------------------------------------------


def test_styles_exist():
    assert set(TIP_STYLES) == {"pointed", "hooked", "rounded-point", "rounded", "very-rounded"}


def test_each_style_distinct_outline():
    outlines = {tip: build("S6", tip).outline for tip in TIP_STYLES}
    names = list(TIP_STYLES)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert outlines[a] != outlines[b], f"{a} == {b}"


def test_pointed_unchanged():
    v0 = build_pointed("S6")
    v1 = apply_tip(v0, "pointed")
    assert v1.outline == v0.outline


# --- validity (no self-intersection) ---------------------------------------


@pytest.mark.parametrize("tip", TIP_STYLES)
def test_tip_outline_is_simple(tip):
    for fid in ("S6", "P1", "T2", "GC1", "MG1"):
        v = build(fid, tip)
        assert is_simple_polygon(v.outline), f"{fid} {tip} self-intersects"


# --- pointed = sharp tip ----------------------------------------------------


def test_pointed_tip_is_sharp():
    v = build_pointed("S6")
    # pointed tip converges to a point at the very top; width in the top 5%
    # of the vane is tiny (well below any cap radius)
    assert cap_width(v) < 0.05 * v.effective_max_width


# --- rounded family: blunter ordering --------------------------------------


def test_radius_fraction_ordering():
    assert TIP_RADIUS_FRACTION["rounded-point"] < TIP_RADIUS_FRACTION["rounded"]
    assert TIP_RADIUS_FRACTION["rounded"] < TIP_RADIUS_FRACTION["very-rounded"]
    assert TIP_RADIUS_FRACTION["pointed"] == 0.0


def test_very_rounded_blunter_than_rounded():
    v = build_pointed("S6")
    w_rounded = cap_width(apply_tip(v, "rounded"))
    w_very = cap_width(apply_tip(v, "very-rounded"))
    w_pointed = cap_width(v)
    assert w_pointed < w_rounded < w_very


def test_rounded_point_between_pointed_and_rounded():
    v = build_pointed("S6")
    w_rp = cap_width(apply_tip(v, "rounded-point"))
    w_r = cap_width(apply_tip(v, "rounded"))
    assert 0 < w_rp < w_r


def test_cap_width_scales_with_feather_size():
    small = build_pointed("MG1")   # tiny feather
    large = build_pointed("P4")    # big feather
    assert tip_radius(large, "rounded") > tip_radius(small, "rounded")


# --- hooked: directional ----------------------------------------------------


def test_hooked_tip_points_outward():
    # S6 is 50:50 symmetric with a straight-ish rachis; the hook must lean
    # toward the outer vane (+x), so the topmost point has x > 0.
    v = build("S6", "hooked")
    top = max(v.outline, key=lambda p: p[1])
    assert top[0] > 0.0


def test_hooked_differs_from_rounded():
    v0 = build("S6", "hooked")
    v1 = build("S6", "rounded")
    assert v0.outline != v1.outline


# --- data set sweep ---------------------------------------------------------


def test_all_feathers_apply_each_style():
    for f in FEATHERS["feathers"]:
        v = compute_vane(f, compute_rachis(f))
        for tip in TIP_STYLES:
            styled = apply_tip(v, tip)
            assert styled.outline[0] == styled.outline[-1]  # closed
            assert is_simple_polygon(styled.outline), f"{f['id']} {tip}"


def test_all_feathers_native_tip():
    # each feather's own tip from feathers.json must apply cleanly
    for f in FEATHERS["feathers"]:
        v = compute_vane(f, compute_rachis(f))
        styled = apply_tip(v, f["tip"])
        assert styled.outline[0] == styled.outline[-1]
        assert is_simple_polygon(styled.outline), f"{f['id']} {f['tip']}"


# --- errors -----------------------------------------------------------------


def test_unknown_tip_raises():
    v = build_pointed("S6")
    with pytest.raises(ValueError, match="unknown tip"):
        apply_tip(v, "spiky")
