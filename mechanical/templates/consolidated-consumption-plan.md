# Plan — point `make_logical_pages.py` at `feathers-aggregate-conslidated.svg`

**Status: Steps 0 and 1 done. Step 2 not started.** Step 1's changes now live in
`make_logical_pages_consolidated.py`, an untracked working copy; the original
`make_logical_pages.py` has been reverted to `032b6fc` and verified byte-identical
to the Step 0 baseline. Both aggregates are untouched. See §8.

**Scope:** `make_logical_pages.py` only — the three readers and the constants they
read. `pages_to_pdf.py` is untouched: it only ever sees `page-NNN.svg`, so it
cannot be affected. Both aggregates are read-only inputs.

**The ask:** make the print script consume the consolidated aggregate. Minimal ID
plumbing first, observed, then decide.

**Note on the filename.** The new file is `feathers-aggregate-conslidated.svg` —
"conslidated", misspelled, and committed that way in `032b6fc`. Referred to below
by its real name. Renaming it is a separate decision.

---

## 1. What the consolidated file is

`032b6fc` ("consolidating aggregates") adds a second aggregate alongside
`feathers-aggregate-min.svg`. It is the same drawing, flattened:

| | `feathers-aggregate-min.svg` | `feathers-aggregate-conslidated.svg` |
|---|---|---|
| container | `<g id="geometry-source" style="display:inline">` | none — groups sit at the root |
| feather geometry | `<g id="X-def">` | `<g id="X">`, nested under a prefix group `<g id="P">`, `<g id="S">`, … |
| topline geometry | `<g id="X-topline-def">` | `<g id="X-toplines">` (plural) |
| placement | `<g id="placement-top-lines">` + `<g id="placement-total-outline">`, built from `<use href="#X-def">` | **no `placement-*` ids, zero `<use>` elements** |
| nearest equivalents | — | `<g id="toplines">` (8 nested groups), `<g id="upper-outline">` |
| whole-wing silhouette | `<g id="upper-outline-def">` | `<g id="upper-outline">` |
| `data-wh` / `data-vb` | on all 36 geometry groups | on all 36 geometry groups, same values |
| id count | 138 | 95 |

The `<use>` elements are gone entirely, which is the structural change that
matters: the geometry groups now carry their own `transform`, where the old file
kept placement on a separate `<use>`.

---

## 2. Step 0 — baseline, before anything is edited

Run the script unmodified against `feathers-aggregate-min.svg` and record the
SHA-256 of the 25 `mechanical/templates/print/logical-pages/page-*.svg`.

This is the parity target. Without it, "the script ran" is unfalsifiable and every
later difference is unattributable. `consolidate-plan.md` §6 used exactly this
baseline, and reported 25 byte-identical pages and 30 sheets from
`pages_to_pdf.py`.

---

## 3. Step 1 — IDs only

The smallest change that lets the script address the new file. No frame math, no
layout math.

| # | change | why |
|---|---|---|
| 1 | `AGG_SVG` → `feathers-aggregate-conslidated.svg` | the point of the exercise |
| 2 | header comment above it: drop the "hidden `#geometry-source` group" description | it is now false |
| 3 | `_def_group(name)`: try `name`, then `f"{name}-def"`, else assert naming **both** spellings | one function feeds all three readers; accepting both keeps the old aggregate working while this lands |
| 4 | `read_topline(name)`: look up `f"{name}s"` | the id is `A-toplines`, not `A-topline` |
| 5 | `PLACEMENT_GROUPS = ["toplines", "upper-outline"]` | the two groups the placement page is measured from |
| 6 | `read_placement()`: replace the `<use>`-walking loop with a loop over `PLACEMENT_GROUPS`, each group emitted with its own `transform` | there are no `<use>` elements left to walk |

Then run it and read the failure. Step 1 is expected to get through the 28
feathers and the 8 toplines and stop at placement.

---

## 4. Step 2 — the three things Step 1 will not fix

### 2a. `toplines` is a group of groups

`_group_content()` iterates a group's **direct** children looking for `path` and
`circle`. `<g id="toplines">` holds eight `<g id="X-toplines">` elements, so it
serializes to the empty string and the placement page measures nothing.

Fix: recurse into nested `<g>`s. Same guard applies to the recursion as to the
loop — only `path` and `circle` become output.

### 2b. Ink

`measure_ink()` renders at 150 dpi and raises `SystemExit("rendered SVG produced
no ink")` when the raster has no pixel below 128.

Two differences from the old file feed into this:

- the consolidated file carries stroke **inline** —
  `style="display:inline;fill:none;stroke:#000000;stroke-width:0.264583px;…"` —
  where the old toplines were bare `<path>` elements that picked up the script's
  own `.guide` class;
- the wing silhouette is `stroke-width: 0.228236`, and the placement page is
  measured at 300 × 300 mm, so the whole thing is a thin outline in a large frame.

Candidate fixes, in the order to try them:

- **(a)** `_group_content()` carries the source `style` over onto the emitted
  path, in addition to the `class="guide"` it already sets;
- **(b)** normalize instead: keep `class="guide"`, drop the source style.

A sanity check already run is worth recording: with the 300 mm harness, a plain
`M 100,100 L 200,200` line measures fine, so the harness itself works. If the
silhouette still measures as no ink with its style carried, the thing to question
is the **measurement** (dpi, threshold, `min(xs)` over a large raster), not the
markup — and changing it is a deliberate decision, not a cleanup.

### 2c. Frames with a transform on the geometry group — **the open decision**

The old `<use>` carried the placement; the consolidated file moved it onto the
geometry group. Verbatim from the file:

```xml
<g id="P" transform="matrix(0.99973673,0,0,1.2001191,89.236625,104.68468)">
  <g id="P1" data-wh="107.70177 348.70091"
     data-vb="171.95 164.833 107.70177 348.70091"
     transform="matrix(1,0,0,-1,-135.6171,554.80515)">
    <path …/>
```

```xml
<g id="B" transform="matrix(1.0060486,0.09641559,-0.01794757,1.1907292,44.966115,-2005.3888)">
  <g id="B1" data-wh="193.15454 81.754908"
     data-vb="108.29541 44.994112 193.15454 81.754908"
     transform="matrix(0.0348995,0.99939083,0.99939083,-0.0348995,-32.5625,1696.7032)">
    <path …/>
```

Today `right_transform()` emits only `translate(-x0 -y0)` and never looks at any
transform on the group, while `read_feathers()` still applies
`rotate90 = name.startswith("B")` — a rule `consolidate-plan.md` §4 says belongs
in the script because the B-group rotation used to live inside the path data.

Two options:

- **(i) minimal** — apply the group's own transform around the content, ahead of
  `translate(-x0 -y0)`, and keep `data-vb` as the frame. The path data is in the
  same coordinate space `data-vb` records, so this is a wrapper, not a
  re-derivation.
- **(ii) general** — derive orientation and frame from the group's transform
  matrix and stop hard-coding `rotate90`.

**Evidence for (i), not verification of it.** A probe run with only the ID
remapping in place reported, for all 28 feathers, a body bounding box inside
`[0,W]×[0,H]`, a placed size equal to `data-wh`, and `mirror=ok`; all 8 toplines
likewise. That is consistent with (i) and inconsistent with "the transform must be
baked in", but it ran while `_group_content` was already being edited, so it is a
signal, not a result.

**This step is not taken unilaterally.** If it is the only thing between the
script and a clean run, the plan is to stop, show the diff, and let the choice be
made explicitly.

---

## 5. Step 3 — parity, not eyeballing

Re-run and diff the 25 pages against the Step 0 hashes. Every page that moves is
either explained or the change is reverted. Report which pages differ and by how
much. `pages_to_pdf.py` is then run only as a check — it is not edited.

---

## 6. Out of scope unless asked

- Renaming `feathers-aggregate-conslidated.svg` to fix the typo.
- Deleting or retiring `feathers-aggregate-min.svg`.
- Changing `measure_ink()`'s dpi or threshold.
- Touching `pages_to_pdf.py` or either aggregate.
- Deciding (i) vs (ii) above without being asked.

---

## 7. Open questions

1. **§2c** — minimal wrapper (i) or transform-derived orientation (ii)?
2. **§2b** — carry the source `style` (a) or normalize to `.guide` (b)? The two
   differ in what the placement page looks like: (a) reproduces the aggregate's
   stroke weights, (b) makes it match the alignment-guide pages.
3. Is the consolidated file the **new intended source**, with `-min.svg` retired —
   or a variant to be supported alongside it? Step 1's dual-spelling lookup is
   written to make this cheap either way, but the endpoint differs.
4. Does `make_logical_pages_consolidated.py` get committed as a second entry
   point, or is it scratch — deleted once its changes are folded back into
   `make_logical_pages.py`? (Committing two near-identical 750-line scripts is
   the thing the last two plans in this directory worked to avoid.)

---

## 8. Log — Steps 0 and 1

### Step 0: baseline, 2026-09-27

`python make_logical_pages.py` against the unmodified script and
`feathers-aggregate-min.svg`: **25 logical pages**, titles and page sizes as the
manifest declares (cover, 20 item sections, 2 placement halves, 2 guide-strip
halves).

Sorted SHA-256 of each page was recorded to
`%TEMP%\wings-baseline\baseline.sha256` — deliberately **outside the repo**, since
`print/logical-pages/` is generated output and does not belong in a commit.

Baseline page count is 25, matching `consolidate-plan.md` §10. The tiled-sheet
count that plan records is 30; `pages_to_pdf.py` was **not** run in Step 0, so Step
3's sheet-count check still needs that baseline established.

### Step 1: the six ID changes

Applied to a **copy**, `make_logical_pages_consolidated.py`. The original
`make_logical_pages.py` was then reverted with `git checkout --` and re-run; it
reproduces the Step 0 baseline **25/25 pages byte-identical**, so the known-good
pipeline is intact and the two files can be diffed against each other.

The copy differs from the original only in the six ID changes below, +32/−30 lines:

1. `AGG_SVG` → `feathers-aggregate-conslidated.svg`, header comment rewritten.
2. `_def_group(name)` tries `name` then `{name}-def`, and raises naming both.
3. `read_topline(name)` looks up `f"{name}s"`.
4. `PLACEMENT_GROUPS = ["toplines", "upper-outline"]` added next to `TOPLINES`.
5. `read_placement()` loops over `PLACEMENT_GROUPS` instead of walking `<use>`s.
6. (same function) the placement-* filter and dangling-reference checks removed
   with the `<use>` walk they guarded.

`make_logical_pages_consolidated.py` was committed in `7e201d6`. Whether it stays
in the repo, or is scratch to delete once the change lands in the original, is an
open question (§7).

### Step 1b: the copy cannot overwrite the known-good output

Two changes to the copy, made before it has ever produced a page:

- **`OUT_DIR`** → `print/logical-pages-consolidated/`, not `print/logical-pages/`.
  The original's output is the validation target for Step 3; a copy writing into
  the same directory would destroy the thing it is being compared against. The new
  directory is added to `.gitignore` beside the old one, since it is the same kind
  of generated intermediate.
- **The pre-write cleanup is now conservative.** `main()` did
  `for p in OUT_DIR.glob("page-*.svg"): p.unlink()` — delete every page-shaped file
  in the output directory before writing. Widening this script's reach made that
  the more dangerous half of the change: a wrong `OUT_DIR` would have deleted
  somebody else's output, not merely written the wrong place. It now unlinks only
  the names this run is about to rewrite.

`pages_to_pdf.py` reads `print/logical-pages/` and was not touched, so the
known-good chain (pages → PDF) still runs end to end while the copy is brought up.

### Step 1 result: everything but placement carries

| stage | result |
|---|---|
| `read_feathers()` | **ok** — 28/28, placed sizes match `data-wh` |
| `verify_body()` per feather | **ok** — every body inside `[0,W]×[0,H]`, none reported out |
| `read_topline()` ×8 | **ok** — model, no assertion |
| `verify_body()` per topline | **ok** — every body inside its box |
| `read_placement()` | **fails**: `SystemExit: rendered SVG produced no ink` |

So the ID remapping alone is sufficient for 36 of the 36 geometry groups, and
`main()` gets all the way to the placement page before dying.

**What this does not yet prove.** `read_placement()` dies inside `measure_ink()`
*before* the frame question in §2c can matter, so Step 1 is silent on whether the
feather bodies are placed correctly — only that they measure as inside their own
boxes. The real test is Step 2c plus the Step 3 page diff. §2c remains the open
decision and was deliberately not touched.

`read_placement()`'s failure is consistent with §2a (the `toplines` group of
groups serializes to nothing) and §2b (inline stroke dropped), and those fixes are
themselves un-applied — Step 1 was defined as IDs only.
