# Backlog — Feather Geometry Engine (Python)

> **Overall status: 🚧 in progress** — G1–G2 done; G3+ not started.
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
| G3 | `compute_rachis` | ⬜ | G2 |
| G4 | `compute_vane` (+ width scaling) | ⬜ | G2, G3 |
| G5 | Tip styles | ⬜ | G4 |
| G6 | Emargination | ⬜ | G4 |
| G7 | `feather_outline` entry point | ⬜ | G2–G6 |
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

## G3 — `compute_rachis(params)` — ⬜ not started

**What:** straight polyline of `total` length along the feather axis, bowed per `curvature`
(control-point offset; `high` for P1 → ~`straight` for coverts). Returns the rachis polyline +
its bend points (offset points used by the LED segment).

**Depends on:** G2

**Tests:** length equals `total`; endpoint-to-endpoint = `total` straight; bend points fall on
the bowed rachis; low vs high curvature change the max lateral offset; straight ≈ no bend.

---

## G4 — `compute_vane(params, rachis)` — ⬜ not started

**What:** the closed vane outline: sweep to `max_width` at ~40–50 % of `vane` length from the
base, tapering to the tip and to the quill root. Two Bézier rails (outer + inner) partitioned by
the rachis split (`out:inn`). **Width scaling:** effective width = `max_width × (1 +
vane_ratio_adjustment)`, applied here (default `0 %` = pure §3 ratios).

**Depends on:** G2, G3

**Tests:** outline is **closed**; max width ≈ effective `max_width` (± tolerance) at ~40–50 % of
vane; width → ~0 at tip and at quill root; symmetric feathers (50:50) have symmetric rails;
asymmetric (e.g. P1 30:70) partition the width per the split; `vane_ratio_adjustment=-5 %`
scales the outline width to ~95 % and `0 %` leaves it unchanged.

---

## G5 — Tip styles — ⬜ not started

**What:** `pointed`, `hooked`, `rounded-point`, `rounded`, `very-rounded` as a tip profile tweak
on the closed outline.

**Depends on:** G4

**Tests:** each tip style produces a distinct, valid (non-self-intersecting) tip profile; hooked
has a directional hook; very-rounded is blunter than rounded.

---

## G6 — Emargination — ⬜ not started

**What:** boolean param; cuts the outer-vane notch near the tip (P1–P5 only).

**Depends on:** G4

**Tests:** absent by default; present when true; notch sits on the **outer** vane near the tip;
profile remains a single closed loop (not fragmented).

---

## G7 — `feather_outline(params, vane_ratio_adjustment=0.0) → {outline, rachis}` — ⬜ not started

**What:** the public entry point composing G2–G6; threads the width flag into `compute_vane`.

**Depends on:** G2–G6

**Tests:** golden samples — P4 and S6 render to known-nominal outlines (snapshot test); no
self-intersections across the whole data set (sweep all rows); lit feathers respect the
**vane ≥ ~14 mm** floor — and `vane_ratio_adjustment` is **refused/clamped** if it would take
any lit feather below that floor (warn/fail per §2 of lighting-and-boards.md).

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
