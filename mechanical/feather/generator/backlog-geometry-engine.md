# Backlog — Feather Geometry Engine (Python)

> **Overall status: 🚧 in progress** — G1–G7 done; G8+ not started.
> Spec source: §7 (vector recipe) + §8 (data layer) of
> [outline-templates.md](../outline-templates.md).
> This document is the *plan*; each task's status lives in the table below and in its own
> section. The arrangement stage is [backlog-arrangement-engine.md](backlog-arrangement-engine.md).

## Task list (status location)

Legend: ✅ done · 🚧 in progress · ⬜ not started

| ID | Task | Status | Depends on |
|----|------|--------|-----------|
| G1 | `feathers.json` data file | ✅ | — |
| G2 | Core listable geometry | ✅ | — |
| G3 | `compute_rachis` | ✅ | G2 |
| G4 | `compute_vane` (+ width scaling) | ✅ | G2, G3 |
| G5 | Tip styles | ✅ | G4 |
| G6 | Emargination | ✅ | G4 |
| G7 | `feather_outline` entry point | ✅ | G2–G6 |
| G8 | Serializers (DXF/SVG) | ⬜ | G7 |
| G9 | Markdown sync / lint | ⬜ | G7 |

## Goal

One parametric function that draws **any** individual feather outline from its data entry,
turning §7's "How to draw one feather" recipe (§7.1–7.6) into a single tested code path.
Primaries vs secondaries vs coverts must differ only in **data**, never in code. This engine
only produces a single feather's geometry — the
[arrangement engine](backlog-arrangement-engine.md) is the separate stage that places/layers
all feather templates into a wing.

## Scope

- **In:** one `feathers.json` entry (a single feather's params) or a dict of the same shape.
- **Out:** two artifacts per feather —
  - the **closed vane outline** (the template polygon/polyline for CAD/laser/DXF/SVG), and
  - the **rachis polyline with bend points** (the "length + bend points" input the LED segment
    boards need — see [lighting-and-boards.md](../lighting-and-boards.md)).
- **Out of scope (later):** arrangement/placement/layering (arrangement engine), diffuser
  geometry, physical substrate material, LED-board mounting.

---

## G1 — `feathers.json` data file — ✅ done

**What:** schema + every feather row from §3.1–§3.7 and the §7 cm tables, incl. the
fully-enumerated covert rows (median MD1–MD12, lesser LS1-1…LS3-12, marginal MG1–MG12) per
§3.4b–§3.4d.

**File:** `mechanical/feather/generator/feathers.json` — 114 feathers, each `{id, group, side,
total_cm, vane_cm, chord_ratio_pct, max_width_cm, rachis_split, tip, curvature, emargination,
z_order, lit}`. `max_width_cm = chord_ratio_pct × total_cm` (half-up to 0.1); any global width
scaling is the separate `vane_ratio_adjustment` generator flag, not a data change.

**Validation:** `_validate_feathers.py` — unique ids; `total = vane + quill`, `quill ≥ 0`;
`0 < max_width`; `out + inn = 100`; lit feathers ≥ 1.4 cm vane floor.

**Tests (pending the pytest harness):** `feathers.json` loads; every entry passes
schema/range validation; fixture covers a representative set (P1, P4, P6, S6, T4, GC1, GC12,
MD1, LS1-1, MG1, SC4, BC4, A-B, A-T).

---

## G2 — Core listable geometry — ✅ done

**What:** represent points/segments/polylines without a hard CAD dep (plain tuple/`dataclass`
geometry first; swap in a viewer/serializer later). Unit: cm. Provides the primitives G3+ build
on.

**Where:** `feathergen/geometry.py` — `Point = (x, y)` tuple, `Polyline = Sequence[Point]`, plus
`distance`, `polyline_length`, `bbox`, `translate`, `rotate`, `reflect_vertical`,
`sample_bezier` (quadratic/cubic via de Casteljau), `resample`. Test infra: `pytest.ini`
(`pythonpath = .`, cache disabled), `requirements-dev.txt` (`pytest`, `ezdxf`),
`bootstrap_pytest.py` (sandbox workaround — downloads pytest wheels directly because pip's
tempfile usage is denied under the DSH sandbox).

**Depends on:** —

**Tests:** `tests/test_geometry.py` — 25 cases covering distance/length, bbox, transforms
(translate/rotate/reflect, length-preservation, involution), Bézier endpoints/midpoint/bad
control counts, and resample spacing/across-vertices/edge cases. All green.

---

## G3 — `compute_rachis(params)` — ✅ done

**What:** straight polyline of `total` length along the feather axis, bowed per `curvature`
(control-point offset; `high` for P1 → ~`straight` for coverts). Returns the rachis polyline +
its bend points (offset points used by the LED segment).

**Where:** `feathergen/rachis.py` — rachis is a quadratic Bézier (base → control → tip along
+y); `CURVATURE_BOW_FRACTION` maps the 6 curvature levels (high/med-high/med/med-low/low/
straight) to a control offset as a fraction of `total`. `Rachis` dataclass holds `total`,
`curvature`, `bow_cm`, `polyline` (64 samples), `bend_points` (resampled at 1.04 cm LED pitch).
`max_lateral_offset` helper. Exported from `feathergen/__init__.py`.

**Depends on:** G2

**Tests:** `tests/test_rachis.py` — 20 cases: length ≈ total, endpoints, straight = no bend,
curvature ordering + max-lateral-offset, bow scales with total, bend points on the rachis
(segment distance), even spacing at LED pitch (+custom), errors, and a full feathers.json sweep
(all 114 rows compute). All green.

---

## G4 — `compute_vane(params, rachis)` — ✅ done

**What:** the closed vane outline: sweep to `max_width` at ~40–50 % of `vane` length from the
base, tapering to the tip and to the quill root. Two Bézier rails (outer + inner) partitioned by
the rachis split (`out:inn`). **Width scaling:** effective width = `max_width × (1 +
vane_ratio_adjustment)`, applied here (default `0 %` = pure §3 ratios).

**Where:** `feathergen/vane.py` — `width_profile(s, max_width, peak_s=0.45)` (piecewise
quadratic, exact max at peak, 0 at both ends); `compute_vane(params, rachis, n=64,
vane_ratio_adjustment=0.0, peak_s=0.45)` offsets the rachis along its unit normal by
`split × width` per rail, closed as outer base→tip + inner tip→base. `Vane` dataclass
(`outline`, `outer_rail`, `inner_rail`, `effective_max_width`, `quill_cm`) + `vane_width_at`.
New geometry helpers: `point_at_arc`, `unit_tangent_at_arc`.

**Depends on:** G2, G3

**Tests:** `tests/test_vane.py` (25) + 11 new geometry-helper tests: closed outline, max width at
peak ±5 %, width → 0 at tip & quill root, 50:50 rails symmetric about the *bowed* rachis, P1
30:70 split partitions the width (perpendicular offsets, not x-offsets), `vane_ratio_adjustment`
± scales effective + actual width, errors, full 114-row sweep + lit floor at 0 %.
All green.

---

## G5 — Tip styles — ✅ done

**What:** `pointed`, `hooked`, `rounded-point`, `rounded`, `very-rounded` as a tip profile tweak
on the closed outline.

**Where:** `feathergen/tips.py` — `apply_tip(vane, tip)` trims both rails back to the vane
fraction where the local width equals the cap diameter (2 × radius =
`TIP_RADIUS_FRACTION × effective_max_width`), then caps with a semicircular arc bulging toward
the original tip (rounded family) or a quadratic Bézier curled outward (hooked). `pointed` is
the untouched sharp taper. `tip_cap_width` measures bluntness (cap diameter in the top 5 % of
the vane). New geometry helpers: `is_simple_polygon`, `segments_intersect`.

**Depends on:** G4

**Tests:** `tests/test_tips.py` — 18 cases: five distinct styles, pointed unchanged, all styles
simple (no self-intersection) across S6/P1/T2/GC1/MG1 + full 114-row sweep per style + native
tips, sharp-pointed check, bluntness ordering (pointed < rounded-point < rounded <
very-rounded), cap scales with feather size, hooked tip leans toward the outer vane (+x),
unknown-tip error. All green.

---

## G6 — Emargination — ✅ done

**What:** boolean param; cuts the outer-vane notch near the tip (P1–P5 only).

**Where:** `feathergen/emargination.py` — `apply_emargination(vane, emargination=True,
span=(0.62, 0.95), depth=0.4)` replaces the outer-rail span near the tip with a quadratic
Bézier whose control is pulled inward toward the inner rail (depth × local half-width),
producing a clean V-notch. Inner rail untouched → single closed loop preserved.

**Depends on:** G4

**Tests:** `tests/test_emargination.py` — 16 cases: flag off = unchanged; on = outline changes,
outer rail only; notch narrows the vane (min notched point-to-inner-rail distance < plain width
at the notch midpoint), notch near tip not base; closed + simple (no self-intersection) for
P1–P5; custom span/depth + errors; data-set checks — exactly P1–P5 flagged emarginated, all
flagged feathers stay simple, unflagged unchanged with flag off. All green.

---

## G7 — `feather_outline(params, vane_ratio_adjustment=0.0) → {outline, rachis}` — ✅ done

**What:** the public entry point composing G2–G6; threads the width flag into `compute_vane`.

**Where:** `feathergen/outline.py` — `feather_outline(params, vane_ratio_adjustment=0.0,
lit_vane_floor_cm=1.4, floor_policy="clamp")` runs compute_rachis → compute_vane →
apply_tip → apply_emargination and returns `{"outline", "rachis"}`. Lit-feather floor
enforcement: adjustment that would drive a lit vane below the 1.4 cm floor is clamped to the
floor (default) or raises (`floor_policy="raise"`); unlit feathers ignore the floor.

**Depends on:** G2–G6

**Tests:** `tests/test_outline.py` — 18 cases: return shape, closed outline, **golden
snapshots** (sha256 of P4 + S6 outlines), full 114-row sweep (no self-intersection, closed,
positive bbox, bend points), lit floor at default & 0 % adjustment, clamp-not-raise, raise
policy, unknown policy, unlit ignores floor, adjustment scales width, emargination + tip
integration for P4/P1. All green.

---

## G8 — Serializers (DXF/SVG) — ⬜ not started

**What:** DXF (via `ezdxf`) and SVG (stdlib) per feather in `generator/out/{dxf,svg}/`.

**Depends on:** G7

**Tests:** artifact emitted for every feather; SVG is well-formed; DXF contains a single closed
polyline on the expected layer.

---

## G9 — Markdown sync / lint (optional first cut) — ⬜ not started

**What:** a generator/lint that checks the §7 tables in outline-templates.md match
`feathers.json` (per §8's never-hand-maintained rule).

**Depends on:** G7

**Tests:** lint passes on the current file; a deliberately drifted §7 row is flagged.

---

## Parameters & spec (the contract)

| Param | Meaning | Source |
|-------|---------|--------|
| `group` | family (P/S/T/GC/MD/LS/MG/A/SC/BC) | §1, §3 |
| `total` | quill-to-tip length, cm | §7 |
| `vane` | barbed-outline length, cm | §7 |
| `max_width` | widest vane width, cm = `chord_ratio_pct × total` (per-feather §3 ratio default) | §3, §7 |
| `vane_ratio_adjustment` | global % on every `max_width` (generator flag, default `0 %`; e.g. `-5 %`) | §6, §8 |
| `rachis_split` | outer:inner width partition | §3.1/§3.2 |
| `tip` | pointed/hooked/rounded-point/rounded/very-rounded | §7 |
| `curvature` | high/med-high/med/med-low/low (~straight) | §7 |
| `emargination` | bool, outer-vane notch near tip | §7 (P1–P5) |

## Test infra / conventions

- `pytest`; tests live in `mechanical/feather/generator/tests/` alongside the code — the repo has
  no test setup yet, so **add `pytest.ini` (+ a `requirements-dev.txt` with `pytest`, `ezdxf`)**
  as part of the first commit that has code (G2 or G3).
- No CAD dependency in the core geometry (pure math); `ezdxf` only for DXF serialization.
- Tolerance-based assertions for anything geometric (avoid exact-float equality on Bézier samples).

## Deliverable / definition of done

A module `feather_outline(params)` that, from any `feathers.json` row, returns a validated
`{outline, rachis}` pair — plus SVG/DXF outputs — with `pytest` green covering G2–G9. The full
data set must sweep without self-intersections and respect the lit vane ≥ 14 mm floor.

## Open items to confirm while building

- Exact tip profile shapes (esp. `hooked`) need an aesthetic pass — start from the doc's note
  ("pointed, hooked" for P1) and iterate on the preview sheet.
- Whether `feather_outline` should also return the diffuser region per feather (currently out of
  scope; re-check with the diffuser investigation).
- Width at default `vane_ratio_adjustment=0 %` = the pure §3 vane ratios (wide for ~76 feathers);
  pick the actual flag value (e.g. `-5 %`) from the preview sheet, and lock golden snapshot tests
  at that chosen value.
