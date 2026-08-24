"""G7 tests — feather_outline entry point."""

import hashlib
import json
from pathlib import Path

import pytest

from feathergen.geometry import bbox, is_simple_polygon, polyline_length
from feathergen.outline import (
    DEFAULT_LIT_VANE_FLOOR_CM,
    feather_outline,
)
from feathergen.rachis import Rachis
from feathergen.vane import Vane

FEATHERS = json.loads(
    (Path(__file__).resolve().parents[1] / "feathers.json").read_text(encoding="utf-8")
)

# golden snapshots (sha256 of repr(outline)) — regenerate only on intent
GOLDEN = {
    "P4": "d6bf9c4fca92706f7ffa982564b614d6a5d7f03dbcbb7838115031f386d1ff39",
    "S6": "466e3b0880b03a317e157b5301ad2a959a3030f5dddfdce17cae0215cb872b57",
}


def row(feather_id):
    return next(f for f in FEATHERS["feathers"] if f["id"] == feather_id)


def digest(outline):
    return hashlib.sha256(repr(outline).encode()).hexdigest()


# --- return shape -----------------------------------------------------------


def test_returns_dict_with_outline_and_rachis():
    res = feather_outline(row("P4"))
    assert set(res) == {"outline", "rachis"}
    assert isinstance(res["outline"], list)
    assert isinstance(res["rachis"], Rachis)


def test_outline_is_closed():
    res = feather_outline(row("P4"))
    assert res["outline"][0] == res["outline"][-1]


# --- golden snapshots -------------------------------------------------------


@pytest.mark.parametrize("fid", ["P4", "S6"])
def test_golden_snapshot(fid):
    res = feather_outline(row(fid))
    assert digest(res["outline"]) == GOLDEN[fid]


def test_golden_snapshot_rachis_total():
    assert feather_outline(row("P4"))["rachis"].total == 75.0
    assert feather_outline(row("S6"))["rachis"].total == 57.0


# --- data set sweep ---------------------------------------------------------


def test_no_self_intersections_across_dataset():
    for f in FEATHERS["feathers"]:
        res = feather_outline(f)
        assert is_simple_polygon(res["outline"]), f"{f['id']} self-intersects"


def test_all_outlines_closed():
    for f in FEATHERS["feathers"]:
        res = feather_outline(f)
        assert res["outline"][0] == res["outline"][-1], f"{f['id']} not closed"


def test_all_outlines_positive_area():
    for f in FEATHERS["feathers"]:
        res = feather_outline(f)
        xs = [p[0] for p in res["outline"]]
        ys = [p[1] for p in res["outline"]]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        assert w > 0 and h > 0, f"{f['id']} degenerate bbox"


def test_all_rachis_bend_points_present():
    for f in FEATHERS["feathers"]:
        res = feather_outline(f)
        assert len(res["rachis"].bend_points) >= 2, f"{f['id']}"

# --- lit vane floor ---------------------------------------------------------


def test_lit_floor_respected_at_default():
    for f in FEATHERS["feathers"]:
        if f["lit"]:
            res = feather_outline(f)
            ys = [p[1] for p in res["outline"]]
            xs = [p[0] for p in res["outline"]]
            assert max(xs) - min(xs) >= 1.4, f"{f['id']} below lit floor"


def test_lit_floor_at_zero_adjustment():
    for f in FEATHERS["feathers"]:
        if f["lit"]:
            res = feather_outline(f, vane_ratio_adjustment=0.0)
            xs = [p[0] for p in res["outline"]]
            assert max(xs) - min(xs) >= 1.4, f"{f['id']}"


def test_floor_clamped_not_raise():
    # harsh negative adjustment on a lit feather must clamp, not raise
    res = feather_outline(row("P4"), vane_ratio_adjustment=-0.95)
    xs = [p[0] for p in res["outline"]]
    assert max(xs) - min(xs) >= DEFAULT_LIT_VANE_FLOOR_CM - 1e-9


def test_floor_policy_raise():
    with pytest.raises(ValueError, match="floor"):
        feather_outline(row("P4"), vane_ratio_adjustment=-0.95, floor_policy="raise")


def test_floor_policy_unknown():
    with pytest.raises(ValueError, match="floor_policy"):
        feather_outline(row("P4"), floor_policy="bogus")


def test_unlit_ignores_floor():
    # an unlit feather may fall below the floor (it carries no strip)
    bc8 = row("BC8")  # lit = false, max_width 9.9
    res = feather_outline(bc8, vane_ratio_adjustment=-0.9)
    xs = [p[0] for p in res["outline"]]
    assert max(xs) - min(xs) < DEFAULT_LIT_VANE_FLOOR_CM


# --- vane_ratio_adjustment threading ----------------------------------------


def test_adjustment_scales_outline_width():
    w0 = max(p[0] for p in feather_outline(row("P4"))["outline"]) - min(
        p[0] for p in feather_outline(row("P4"))["outline"]
    )
    w1 = max(p[0] for p in feather_outline(row("P4"), vane_ratio_adjustment=-0.5)["outline"]) - min(
        p[0] for p in feather_outline(row("P4"), vane_ratio_adjustment=-0.5)["outline"]
    )
    assert w1 < w0


# --- tip + emargination integration -----------------------------------------


def test_emargination_applied_for_p4():
    res = feather_outline(row("P4"))
    # P4 is flagged emarginated; the outline must differ from tip-only (no notch)
    plain = feather_outline({**row("P4"), "emargination": False})
    assert res["outline"] != plain["outline"]


def test_tip_applied_for_p1():
    # P1 is hooked + emarginated; must stay simple
    res = feather_outline(row("P1"))
    assert is_simple_polygon(res["outline"])
