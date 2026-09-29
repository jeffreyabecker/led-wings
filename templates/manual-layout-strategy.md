# Plan — hand-editable print layout in feathers-aggregate.svg

**Status: proposed, not implemented.** The direction below is settled except for
one defaulted decision (marked **default** in §7) that should be signed off
before any code is written. Nothing is changed yet.

**The problem this addresses:** the print layout is *computed* — `SECTIONS` in
`make_logical_pages.py` decides page composition, and `build_sheets()` in
`make_print_sheets.py` decides sheet tiling — so the final output is only as good
as the two algorithms, and neither is editable by hand. The fix is to make layout
a first-class, hand-editable artifact in the Inkscape document that already owns
the geometry, and demote the scripts from *deciders* to *seeders + extractors*.

**Baseline to capture before any work (§5 step 0):** a live run of the three
committed scripts, with the same shape as the `split-pdf-script-plan.md` baseline:

| | |
|---|---|
| logical pages | 39 (`page-001.svg` … `page-039.svg`) |
| sheets | 52 (`sheet-001.svg` … `sheet-052.svg`) |
| tiled pages | 11 — `002`–`006`, `024`–`027`, `038`, `039` |
| fit pages | 28 |
| merged PDF | `feathers-letter-landscape.pdf`, 654 207 bytes (52 pages) |

## 1. Current state

Three scripts, two of which own layout decisions the user cannot touch without
editing Python:

| script | reads | decides (auto) | writes |
|---|---|---|---|
| `make_logical_pages.py` | `feathers-aggregate.svg` (feather geometry) | **page composition**: which feathers share a page, order, the 90° rotations — hardcoded in `SECTIONS` (lines 304–337); the mirrored-pair / shelf / label math | `logical-pages/page-NNN.svg` |
| `make_print_sheets.py` | `logical-pages/page-*.svg` | **sheet layout**: fit vs tile, the tile grid, transforms, clip, crop marks | `sheets/sheet-NNN.svg`, `sheets/manifest.json` |
| `sheets_to_pdf.py` | `sheets/sheet-NNN.svg`, `manifest.json` | (none) | per-sheet PDFs, merged `feathers-letter-landscape.pdf`, `contact-sheet.png`, the scale check |

`feathers-aggregate.svg` is already the single hand-editable source of truth for
*geometry* — the family groups (`B`, `P`, `PC`, `A`, `SC`, `MC`, `LC`, `S`), the
`outline-toplines` placement group, and one Inkscape layer (`align`). The
*geometry catalog* is deliberately `<use>`-free (the consolidation inlined it);
the new layout layers reintroduce `<use>`s, scoped to references only (§3a, §7
#5).

## 2. Target model — three tiers in one file

The aggregate gains two new top-level Inkscape layers, so the file owns the whole
pipeline as one editable document:

1. **Feathers** (already there, unchanged) — geometry. Single source of truth for
   shape.
2. **`pages`** (new layer) — one group per logical page, whose composition is
   *declarative* — `data-items="A1 A2 A3"`, `data-rotate="90"`,
   `data-kind="pairs|whole|overlay|cover"` — replacing the Python `SECTIONS`
   manifest. The seeder expands each declaration into a page group of `<use>`
   references to clean feather defs (§3a): the right half is a direct reference,
   the left half the same reference under `scale(-1 1)`, and each pair keeps its
   stable id (`<g id="X-pair">`, plus `X-left` / `X-right`). The declaration is
   the primary edit surface; the pair groups are a drag escape hatch.
3. **`sheets`** (new layer) — one child layer per sheet, containing placed page
   references (`<use href="#page-NNN">`) positioned and rotated by hand. The user
   drags pages between sheets, repositions and rotates them, reorders or
   adds/removes sheets. Oversized pages appear as explicit per-tile `<use>`
   instances with clip paths (seeded from today's tile math), so "manual splits"
   means *adjust from correct*, never rebuild from scratch.

Editing maps to the two levers the user asked for:

| control | edit surface |
|---|---|
| sheet layout | `sheets` layer — drag / rotate / reorder page instances |
| page composition | `pages` layer — `data-items` list (+ rotate / kind) per page |

## 3. The new pipeline — seed → edit → extract → render

- **`seed_layout.py` (new)** — reads the feathers and the `pages` declarations out
  of the aggregate and writes both the `pages` and `sheets` layers into it in one
  atomic pass. It *reuses* the building and verification code from
  `make_logical_pages.py` (`mirror_check`, `verify_body`, the shelf layout,
  `read_align`, `read_placement`) and the tile math from `make_print_sheets.py`
  unchanged — only the sink changes: instead of `page-NNN.svg`/`sheet-NNN.svg`
  with inlined geometry, it emits clean feather defs (reference targets) plus
  `<use>`-based `pages` and `sheets` layers. One writer, not two, so nothing can
  clobber the aggregate.
- **`extract_sheets.py` (new)** — reads the `sheets` layer back out of the
  aggregate, **resolves the `<use>` graph to inline geometry**, validates it, and
  writes `sheets/sheet-NNN.svg` + `sheets/manifest.json`. The emitted sheets are
  therefore `<use>`-free, exactly as today, so the renderer contract is unchanged
  (§3a).
- **`sheets_to_pdf.py` (unchanged)** — still consumes sheet SVGs + manifest and
  renders the merged PDF, contact sheet, and scale check.

`make_logical_pages.py` and `make_print_sheets.py` become the engine the seeder
imports (their pure functions survive); their file-writing `main()`s are retired
once the seeder reproduces the baseline (§5).

The seeder is re-runnable but **additive**: a re-seed regenerates the `pages` and
`sheets` layers (the way today's scripts regenerate `logical-pages/` and
`sheets/`), so it is the deliberate "throw away my layout edits and re-derive
from current geometry" gesture — exactly the on-demand seed the user asked for.

### 3a. Reference targets and `<use>` resolution

The `<use>`s point at clean, true-scale def groups the seeder emits into a
delimited section, **not** at the catalog's family groups: a feather's catalog
position is the product of its family group transform, which is an arrangement of
the Inkscape *view*, not the print geometry `make_logical_pages.py` uses. So the
seeder writes one def group per item in the same local `[0,W]x[0,H]` frame the
current script builds (`right_transform`), and the layout layers reference those
defs. This is the `-def` reference-target structure the consolidation removed —
reintroduced, deliberately, *only* for the layout layers; the geometry catalog
stays inlined and untouched.

The extractor flattens the whole reference graph to concrete geometry before
writing a sheet: nested `<use>` (sheet → page → feather def) and the `scale(-1 1)`
mirror on the left half are resolved into the same inline paths today's
`build_pair()` produces. That is what keeps the renderer and the §5
byte-identical baseline honest — cairosvg never sees a `<use>`; it renders the
same flattened sheet SVGs it renders today.

### 3b. The manifest survives

`extract_sheets.py` writes the same `manifest.json` shape
`make_print_sheets.py` writes today (`paper`, `margin`, `stride`, `sheets[]`
with `file`, `page`, `title`, `tile`, `cols`, `rows`, `transform`), so
`sheets_to_pdf.py` is untouched. The cover's sheet and offset — which
`verify_scale()` reads — come from the sheet layer's metadata rather than from a
re-derived assumption, the same improvement `split-pdf-script-plan.md` §2b made.

### 3c. `.gitignore`

`templates/print/sheets/` stays gitignored (the extractor regenerates it).
`templates/print/logical-pages/` can stay gitignored or be dropped: the pages now
live in the aggregate, not in `page-NNN.svg`. The aggregate itself — now carrying
layout — is tracked, which is the point of the refactor.

## 4. What must not move

- The feather geometry in the aggregate, byte for byte, unless the user edits it
  by hand.
- The verification logic, relocated, not dropped: `mirror_check`,
  `verify_body`, `verify_tiling`, `verify_sheets`, and `verify_scale` all survive
  — the first two inside the seeder, the tiling/paper checks inside the extractor,
  the scale check stays in `sheets_to_pdf.py`.
- The **geometry catalog** stays `<use>`-free: only the new layout layers
  (`pages`, `sheets`) and their def targets use references. The emitted sheet
  SVGs stay `<use>`-free, so the renderer contract is unchanged (§7 #5).
- The emitted sheet SVGs remain the contract the extractor produces and the
  renderer consumes, with the same `sheet-NNN.svg` naming.

## 5. Acceptance test

Step 0 is the baseline table at the top. Re-take it if the work starts from a
different commit.

1. **Seed → extract → render reproduces today's output byte-identically.**
   Running `seed_layout.py` on the default declarations, then `extract_sheets.py`,
   then `sheets_to_pdf.py` produces 52/52 byte-identical `sheet-*.svg` files and a
   byte-identical `feathers-letter-landscape.pdf`. This is the round-trip
   guarantee, and it now also proves the `<use>` resolution is lossless: the
   extractor's flattened output must equal the inline sheets the current scripts
   emit. So every later divergence is attributable to a hand edit, not to the
   machinery.
2. **Inkscape round-trip.** Open the seeded aggregate in Inkscape, save it with no
   edits; `extract_sheets.py` still reproduces the baseline. This pins down the
   "re-save drift" hazard in §6.
3. **A hand edit is honored.** Move one page instance from one sheet layer to
   another (and, for an oversized page, reshape a clip), re-extract, and confirm
   the moved page appears on the new sheet and the reshaped clip changes the split
   — with no other sheet's bytes changing.
4. **Guardrails fail loudly.** The extractor rejects: a sheet layer that is not
   paper-sized; a page instance whose ink sits outside the printable area with no
   clip; a `sheets` layer referencing a page id that no longer exists; a missing
   cover. Each rejection names the layer and the object.
5. **`sheets_to_pdf.py` is untouched** and still passes its own merge + scale
   checks against the extractor's output.
6. **No stale-file confusion.** After a re-seed, every `sheet-*.svg` on disk is
   regenerated from the current aggregate; running `extract_sheets.py` with a
   stale sheet set fails the manifest-count check (unchanged from today).

## 6. Hazards

| hazard | containment |
|---|---|
| Inkscape re-serialises the aggregate and the extractor misreads it | the extractor reads semantics (ids, `data-*`, transforms, clip paths, layer `groupmode`), never byte layout; acceptance step 2 is the check |
| nested `<use>` / `scale(-1 1)` mirror resolution diverges from the current inline output | the extractor flattens to inline geometry before writing, and acceptance step 1 pins that flattening to today's byte output; cairosvg never sees a `<use>` (§3a) |
| the seeder's def targets drift from the catalog geometry | both are derived from the same `data-wh` / `data-vb` / `d` in one pass, and `verify_body` still renders each def target |
| the aggregate grows and mixes catalog with layout | layout lives in two delimited top-level layers; `<use>` references (not copies) are what keep it lean (§7 #5) |
| a hand edit silently prints wrong (page off-sheet, split wrong) | extractor guardrails (acceptance step 4) + the surviving scale check |
| two writers clobber the aggregate | one seeder writes both layers in one pass; re-seed regenerates both, never merges |
| the declarative manifest drifts from the emitted pages | the seeder writes both from the same declaration in one pass; the extractor asserts every sheet references a declared page |
| retiring the old `main()`s orphans their verification | each check is relocated to a surviving stage (§4), not deleted |

## 7. Decisions

All are settled for the plan except the one marked **default**, which should be
signed off before implementation. They are decisions, not preferences: implement
to them.

| # | question | decision |
|---|---|---|
| 1 | scope of manual control | **both** sheet layout and page composition |
| 2 | starting point | **seed from today's output**; re-seed on demand, never start blank |
| 3 | oversized pages | **manual splits** — per-tile clip instances seeded from today's tile math |
| 4 | where the layers live | **add `pages` + `sheets` layers to `feathers-aggregate.svg`** (one file, one source of truth) |
| 5 | inline vs `<use>` for placed pages | **`<use>` references.** Pages reference clean feather defs; sheets reference pages. The extractor flattens the graph to inline geometry, so the emitted sheets stay `<use>`-free and the renderer is unchanged. This keeps the layout layers small and makes a feather edit propagate to every sheet without a re-seed; it reintroduces the `-def` reference-target structure the consolidation removed, scoped to the layout layers only (§3a) |
| 6 | page-composition edit model | **declarative `data-*` attributes** expanded by the seeder (mirror/shelf/label math stays in code); the seeder still emits `<g id="X-pair">` groups as a drag escape hatch |
| 7 | acceptance bar | **default: seed → extract → render reproduces today's 52 sheets + 654 207-byte PDF byte-identically.** The alternative — design a new layout from scratch instead of seeding today's — is deferred, not dropped |
| 8 | script names | `seed_layout.py` (new), `extract_sheets.py` (new), `sheets_to_pdf.py` (unchanged); `make_logical_pages.py` / `make_print_sheets.py` become imported engines, their file-writing `main()`s retired in the same commit that first reproduces the baseline |
| 9 | page-NNN.svg fate | **obsolete** — pages live in the aggregate; the `logical-pages/` gitignore entry can stay or go, the files stop being written |

Consequences worth stating:

- The aggregate is promoted from "geometry catalog" to "the whole print
  pipeline, editable". The tracked artifact that mattered (`feathers-letter-
  landscape.pdf`) now has an upstream tracked artifact (the layout layers), so a
  layout change is a diff in the aggregate, not a regenerate-and-hope.
- `make_logical_pages.py`'s two docstring references to `pages_to_pdf.py` /
  `make_print_sheets.py` and the `shelf()` comment about the left margin must be
  updated to name the seeder/extractor in the same commit that retires the old
  `main()`s, so no docstring points at a deleted entry point.

## 8. Order of work

1. capture the §5 step-0 baseline (hashes of all 52 sheets, the PDF, the 39
   logical pages);
2. write `seed_layout.py`; run it; assert it emits `pages` + `sheets` layers into
   a copy of the aggregate;
3. write `extract_sheets.py`; run it on the seeded aggregate; assert the 52 sheet
   hashes and the PDF are byte-identical (acceptance step 1);
4. run the Inkscape round-trip spike (acceptance step 2);
5. run one hand edit end-to-end (acceptance step 3) and the guardrail cases
   (acceptance step 4);
6. move `SECTIONS` into the aggregate as the declarative `pages` manifest, retire
   the two file-writing `main()`s, and update the stale docstring references in
   the same commit.

## Appendix — measurements taken for this plan

| probe | result |
|---|---|
| current pipeline shape | 3 scripts; 2 own auto layout decisions (`SECTIONS`, `build_sheets`) |
| logical pages | 39 — cover 1, mirrored pairs 15, rot90 4, whole-wing 2, overlays 8 × 2 |
| sheet baseline | 52 sheets, 11 tiled (`002`–`006`, `024`–`027`, `038`, `039`), 28 fit |
| merged PDF | 654 207 bytes, 52 pages |
| aggregate | `feathers-aggregate.svg`, 42 905 bytes, geometry catalog `<use>`-free, one layer (`align`); layout layers add `<use>`s |
| existing pair ids | `build_pair()` emits `<g id="X-pair">` with `X-left` / `X-right` |
| manifest fields | `paper`, `margin`, `stride`, `sheets[]` (`file`, `page`, `title`, `tile`, `cols`, `rows`, `transform`) |
| reused verification | `mirror_check`, `verify_body` (seeder); `verify_tiling`, `verify_sheets` (extractor); `verify_scale` (`sheets_to_pdf.py`) |
