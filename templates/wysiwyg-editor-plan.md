# Plan — Web WYSIWYG editor for `layout.yaml`

**Status: proposed — direction decided, not implemented.**

A browser-based editor for `templates/layout.yaml`, TypeScript + React, static app
inside this repo. The spec stays the single source of truth; the editor and the
assembler are **one TypeScript engine**, and that engine **replaces
`assemble_sheets.py`**.

## Decisions (settled)

| # | decision |
|---|---|
| 1 | **The assembler is re-implemented in TypeScript and becomes canonical.** `assemble_sheets.py` is retired and replaced by the TS version. |
| 2 | **One engine, two runtimes.** The same TS module runs in the browser (live WYSIWYG preview) and in Node (CLI bake + tests), so preview and output cannot diverge. |
| 3 | **`layout.yaml` is the single source of truth.** The editor reads/writes it in place; structured controls edit fields, the raw YAML/CSS/comments are preserved. |
| 4 | **Static app inside this repo, TypeScript + React.** |
| 5 | **Rendering moves to Node too.** `sheets_to_pdf.py` + `contact_sheet.py` (cairosvg/GStreamer) are replaced by `@resvg/resvg-js` (PNG) + `pdf-lib`/`pdfkit` (PDF). |

## 1. Goal

Five core operations, mapped onto what already exists:

| you asked for | editor feature |
|---|---|
| select a source SVG | source picker (open / library) + element palette built from the SVG's `id`s |
| add sheets | sheet list: add / duplicate / reorder / rename / delete |
| place elements on sheets | drag elements from a palette onto the sheet canvas; click-to-place; text elements |
| set element transforms | transform inspector: translate (drag or numeric), rotate, scale, and the negative-scale mirror idiom |
| define paper outputs | paper editor (trim / safe-area / overlap) + tiling preview + export sheet SVGs / PDF / contact sheet |

## 2. Ground truth the TS engine must reproduce

The engine is only correct if it reproduces the current Python behaviour exactly.
Every line here is a contract, not a design choice:

| concern | current behaviour (from `assemble_sheets.py`) |
|---|---|
| units | everything mm, SVG y-down |
| `source-id` | XPath against the source file; namespaces stripped; engine retries with `.`-prefixed and quote-swapped forms; resolves to **one or more** elements; dangling id fails the build |
| copy semantics | selected element is copied **verbatim** (attributes + `class`), in its own frame; ancestor view-transforms are *not* copied (why `/path` XPaths exist) |
| transform order | `translate(x y) rotate(r) scale(sx sy)` — position outermost; scale/rotate act about the element's **local origin** |
| mirror | `scale: [-1, 1]` — no pairing primitive; a mirrored pair is two explicit elements |
| text element | `<text class="{class}">` at `position`; `class` defaults to `.label`; face/size from `output-style` |
| sheet `dimensions` | logical drawing area `[0,w] × [0,h]`, independent of paper |
| tiling | fits → one page, centered in safe-area; overflows → `cols×rows` grid, `stride = safe-area − overlap`, clipped to safe-area, overlap/crop marks |
| bounds check | element ink bbox outside `dimensions` is a **warning** (tol 0.5), never a silent clip (clipping happens only at the tile boundary) |
| output | `sheet-NNN.svg` per physical page + `manifest.json`, in spec order = print order |

Two runtime-specific subtleties to carry over:

- **XPath + namespaces.** Browser `document.evaluate` needs a namespace
  resolver; Python strips namespaces (`strip_ns`) first. The TS engine must
  normalize the same way (strip `{…}` prefixes or use an agnostic resolver) and
  apply the same fallback chain (`//…`, `.//…`, quote swap) so `//g[@id="P1"]/path`
  resolves identically everywhere.
- **One DOM abstraction.** Use the real DOM in the browser and a lightweight DOM
  (`@xmldom/xmldom` + `xpath`, or equivalent) in Node, behind one interface, so
  resolve/serialize/tile code is shared verbatim.

## 3. Feature map

### 3.1 Core (the five, expanded)

1. **Source SVG selection** — open a local SVG or pick from a library; build an
   **element palette** of everything addressable by id, with thumbnails and
   ready-made `source-id` expressions (e.g. `//g[@id="P1"]/path`,
   `//g[@id="B-align"]/g`), plus a live dangling-id indicator.
2. **Sheets** — add / duplicate / rename / reorder / delete; `dimensions`
   editable numerically, with optional auto-fit to the union of element bounds.
3. **Place elements** — palette drag or click-to-place; live ghost; reorder
   within a sheet (z-order = list order, which matters).
4. **Transforms** — drag to translate; inspector holds numeric `position.x/y`,
   `rotate` (deg), `scale.x/y` (incl. negative mirror), with the
   `translate → rotate → scale` order readout so the mirror anchor is visible.
5. **Paper outputs** — edit `paper.trim` / `paper.safe-area` / `paper.overlap`
   (single number or `{x, y}`), with a **tiling preview** (physical page grid,
   safe-area, overlap/crop marks) for oversized sheets; export produces the
   sheet SVGs + PDF + contact sheet.

### 3.2 Must-have additions (correctness)

- **Migration parity test.** Before `assemble_sheets.py` is deleted, the TS engine
  must reproduce the current 39-sheet / 52-physical-page baseline (same SVGs,
  same manifest, same tiling) as an acceptance gate.
- **Live bounds check.** Red-shade elements whose ink bbox pokes outside the
  sheet `dimensions` (tol 0.5), mirroring the engine warning.
- **Validation panel with named errors.** Dangling `source-id`, non-finite or
  non-positive positions/dimensions, malformed `transform`, duplicate sheet
  titles — each naming sheet and element.
- **YAML round-trip fidelity.** The `output-style` CSS block and comments survive
  edits untouched (comment-preserving YAML, e.g. `yaml` Document API).
- **Scale calibration check.** Surface the 100 mm / 4 in bars' expected vs printed
  size so output prints at true size.

### 3.3 Should-have additions (workflow / UX)

- Undo/redo + autosave + dirty indicator.
- **Mirror helper** — writes the explicit left/right pair (two `source-id`s,
  `scale [1,1]` / `[-1,1]`), no engine magic.
- Snapping / grid / guides / alignment; numeric entry is the floor.
- Measure/ruler overlay in mm, y-down labelled.
- Paper presets (Letter landscape 279.4×215.9 / 269.4×205.9, A4, custom) with
  trim-vs-safe-area margin shown.
- Contact-sheet thumbnails; keyboard + multi-select; source reload + re-resolve;
  multi-file projects.

## 4. Architecture

```
editor/ (React app)          packages/assembler (shared TS engine)
├── source palette           ├── yaml: parse/serialize layout.yaml (round-trip)
├── sheet canvas (WYSIWYG)   ├── resolve: XPath + namespace normalization
├── transform inspector      ├── assemble: transform + serialize elements
├── paper/tiling preview     ├── tile: grid/overlap/crop marks
└── validation panel         ├── verify: bounds + named errors
                             └── emit: sheet-NNN.svg + manifest.json
                                      ▲                    ▲
                              browser (preview)     node CLI (bake/test)
```

- **One engine.** `packages/assembler` is imported by both the React editor
  (browser) and a small Node CLI (`node scripts/assemble.mjs`) that replaces
  `assemble_sheets.py`. No second implementation to drift.
- **`layout.yaml` round-trip.** The editor keeps the parsed YAML `Document` and
  edits structured nodes in place, so formatting/comments (especially the
  `output-style` block) are preserved.
- **Rendering (SVG → PDF/PNG).** Moves to Node: `@resvg/resvg-js` for PNG
  (contact sheet) and `pdf-lib`/`pdfkit` for PDF. The TS engine's contract is to
  emit `sheet-NNN.svg` + `manifest.json` byte-compatible with today; the Node
  renderers consume those. This removes the last Python/GStreamer dependency.

## 5. Phases

1. **Model + engine + migration gate.** Build `packages/assembler` (yaml model,
   resolve, transform, tile, verify, emit). Reproduce the current baseline in
   Node and diff against `assemble_sheets.py` output until identical. **Do not
   delete the Python until this passes.**
2. **Node CLI swap.** `scripts/assemble.mjs` replaces `assemble_sheets.py`; CI runs
   both and diffs until the migration gate is green, then the Python assembler is
   deleted.
3. **Read-only WYSIWYG.** React app loads source + spec, renders sheets/elements/
   transforms/tiling from the shared engine. Nothing editable yet — prove the
   browser preview matches the Node bake.
4. **Editing.** Sheets CRUD, element palette + place/drag, transform inspector,
   text elements, z-order reordering.
5. **Paper outputs.** Paper editor, tiling preview, export (SVG/PDF/contact sheet),
   download.
6. **Guardrails + UX.** Validation panel, live bounds check, undo/redo, snapping,
   presets, mirror helper, source reload, parity in CI.
7. **Node renderers.** Replace `sheets_to_pdf.py` / `contact_sheet.py` with Node
   (`@resvg/resvg-js` PNG, `pdf-lib`/`pdfkit` PDF); delete the cairosvg/GStreamer
   path once output matches the current PDF/contact-sheet baseline.

## 6. Remaining open decision

1. **YAML round-trip library** — confirm comment-preserving behaviour on the real
   `output-style` block before committing (e.g. `yaml` npm `Document`). This is the
   only open item; everything else is settled.
