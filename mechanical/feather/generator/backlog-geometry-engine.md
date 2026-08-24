# Backlog — Feather Geometry Engine (Python)

> Status: **backlog** · not started. Spec source: §7 (vector recipe) + §8 (data layer) of
> [outline-templates.md](../outline-templates.md). Depends on the data file
> ([backlog data layer](#data-layer-prereq)) existing first.
> This document is the *plan* — it is not yet implemented.

## Goal

One parametric function that draws **any** individual feather outline from its data entry,
turning §7's "How to draw one feather" recipe (§7.1–7.6) into a single tested code path.
Primaries vs secondaries vs coverts must differ only in **data**, never in code. This engine
only produces a single feather's geometry — see
[backlog-arrangement-engine.md](backlog-arrangement-engine.md) for the separate stage that
places/layers all feather templates into a wing.

## Scope

- **In:** one `feathers.json` entry (a single feather's params) or a dict of the same shape.
- **Out:** two artifacts per feather —
  - the **closed vane outline** (the template polygon/polyline for CAD/laser/DXF/SVG), and
  - the **rachis polyline with bend points** (the "length + bend points" input the LED segment
    boards need — see [lighting-and-boards.md](../lighting-and-boards.md)).
- **Out of scope (later):** arrangement/placement/layering (separate engine), diffuser geometry,
  physical substrate material, LED-board mounting.

## Data-layer prereq

Before this engine is meaningful we need the source of truth:
`mechanical/feather/generator/feathers.json` (§8 of outline-templates.md) — one entry per
feather: `{id, group, total, vane, max_width, rachis_split, tip, curvature, emargination,
z_order, ...}`. `max_width` is stored **per-feather at its §3 vane ratio**; any global width
scaling is the separate `vane_ratio_adjustment` generator flag, not a data change. Until the file
exists, the engine can be built and tested against inline dicts
matching that shape. **First task: author the data file** (schema + all rows from §3/§7).

## Tasks (in suggested order)

1. **Author `feathers.json`** — schema + every feather row from §3.1–§3.7 and the §7 cm tables.
   Include shared-strip placeholder rows (median/lesser/marginal coverts) per §3.4b. Validate:
   `total = vane + quill`, `quill ≥ 0`, `0 < max_width`, `out + inn = 100` for rachis split.
   - Tests: `feathers.json` loads; every entry passes schema/range validation; fixture covers a
     representative set (P1, P4, P6, S6, T4, GC1, GC12, SC4, BC4, A-B, A-T, median-strip).
2. **Core listable geometry** — represent points/segments/polylines without a hard CAD dep
   (plain tuple/`dataclass` geometry first; swap in a viewer/serializer later). Unit: cm.
3. **`compute_rachis(params)`** — straight polyline of `total` length along the feather axis,
   bowed per `curvature` (control-point offset; `high` for P1 → ~`straight` for coverts). Return
   the rachis polyline + its bend points (offset points used by the LED segment).
   - Tests: length equals `total`; endpoint-to-endpoint = `total` straight; bend points fall on
     the bowed rachis; low vs high curvature change the max lateral offset; straight ≈ no bend.
4. **`compute_vane(params, rachis)`** — the closed vane outline: sweep to `max_width` at ~40–50 %
   of `vane` length from the base, tapering to the tip and to the quill root. Two Bézier rails
   (outer + inner) partitioned by the rachis split (`out:inn`). **Width scaling:** effective width
   = `max_width × (1 + vane_ratio_adjustment)`, applied here (default `0 %` = pure §3 ratios).
   - Tests: p1/outline is **closed**; max width ≈ effective `max_width` (± tolerance) at ~40–50 %
     of vane; width → ~0 at tip and at quill root; symmetric feathers (50:50) have symmetric rails;
     asymmetric (e.g. P1 30:70) partition the width per the split; `vane_ratio_adjustment=-5%`
     scales the outline width to ~95 % and `0 %` leaves it unchanged.
5. **Tip styles** — `pointed`, `hooked`, `rounded-point`, `rounded`, `very-rounded` as a tip
   profile tweak on the closed outline.
   - Tests: each tip style produces a distinct, valid (non-self-intersecting) tip profile; hooked
     has a directional hook; very-rounded is blunter than rounded.
6. **Emargination** — boolean param; cuts the outer-vane notch near the tip (P1–P5 only).
   - Tests: absent by default; present when true; notch sits on the **outer** vane near the tip;
     profile remains a single closed loop (not fragmented).
7. **`feather_outline(params, vane_ratio_adjustment=0.0) → {outline, rachis}`** — the public
   entry point composing step 2–6; threads the width flag into `compute_vane`.
   - Tests: golden samples — P4 and S6 render to known-nominal outlines (snapshot test); no
     self-intersections across the whole §3 data set (sweep all rows); lit feathers respect the
     **vane ≥ ~14 mm** floor at the ribbon — and `vane_ratio_adjustment` is **refused/clamped**
     if it would take any lit feather below that floor (warn/fail per §2 of
     lighting-and-boards.md).
8. **Serializers** — DXF (via `ezdxf`) and SVG (stdlib) per feather in `generator/out/{dxf,svg}/`.
   - Tests: artifact emitted for every feather; SVG is well-formed; DXF contains a single closed
     polyline on the expected layer.
9. **Markdown sync (optional first cut)** — a generator/lint that checks the §7 tables in
   outline-templates.md match `feathers.json` (per §8's never-hand-maintained rule).

## Parameters & spec (the contract)

| Param | Meaning | Source |
|-------|---------|--------|
| `group` | family (P/S/T/GC/A/SC/BC/cover-strip) | §1, §3 |
| `total` | quill-to-tip length, cm | §7 |
| `vane` | barbed-outline length, cm | §7 |
| `max_width` | widest vane width, cm = `chord_ratio × vane` (per-feather §3 ratio default) | §3, §7 |
| `vane_ratio_adjustment` | global % on every `max_width` (generator flag, default `0 %`; e.g. `-5 %`) | §6, §8 |
| `rachis_split` | outer:inner width partition | §3.1/§3.2 |
| `tip` | pointed/hooked/rounded-point/rounded/very-rounded | §7 |
| `curvature` | high/med/med-low/low (~straight) | §7 |
| `emargination` | bool, outer-vane notch near tip | §7 (P1–P5) |

## Test infra / conventions

- `pytest`; tests live in `mechanical/feather/generator/tests/` alongside the code — the repo has
  no test setup yet, so **add `pytest.ini` (+ a `requirements-dev.txt` with `pytest`, `ezdxf`)**
  as part of the first commit that has code.
- No CAD dependency in the core geometry (pure math); `ezdxf` only for DXF serialization.
- Tolerance-based assertions for anything geometric (avoid exact-float equality on Bézier samples).

## Deliverable / definition of done

A module `feather_outline(params)` that, from any `feathers.json` row, returns a validated
`{outline, rachis}` pair — plus SVG/DXF outputs — with `pytest` green covering every task above.
The full §3 data set must sweep without self-intersections and respect the lit vane ≥ 14 mm floor.

## Open items to confirm while building

- Exact tip profile shapes (esp. `hooked`) need an aesthetic pass — start from the doc's note
  ("pointed, hooked" for P1) and iterate on the preview sheet.
- Whether `feather_outline` should also return the diffuser region per feather (currently out of
  scope; re-check with the diffuser investigation).
- Width at default `vane_ratio_adjustment=0 %` = the pure §3 vane ratios (wide for ~76 feathers);
  pick the actual flag value (e.g. `-5 %`) from the preview sheet, and lock golden snapshot tests
  at that chosen value.
