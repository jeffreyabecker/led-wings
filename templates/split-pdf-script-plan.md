# Plan — split `pages_to_pdf.py` into sheet building and PDF assembly

**Status: decided, not implemented.** The five open questions were settled on
2026-09-28 and are folded into §2 and §7 below. Nothing is changed yet:
`pages_to_pdf.py` is as committed in `d0cf1eb` through `0ec54a7`, and
`make_logical_pages.py` is untouched by this plan.

**Baseline for §5, already captured** (a live run of the committed
`pages_to_pdf.py`, kept in `.tmp-align/split-baseline*.json`):

| | |
|---|---|
| sheets | 52 (`sheet-001.svg` … `sheet-052.svg`) |
| tiled pages | 11 — `002`–`006`, `024`–`027`, `038`, `039` |
| fit pages | 28 |

The 52 sheet hashes are the real assertion in step 1; the counts are only a
sanity check on them.

**Scope:** `pages_to_pdf.py` only, plus the two files it becomes and the
documentation that names them. `make_logical_pages.py` keeps owning
`logical-pages/page-NNN.svg` exactly as it does now.

**The ask:** (1) a script that lays the logical pages out onto SVGs targeting a
particular print page size; (2) a script that renders a set of SVGs to PDF and
concatenates them.

**Verdict:** the seam is already there. The script renders nothing until
`render_sheets()` (line 234) and computes no layout after it; the only real cost
is deciding where the two checks live and stopping the two halves from each
delete-then-rewrite `print/sheets/`. Both settled in §2 and §7.

## 1. What the current script does

`pages_to_pdf.py`, 374 lines, in the order it runs:

| stage | lines | what it owns |
|---|---|---|
| constants | 56–70 | `PAPER_W/H`, `MARGIN`, `OVERLAP`, `FIT_SLACK`, and the derived `pw`, `ph`, `stride_x`, `stride_y` |
| read | 122–159 | `read_page()` — pulls title, W, H, CSS and content out of a page SVG by string slicing |
| fit/tile | 193–227 | `build_sheets()` — the single-sheet fast path, or the cols x rows grid with a clip path, corner ticks and a tile note |
| render | 234–254 | writes `sheets/sheet-NNN.svg`, `cairosvg.svg2pdf`s each, merges with `pypdf` into `feathers-letter-landscape.pdf` |
| thumbnails | 257–272 | `contact-sheet.png` from the merged PDF |
| verify | 279–328 | `verify_tiling()` (re-derive the grid and each transform) and `verify_scale()` (rasterise the cover, measure both calibration bars) |
| driver | 335–370 | reads pages, builds sheets, verifies, renders, writes the contact sheet, prints the summary |

Two couplings worth naming before touching anything:

- **`verify_tiling()` is the only thing that checks the arithmetic in
  `build_sheets()`.** It re-derives `cols`, `rows` and every tile transform from
  the paper constants and the emitted sheet. If the split puts those in different
  scripts, the self-check is orphaned and the tiling goes unverified.
- **`verify_scale()` measures the *cover*, and knows how to find it.** It assumes
  the cover is logical page 1 and that a page that fits is placed at
  `(MARGIN, MARGIN)`, so the bars drawn at page coords `(40, 70)` and `(40, 115)`
  land at `+MARGIN`. That assumption is about *layout*, which Script 1 owns, and
  it is checked in script 2 by rasterising the output.

## 2. The split

| | Script 1 — `make_print_sheets.py` | Script 2 — `sheets_to_pdf.py` |
|---|---|---|
| reads | `logical-pages/page-*.svg` | `sheets/sheet-*.svg` |
| writes | `sheets/sheet-NNN.svg` | `sheets/sheet-NNN.pdf`, `feathers-letter-landscape.pdf`, `contact-sheet.png` |
| owns | paper size, margins, overlap, fit slack, the fit/tile decision, clip, ticks, tile notes | rasterisation, merge order, thumbnails |
| checks | tiling (re-derived from its own constants); that its output is one SVG per record; that every sheet is exactly the paper size | every named SVG exists, is the paper size, and appears in the merged PDF in filename order; the scale bars |
| needs to know | nothing about the pages beyond what `read_page()` extracts | nothing about tiling or paper geometry |

The interface is a directory of same-size SVGs plus a manifest. Script 2 does not
need to know what a tile is, and Script 1 does not need cairosvg or pypdf.

### 2a. Paper size — flags

Today the size is four module constants. The ask is "targeting a specific print
page size", so Script 1 takes it as flags, with today's Letter-landscape values
as the defaults:

```
--paper WxH     279.4x215.9   sheet size in mm
--margin MM     5.0           unprintable border
--overlap MM    12.0          printed twice on adjacent tiles
--slack MM      2.0           overshoot that still gets one sheet
--pages-dir DIR logical-pages source (default: the pipeline's own)
--out-dir DIR   sheet SVGs + manifest (default: the pipeline's own)
```

`pw`, `ph`, `stride_x`, `stride_y` stay *derived*, never passed, so a caller
cannot hand in a combination the tiling formula disagrees with — which is exactly
the drift `verify_tiling()` exists to catch. A4 landscape (`297x210`) is the
obvious second value and belongs in the acceptance run, not in a default.

Flags rather than constants because the ask was explicitly to target a size:
a second size must be reachable without editing the script. The validation has to
carry the weight the constants used to: reject a margin that leaves no printable
area, an overlap wider than the printable area, and a slack larger than the
margin (which would let a page print into the unprintable border). Those three
assertions are the price of the flags and belong in Script 1's argument handling.

### 2b. The manifest

Script 2 needs one thing it cannot re-derive: which sheet carries the cover's
calibration bars, and with what offset. Script 1 writes
`sheets/manifest.json`:

```json
{
  "paper": {"w": 279.4, "h": 215.9}, "margin": 5.0,
  "stride": {"x": 257.4, "y": 193.9},
  "sheets": [
    {"file": "sheet-001.svg", "page": "page-001.svg", "title": "cover",
     "tile": 1, "cols": 1, "rows": 1, "transform": "translate(5 5)"}
  ]
}
```

Everything in it is already computed by `build_sheets()`; the manifest only
records it. It is also what makes Script 2's own check possible — "every sheet in
the manifest is present, is the paper size, and was merged in order" — and it
retires the `verify_scale()` assumption above, because the cover's offset comes
from the manifest rather than from a hardcoded `MARGIN`.

Rejected: having Script 2 read each sheet's `<text class="note">` tile label. It
works, but it makes the renderer parse a human-readable caption to recover
machine state, and the note is not emitted at all for the single-sheet fast path.

### 2c. Verification, split

| check | goes to | why |
|---|---|---|
| tiling re-derivation | Script 1 | it is arithmetic about tiling; the constants live here |
| each emitted sheet is the paper size, one per tile | Script 1 | same reason |
| every manifest SVG exists and is paper-sized | Script 2 | it is the renderer's input contract |
| merged PDF page count == sheet count, in order | Script 2 | it is the renderer's output contract |
| calibration bars measure 100 mm / 101.6 mm | Script 2 | it needs a rasterised sheet, which is Script 2's job |
| contact sheet | Script 2 | already there |

The scale check itself does not change: same 300 dpi render, same two bar probes,
same ±1 mm tolerance. Only its *input* changes — it measures the sheet named in
the manifest instead of `doc[0]`. That is a strict improvement: `doc[0]` was
right only while the cover stayed logical page 1 and fitted untitled.

## 3. What must not move

The emitted sheet SVGs are the contract between the halves and the record of the
tiling. Splitting the script must not change a single byte of them.

- `read_page()`, `build_sheets()`, `sheet_svg()`, `corner_ticks()`, `CLIP_DEF`,
  `CSS2`, and every derived constant move to Script 1 **unchanged**.
- `render_sheets()`'s render loop, `contact_sheet()`, and `OUT_PDF` move to
  Script 2 **unchanged**.
- `logical-pages/page-*.svg` and `feathers-letter-landscape.pdf` keep their paths.
- `sheets/` keeps its path, so the existing `.gitignore` entries for `sheets/` and
  `contact-sheet.png` still cover the intermediates.

## 4. Hazards

| hazard | containment |
|---|---|
| the two scripts each clear `sheets/` and delete the other's output | Script 1 unlinks only `sheet-*.svg` (plus its own `manifest.json`); Script 2 unlinks only `sheet-*.pdf`. Today's `render_sheets()` clears **both** — splitting that loop is the one edit that must not be a copy/paste |
| Script 2 silently renders a stale sheet set | Script 1 rewrites every `sheet-*.svg` and the manifest in one run; Script 2 asserts the PDF page count equals the manifest length. A stale `.pdf` next to a fresh `.svg` cannot survive the count check |
| the scale check loses its fixed reference point | the manifest carries the cover's sheet and offset (§2b) |
| a paper-size flag combination the formula disagrees with | keep `pw`/`ph`/`stride` derived; `verify_tiling()` re-derives from the same numbers Script 1 used |
| the split changes sheet bytes | Script 1 must produce byte-identical `sheet-*.svg` for the default Letter arguments; capture hashes before the split and compare after |
| someone runs the old name | delete `pages_to_pdf.py` in the same commit; there is no README to redirect, so the module docstring is the only place a stale command could linger |

## 5. Acceptance test

Step 0 is already done — see the baseline table at the top of this document.
Re-take it if the split starts from a different commit.

1. `make_print_sheets.py` with default arguments reproduces **52/52
   byte-identical** `sheet-*.svg` files, and prints the same line the legacy
   script did: `39 logical pages -> 52 Letter sheets (11 tiled, 28 fit)`. The
   hashes are the assertion; the counts only say whether the shape changed too;
2. `sheets_to_pdf.py` produces `feathers-letter-landscape.pdf` with **52 pages**,
   each 279.4 x 215.9 mm, in filename order. **The merged file can be compared by
   hash**: `cairosvg.svg2pdf` was checked and produces byte-identical output
   across runs for the same input, so the baseline's 654 207-byte PDF is a valid
   target. If the bytes do differ, treat that as a finding to explain before
   accepting the split, not as expected noise;
3. both scripts print their own checks and pass:
   `tiling structural check: OK` from Script 1, and the merge check plus the two
   calibration-bar measurements from Script 2;
4. `make_print_sheets.py --paper 297x210` succeeds and every emitted sheet is
   297 x 210 mm. A4 landscape also yields **more** sheets than Letter — measured
   at 55 against 52, because its printable height is 200 mm against 205.9 and
   that is what costs the extra rows — so both the size *and* the count can be
   asserted. Run it into a scratch `--out-dir` so it cannot clobber the Letter
   sheet set that steps 1–3 depend on;
5. `grep -rn "pages_to_pdf" --include=*.py .` returns **nothing**; the two
   historical plan docs may still mention it and should be left as written;
6. neither script writes into the other's file set: after `sheets_to_pdf.py`
   runs, every `sheet-*.svg` from `make_print_sheets.py` is still present and
   byte-identical. This is the check for the shared-directory hazard in §4.

## 6. Risks

| risk | containment |
|---|---|
| splitting orphans the tiling self-check | §2c puts it with the constants it checks; acceptance step 3 requires Script 1 to print it |
| the scale check becomes vacuous (passes because it measured nothing) | it asserts ink is present where the manifest puts each bar, and `main()` fails on a mismatch rather than on a missing measurement |
| the manifest drifts from the sheets | it is written in the same loop that emits them, and Script 2 asserts the sheet list matches the files on disk |
| a second paper size silently keeps Letter geometry | acceptance step 4 checks each sheet's *size*, not just that the run exits 0 |
| the two halves clear each other's output | Script 1 unlinks only `sheet-*.svg` (+ the manifest); Script 2 only `sheet-*.pdf`. Today's `render_sheets()` clears **both**, so splitting that loop is the one edit that must not be a copy/paste — acceptance step 6 is the check |
| `contact-sheet.png` layout assumes a page count | `contact_sheet()` already takes `n_pages` and derives rows; unchanged |

## 7. Decisions

All five were settled before implementation. They are decisions, not preferences:
implement to them.

| # | question | decision |
|---|---|---|
| 1 | names | `make_print_sheets.py` and `sheets_to_pdf.py`, as proposed. The pair reads as the pipeline it is: logical pages → print sheets → PDF. |
| 2 | paper size as flags or constants? | **Flags**, with today's Letter landscape values as the defaults. See §2a for the three validations the flags make mandatory. |
| 3 | should Script 1 also emit a page-size summary (paper used, tiles per page) for a README? | **No, not now.** No pipeline README exists; adding one is separate work. |
| 4 | render-quality knob on Script 2? | **No.** `cairosvg` renders vector-clean at the PDF's own resolution, so there is nothing to tune. A knob with no effect is worse than no knob. |
| 5 | delete `pages_to_pdf.py`, or keep it as a thin wrapper? | **Delete it**, once both new scripts pass §5. A wrapper is a third thing to keep honest, and it would still be the file people reach for by habit. |

Consequences of #5 worth stating, because they are easy to miss:

- The deletion lands in the **same commit** as the two new scripts. A commit
  that leaves both the old script and its replacements present is the one state
  where "which one do I run" has two answers.
- There is no README to update, so the surviving references are the module
  docstrings, `make_logical_pages.py`'s two mentions of `pages_to_pdf.py` (its
  module docstring and the `shelf()` comment about the left margin), and the two
  historical plan docs. §5 step 5 covers the greps; the historical plan docs are
  left as written because they describe the pipeline as it was when they were
  written.
- `make_logical_pages.py`'s references should be updated to name
  `make_print_sheets.py` in the same commit, since a docstring pointing at a
  deleted file is worse than no pointer.

## 8. Order of work

1. capture the §5 step-0 baseline;
2. write `make_print_sheets.py`; run it; assert the 52 sheet hashes are
   byte-identical;
3. write `sheets_to_pdf.py`; run it; assert the merge and scale checks pass;
4. run the A4 acceptance check (§5 step 4);
5. update `make_logical_pages.py`'s two references, delete `pages_to_pdf.py`,
   and re-grep.

## Appendix — measurements taken for this plan

| probe | result |
|---|---|
| `pages_to_pdf.py` length | 374 lines |
| render boundary | `render_sheets()` starts at line 234; nothing above it renders, nothing below it computes layout |
| shared state the split must not duplicate | the `sheets/` cleanup in `render_sheets()` (lines 237–240) unlinks **both** `.svg` and `.pdf` |
| the only layout assumption outside `build_sheets()` | `verify_scale()`'s `doc[0]` + `MARGIN` offset (lines 323–327) |
| page size now | Letter landscape 279.4 x 215.9 mm, margin 5, overlap 12, slack 2 |
| files named by both scripts | `sheets/sheet-NNN.svg`, `sheets/sheet-NNN.pdf`, `feathers-letter-landscape.pdf`, `contact-sheet.png` |
| third-party imports by half | Script 1: none. Script 2: `cairosvg`, `pypdf`, `pdfium`, `PIL` |
| baseline sheet count / tiled | 52 sheets, 11 tiled, 28 fit — all 52 hashes captured |
| baseline PDF | 654 207 bytes |
| A4 landscape sheet count, same pages | 55 (printable 287 x 200 mm, against Letter's 269.4 x 205.9) |
| `cairosvg.svg2pdf` repeatability | byte-identical across runs, so the merged PDF can be hash-compared |
