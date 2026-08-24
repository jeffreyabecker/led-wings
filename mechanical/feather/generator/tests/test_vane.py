"""G4 tests — compute_vane."""

import json
from pathlib import Path

import pytest

from feathergen.geometry import distance
from feathergen.rachis import compute_rachis
from feathergen.vane import Vane, compute_vane, vane_width_at, width_profile

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)


def row(feather_id):
    return next(f for f in FEATHERS["feathers"] if f["id"] == feather_id)


def build(feather_id, **kw):
    r = row(feather_id)
    return compute_vane(r, compute_rachis(r), **kw)


# --- width profile ----------------------------------------------------------


def test_width_profile_ends():
    assert width_profile(0.0, 10.0) == 0.0
    assert width_profile(1.0, 10.0) == 0.0


def test_width_profile_peak():
    assert width_profile(0.45, 10.0) == pytest.approx(10.0)
    assert width_profile(0.5, 10.0) < 10.0


def test_width_profile_peak_param():
    assert width_profile(0.6, 10.0, peak_s=0.6) == pytest.approx(10.0)


def test_width_profile_negative_s_clamped():
    assert width_profile(-0.1, 10.0) == 0.0


# --- closed outline ---------------------------------------------------------


def test_outline_is_closed():
    v = build("S6")
    assert v.outline[0] == v.outline[-1]


def test_outline_rails_build():
    v = build("S6")
    assert len(v.outer_rail) == len(v.inner_rail) == 65


# --- max width --------------------------------------------------------------


def test_max_width_at_peak():
    v = build("S6")  # 50:50 symmetric, max_width 14.3
    assert v.effective_max_width == pytest.approx(14.3)
    assert vane_width_at(0.45, v) == pytest.approx(14.3, rel=0.05)


def test_max_width_across_sweep():
    v = build("S6")
    widths = [vane_width_at(i / 64, v) for i in range(65)]
    assert max(widths) == pytest.approx(14.3, rel=0.05)


def test_width_zero_at_quill_root():
    v = build("S6")
    assert vane_width_at(0.0, v) == pytest.approx(0.0, abs=1e-6)


def test_width_zero_at_tip():
    v = build("S6")
    assert vane_width_at(1.0, v) == pytest.approx(0.0, abs=1e-6)


def test_quill_cm():
    v = build("P4")  # 75 total, 56 vane
    assert v.quill_cm == pytest.approx(19.0)


# --- symmetry / split -------------------------------------------------------


def test_symmetric_rails_50_50():
    v = build("S6")  # rachis split 50:50
    # rails are symmetric about the (bowed) rachis, not the y-axis:
    # at each sample, outer and inner offsets from the rachis are equal
    r = compute_rachis(row("S6"))
    from feathergen.geometry import point_at_arc
    n = len(v.outer_rail) - 1
    for k, (o, i) in enumerate(zip(v.outer_rail, v.inner_rail)):
        s = k / n
        arc = v.quill_cm + s * (r.total - v.quill_cm)
        p = point_at_arc(r.polyline, arc)
        assert distance(o, p) == pytest.approx(distance(i, p), abs=1e-6)


def test_asymmetric_split_p1():
    v = build("P1")  # 30:70 — outer vane 30 %, inner 70 %
    r = compute_rachis(row("P1"))
    from feathergen.geometry import point_at_arc
    idx = round(0.45 * 64)
    s = idx / 64.0
    arc = v.quill_cm + s * (r.total - v.quill_cm)
    p = point_at_arc(r.polyline, arc)
    d_out = distance(v.outer_rail[idx], p)
    d_in = distance(v.inner_rail[idx], p)
    total_off = d_out + d_in
    assert d_out / total_off == pytest.approx(0.30, abs=0.02)
    assert d_in / total_off == pytest.approx(0.70, abs=0.02)


def test_split_preserves_total_width():
    v = build("P1")
    assert vane_width_at(0.45, v) == pytest.approx(v.effective_max_width, rel=0.05)


# --- vane_ratio_adjustment --------------------------------------------------


def test_adjustment_zero_unchanged():
    v0 = build("P4")
    v1 = build("P4", vane_ratio_adjustment=0.0)
    assert v0.effective_max_width == v1.effective_max_width


def test_adjustment_negative_scales_width():
    v0 = build("P4")
    v1 = build("P4", vane_ratio_adjustment=-0.05)
    assert v1.effective_max_width == pytest.approx(v0.effective_max_width * 0.95)


def test_adjustment_positive_scales_width():
    v0 = build("P4")
    v1 = build("P4", vane_ratio_adjustment=0.10)
    assert v1.effective_max_width == pytest.approx(v0.effective_max_width * 1.10)


def test_adjustment_scales_actual_outline():
    v0 = build("P4")
    v1 = build("P4", vane_ratio_adjustment=-0.05)
    assert vane_width_at(0.45, v1) == pytest.approx(vane_width_at(0.45, v0) * 0.95, rel=0.02)


# --- errors -----------------------------------------------------------------


def test_vane_longer_than_total_raises():
    r = compute_rachis({"total_cm": 50.0, "curvature": "low"})
    with pytest.raises(ValueError, match="vane_cm"):
        compute_vane({"vane_cm": 60.0, "max_width_cm": 5.0,
                      "rachis_split": {"outer": 50, "inner": 50}}, r)


def test_zero_max_width_raises():
    r = compute_rachis({"total_cm": 50.0, "curvature": "low"})
    with pytest.raises(ValueError, match="max_width_cm"):
        compute_vane({"vane_cm": 40.0, "max_width_cm": 0.0,
                      "rachis_split": {"outer": 50, "inner": 50}}, r)


def test_adjustment_kills_width_raises():
    r = compute_rachis({"total_cm": 50.0, "curvature": "low"})
    with pytest.raises(ValueError, match="vane_ratio_adjustment"):
        compute_vane({"vane_cm": 40.0, "max_width_cm": 5.0,
                      "rachis_split": {"outer": 50, "inner": 50}}, r,
                     vane_ratio_adjustment=-1.0)


def test_bad_peak_s_raises():
    r = compute_rachis({"total_cm": 50.0, "curvature": "low"})
    with pytest.raises(ValueError, match="peak_s"):
        compute_vane({"vane_cm": 40.0, "max_width_cm": 5.0,
                      "rachis_split": {"outer": 50, "inner": 50}}, r, peak_s=1.5)


# --- data set sweep ---------------------------------------------------------


def test_all_feathers_build_vane():
    for f in FEATHERS["feathers"]:
        v = compute_vane(f, compute_rachis(f))
        assert v.outline[0] == v.outline[-1]  # closed
        assert v.effective_max_width > 0
        assert len(v.outline) >= 4


def test_vane_returns_vane_type():
    v = build("T2")
    assert isinstance(v, Vane)


def test_lit_feathers_respect_floor_at_zero_adjustment():
    # at 0 % adjustment every lit feather already exceeds the 14 mm floor
    for f in FEATHERS["feathers"]:
        if f["lit"]:
            v = compute_vane(f, compute_rachis(f))
            assert v.effective_max_width >= 1.4
