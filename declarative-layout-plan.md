# Plan — explicit sheet spec + deterministic tiling

**Status: proposed, not implemented.**

This replaces the earlier drafts of this file and supersedes the editor-centric
half of `manual-layout-strategy.md`. The direction is settled:

- **The spec declares sheets directly and manually** — every element, position,
  and transform is spelled out; nothing is grouped, paired, or packed for you.
- **Each sheet has a logical `dimensions`** — the drawing area its geometry must
  fit within.
- **A single `paper` element** describes the physical page (trim + safe-area) and
  the tiling overlap.
- **`source-file`** names the one file the geometry comes from; **`output-style`**
  holds the CSS that styles the output.
- **A tiling engine** maps a sheet's logical drawing area onto physical pages
  using the paper's safe-area, splitting oversized sheets across multiple pages
  with `overlap` and crop marks at the overlap lines.

The two inputs this plan is built to satisfy:

1. **Maximum manual control.** Every sheet, every element, every position and
   transform is spelled out. Nothing is inferred.
2. **No generated content, no generated mirrors.** All geometry lives in the
   source file and is referenced by id; a mirrored pair is two explicit elements
   with explicit scales.

## The principle (decided)

- **No magic about generating content.** All geometry comes from the source file,
  referenced by `source-id`. Text is written inline in the spec.
- **No magic about mirrored pairs.** A left/right pair is two `source-id`
  elements with different explicit `transform.scale` values. The engine never
  pairs anything.
- **No modes / splits / aligns.** These propagate the exact issues they were
  meant to fix. A sheet is an explicit list of elements; the spec is the whole
  story.
- **Content and paper are separate.** A sheet's `dimensions` is a *logical*
  drawing area (it may exceed one page — that is what tiling is for); `paper`
  is the *physical* page. The spec never conflates the two.
- **The engine is an assembler + tiler + verifier, not a layout engine.** It
  resolves references, assembles each sheet's drawing area, tiles it onto paper
  by a fixed rule, and checks bounds. It makes no placement, grouping, or content
  decisions. If output is wrong, the spec is wrong — and is fixed by editing the
  spec.

## 1. Current state

Three scripts meet only at the filesystem, and two of them *decide* layout the
user cannot touch without editing Python:

| script | what it decides (implicitly) |
|---|---|
| `make_logical_pages.py` | `SECTIONS` groups items into pages; `shelf()`/`build_pair()` auto-generate the mirrored pair and placement; `cover_page()` generates the calibration rulers; the `CSS` block styles everything |
| `make_print_sheets.py` | one page → one sheet (or one sheet per tile); tiling grid, clip, corner ticks, overlap |
| `sheets_to_pdf.py` | (none) — render + merge + scale check |

The complaints all trace to this: content is *generated* and layout is *computed*
rather than *declared*. This plan deletes both decision-making scripts and
replaces them with one spec file plus a small assembler/tiler.

## 2. Target model

Three pieces:

1. **Source file** (one, named by `source-file`) — SVG holding placement-ready
   content in millimetres: feather geometry, calibration rulers, and any marks,
   each in a group addressable by id. Content only; no layout.
2. **The spec (`templates/layout.yaml`)** — top-level `source-file`, `paper`,
   `output-style`, and a list of `sheets`, each with a `dimensions` drawing area
   and an explicit list of `elements`.
3. **The engine (`assemble_sheets.py`, new)** — resolve `source-id` against the
   source file → assemble each sheet's drawing area → tile onto physical pages →
   verify → hand off to the renderer. It contains no layout logic and no content.

The render contract survives with one small adjustment: the engine emits
`sheet-NNN.svg` + `manifest.json`, and `sheets_to_pdf.py` still renders + merges
+ runs the scale check; the manifest's `paper` now carries `trim`/`safe-area`/
`overlap` instead of a bare `w`/`h`, and the scale check reads its bar positions
from the manifest rather than hardcoded page coordinates (§7).

## 3. The spec schema

```yaml
# All coordinates are in mm. The spec is the layout: nothing is generated.

source-file: feathers-aggregate.svg        # the single source of geometry

paper:                                     # single, top-level — the physical page + tiling
  trim: { width: 279.4, height: 215.9 }    # absolute paper dimensions
  safe-area: { width: 269.4, height: 205.9 }   # ink-able area (centered in trim)
  overlap: 12.0                            # tiling overlap; or { x: 12.0, y: 8.0 }

output-style: |                            # CSS applied to the output; styles copied geometry
  .outline { stroke: #000000; stroke-width: 0.5; fill: none; }
  .guide   { stroke: #000000; stroke-width: 0.264583; fill: none; }
  .label   { font-family: sans-serif; fill: #000000; text-anchor: middle; }
  .title   { font-family: sans-serif; fill: #000000; font-size: 9; text-anchor: middle; font-weight: bold; }

sheets:
  - title: "Cover Page"
    dimensions: { width: 250, height: 200 }    # logical drawing area; all geometry fits inside
    elements:
      - text: "Feathers"
        position: { x: 50, y: 12 }
        class: title
      - source-id: '//g[@id="calibration-ruler-metric"]'
        position: { x: 50, y: 12 }
      - source-id: '//g[@id="calibration-ruler-us"]'
        position: { x: 50, y: 25 }

  - title: "Feather - P1"
    dimensions: { width: 250, height: 400 }    # taller than safe-area -> tiles vertically
    elements:
      - source-id: '//g[@id="P1"]/path'
        position: { x: 50, y: 12 }
        transform: { scale: [1.0, -1.0] }
      - text: "P1R"
        position: { x: 50, y: 12 }
      - source-id: '//g[@id="P1"]/path'
        position: { x: 120, y: 12 }
        transform: { scale: [-1.0, -1.0] }
      - text: "P1L"
        position: { x: 120, y: 12 }
```

Element kinds:

| kind | fields | meaning |
|---|---|---|
| `text` | `text`, `position`, optional `class` | a label drawn at the position; styling comes from the `class` rule in `output-style` |
| `source-id` | `source-id` (XPath), `position`, optional `transform` | geometry copied from the source file, placed and transformed |

`transform` is optional and, when present, is `{ scale: [sx, sy] }` and/or
`{ rotate: deg }`. **Negative scale is the mirror operator** — there is no
pairing primitive, so `scale: [-1, -1]` is how a left half is written, literally.

`dimensions` is the *logical* extent of the sheet's content — not the paper. It
may be smaller than the safe-area (centered in it, leaving the rest blank) or
larger (which triggers tiling).

## 4. Resolution semantics (the "no magic" contract)

These four rules are the contract; anything not stated here is out of scope for
the engine:

1. **`source-id` is an XPath expression** evaluated against the source file. It
   must resolve to at least one element; a dangling id fails the build with the
   expression, not a blank sheet.
2. **The engine copies exactly the selected element, verbatim** — its geometry
   and its own attributes, in the coordinate frame it is authored in — and
   applies *no* re-framing, *no* `data-wh`/`data-vb` normalization, and *no*
   ancestor-transform recovery. **XPath is used precisely because the source's
   id-bearing elements also carry transforms that must not be copied**: selecting
   `//g[@id="P1"]/path` takes the child path *without* its group's view-
   arrangement transform, so what lands in the output is the placement-ready
   geometry, not the view. Copied geometry keeps its `class` attributes, and the
   spec's `output-style` is responsible for defining those classes.
3. **The element's local origin is the transform anchor.** The emitted transform
   is `translate(x y) rotate(r) scale(sx sy)`: position applied outermost, so
   scale/rotate act about the element's own origin first. Mirroring is therefore
   about the element's origin; the source file chooses a sensible origin (centre
   or top-left) per element.
4. **`position` is the element origin's location in the sheet's drawing-area
   coordinates, in mm, y-down** per SVG convention. The drawing area is the
   `[0, width] × [0, height]` box named by the sheet's `dimensions`.

## 5. Engine stages

`assemble_sheets.py`, five stages, no layout decisions:

1. **Resolve** — evaluate every `source-id` against the source file; collect the
   selected element(s). Fail loudly on a dangling id or a missing source file.
2. **Assemble** — for each sheet, build an SVG of the sheet's `dimensions`
   containing each element in order: `text` → a `<text>` node (classed per the
   element's `class`, default `.label`); `source-id` → the copied element wrapped
   in a `<g transform="…">` carrying `position` + `transform`. The output `<style>`
   carries the spec's `output-style`.
3. **Tile** — map each drawing area onto physical pages, the one fixed rule:
   - **fits** (`dimensions ≤ safe-area`): one page, the drawing area **centered in
     the safe-area** — offset `(safe-area − dimensions) / 2` per axis from the
     safe-area origin.
   - **overflows**: the drawing area is cut into a `cols × rows` grid of
     safe-area-sized windows, each adjacent window shifted by
     `stride = safe-area − overlap` (so neighbours re-print `overlap` mm of
     content). One physical page per window, clipped to the safe-area, with
     **crop marks drawn along each overlap line** — the shared edge where the
     adjacent tile repeats content — so tiles can be registered by matching the
     repeated strip. This replaces today's corner ticks.
4. **Verify** — §6.
5. **Emit** — write `sheet-NNN.svg` (one per physical page) and `manifest.json`
   carrying `paper` (`trim`/`safe-area`/`overlap`), each sheet's `dimensions`,
   and per-page `tile`/`cols`/`rows`/`transform`.

The grid formula is today's `make_print_sheets.py` math unchanged, only
re-parameterised on the spec's `safe-area` and `overlap` instead of hardcoded
`PAPER_W/H` and `OVERLAP`: `cols = 1 if W ≤ safe_w else ceil((W − safe_w) / stride_x) + 1`
(and the same for rows), `stride_x = safe_w − overlap_x`.

## 6. Verification

Checks that run before render — named failures, not silent wrong output:

| check | catches |
|---|---|
| `source-file` exists; every `source-id` resolves | dangling reference |
| every element's ink lies within the sheet's `dimensions` | geometry outside the declared drawing area |
| re-derived tile grid + transforms match what was emitted | tiling drift (today's `verify_tiling`) |
| every physical page declares `paper.trim` size | paper drift (today's `verify_sheets`) |
| every `position`/`dimensions` is a finite positive value | malformed spec |
| sheets are emitted in spec order; manifest matches disk | stale-file confusion (unchanged) |
| cover present; 100 mm / 4 in bars measure true | scale (renderer, bar positions read from manifest) |

The "fits within `dimensions`" check is the hard boundary the user asked for:
**all sheet geometry must fit within the drawing area.** An element that pokes
out is a named failure, not a silent clip — clipping only ever happens at the
tile boundary, where it is deliberate and marked. Unreferenced source elements
are a **warning**, not a failure: the source file may hold more content than a
given run uses.

## 7. Migration

1. **Promote generated content into source groups.** The cover's calibration
   rulers (currently `cover_page()` in `make_logical_pages.py`) and anything else
   the scripts fabricate become explicit `<g id="…">` groups in the source file,
   so the spec can reference them by id.
2. **Prepare source groups for placement** (rule 2): each referenced group gets a
   self-contained mm frame with a chosen origin, and the view-arrangement
   transforms stay on the parent groups (bypassed via `/path` XPaths). This is the
   one real source-file change, and it is deliberate.
3. **Write the spec** as the current output, sheet by sheet: today's logical page
   becomes a sheet with `dimensions` = that page's size and `elements` = its
   content; today's tiling of an oversized page becomes the tiling engine acting
   on that sheet's `dimensions`; the `CSS` block moves into `output-style`;
   `source-file` points at the aggregate. 39 pages → 39 sheets, tiling reproduces
   the 11 tiled pages' multi-page output, total 52 physical pages.
4. **Write `assemble_sheets.py`** (resolve / assemble / tile / verify / emit),
   reusing only the `fmt`/`parse_mm` helpers and the tiling math from the old
   scripts.
5. **Adjust `sheets_to_pdf.py`** minimally: read `paper.trim` (and the safe-area
   and overlap) from the manifest; read the calibration-bar positions from the
   manifest rather than the hardcoded page coordinates in `verify_scale`.
   Rendering, merging, and the scale measurement itself are unchanged.
6. **Retire** `make_logical_pages.py` and `make_print_sheets.py` in the same
   commit that first reproduces the baseline. Update the old scripts' stale
   docstring references as `manual-layout-strategy.md` §7 required.

Acceptance, in order:

- **A — reproduce.** The transcribed spec → assemble → tile → render yields the
  52 physical pages and the 654 207-byte PDF byte-for-byte (pins the machinery).
- **B — each complaint is now a spec edit.** Combine content → move an element to
  another sheet's `elements`. Split combined content → delete the extra
  `source-id`s into a new sheet. Better placement → change `position`. Bigger
  paper → change `paper.trim`/`safe-area`. Different overlap → change
  `paper.overlap`. Styling → edit `output-style`. Overlap marks → the tiling
  engine draws them whenever a sheet tiles. None touches code.
- **C — guardrails fail loudly.** A dangling `source-id`, an element outside
  `dimensions`, a tiling mismatch — each names the sheet, the element, and the
  amount.

## 8. Decisions (settled)

| # | question | decision |
|---|---|---|
| 1 | transform anchor | **local origin** — `translate(position) rotate(r) scale(sx sy)`, position outermost |
| 2 | resolution | **copy the selected element verbatim** — no re-framing, no normalization, no ancestor recovery |
| 3 | safe-area placement on the paper | **always centered** in `trim`; margin = `(trim − safe-area) / 2` per axis |
| 4 | drawing-area placement when it fits | **centered within the safe-area** (not top-left) |
| 5 | overlap form | single number = same x and y; `{ x, y }` for different |
| 6 | source layout | **one file** (`source-file`) |
| 7 | why XPath | **id-bearing source elements carry view transforms that must not be copied**; the XPath selects the exact child (e.g. `/path`) whose own frame is placement-ready |
| 8 | text styling | `text` may carry an optional `class`; sizing/face come from `output-style` |

## Appendix — measurements taken for this plan

| probe | result |
|---|---|
| pipeline shape today | 3 scripts; 2 generate content/layout (`SECTIONS`+`build_pair`+`cover_page`+`CSS`, `build_sheets`) |
| baseline | 39 logical pages → 52 physical pages (11 tiled, 28 fit); merged PDF 654 207 bytes |
| paper today | trim 279.4 × 215.9 mm (Letter landscape); margin 5.0 mm → safe-area 269.4 × 205.9 mm; overlap 12.0 mm |
| content generated in code | mirrored pairs (`build_pair`), shelf placement (`shelf`), calibration rulers (`cover_page`), corner ticks (`corner_ticks`), the `CSS` block |
| content that must move to source groups | calibration rulers, feather geometry (already present) |
| reused unchanged | `fmt`/`parse_mm`, the tiling grid formula, `verify_scale`'s measurement |
| spec top-level fields | `source-file`, `paper` (`trim`/`safe-area`/`overlap`), `output-style`, `sheets[]` |
| manifest change | `paper` gains `trim`/`safe-area`/`overlap`; `sheets[]` gains `dimensions`; scale-check bar positions move into the manifest |
