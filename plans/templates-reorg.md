# Plan: reorganize `templates/`

**Status:** tiler prerequisite **done**; the reorg itself is proposed, not executed.

- The `tile_sheets.py` behaviour changes that the re-tile depends on have landed (commit
  `e568aed`) and are recorded under [Tiler state](#tiler-state-landed) below, which is the
  residual of the former `plans/tile-sheets-changes.md`. Nothing else from that plan remains.
- What is left is everything below: the directory structure, file renames, reference rewrites, the
  CSS consolidation (one source per audience, generated into every document), and the folder docs
  that make the layout self-explanatory. No geometry or content changes.

Facts below were re-verified against the working tree at the time of writing.

## Decisions this plan encodes

| decision | choice |
|---|---|
| sheet masters vs targets | masters are target-agnostic, so they live **above** `targets/` |
| layout shape | `templates/<content>/sheets.svg` + `templates/targets/<target>/<content>/print-<paper>.svg` |
| print document references | keep thin `<use>` references (no inlining), accepting parent-directory hrefs |
| stylesheet | one source per audience under `templates/css/`, **generated into every SVG** at build time; nothing referenced at runtime |
| paper naming | `print-letter.svg`, `print-a4.svg` — the `--paper` token, so flag value and filename agree |
| `aggregate.svg` | the geometry master that sheets reference by id (today's `feathers-elongated.svg`) |
| PDFs | rendered from the print documents, parked at the target level |

## Tiler state (landed)

`tile_sheets.py` at the repo root already speaks the grammar this plan assumes, so the re-tile in
[step 4](#steps) needs no code change. Verified against the current masters:

| behaviour | state |
|---|---|
| sheet reference | relative to the output directory (`os.path.relpath` + `os.sep` → `/`), via `rel_href()` |
| output | `--out` required and its directory created; `--whatif` reports path, resolved href and output size |
| `sodipodi:docname` | the real output basename (`doc_name=os.path.basename(out_path)`) |
| provenance | one XML comment before `<svg>`: `tiled by tile_sheets.py: source=… paper=… trim=… safe=… overlap=… gap=… pages=… orientation=per-sheet` |
| shared defs | rendered by `emit_multipage_svg(shared_defs=…)`; no post-hoc `replace()` of the `<defs>` marker, so the silent no-op is gone |
| stylesheet | carried over from the master and gated: `require_style_rules()` fails unless the carried CSS plus `JOIN_CSS` defines `.join-line`, `.join-bar`, `.overlap`, `.note`. The old unconditional `CSS2` append is gone |
| CLI | `--paper <name>` required (or `--size WxH`), `--margin`/`--safe`, `--overlap`/`--gap`, `--list-papers`; sheet discovery is a class **token** test, so `sheet-bounds` and friends cannot match |

Measured with the current masters (letter, default overlap 12 / gap 10):

```
templates/sheets-home-feathers.svg    -> 28 pages from 15 sheets (13 tiled, 2 single-page)
templates/sheets-home-alignment.svg   -> 19 pages from 12 sheets (7 tiled, 5 single-page)
```

Both documents were regenerated and inspected: page counts 28 / 19, `class="…"` usage limited to
`join-line`, `join-bar`, `overlap`, `note`, two hoisted clip defs (`clip`, `clip-shared-2`), and a
provenance comment matching the parameters. These are the reference numbers for the post-reorg
re-tile; the regenerated files were not kept (see [step 4](#steps)).

## Target layout

```
templates/
  README.md                       naming grammar, pipeline, regeneration commands
  AGENTS.md                       folder rules (masters vs generated, machining model, registration)
  aggregate.svg                   geometry master, id-referenced by <use>
  css/
    geometry.css                  part, guide and mark presentation
    sheets.css                    sheet, label and registration presentation
  inline_css.py                   writes each master's <style> from css/; --check reports drift
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
        print-letter.svg
        print-a4.svg
      alignment/
        print-letter.svg
      feathers-letter.pdf
      alignment-letter.pdf
```

The `multipage` moniker is retired: the stage word is `print`, and the only thing that varies in
the name is the paper.

## File mapping

| now | after | notes |
|---|---|---|
| `templates/feathers-elongated.svg` | `templates/aggregate.svg` | geometry master, 250×700 mm, own stylesheet, 0 `<use>` |
| `templates/sheets-home-feathers.svg` | `templates/feathers/sheets.svg` | 15 sheets; 29 external hrefs + 14 internal mirror `<use>` |
| `templates/sheets-home-alignment.svg` | `templates/alignment/sheets.svg` | 12 sheets; 18 external hrefs |
| `templates/sheets-home-feathers-multipage.svg` | `templates/targets/home/feathers/print-letter.svg` | 28 pages; 28 external refs — **regenerate**, the file was deleted in `e568aed` |
| `templates/sheets-home-alignment-multipage.svg` | `templates/targets/home/alignment/print-letter.svg` | 19 pages; 19 external refs — **regenerate** |
| — | `templates/targets/home/feathers/print-a4.svg` | new output, same master, A4 paper |
| — | `templates/targets/home/feathers-letter.pdf` | render of `feathers/print-letter.svg` |
| — | `templates/targets/home/alignment-letter.pdf` | render of `alignment/print-letter.svg` |
| — | `templates/css/geometry.css`, `templates/css/sheets.css` | new: the stylesheet sources |
| — | `templates/inline_css.py` | new: generates each master's `<style>` from `css/` |
| `tile_sheets.py` (repo root) | `templates/tile_sheets.py` | move only; behaviour work has landed |
| `templates/print/` | *deleted* | empty directory, absorbed by `targets/` |
| `templates/sheets-home-print.pdf` | *deleted* | orphan: its source SVG was removed at the split |
| `templates/feathers-letter-landscape.pdf` | *deleted* | orphan: `feathers-aggregate.svg` no longer exists |

The two multipage SVGs are the one place this plan differs from a pure rename: they were deleted in
the "cleaning up svgs and tiling" commit and are untracked-generated now, so there is no history to
carry. Generate them at their new paths and let the first commit record them as additions.

## Reference rewrites

Only two kinds, both mechanical:

1. **Masters → geometry master.** Every external `<use>` in both `sheets.svg` files changes
   `feathers-elongated.svg#<id>` to `../aggregate.svg#<id>`:
   - `feathers/sheets.svg`: 29 occurrences (28 outline symbols + `calibration`)
   - `alignment/sheets.svg`: 18 occurrences (8 `*-align` symbols + `assembly-template`)
2. **Print documents → masters.** Regenerated, never hand-edited. The tiler emits
   `../../../feathers/sheets.svg#sheet-P1` (three levels: `feathers` → `home` → `targets` →
   `templates`). 28 references for feathers, 19 for alignment.

Untouched by any of this: all element ids, sheet ids, `inkscape:current-layer`, `data-sort-order`,
the registration geometry, and the mirror `<use href="#sheet-*-half">` references. The `<style>`
bodies are rewritten, but their rules keep their meaning apart from the fixes listed below.

## CSS consolidation

The presentation exists in three hand-maintained copies that have already drifted — `aggregate.svg`
1,549 chars / 19 rule blocks, `feathers/sheets.svg` 2,836 / 39, `alignment/sheets.svg` 2,668 / 35.
The tiler no longer adds a fourth: it carries the master's stylesheet over unchanged and only adds
the two rules for its own join marks (`JOIN_CSS`).

**Shape:** one source per audience, generated into every document at build time. Nothing is
referenced at runtime.

| source | contents | generated into |
|---|---|---|
| `css/geometry.css` | `.outline`, `.guide`, `.arrow`, `.divider`, `.mark`, family fills | `aggregate.svg`, both `sheets.svg` |
| `css/sheets.css` | `.label`, `.title`, `.note`, `.sheet-bounds`, `.crop`, `.overlap`, `.reg*` | both `sheets.svg` |

Each document therefore carries the rules it needs for its own rendering, so a `sheets.svg` styles
its own clones of `aggregate.svg` geometry without depending on the geometry master being reachable
*as a stylesheet*.

- **Generator**: `templates/inline_css.py` rewrites each master's `<style>` body from the sources;
  `--check` fails when a document's rules no longer match the source. Compare rules
  (selector → declarations, order-insensitive), not bytes: Inkscape normalises CSS syntax when it
  re-saves a file, so a byte comparison would report drift that isn't.
- **Which source each document gets**: `aggregate.svg` gets `geometry.css` only — it renders
  geometry, not sheets — and both `sheets.svg` files get `geometry.css` + `sheets.css`. A
  `sheets.svg` must keep the geometry rules because it clones `aggregate.svg` content, and the
  tiler carries that same style text into every print document.
- **Why inline instead of `@import`**: a stylesheet reference is a runtime dependency with a silent
  failure mode. Any consumer that is not Inkscape — a CAM tool, a browser, a PDF flattener — may drop
  it, and cut paths would quietly lose their stroke. Inlining keeps every document self-contained.
- **Measured rather than assumed** (Inkscape 1.4, the version the files declare; probes left in
  `.tmp/css-probe/`): inline `<style>` works; `@import url(…)` inside `<style>` works; the
  `<?xml-stylesheet?>` processing instruction is ignored; and a referenced document's `<style>` *does*
  style the cloned content, scoped to the clone and propagating through two external hops. The old
  comment in `tile_sheets.py` ("CSS does not cascade across an external `<use>` reference") is not
  true on 1.4 — the stylesheet is still inlined here, but for consumer independence, not because
  cross-document styling fails.
- **Rejected**: deleting the geometry block from the sheets masters and leaning on `aggregate.svg`'s
  stylesheet reaching the clones. It works in Inkscape per the probe, but it makes appearance depend
  on cross-document behaviour that other consumers need not honour — and there is nothing left to save
  once the rules are generated rather than forked.
- **Defects fixed in the sources, so every document inherits the fix**:
  - `.outline`'s `stroke-dasharray: 2.5, 2.5` is never reset — dashed *cut paths*, currently live in
    all three files. Remove it, or reset it in the later `.outline` rule.
  - `.outline` is defined more than once per file; collapse to one definition per source.
  - family fills lost their `.highlighted` scoping when the style was forked from the master into the
    sheets; restore the scope, or drop it deliberately.
- **The ragged middle is expected, and `.crop` is the one casualty.** Generated print documents use
  exactly `join-line`, `join-bar`, `overlap` and `note` (`class="…"` values in both regenerated
  documents); the tiler draws no crop ticks, so its style gate (`require_style_rules`) deliberately
  does not require `.crop`. `.crop` belongs in `sheets.css` because both sheets masters style their
  own crop furniture with it — it simply stops mattering downstream. Do not "fix" that by having the
  tiler demand every class the masters define; the gate is about what a *page* renders.

## Folder docs to add

- **`templates/README.md`** — the naming grammar, the pipeline (`aggregate.svg` → `<content>/sheets.svg`
  → `targets/<target>/<content>/print-<paper>.svg` → `<content>-<paper>.pdf`), which files are
  hand-edited vs generated, the CSS pipeline (edit `css/`, run `inline_css.py`), and the regeneration
  commands.
- **`templates/AGENTS.md`** — masters vs generated; the machining model (one pattern per sheet, the
  left half is the mirrored back of the right, no drawn left geometry and no second program); the
  mirror `<use>` and why labels are baked rather than cloned; registration conventions (axis along
  sheet Y at the bounds-rect centre, Ø6 through-holes, on-axis hole plus ±20 mm twin pair, top-left
  key, all marks inside the bounds rect); id conventions (`{Group}{N}{L|R}`, `sheet-<name>-*`);
  the `<style>` bodies are **generated from `templates/css/`** — edit the source and run
  `inline_css.py`, never hand-edit a `<style>`, and keep the presentation inline because a `@import`
  is a runtime dependency other consumers may drop (`<?xml-stylesheet?>` is ignored by Inkscape
  outright); cut paths must never be dashed; any master edit invalidates its print documents.
- **`templates/feathers/AGENTS.md`** — author only inside `sheet-*-half`; never add left geometry by
  hand; labels live in `sheet-<name>-labels`; sheet ids are referenced by the print documents, so
  renaming one means re-tiling.
- **`templates/alignment/AGENTS.md`** — the same, minus the mirror pattern, noting the alignment
  sheets are single-sided today.
- **`templates/targets/AGENTS.md`** — generated output: never hand-edit, regenerate instead; keep
  committing the generated documents.
- **`templates/targets/home/AGENTS.md`** — what `home` means and the exact per-paper commands, spelled
  so they can be checked against a shipped file's provenance comment.

## Steps

1. **Create directories and move what exists** (`git mv`, so history follows):
   ```
   git mv tile_sheets.py templates/tile_sheets.py
   git mv templates/feathers-elongated.svg templates/aggregate.svg
   mkdir templates/feathers templates/alignment templates/css templates/targets/home/feathers templates/targets/home/alignment
   git mv templates/sheets-home-feathers.svg templates/feathers/sheets.svg
   git mv templates/sheets-home-alignment.svg templates/alignment/sheets.svg
   ```
   The print documents are not moved — they no longer exist (see [step 4](#steps)).
2. **Rewrite the masters' external hrefs**: `feathers-elongated.svg#` → `../aggregate.svg#`
   (29 + 18 occurrences). Verify the counts before and after; nothing else in those files changes.
   Apply the same rewrite to the two `sodipodi:docname` values that still name the old files
   (`sheets-home-print.svg` in the alignment master, its own old name in the feathers master).
3. **Extract and generate the CSS.** Create `css/geometry.css` and `css/sheets.css` from the existing
   stylesheets (fixing the three defects above), add `inline_css.py`, run it over all three masters,
   and confirm `--check` is clean. This has to precede the re-tile so the generated print documents
   pick up the regenerated styles.
4. **Re-tile** the print documents at their new paths, then add the A4 variant:
   ```
   python templates/tile_sheets.py templates/feathers/sheets.svg --paper letter --out templates/targets/home/feathers/print-letter.svg
   python templates/tile_sheets.py templates/alignment/sheets.svg --paper letter --out templates/targets/home/alignment/print-letter.svg
   python templates/tile_sheets.py templates/feathers/sheets.svg --paper a4 --out templates/targets/home/feathers/print-a4.svg
   ```
   Expect 28 / 19 pages for the letter documents, and the same counts from `--whatif` before and
   after the reorg. Two scratch runs of the pre-reorg masters already produced 28 / 19 pages and
   were inspected (see [Tiler state](#tiler-state-landed)); they were deleted again rather than
   committed, so this step is what puts the documents back in the tree.
5. **Render the PDFs** from the print documents (Inkscape CLI at
   `C:\Program Files\Inkscape\bin\inkscape.com`, `--export-type=pdf`), writing them at the target level.
6. **Delete the orphans and the empty directory**: `templates/print/`,
   `templates/sheets-home-print.pdf`, `templates/feathers-letter-landscape.pdf` (the last two are
   already deleted in the working tree; stage them).
7. **Write `README.md` and the five `AGENTS.md` files** (outline above).
8. **Verify** (see below), then commit.

## Verification

- No file under `templates/` still contains `sheets-home` or `multipage` (grep the whole tree,
  including the generated documents).
- From `templates/feathers/`, `../aggregate.svg` resolves; from `templates/targets/home/feathers/`,
  `../../../feathers/sheets.svg` resolves. The earlier missing-sibling incident is the reason this
  check is explicit.
- `python templates/inline_css.py --check` is clean for all three masters, and a hand-edit to a
  `<style>` body is reported as drift (try it once, then revert).
- Outlines render **solid**: no `stroke-dasharray` survives in any stylesheet, and a rendered sheet
  shows continuous strokes — this is cut-path correctness, not cosmetics.
- Print documents carry each shared rule once (no duplicate `.overlap` / `.note`), and their
  `class="…"` values are a subset of `join-line`, `join-bar`, `overlap`, `note`.
- Shared defs: one `<clipPath>` per distinct page geometry (letter gives two: `clip`,
  `clip-shared-2`), no repeated id anywhere in the document.
- The provenance comment in each print document matches the command in
  `templates/targets/home/AGENTS.md` — paper token, trim, safe, overlap, gap, page count.
- The sheet href in a generated page is `../../../feathers/sheets.svg#sheet-P1` and resolves from
  `templates/targets/home/feathers/`.
- `python templates/tile_sheets.py … --whatif` matches the committed page counts before and after:
  **28** for feathers, **19** for alignment at `--paper letter`.
- Open both print documents (Inkscape): page counts 28 and 19, and the referenced sheet content
  renders — not a blank page and not dashes-only.
- `git status` shows the moves as renames, so the content diffs are the href rewrites and the
  regenerated `<style>` bodies.

## Rollback

Everything is a `git mv` plus the href rewrite in two files and regenerated `<style>` bodies; reverting
the commit restores the previous layout. The generated documents can be re-tiled from either layout,
and the CSS sources are additive until the old copies are deleted.

## Risks and notes

- **Parent-directory hrefs**: a print document copied away from the tree no longer renders. The PDFs
  are self-contained, so printing does not depend on the tree.
- **Deep relative paths**: `../../../<content>/sheets.svg` is valid and Inkscape resolves it, but it
  is one more silent failure mode. Keep `targets/` inside `templates/` rather than moving it to the
  repo root.
- **Generated `<style>` bodies fight hand edits**: the moment someone tweaks a rule in Inkscape,
  `--check` will flag it. That is the point, but it needs to be stated in `templates/AGENTS.md` so it
  reads as intended rather than as noise.
- **Inkscape rewrites CSS syntax on save** (spacing, `2.5, 2.5` → `2.5,2.5`). Compare rules, not
  bytes, or every save looks like drift.
- **The feathers master's root page is currently 10 mm × 10 mm** (`viewBox="-495.664 751.564 10 10"`).
  Unrelated to this plan and harmless to the tiler (which reads the sheet bounds rects), but
  whole-document PDF/PNG exports of that file will be a 10 mm square. Worth fixing while the file is
  open.
- **A4 parameter set** (210×297 trim, 200×287 safe, overlap 12, gap 10) is an assumption; confirm it.
- **Proof of the re-tile is what grounds this plan**: the 28 / 19 page figures and the generated-file
  facts above came from running the landed tiler over the *current* masters. Re-run
  `--whatif` after the moves and compare, rather than trusting the numbers as copied.
- **Naming**: `emit_multipage_svg` and a few comments still say "multipage". That is the retired
  moniker; renaming the function is optional cleanup, not part of the reorg.

## Out of scope

- Runtime `@import` externalisation of the stylesheet — decided against in favour of generated inline
  styles (see "CSS consolidation").
- Any change to the sheet geometry, registration or mirror pattern.
- Inlining sheet content instead of `<use>` (decided against: print documents stay thin references).
- Page-orientation policy, overlap/gap defaults, and paper sizes beyond the tiler's table.
- Any change to what the sheets documents contain — the tiler reads them, it does not author them.
- A commit policy for generated files: recommendation is to keep committing them, and say so in
  `templates/targets/AGENTS.md`.
