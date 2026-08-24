# Backlog — Feather Arrangement Engine (Python)

> Status: **backlog** · not started. Spec source: §4 (arrangement & layering) + §6 (layout) of
> [outline-templates.md](../outline-templates.md). Depends on the geometry engine
> ([backlog-geometry-engine.md](backlog-geometry-engine.md)) and the `feathers.json` data file.
> This document is the *plan* — it is not yet implemented.

## Goal

A second stage, separate from [backlog-geometry-engine.md](backlog-geometry-engine.md), that
places every individual feather outline into the folded wing assembly per §4/§6. Geometry is
drawn once (single feather); arrangement applies **placement transforms** — it never modifies a
feather's outline. Layout decisions (§5 open items) become knobs here, not code changes.

## Scope

- **In:** all per-feather outlines from the geometry engine (or the data needed to draw them),
  plus arrangement params (panel size, overlap %, hang angle, mirroring, anchor points).
- **Out:** one wing assembly (left wing placed, right wing mirrored about the body axis, back
  coverts centered), with:
  - a **z-order list** (topmost → bottommost per §4), and
  - placed outlines ready for an assembled DXF + annotated SVG preview sheet.
- **Out of scope (done elsewhere):** single-feather geometry (geometry engine), lighting/board
  mapping ([lighting-and-boards.md](../lighting-and-boards.md)), electronics-bay removable-lid
  mechanism (§5), harness/backplate mounting design ([structural]);

## Tasks (in suggested order)

1. **Placement data** — extend `feathers.json` entries with id/`group` (already there) plus
   per-wing placement: base anchor point on the panel, hang angle, `z_order`. Defaults derived
   from §6 layout (folded wing, 50 cm panel, outer ~20–22 cm per wing).
   - Tests: placements cover every feather in §3; every feather has a base anchor + z-order;
     no two non-overlapping feathers collide without intended shingle overlap.
2. **Anchor geometry** — define base/tip conventions so a placed feather knows its root anchor
   on the panel and the direction it hangs. Reuse the outline's base point from the geometry
   engine (quill root = the mount end, top).
   - Tests: each feather's root anchor lands on/inside the panel; tip-hangs downward (per §6);
     longest primaries reach the hem (furthest from the mount).
3. **Local → global transform** — affine transform (translate + rotate) taking a feather from its
   local model frame to its placed frame (anchor point + hang angle). No outline mutation.
   - Tests: transform preserves shape (lengths/areas invariant); rotation by hang angle behaves as
     expected; inverse transform round-trips to the original local frame.
4. **Mirroring** — right wing = left wing flipped about the body axis (§4). A single mirrored
   master (per §5 "confirm a single mirrored master is sufficient"). Scapulars per side; back
   coverts are one center-back set (not mirrored).
   - Tests: mirrored feather is the mirror image (vertices reflect about the body axis, order
     preserved); flipping is an involution (flip twice = identity); back coverts emit once
     (not doubled by mirroring).
5. **Covert anchoring** — `GCn` placed over `Sn` at ≈ 50 % of `Sn` length (§3.4, §4). Derive
   covert placement from flight-feather placement so the wing re-flows when one knob changes.
   - Tests: GCn lies over its `Sn`'s base at ≈ 50 % length; shoulder/back coverts (SC/BC) anchor
     per §6 outer-center rule; alula anchored at the wrist point (§3.5).
6. **Shingle overlap** — apply the overlap % knob (the §5 open decision) so each feather
   overlaps the one behind/inside: each feather's base is covered by the feather over it;
   tip remains free. Z-order drives draw order.
   - Tests: for pairs in §4's layering, the top feather covers the lower's base by the overlap %;
     tips stay free (not covered); z-order list matches §4's topmost→bottommost order.
7. **Panel fit** — validate the assembled layout stays within the 50 cm wide × ~75 cm tall
   envelope and the ~20–22 cm per-wing columns + center-back band (§6).
   - Tests: bounding box of the full assembly fits the panel; per-wing columns stay in their
     x-band; longest primary (P4) reaches the hem; no outline pokes outside the panel.
8. **Serializers** — assembled **DXF** (one layer per group, per §4/§6) + an **annotated SVG
   preview sheet** (dimension labels: total/vane/max-width) for review and for locking §5.
   - Tests: assembled DXF emitted per group; preview sheet shows every feather with its labels;
     label points sit inside the sheet.

## Layout model (from §6 — folded wing, flat on back)

- Panel: **50 cm wide × ~75 cm tall**, centered on the spine, mounted at the shoulders.
- Left/right wings in the **outer ~20–22 cm**; **back coverts** in center over the electronics
  bay. Feathers hang downward, overlapping top-over-bottom; longest (primaries) at the hem.
- §4 layering (topmost → bottommost) is the z-order contract: back coverts → scapulars → flight
  feathers → greater coverts → median → lesser → marginal → alula.

## Placement params (the knobs)

| Param | Default | Meaning |
|-------|---------|---------|
| `panel_w` / `panel_h` | 50 / 75 cm | assembly envelope (§6) |
| `wing_band` | ~20–22 cm | half-width each wing column (§6) |
| `hang_angle` | per group | feather tilt from vertical (§6) |
| `overlap` | ⚠️ TBD | % of base covered by the feather over it (§5) |
| `mirror` | right = flip(left) | left/right strategy (§4, §5) |
| `anchor_points` | per feather ✓ | root + hang origin on the panel |

## Test infra / conventions

- Shares the `pytest` + `generator/tests/` layout established by the geometry engine (add
  `pytest.ini` + `requirements-dev.txt` with `pytest`, `ezdxf` if not already added).
- Placement asserted by transform math (determinants, inverse round-trips, bounding boxes), not
  pixel-looking at the SVG.
- A golden snapshot of the assembled geometry (bounding box + feature anchors) once §5 widths are
  locked.

## Deliverable / definition of done

An arrangement module that, from all feather outlines + placement params, returns the placed,
z-ordered wing assembly and emits an assembled DXF + annotated SVG preview, with `pytest` green
covering every task above. The assembly must fit the 50×75 cm panel, mirror correctly, anchor
covert to their flight feathers, and apply a configurable shingle overlap.

## Open items to confirm while building

- §5: exact **overlap %** per shingle direction — the key visual/physical knob; needs an
  aesthetic pass on the preview sheet.
- §5: **single mirrored master** vs hand-tuned pairs — this doc assumes the single-master,
  mirrored-right approach; revisit if it fails the preview.
- §5: left/right wing columns **+ center back** vs one continuous feather field — this doc follows
  the column layout; flag if the continuous field wins.
- Electronics-bay removable-lid mechanism is separate (out of scope here).
