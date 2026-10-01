# Sheet Layout Editor

A browser-only WYSIWYG editor for the wing-PCB sheet-layout project. It edits a
**JSON project model** (`templates/project.json`) and drives a TypeScript
assembler that tiles sheets onto physical pages. The legacy `templates/layout.yaml`
and `assemble_sheets.py` are the previous system's artifacts; `layout.yaml` is
migrated into `project.json` by a one-time importer.

## Quick start

```bash
npm install --ignore-scripts --cache .npm-cache   # deps (esbuild binary ships as an optional dep)
npm run verify                                     # build + run the engine behavior tests
npm run build:editor                               # bundle the React app -> dist/editor.js
npm run serve                                      # static server on http://127.0.0.1:8000
```

Open `http://127.0.0.1:8000`. The editor loads `templates/project.json` by default;
use **Open…** to load another project JSON and **Save JSON** to download your edits.

## What it does

- **Sources & element palette** — enumerates every `id`-addressed group in the
  source SVGs (with its `/path` and `/g` variants) and places them onto a sheet.
- **Sheets** — add / duplicate / rename / delete; width and height.
- **Place & transform** — drag elements on the canvas; edit `x/y`, `rotate`, and
  `scale` (negative scale = mirror) numerically. A **Mirror (copy)** button writes
  the explicit mirrored pair.
- **Paper outputs** — edit trim / safe-area / overlap; the output panel shows the
  resulting page count and any bounds warnings; export sheet **SVGs**, a combined
  **PDF** (high-DPI raster), or a **contact-sheet** PNG.
- **Guardrails** — validation errors and ink-bounds warnings are shown live.

## Layout

```
packages/
  model/       types, validation, layout.yaml importer
  assembler/   resolve (XPath-ish) -> flatten -> assemble -> tile -> verify -> emit
editor/
  src/         React app (App.tsx, lib.ts, export.ts, main.tsx)
  style.css
scripts/
  import-layout.ts   one-time layout.yaml -> project.json migration
  verify.ts          behavior checks (engine + editor lib)
  build-editor.mjs   esbuild bundler (native binary, inherited stdio)
templates/
  project.json       the migrated project (source of truth)
  layout.yaml        legacy artifact (kept for reference)
```

## Notes

- The assembler is a **pure TS module**: the same code runs in the browser
  (preview/export) and under Node (tests).
- The tiler emits the `clipPath` defs that the legacy tiler referenced but forgot
  to include, so oversized sheets are actually clipped to the safe area.
- Node is build/test tooling only. `esbuild` is driven as a native binary because
  its JS API spawns a piped service process (blocked in some sandboxes).

## Not yet implemented (nice-to-have)

Undo/redo, snapping/guides, paper presets, multi-paper UI, layers UI, reusable
asset/instance UI, and vector (rather than raster) PDF export. The engine already
supports instances, assets, and multiple papers in the model.
