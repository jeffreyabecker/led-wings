# Plan: reorganize `templates/`

**Status:** proposed, not executed.
**Scope:** directory structure, file renames, reference rewrites, and the folder docs that make the
layout self-explanatory. No geometry, styling or content changes.

Behaviour changes to `tile_sheets.py` are a separate document:
[`plans/tile-sheets-changes.md`](tile-sheets-changes.md). This plan covers only *moving* the script.

Facts below were verified against the working tree at the time of writing.

## Decisions this plan encodes

| decision | choice |
|---|---|
| sheet masters vs targets | masters are target-agnostic, so they live **above** `targets/` |
| layout shape | `templates/<content>/sheets.svg` + `templates/targets/<target>/<content>/print-<paper>.svg` |
| print document references | keep thin `<use>` references (no inlining), accepting parent-directory hrefs |
| paper naming | `print-8_5x11.svg`, `print-a4.svg` — dimension form, unambiguous in US and ISO contexts |
| `aggregate.svg` | the geometry master that sheets reference by id (today's `feathers-elongated.svg`) |
| PDFs | rendered from the print documents, parked at the target level |

## Target layout

```
templates/
  README.md                       naming grammar, pipeline, regeneration commands
  AGENTS.md                       folder rules (masters vs generated, machining model, registration)
  aggregate.svg                   geometry master, id-referenced by <use>
  tile_sheets.py                  the tiler (moved here as drawn)
  feathers/
    sheets.svg                    sheet layouts, mm, registration + mirror pattern
    AGENTS.md
  alignment/
    sheets.svg
    AGENTS.md
  targets/
    AGENTS.md                     everything below here is generated
    home/                         US/ISO home-printer paper
      AGENTS.md                   canonical commands + parameter sets per paper
      feathers/
        print-8_5x11.svg
        print-a4.svg
      alignment/
        print-8_5x11.svg
      feathers-8_5x11.pdf
      alignment-8_5x11.pdf
```

The `multipage` moniker is retired: the stage word is `print`, and the only thing that varies in
the name is the paper.

## File mapping

| now | after | notes |
|---|---|---|
| `templates/feathers-elongated.svg` | `templates/aggregate.svg` | geometry master, 250×700 mm, own stylesheet, 0 `<use>` |
| `templates/sheets-home-feathers.svg` | `templates/feathers/sheets.svg` | 15 sheets; 29 external hrefs + 14 internal mirror `<use>` |
| `templates/sheets-home-alignment.svg` | `templates/alignment/sheets.svg` | 12 sheets; 18 external hrefs |
| `templates/sheets-home-feathers-multipage.svg` | `templates/targets/home/feathers/print-8_5x11.svg` | 28 pages; 28 external refs |
| `templates/sheets-home-alignment-multipage.svg` | `templates/targets/home/alignment/print-8_5x11.svg` | 19 pages; 19 external refs |
| — | `templates/targets/home/feathers/print-a4.svg` | new output, same master, A4 paper |
| — | `templates/targets/home/feathers-8_5x11.pdf` | render of `feathers/print-8_5x11.svg` |
| — | `templates/targets/home/alignment-8_5x11.pdf` | render of `alignment/print-8_5x11.svg` |
| `tile_sheets.py` (repo root) | `templates/tile_sheets.py` | move only; behaviour work is the other plan |
| `templates/print/` | *deleted* | empty directory, absorbed by `targets/` |
| `templates/sheets-home-print.pdf` | *deleted* | orphan: its source SVG was removed at the split |
| `templates/feathers-letter-landscape.pdf` | *deleted* | orphan: `feathers-aggregate.svg` no longer exists |

## Reference rewrites

Only two kinds, both mechanical:

1. **Masters → geometry master.** Every external `<use>` in both `sheets.svg` files changes
   `feathers-elongated.svg#<id>` to `../aggregate.svg#<id>`:
   - `feathers/sheets.svg`: 29 occurrences (28 outline symbols + `calibration`)
   - `alignment/sheets.svg`: 18 occurrences (8 `*-align` symbols + `assembly-template`)
2. **Print documents → masters.** Regenerated, never hand-edited. The tiler must emit
   `../../../feathers/sheets.svg#sheet-P1` (three levels: `feathers` → `home` → `targets` →
   `templates`). 28 references for feathers, 19 for alignment.

Untouched by any of this: all element ids, sheet ids, `inkscape:current-layer`, `data-sort-order`,
the registration geometry, the mirror `<use href="#sheet-*-half">` references, and the stylesheet.

## Folder docs to add

- **`templates/README.md`** — the naming grammar, the pipeline (`aggregate.svg` → `<content>/sheets.svg`
  → `targets/<target>/<content>/print-<paper>.svg` → `<content>-<paper>.pdf`), which files are
  hand-edited vs generated, and the regeneration commands.
- **`templates/AGENTS.md`** — masters vs generated; the machining model (one pattern per sheet, the
  left half is the mirrored back of the right, no drawn left geometry and no second program); the
  mirror `<use>` and why labels are baked rather than cloned; registration conventions (axis along
  sheet Y at the bounds-rect centre, Ø6 through-holes, on-axis hole plus ±20 mm twin pair, top-left
  key, all marks inside the bounds rect); id conventions (`{Group}{N}{L|R}`, `sheet-<name>-*`); CSS
  must stay inline because a `<use>` clone inherits no cross-document CSS; any master edit invalidates
  its print documents.
- **`templates/feathers/AGENTS.md`** — author only inside `sheet-*-half`; never add left geometry by
  hand; labels live in `sheet-<name>-labels`; sheet ids are referenced by the print documents, so
  renaming one means re-tiling.
- **`templates/alignment/AGENTS.md`** — the same, minus the mirror pattern, noting the alignment
  sheets are single-sided today.
- **`templates/targets/AGENTS.md`** — generated output: never hand-edit, regenerate instead.
- **`templates/targets/home/AGENTS.md`** — what `home` means and the exact per-paper commands.

## Steps

0. **Prerequisite.** Land the reference-path and output-name changes from
   `plans/tile-sheets-changes.md` first, or the re-tile in step 4 will write hrefs pointing at the
   old paths. Confirm `git status` is clean apart from `tile_sheets.py`.
1. **Create directories and move files** (`git mv`, so history follows):
   ```
   git mv tile_sheets.py templates/tile_sheets.py
   git mv templates/feathers-elongated.svg templates/aggregate.svg
   mkdir templates/feathers templates/alignment templates/targets/home/feathers templates/targets/home/alignment
   git mv templates/sheets-home-feathers.svg templates/feathers/sheets.svg
   git mv templates/sheets-home-alignment.svg templates/alignment/sheets.svg
   git mv templates/sheets-home-feathers-multipage.svg templates/targets/home/feathers/print-8_5x11.svg
   git mv templates/sheets-home-alignment-multipage.svg templates/targets/home/alignment/print-8_5x11.svg
   ```
2. **Rewrite the masters' external hrefs**: `feathers-elongated.svg#` → `../aggregate.svg#`
   (29 + 18 occurrences). Verify the counts before and after; nothing else in those files changes.
3. **Write `README.md` and the five `AGENTS.md` files** (outline above).
4. **Re-tile** the print documents at their new paths, then add the A4 variant:
   ```
   python templates/tile_sheets.py templates/feathers/sheets.svg  215.9x279.4 205.9x269.4 12 10 --out templates/targets/home/feathers/print-8_5x11.svg
   python templates/tile_sheets.py templates/alignment/sheets.svg 215.9x279.4 205.9x269.4 12 10 --out templates/targets/home/alignment/print-8_5x11.svg
   python templates/tile_sheets.py templates/feathers/sheets.svg  210x297 200x287 12 10 --out templates/targets/home/feathers/print-a4.svg
   ```
5. **Render the PDFs** from the print documents (Inkscape CLI at
   `C:\Program Files\Inkscape\bin\inkscape.com`, `--export-type=pdf`), writing them at the target level.
6. **Delete the orphans and the empty directory**: `templates/print/`,
   `templates/sheets-home-print.pdf`, `templates/feathers-letter-landscape.pdf`.
7. **Verify** (see below), then commit.

## Verification

- No file under `templates/` still contains `sheets-home` or `multipage` (grep the whole tree,
  including the generated documents).
- From `templates/feathers/`, `../aggregate.svg` resolves; from `templates/targets/home/feathers/`,
  `../../../feathers/sheets.svg` resolves. The earlier missing-sibling incident is the reason this
  check is explicit.
- Open both print documents (Inkscape): page counts 28 and 19, and the referenced sheet content
  renders — not a blank page and not dashes-only.
- `python templates/tile_sheets.py … --whatif` matches the committed page counts before and after.
- `git status` shows the moves as renames, so the only content diff is the masters' href strings.

## Rollback

Everything is a `git mv` plus one string rewrite in two files; reverting the commit (or
`git mv`-ing back and `git checkout`-ing the two masters) restores the previous layout. The
generated documents can be re-tiled from either layout.

## Risks and notes

- **Parent-directory hrefs**: a print document copied away from the tree no longer renders. The PDFs
  are self-contained, so printing does not depend on the tree.
- **Deep relative paths**: `../../../<content>/sheets.svg` is valid and Inkscape resolves it, but it
  is one more silent failure mode. Keep `targets/` inside `templates/` rather than moving it to the
  repo root.
- **The feathers master's root page is currently 10 mm × 10 mm** (`viewBox="-495.664 751.564 10 10"`).
  Unrelated to this plan and harmless to the tiler (which reads the sheet bounds rects), but
  whole-document PDF/PNG exports of that file will be a 10 mm square. Worth fixing while the file is
  open.
- **A4 parameter set** (210×297 trim, 200×287 safe, overlap 12, gap 10) is an assumption; confirm it.
- `tile_sheets.py` is being actively edited, so verify the working copy before re-tiling.

## Out of scope

- Extracting the stylesheet (the three copies have already drifted, and `<use>` requires the styles to
  be present in the consuming document; a shared CSS source inlined at build time is a separate
  proposal).
- Any change to the sheet geometry, registration or mirror pattern.
- A commit policy for generated files (recommendation: keep committing them, and say so in
  `templates/targets/AGENTS.md`).
