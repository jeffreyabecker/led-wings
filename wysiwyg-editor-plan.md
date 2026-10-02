# Plan — Web WYSIWYG editor (browser-only, JSON project model)

**Status: proposed — direction decided, not implemented.**

A browser-only editor, TypeScript + React, static app inside this repo. The
shipped artifact is the web app; Node is **build/test tooling only** (Vite,
Vitest + jsdom), not a runtime component. The editor owns a **JSON project file**
(the source of truth) and is the only authoring surface. The legacy
`layout.yaml` is an **import-only migration format**. The TypeScript assembler is
a pure module and replaces `assemble_sheets.py`.

## Decisions (settled)

| # | decision |
|---|---|
| 1 | **The assembler is re-implemented in TypeScript as a pure module.** `assemble_sheets.py` is retired once the migration gate passes. |
| 2 | **Browser-only runtime.** The app is the product; Node exists only to build and test (Vite, Vitest + jsdom — jsdom gives the same DOM the app uses). No CLI, no Node renderers. |
| 3 | **A JSON project file is the source of truth.** Authored only through the editor (no hand-editing). `layout.yaml` is import-only, no exporter. |
| 4 | **Static app inside this repo, TypeScript + React.** |
| 5 | **Rendering/export happens in the browser.** SVG download; PNG contact sheet via `<canvas>` (or `resvg` WASM); PDF via `pdf-lib` (high-DPI raster default, vector optional later). |
| 6 | **Functional equivalence, not byte parity.** The migration gate checks the same *meaning* (placements, transforms, tile grid, warnings) — not byte-identical SVG. |

## 1. Goal

Five core operations, mapped onto what already exists:

| you asked for | editor feature |
|---|---|
| select a source SVG | source library: add/remove source files; element palette built from their `id`s |
| add sheets | sheet list: add / duplicate / reorder / rename / delete |
| place elements on sheets | drag elements (assets) from a palette onto the sheet canvas; click-to-place; text elements |
| set element transforms | transform inspector: translate (drag or numeric), rotate, scale, and the negative-scale mirror idiom |
| define paper outputs | paper definitions + tiling preview + named output jobs; in-browser export of sheet SVGs / PDF / contact sheet |

## 2. The project model (JSON, source of truth)

The model is a typed JSON document the editor loads and saves. It supersets the
flat YAML so the editor can express things the old format could not, while still
being able to import every existing spec:

```
Project
├── meta                 { name, units: "mm", defaultPaper, defaultSource }
├── sources[]            { id, name, svg }                       # many source files, not one
├── assets[]             { id, name, sourceId, sourceSelector,   # reusable, named pieces
│                          baseTransform? }                      #   = resolved source-id + optional base transform
├── styles               { name → { font, size, fill, stroke, … } }   # structured; replaces the raw CSS blob
├── papers[]             { id, name, trim, safeArea, overlap }   # many paper definitions, not one
├── sheets[]             { id, title, dimensions,
│                          layers?[] { id, name, visible, locked, elements[] } }
│                          elements[]  (see below)
└── outputs[]            { id, name, sheetIds?, paperId, format }     # named paper-output jobs
```

Element kinds (richer than today's `text` / `source-id`):

- **instance** — `{ assetId, position, transform }` — references a reusable
  asset; edit the asset once, every instance follows.
- **source** — `{ sourceId, sourceSelector, position, transform }` — inline
  source reference (fallback for one-offs, exactly today's `source-id`).
- **text** — `{ text, position, styleId }` — styled by a named style.

Capabilities this adds over the flat YAML:

- **multiple source files** (a library) instead of a single `source-file`;
- **reusable assets / instances** instead of repeating `source-id` XPaths;
- **structured text/outline styles** instead of one raw CSS string;
- **multiple paper definitions** and **named output jobs** instead of one `paper`;
- **layers** (visibility/lock) within a sheet;
- **project metadata** (defaults, naming) instead of an unnamed flat file.

### YAML relationship (import-only migration)

- **Import** — a one-time `importLayoutYaml()` parses the existing
  `templates/layout.yaml` into the model: one source file → `sources[0]`, `paper`
  → `papers[0]`, `output-style` → a styles entry, each sheet and element mapped
  1:1. The result is saved as the project JSON; the YAML is then retired.
- **No exporter.** The editor saves JSON; `layout.yaml` is never regenerated.

### Project file loading/saving (browser)

- Open/save via file picker + download, and (where supported) the File System
  Access API to work in place.
- Autosave to IndexedDB, with the JSON saved to a chosen file as the durable
  form; source SVGs are loaded as assets via file picker or bundled.

## 3. Behavioural contract (what "correct" means)

Byte parity is dropped; meaning parity is not. The engine must still get these
right, because they define what the output *is*:

| concern | required behaviour |
|---|---|
| units | mm, SVG y-down |
| source selection | XPath against a source SVG; namespaces normalized (strip `{…}`); retry `.`-prefixed and quote-swapped forms; resolves to **one or more** elements; dangling selector fails with a named error |
| copy semantics | selected element copied **verbatim** (attributes + `class`) in its own frame; ancestor view-transforms are *not* copied |
| transform order | `translate(x y) rotate(r) scale(sx sy)` — position outermost; scale/rotate act about the element's **local origin** |
| mirror | `scale: [-1, 1]`; no pairing primitive — a mirrored pair is two explicit elements |
| text | `<text class="…">` at `position`; face/size from the named style |
| sheet `dimensions` | logical drawing area `[0,w] × [0,h]`, independent of paper |
| tiling | fits → one page centered in safe-area; overflows → `cols×rows` grid, `stride = safe-area − overlap`, clipped to safe-area, overlap/crop marks |
| bounds check | element ink bbox outside `dimensions` is a **warning** (tol 0.5), never a silent clip |

One subtlety to carry over, now browser-native:

- **XPath + namespaces.** In the browser, `document.evaluate` over inline SVG
  needs a namespace resolver. The engine normalizes the same way Python's
  `strip_ns` did (drop `{…}` prefixes / `xmlns`), and applies the same fallback
  chain so legacy selectors like `//g[@id="P1"]/path` resolve identically.
  Vitest runs the same code under jsdom, so the gate is tested with the real DOM.

## 4. Feature map

### 4.1 Core (the five, expanded)

1. **Source SVG library** — add/remove source files; element palette built from
   their `id`s with thumbnails and ready-made selectors; live dangling-id
   indicator.
2. **Sheets** — add / duplicate / rename / reorder / delete; `dimensions`
   editable, with optional auto-fit to element bounds; optional layers.
3. **Place elements** — drag assets onto the canvas or click-to-place; live ghost;
   reorder within a sheet (z-order = list order, which matters).
4. **Transforms** — drag to translate; inspector holds numeric `position.x/y`,
   `rotate`, `scale.x/y` (incl. negative mirror), with the
   `translate → rotate → scale` order readout so the mirror anchor is visible.
5. **Paper outputs** — multiple paper definitions + named output jobs; tiling
   preview (physical page grid, safe-area, overlap/crop marks); in-browser export
   of sheet SVGs / PDF / contact sheet.

### 4.2 Must-have additions (correctness)

- **Functional migration gate.** Capture the current Python output's *meaning*
  once into a baseline fixture (sheet count and titles, per-sheet dimensions,
  element positions/transforms, the 52-physical-page / 11-tiled grid, warnings).
  `importLayoutYaml()` + the engine must reproduce that fixture, asserted in
  Vitest + jsdom. **Do not retire `assemble_sheets.py` until this passes.**
- **Live bounds check.** Red-shade elements whose ink bbox pokes outside the
  sheet `dimensions` (tol 0.5).
- **Validation panel with named errors.** Dangling selector, non-finite or
  non-positive positions/dimensions, malformed transform, duplicate sheet titles
  or asset/style names — each naming the sheet and element.
- **Scale calibration check.** Surface the 100 mm / 4 in bars' expected vs printed
  size so output prints at true size.

### 4.3 Should-have additions (workflow / UX)

- Undo/redo + autosave + dirty indicator.
- **Mirror helper** — writes the explicit left/right pair (two instances with
  `scale [1,1]` / `[-1,1]`), no engine magic.
- Snapping / grid / guides / alignment; numeric entry is the floor.
- Measure/ruler overlay in mm, y-down labelled.
- Paper presets (Letter landscape 279.4×215.9 / 269.4×205.9, A4, custom) with
  trim-vs-safe-area margin shown.
- Asset/style browsers; contact-sheet thumbnails; keyboard + multi-select;
  source reload + re-resolve; multi-project open/save.

## 5. Architecture

```
editor/ (React app)            packages/model + packages/assembler (pure TS)
├── source library             ├── model: typed schema, load/save JSON, validate
├── asset / style browsers     ├── yaml-import: importLayoutYaml() (one-time migration)
├── sheet canvas (WYSIWYG)     ├── flatten: resolve assets/instances/styles → concrete elements
├── transform inspector        ├── resolve: XPath + namespace normalization
├── paper / tiling preview     ├── assemble: transform + serialize elements
├── validation panel           ├── tile: grid / overlap / crop marks
└── export (SVG/PNG/PDF)       ├── verify: bounds + named errors
                               └── emit: sheet-NNN.svg + manifest.json
```

- **One runtime, one DOM.** The engine and the editor share the browser DOM
  (inline `<svg>` + `document.evaluate`). No Node DOM backend to drift from it.
- **Model is canonical.** `packages/model` holds the typed JSON schema and
  validation; the editor loads/saves the project JSON and is the only authoring
  surface. The assembler consumes the model directly.
- **Flatten is a compiler link step, not layout logic.** Resolve asset references,
  instance → concrete element, style id → class/style, paper id → paper. No
  placement, grouping, or content is inferred — same "no magic" contract as today.
- **In-browser export.** Sheet SVGs as Blob download; PNG contact sheet via
  `<canvas>` (or `resvg` WASM); PDF via `pdf-lib` embedding high-DPI PNG (vector
  PDF is a later optional enhancement).
- **Tests, not a runtime.** Vitest + jsdom run the engine against the baseline
  fixture; Vite builds the app. Node's role ends there.

## 6. Phases

1. **Model + engine + functional gate.** Build `packages/model` (typed JSON
   schema, validate) and `packages/assembler` (flatten → resolve → assemble →
   tile → verify → emit). Write `importLayoutYaml()`, migrate the current
   `templates/layout.yaml` → `templates/project.json`, render through the engine,
   and assert functional equivalence against the captured Python baseline in
   Vitest + jsdom (sheet count, dimensions, positions/transforms, tile grid,
   warnings). **Do not retire `assemble_sheets.py` until this passes.**
2. **Read-only WYSIWYG.** React app loads a project JSON + sources, renders
   sheets/elements/transforms/tiling from the shared engine. Nothing editable yet —
   prove the browser preview matches the engine output.
3. **Editing.** Sheets CRUD, source library, asset palette + place/drag, transform
   inspector, text elements + styles, layers, z-order reordering.
4. **Paper outputs + export.** Paper definitions + output jobs, tiling preview,
   in-browser export (sheet SVGs / PDF / contact sheet), project save/load.
5. **Guardrails + UX.** Validation panel, live bounds check, undo/redo, snapping,
   presets, mirror helper, source reload, functional-parity tests in CI. Then
   retire `assemble_sheets.py` (and the migrated-from YAML once the JSON is the
   tracked source).

## 7. Open decisions

1. **Model schema shape** — exact JSON field names and types for `meta`, `assets`,
   `styles`, `papers`, `outputs`, and `layers`. Direction is set (§2); the
   concrete schema is still to be pinned (plain JSON, editor-owned).
2. **Where the project JSON lives** — replace `templates/layout.yaml` in place with
   `templates/project.json`, or a new location/extension for the tracked project
   file.
3. **PDF fidelity** — high-DPI raster (default, simplest) vs true vector via a
   pure-JS SVG-path converter (more work). Decide whether vector crispness
   matters for your print use case.
