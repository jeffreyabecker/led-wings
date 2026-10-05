# Plan: flatten a work file into CAM geometry (`flatten_geometry.py`)

**Status:** proposed, not executed.
**Scope:** a new stdlib-only Python script that reads a *work file* — a document
that composes geometry out of a geometry core by `<use>`, orients it, and selects a
subset — and writes raw, flat, bed-ignorant geometry for CAM software to position
inside a machine. It does not change `tile_sheets.py`, `plans/templates-reorg.md`'s
print pipeline, or the geometry core's ids.

Settled in review (this is the design driver, not an inference):

- the input is a **new kind of document**, not the tiler's print output and not the
  geometry core: it carries `<use>` references into the core, plus rotation,
  reorientation and subset selection;
- the output is **ignorant of the CAM bed** — no tiling, no paper, no pages, no
  registration marks, no bed frame. The CAM software positions the work under the
  user's own target conditions, so the flattener's job is *simplify*, not *lay out*.

Consequence: `tile_sheets.py` is not in this pipeline at all. Tiling is a printing
concern (page-sized stock, overlap bands, join marks) and the bed is a CAM concern;
each is somebody else's stage. The flattener only resolves and simplifies.

## Decisions this plan encodes

| decision | choice |
|---|---|
| script name | `flatten_geometry.py` |
| input | a work file: `<content>-work.svg` (see §2 — the one naming question still open) |
| geometry core | referenced by the work file, never opened as the top-level input |
| output location | `templates/cam/` (as directed) |
| output names | `templates/cam/<work>-<subset>.svg`, one file per selected work |
| output frame | **no bed frame**; units declared as mm, origin owned by the work file |
| coordinate system | absolute millimetres, **every transform baked into path data** |
| shapes | `rect`/`circle`/`ellipse`/`line`/`polyline`/`polygon` → `<path>` |
| emitted geometry | centreline cut paths only; labels, bounds, guides, reg marks dropped |
| CSS | all styling stripped; geometry is `fill:none`, `stroke:none`; kerf offered as an optional non-authoritative attribute and in the manifest |
| manifest | `templates/cam/index.tsv`, one row per emitted path plus a census of what was dropped |

## 1. What the script is called

**`flatten_geometry.py`**, at the repo root beside `tile_sheets.py` (or in
`templates/` if `plans/templates-reorg.md` moves the tools there). `flatten` is the
SVG term for resolving `<use>` into copies; `geometry` names what survives — this is
not a general-purpose flattener, because labels, bounds, guides and marks are
losses it makes on purpose.

Rejected: `flatten_for_cam.py` (names the audience, not the transform),
`resolve_use.py` (describes only the first of the three things it does),
`flatten.py` (too generic beside `tile_sheets.py` / `inline_css.py`).

CLI, mirroring `tile_sheets.py`'s conventions (`USAGE` string, positional input,
explicit `--out`, `--whatif`, stdlib only, no argparse):

```
python flatten_geometry.py <content>-work.svg --out templates/cam/<work>-<subset>.svg
                            [--subset <group-id>]... [--all-subsets]
                            [--geometry <core.svg>] [--ref-dir <dir>]...
                            [--kerf] [--include-reference] [--include-marks]
                            [--keep-groups] [--check] [--whatif]
```

- `--subset` takes a group id inside the work file; repeatable. Without it, the whole
  work file is flattened as one work (the file's own selection stands).
- `--out` is required and is the file when exactly one work is emitted, the directory
  when several are (`--all-subsets`); the stem is derived per subset. Same rule as
  the tiler: no inferred output location, because a relative path written into a
  file is the failure mode this whole pipeline exists to delete.
- `--geometry` pre-seeds the core document so a work file copied away from its tree
  still resolves; `--ref-dir` adds search paths.
- `--check` re-flattens and compares against the committed output without writing.
- `--whatif` prints the resolved chain per path, the subset census, and the paths it
  would write.

## 2. What the input files are named

Two documents, two roles:

| role | name | contents |
|---|---|---|
| geometry core | `aggregate.svg` (reorg plan's name for today's `templates/feathers-elongated.svg`) | the 74 `<path>`s, ids `A1-outline` … `LC-All-outline`; 0 `<use>` |
| work file | `templates/<content>/<content>-work.svg` | `<use>` into the core, transforms, and the subset groups |

The work file is the composition layer: *this* content, rotated and reoriented like
this, using *these* parts. Today that role is played by
`templates/sheets-home-feathers.svg` and `templates/sheets-home-alignment.svg` —
43 and 18 `<use>` respectively, including the 14 self-referencing mirror clones
(`#sheet-P1-half` through `matrix(-1,0,0,1,210,0)`). Those files are exactly the
"new type of input" the brief describes; the plan's assumption is that they get the
`<content>-work.svg` name rather than a new sibling being invented beside them.

> **Open question, flagged not decided:** whether the work file *is* the existing
> sheets document renamed, or a third layer above it. Everything else in this plan is
> independent of the answer — the flattener takes one work file and a core, whatever
> they are called — but §3's output names are derived from the work file's stem, so
> the name has to be settled before the first run.

Naming grammar, so the pipeline reads out loud:

```
aggregate.svg             the geometry core (ids, no references)
<content>-work.svg        selection + orientation of core geometry
templates/cam/<stem>.svg  flattened, bed-ignorant output
```

No output name contains a `templates/` path, a paper token, a page number, or an
`id` from the core, so the whole tree can be renamed without touching the script.

## 3. What the output files are called

`templates/cam/`, as directed — below the tree that owns the sources, and outside
`targets/` because the CAM output is neither a print target nor paper-specific:

```
templates/cam/
  index.tsv                            manifest: every emitted path + the drop census
  README.md                            what regenerates this; nothing here is hand-edited
  feathers-work.svg                    whole work file, one work
  feathers-work-P1.svg                 --subset P1 (if subsets are emitted separately)
  alignment-work.svg
```

- The stem is the work file's stem, so source and output pair up by name
  (`feathers-work.svg` → `templates/cam/feathers-work.svg`).
- `--subset <group-id>` appends the subset token: one file per selected work, because
  a subset is a cutting job and mixing two jobs in one file is how the wrong profile
  gets cut.
- The **manifest** `templates/cam/index.tsv` is the thing that makes the tree
  auditable (tab-separated, one row per emitted path):

  | column | meaning |
  |---|---|
  | `work`, `subset`, `group` | source work file stem, subset id, the `id` of the group holding the path |
  | `role` | `cut` · `reference` · `mark` |
  | `path_id` | the emitted path's id |
  | `min_x`,`min_y`,`max_x`,`max_y` | tight bounds, mm, in output coordinates |
  | `kerf_mm` | the source stroke width, when `--kerf`; empty otherwise |
  | `src` | the resolution chain: `feathers-work.svg#P1R-use → aggregate.svg#P1-outline` |
  | `dup_of` | first entry that emitted identical geometry (mirror / duplicate detection) |

- `index.tsv` also carries a **drop census**: every dropped class with its count
  (`.label`, `.title`, `.note`, `.sheet-bounds`, `.reg*`, `.crop`, `.overlap`,
  `.guide`, `.divider`, `.cal*`, `.align`) and every subset that produced zero cut
  paths **with the reason**. In this tree that matters immediately: the cover and
  every `sheet-Alignment-*` group is layout and guide geometry, not parts, so those
  subsets are legitimately empty and must say so rather than look like a bug.

## 4. How the geometry is placed and organized

A work file is a cutting job, so the output is one document = one job, with no
notion of a bed, page, paper or machine:

1. **No frame is invented.** The flattener must not emit a `viewBox` sized to a
   sheet, a page or a bed — that is the bed coupling the brief rejects, and it would
   smuggle a placement decision into a file whose whole point is that placement is
   the CAM software's job. To make units unambiguous the root declares
   `viewBox="0 0 W H"` spanning the emitted geometry's tight bounds and
   `width="Wmm" height="Hmm"`, i.e. 1 user unit = 1 mm *by construction* — the frame
   is derived from the geometry, never the geometry fitted to a frame.
2. **No transforms survive.** The work file's rotations (e.g. `rotate(-4.0415212,
   -2276.4602,237.48561)` on `P1R-use`) and the mirror's `matrix(-1,0,0,1,210,0)`,
   the enclosing `translate` on `#sheets`, and the core's own
   `translate(-1317.2834,-272.68523)` on `full-outline` are all multiplied into path
   coordinates. Geometry gets `transform=None`, so an importer that ignored
   `transform` entirely would still be correct. `--keep-groups` preserves nesting
   with its transforms for eyeballing only.
3. **Path conversion.** `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`
   become `<path>` (circles as two 180° arcs, `rx`/`ry` as corner arcs). No `<use>`,
   `<symbol>`, `<defs>`, `<clipPath>`, `<text>`, `<image>`, `style=`, or `class=`
   remains — the output has no dependency any consumer could drop.
4. **Groups keyed on source identity, never on position.** One `<g>` per subset and
   one per part, children in work-file document order:

   ```xml
   <g id="work" data-work="feathers-work" data-units="mm">
     <g id="subset-P1" data-subset="P1">
       <g id="part-P1R" data-part="P1" data-side="right" data-role="cut">
         <path id="P1-outline"
               d="…"
               data-src="feathers-work.svg#P1R-use → aggregate.svg#P1-outline"/>
       </g>
       <g id="part-P1L" data-part="P1" data-side="left" data-role="cut" data-mirror="of:part-P1R">
         <path id="P1-outline-mirror" d="…"/>
       </g>
     </g>
   </g>
   ```

   Ids come from the resolution chain (`part-P1R`, `P1-outline-mirror`), not from an
   array index, so adding a part does not renumber the others — the masters already
   name their groups this way (`sheet-P1-half`, `sheet-P1-labels`). The mirror stays
   explicit: it is a real geometric distinction (a flipped part is not a duplicate),
   and CAM needs to know a path is the reflected copy.
5. **What is kept by default** — the subset that represents material to be cut:

   | source class | emitted as | default |
   |---|---|---|
   | `.outline` inside a `class="feather"` group | `data-role="cut"` | **kept** |
   | `.outline` inside `.align` (the `*-align` / `A-align` overlay) | `data-role="reference"` | dropped (`--include-reference`) |
   | `.guide`, `.divider`, `.arrow` | `data-role="reference"` | dropped (`--include-reference`) |
   | `.reg`, `.reg-hole`, `.reg-axis`, `.reg-key` | `data-role="registration"` | dropped (`--include-marks`; these are print/assembly registration, not bed registration) |
   | `.cal`, `.minor`, `.major`, `.num`, `.caltext` | `data-role="mark"` | dropped (`--include-marks`) |
   | `.label`, `.title`, `.note` (`<text>`) | never emitted | dropped always — a cutter cannot cut text |
   | `.sheet-bounds`, background rects, `.crop`, `.overlap` | never emitted | dropped always |

   The drops are the "simplify for CAM" half of the brief: the operator wants cut
   profiles, and every other element is a printing or proofing aid. The `--include-*`
   flags exist so the same resolver can emit a reference or alignment program
   without a second tool.
6. **Ordering is the work file's, and it is preserved.** Nesting order, sibling
   order and each rotation land in the output exactly as the work file composed
   them; the flattener never sorts, optimises, or re-nests. If the work file says
   "P1 is rotated 4° anti-clockwise to fit the stock," that rotation is baked and the
   output records it in `data-src`, so the CAM operator inherits the decision instead
   of being asked to reproduce it.

## 5. What CSS is emitted

**None.** No `<style>` element, no `class` attribute, no presentation attribute on
the document — the CAM consumer's CSS support is unknown and unknowable, and a
stylesheet that *is* honoured produces a different file from the one that is not.
Styling is not geometry, so nothing about the geometry's *position* depends on it:

1. **Geometry carries only geometry.** Every emitted shape gets `fill="none"` and
   `stroke="none"` so no downstream default (a viewer's black fill, a CAM import's
   fill-to-path) can turn a cut profile into a filled region. No `stroke-width`,
   `stroke-dasharray`, `opacity`, colour or `font-*` survives — the source's
   `.outline { stroke-dasharray: 2.5, 2.5 }` (present in every master today) and the
   `.overlap { stroke-dasharray: 2 2 }` rule both disappear with the stylesheet, which
   removes by construction the class of bug the reorg plan calls out as live dashed
   cut paths.
2. **Kerf is data, not style, and it is opt-in.** `--kerf` adds
   `data-kerf-mm="0.5"` (the stroke width the source cascade resolved to) to each cut
   path and fills the manifest's `kerf_mm` column. It is deliberately *not* a
   `stroke-width`: a CAM file must not let a renderer's stroke be mistaken for a
   toolpath offset, and cutter compensation is the CAM software's decision. With the
   flag off, the manifest still records the resolved value, so a wrong kerf is visible
   before cutting without putting it in the geometry.
3. **Widths are millimetres and stated once.** The unitless source widths are only
   meaningful against an mm viewBox; §4.1 makes that true by construction and the
   manifest restates it, so `0.5` cannot be silently read as 0.5 px.
4. **Provenance is a comment, not styling** (same shape as the tiler's stamp):

   ```
   <!-- flattened by flatten_geometry.py: work=<path> sha256=<8> core=<path> sha256=<8>
        subsets=1 cut_paths=28 mirrors=14 dropped=labels:56,bounds:15,reg:105,guide:8
        css=none kerf=0.5 -->
   ```

   The source hashes are what make a flattened file traceable to the exact revision
   that produced it — the property the `<use>` documents get for free by pointing at
   their sources, and the reason a stripped file needs a stamp.

## 6. Verification

- No `<use>`, `<symbol>`, `<defs>`, `<clipPath>`, `<text>`, `transform=`, `url(#…)`,
  `href=`, `class=`, `style=`, `<style>` or `stroke-width` survives in any
  `templates/cam/*.svg`. Grep the emitted tree: this is the check that catches the
  no-op-that-looks-like-success failure mode, so it is a hard gate.
- Feathers work file: 28 distinct cut profiles per the catalog (14 parts × right/left),
  the 14 mirrored paths are reflections about their part's axis and are paired in the
  manifest by `dup_of`, and no two entries share identical `d` unless genuinely
  congruent parts do.
- Bounds: every emitted path's bounds lie inside the root `viewBox`, and the viewBox
  is the tight union of them.
- `index.tsv` lists the cover and every `Alignment-*` subset with `cut_paths=0` and a
  reason, and the drop census counts match the source (`labels:56`, `bounds:15`,
  `reg:105` for the current feathers sheets — measured, see the working tree).
- Render one flattened output at 1 mm/unit and overlay the source's equivalent region
  (Inkscape CLI `--export-type=png`, `--export-dpi`): the cut ink is congruent. A
  mismatch means a transform was multiplied in the wrong order (outermost first).
- A hand-edit to a baked `d` is reported by `--check` (try it once, revert).
- Re-flattening unchanged inputs is byte-identical, which is what lets the tree be
  regenerated on every master edit.

## 7. Risks and notes

- **The input name is the open decision** (§2). Everything else here is independent
  of it, but `templates/cam/` output stems derive from the work file's stem.
- **`templates/` is moving.** `plans/templates-reorg.md` renames the core to
  `aggregate.svg` and relocates every document. The naming grammar above is chosen to
  survive it: no output name encodes a `templates/` path, a paper token, or a sheet
  id.
- **The core is referenced by id, so a core rename breaks the work files**, not the
  flattener. The flattener fails loudly on an unresolvable href, naming the href and
  the file it looked in — the deep-relative-path silent failure is the known incident
  this repo keeps re-learning.
- **Nothing about cutting offsets.** With `stroke="none"` and no width, the output is
  centrelines; a CAM post that needs an offset outline does it downstream. That is
  the intended division of labour, and the reason `--kerf` is advisory.
- **Commit the output tree**, like `templates/targets/` per the reorg plan, so an
  operator can check out the repo and get the exact geometry that was cut.

## 8. Out of scope

- Tiling, pagination, overlap bands, join marks, paper sizes, registration marks —
  the printing pipeline's job (`tile_sheets.py`), and explicitly not the flattener's.
- Bed fitting, nesting, work offsets and toolpath ordering — the CAM software's job,
  which is the point of a bed-ignorant output.
- Stroke-to-path / offset outlines, DXF, HPGL, G-code, and any machine post.
- Any change to the geometry core's ids or the work files' geometry.
