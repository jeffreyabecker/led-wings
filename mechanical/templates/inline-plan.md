# Plan — inline the feather geometry, keep the print scripts dumb

**Status: proposal, decisions taken.** Nothing has been changed yet.

**Scope:** `mechanical/templates/feathers-aggregate-min.svg`, a new sync tool in
`mechanical/templates/`, and the three reader functions in `make_logical_pages.py`.
`pages_to_pdf.py` is **untouched** — it only ever sees `page-NNN.svg`, so it cannot be
affected. *(Still checked, because "cannot be affected" is a claim, not a fact.)*

**The ask:** edit a feather where it is drawn, with no hidden source copy; keep the
rotation numbers somewhere the generator can read; do not make the generator clever.

**Verdict: yes, and it is smaller than it looks.** Everything the readers need is
already in the file — it just lives in the wrong place.

## Decisions taken

| question | decision |
|---|---|
| path form | **bake the placement into `d`**; geometry in canvas coordinates |
| where the offsets live | **`data-rot` / `data-frame` on the catalog paths** (Inkscape preserves `data-*`; measured) |
| the P/S/B 1.2× scale + shear | **normalise the catalog to plain `rotate(θ)`** while inlining |
| `#geometry-source` | **delete it** |
| angle rounding | **whole degrees**, snapped at conversion time, individually tweakable (§3a) |
| styling | **delete the aggregate's `<style>` block and every `class` on the feather paths** (§2a) |

---

## 1. What is actually true today

Measured, read-only, on the current working copy (Inkscape 1.4 `--query-all`, a prototype
decomposition of all 28 placements, a frame-recovery round trip).

| claim | evidence |
|---|---|
| Each feather is drawn once as a `<g id="X-def">` in `#geometry-source`, and *again* by a `<use>` in a prefix group | 36 def groups, 42 `<use>` elements |
| The print scripts never look at the arrangement | `read_feathers()` reads only `data-wh`/`data-vb` + the def's `<path d>`; `read_topline()` the same; `read_placement()` reads the `placement-*` groups. No code reads a `P`/`S`/`B`/… group id |
| The arrangement's transforms are matrices, and not pure rotate+scale | `B1`: `matrix(0.034899,0.999390,0.999390,-0.034899,…)` — columns orthogonal to 0.05°, but lengths 1.1935 vs 1.0052, so rotation + 1.19/1.00 non-uniform scale + a small real shear |
| 20 of 28 placements are exactly `rotate(θ)·scale(1,−1)` | decomposition residual **0.0** for every `A`, `PC`, `SC`, `MC`, `LC` item |
| the other 8 carry the scale and a shear ≤ 0.11 user units | `P`, `S`, `B`; worst `1.09e-01` at `S4` (≈ 17 mm on that feather's long axis) |
| `data-*` attributes survive an Inkscape save/export | probe: `--export-plain-svg` kept `data-rot`, `data-scale`, `data-frame` verbatim; it stripped only `inkscape:label` |
| baked geometry maps exactly | each placement is affine, so moving the control points of `M`/`L`/`C`/`Q`/`H`/`V` is lossless to ~1e-15 |
| the readers need more than a path | `right_transform()`/`mirror_check()` need the frame origin `x0, y0`; `placed_size()` needs `W, H` |
| the toplines cannot be folded into the drawing | they feed **both** the placement template **and** the alignment-guide strip page, and `_group_content()` reads their `<circle>` origin markers (all 8 carry one) |
| the working copy is mid-experiment | `#geometry-source` carries `style="display:inline"` **and** `transform="translate(-1258.8875,-69.320831)"`, so every feather currently draws twice; the note above it still describes the hidden form |

**Consequence:** nothing about the print output depends on where geometry is stored or how
the arrangement is expressed. The only contract is *"one path + one frame + one rotation
rule, per feather"*. So the file can be reorganised freely, and the parts that matter can
be verified exactly.

---

## 2. Target shape

```xml
<svg width="247.95744mm" height="570.17749mm" viewBox="0 0 247.95744 570.1775" …>
  <defs id="defs1">
    <!-- the 8 toplines: pure source geometry, referenced twice, drawn only through a <use>.
         They keep their class="guide" and their presentation style, because the
         alignment-guide page's CSS styles them by that class. -->
    <g id="A-topline-def" data-wh="2 89.629811" data-vb="190.064856 1723.540766 2 89.629811">
      <path …/><circle id="A-topline-origin" …/>
    </g>
    …
  </defs>

  <!-- the catalog: 28 paths, one per feather, each drawn exactly where it belongs -->
  <path id="P1" data-rot="0" data-frame="171.95 164.833 107.70177 348.70091"
        transform="translate(…) rotate(0)" d="M 218.249,… z" />
  <path id="P2" data-rot="0" data-frame="…" transform="…" d="…" />
  …
  <path id="B1" data-rot="89" data-frame="108.29541 44.994112 193.15454 81.754908"
        transform="translate(…) rotate(89)" d="…" />
  …

  <sodipodi:namedview …/>
  <title>…</title><desc>…</desc>

  <!-- the placement template: hidden, because the catalog no longer draws the toplines -->
  <g id="placement-top-lines" style="display:none" transform="matrix(…)"> … 8 <use> … </g>
  <g id="placement-total-outline" style="display:none" transform="matrix(…)"> … </g>
  <use id="top-lines-ref" href="#placement-top-lines"
       transform="translate(-33.258665,-26.770171)" />

  <metadata>…</metadata>
</svg>
```

No `<style>` block, and no `class` on any feather path: the catalog draws as an unstyled
drawing (black 1-unit strokes at document scale), which is what "get rid of the styling"
means here. §2a records the two places this is load-bearing and the one place it is not.

### 2a. What "no styling" does and does not touch

Everything below was read out of the current file and the two scripts.

| styling | disposition | why |
|---|---|---|
| `<style id="style1">` (`.group`, `.outline`, `.label`, eight per-family fills, `.centerline`, `.visibility-line`) | **delete the block** | nothing reads it. The print script carries its own `CSS` and re-emits `class="outline"` / `class="guide"` on what it builds |
| `class="group X"` on the 28 def groups | goes with the def groups | — |
| `class="outline"` on the 28 feather paths | **delete** | `_path_d()` only reads `d`; the page CSS re-adds `.outline` when it emits the path |
| `inkscape:label` on 7 elements | already lost on any Inkscape save; drop | it rendered nothing |
| `class="guide"` + `style="fill:none;stroke:#000;"` on the 8 toplines | **keep** | `_group_content()` writes `class="guide"` into the alignment-guide page, whose CSS supplies the stroke. Their inline `stroke-width` (0.2415 on `S-topline`, 0.2646 elsewhere) is a real rendering difference, not decoration |
| `class="outline"` on `upper-outline`'s path (the 29th occurrence) | **delete the class, keep the inline `style`** | the class is dead: the aggregate no longer defines `.outline`, and this path's `fill:none;stroke-width:0.228236` is already inline on the element. `read_placement()` emits its own `class="guide"`, so nothing downstream reads it either |
| `style="display:inline"` on the 33 `<use>` elements in the catalog | goes with the `<use>` elements | the aggregate's own fallback |
| `style="display:inline"` on the 8 `<use>` elements inside `placement-top-lines` | **keep or drop, no effect** | harmless either way once the catalog stops drawing toplines; leave them, they are Inkscape's own noise |
| `style="display:none"` on the three `placement-*` groups | **required** | the catalog no longer draws the toplines, so the placement template is the only thing left that would |

Two consequences worth stating plainly:

- **The catalog gets visually heavier.** With `.group { stroke-width: 0.5 }` gone, the
  paths fall back to SVG's default `stroke-width: 1` at 1 user unit = 1 mm, so outlines
  draw ~2× thicker. Step 3 of the validation compares against the old render at the same
  default, so the heavier strokes are expected rather than surprising. If it reads badly,
  the fix is one presentation attribute per path (`stroke-width="0.5"`), added in commit 2.
- **The print output is untouched by all of it.** The scripts synthesize their own CSS,
  classes and geometry per page; they read exactly `id`, `d`, `data-frame`, `data-wh`,
  `data-vb` and the placement groups. No `class` or `style` attribute in the aggregate is
  read by either script.

One inconsistency found while checking this, recorded rather than fixed: `upper-outline`'s
own file intended `stroke-width: 0.5` (its per-file CSS said so), but its inline
`stroke-width: 0.228236` wins and has done since before the consolidation. The **placed**
copy on the placement page draws at `0.264583`, because `read_placement()` emits
`class="guide"` and drops the source style. So that silhouette has never drawn at the
width its source asked for. Preserving today's rendering means leaving all of it alone;
`_group_content()` would need to carry `class`/`style` through to change it, which is a
separate decision with a visible output change.

### 2b. The conversion rule, stated exactly

For each `<use id="X" href="#X-def">` in a prefix group:

1. find the def group; assert it holds exactly one `<path>` and nothing else;
2. form `M` = (all ancestor group transforms) · (the `<use>`'s own transform) ·
   `translate(−x0, −y0)`;
3. **bake** `M` into the def path's `d` — every coordinate, including Bézier control
   points and the endpoints hiding behind relative commands — and emit the result as a
   top-level `<path id="X" class="outline">` at the `<use>`'s position;
4. normalise the linear part to a pure rotation: write
   `transform="translate(tx,ty) rotate(θ)"`, where `θ` is the placed geometry's column
   angle rounded to the nearest degree, and `tx,ty` are chosen so the **placed centre is
   unchanged**;
5. add `data-rot="θ"` and `data-frame="x0 y0 W H"` (the frame, copied from `data-vb`);
6. delete the def group and the `<use>`.

Then delete the now-empty prefix groups (`P`, `S`, `B`, `A`, `PC`, `SC`, `MC`, `LC`) and
delete `#geometry-source`, after moving its 8 topline groups into `<defs>` and putting
`display:none` on the three `placement-*` groups.

### Why the toplines keep their `-def` groups

They are the one thing that cannot be inlined, and the reason is not sentiment:

- `read_topline("A-topline")` prints the guide strip from the **frame-local** geometry,
  and `_group_content()` reads the `<circle>` origin marker explicitly. Baking a topline
  into the placement drawing would destroy the circle (`<circle>` under a 1.2 scale is an
  ellipse) and would leave the strip page with nothing to read.
- The placement template needs the same eight shapes at eight different rotations. That
  is exactly what "definition + use" is for.

So they move from a hidden `<g id="geometry-source">` into the `<defs>` that is already
sitting empty at the top of the file — which is what `<defs>` is for, and which removes
the construct the request is about: the visible duplicate of the feather geometry.

### The normalisation, and what it costs

The eight `P`/`S`/`B` placements were written with a 1.19/1.00 scale. `rotate(θ)` alone is
a **shape change** on those feathers, not a rounding: up to ~17 mm of movement along
`S4`'s long axis, and the whole catalog shifts slightly because the bounding boxes change
size while the centres stay put.

That is fine, and it is the better drawing. What it is *not* is render-identical, so the
validation below asks a different question than the last consolidation did: not "are the
pixels the same" but "**is the print output byte-identical, and is the drawing still the
drawing**". The print output is exact, because the script never reads the arrangement —
the catalog could be a rectangle and the 25 logical pages would not change by a bit.

If the shift turns out to look wrong, §9 has the escape hatch: snap fewer angles, or
re-run the conversion with the old scale preserved.

### Where the rotation offsets go

`data-rot` on each path, because:

- Inkscape 1.4 preserves `data-*` through a save and through `--export-plain-svg`
  (measured, §1) — the same cannot be said for `inkscape:label`, which the probe showed
  being stripped;
- the number sits next to the shape it describes, so "one feather, one element, all of
  its data" holds;
- the generator reads a dict either way, so a `feather-placement.json` sidecar stays
  available as a mechanical change if the numbers ever want a table view.

---

## 3. The sync tool — `mechanical/templates/inline_feathers.py`

One script, two jobs, both idempotent, both refusing to write a file they cannot verify:

```
python mechanical/templates/inline_feathers.py            # report only
python mechanical/templates/inline_feathers.py --apply    # write the aggregate
```

- **`--inline`** (default while def groups exist): performs §2's conversion.
- **`--refresh`** (the steady-state job): for each catalog path, recompute the placed
  bbox and rewrite `data-frame`; report which frames changed and by how much. This is what
  makes "edit in place, then generate" a two-command workflow instead of a reasoning
  exercise. It also re-derives `data-rot` from the transform if the path was rotated.

Guards, all of which must pass before anything is written: every `<use>` resolves; every
id is unique; no two sources claim the same id; all 28 + 8 catalog items are present;
exactly one `<path>` per feather def; `data-frame` agrees with `data-vb` where both exist.
The tool never touches `pages_to_pdf.py`, the CSS, the toplines, or the placement groups.

### 3a. Tweakable whole-degree angles

The rotation is **baked into `d`**, so `data-rot` is a record, not something that can
drive the drawing by itself. That is the right trade for editability — but it means
"tweakable" needs one explicit knob, or the only way to change an angle would be to
re-run the whole conversion.

```
inline_feathers.py --set-rot B1=89,B2=83,P3=-6      # rotate those feathers, then bake
inline_feathers.py --set-rot B1=89 --dry-run        # report the new frame, write nothing
```

Each assignment re-bakes that feather's geometry about its **placed centre** by
`new − old` degrees, snaps the result to a whole degree, and rewrites `data-rot`. Because
the rotation happens about the placed centre, the drawing stays where it was and only
turns; `data-frame` is refreshed in the same pass because a rotated frame is a different
frame (`W`/`H` swap at 90°).

So the steady-state edit loop is:

| want | command |
|---|---|
| change an angle | `--set-rot X1=NN --apply` |
| change an outline | edit the node in Inkscape, then `--apply` (`--refresh` reports which frames moved first) |
| inspect only | run with no arguments, or `--dry-run` |

Angles are stored as plain decimals (`data-rot="89"`, not `89.000000`), so hand-editing
the attribute is also viable — the tool re-derives the geometry from `data-rot` on the
next `--apply`, and reports any path whose baked rotation disagrees with its record.

### The generator stays dumb — three lines change

```python
def _def_group(name):
    el = aggregate_by_id().get(name)                  # was f"{name}-def"
    assert el is not None, f"{name}: no <path id=\"{name}\"> in {AGG_SVG.name}"
    return el

def _frame(name, el):
    vb = (el.get("data-frame") or "").split()         # was data-wh + data-vb
    assert len(vb) == 4, f"{name}: placed path needs data-frame=\"x0 y0 W H\""
    return tuple(float(v) for v in vb)
```

- `_frame()` loses the two-attribute cross-check (one attribute now) and loses `data-wh`:
  `W, H` are `data-frame[2:]`.
- `read_feathers()` is otherwise unchanged. `rotate90 = name.startswith("B")` stays in the
  script, where it belongs — it is a pipeline fact, not a property of the file.
- `read_topline()` and `read_placement()` are **unchanged**: the `*-topline-def` groups and
  the `placement-*` groups keep their ids, attributes and structure.
- `data-rot` is **not consumed**. The catalog's angle is a presentation fact; the print
  arrangement is owned by `SECTIONS`. If a future page ever needs "as drawn", it is there.

Net effect on the generator: one identifier changes, one attribute name changes, one
cross-check is deleted. That is the whole cost.

---

## 4. The editing loop this buys

| want | how |
|---|---|
| change a feather's outline | open the aggregate, click the feather **in the catalog**, node-edit, save |
| check the frames | `python mechanical/templates/inline_feathers.py` — lists every path whose bbox no longer matches `data-frame` |
| accept new geometry | `--apply`, then `make_logical_pages.py`, then `pages_to_pdf.py` |
| move a feather in the catalog | drag it; `data-frame` follows on the next `--apply` (a pure translation changes nothing that matters) |
| move a feather in the **print layout** | edit `SECTIONS` in `make_logical_pages.py`, as today |
| rotate a feather in the catalog | rotate it in Inkscape; `data-rot` is refreshed from the transform |

The loop is honest about its one sharp edge: `data-frame` is a *recorded* frame, so a
geometry edit is picked up by `--apply`, never silently by the generator. A forgotten run
is stale, not wrong — the print output keeps using the last accepted frame.

---

## 5. Validation

Baselines taken **before** the change.

1. **Baseline** — SHA-256 of all 25 `logical-pages/page-*.svg`; the current
   `feathers-letter-landscape.pdf` (30 sheets: 5 tiled, 20 fit).
2. **Structure** — every `<use href="#X-def">` in a prefix group has exactly one
   replacement `<path id="X">`; every replacement has `data-frame` with four numbers;
   `data-rot` present and finite; no dangling `href`; no duplicate ids; `#geometry-source`
   gone; `<defs>` holds exactly the 8 toplines.
3. **Drawing is still the drawing** — render old and new at 96 dpi and diff. The diff is
   now *expected* to be non-zero for two known reasons: the angle/scale normalisation
   (§2) and the heavier default stroke where `.group { stroke-width: 0.5 }` used to be
   (§2a). So this check asserts shape rather than pixels:
   - **28 outlines are present** in the new render, and no feather is missing or doubled;
   - each feather's **placed centre moves < 0.5 mm** and the whole catalog's **ink
     bounding box moves < 1 mm** versus the baseline;
   - the diff is **confined to the catalog area** — no new ink appears where the toplines'
     hidden placement template sits.

   The failure this check exists for — a transform composed in the wrong order — throws a
   feather across the canvas or drops it entirely, so it still fires loudly.
4. **Frames preserved** — right after conversion, `inline_feathers.py` reports zero frame
   changes and every `data-rot` agreeing with its baked geometry.
5. **`--set-rot` round-trips** — set one angle, confirm exactly one path's geometry and
   frame changed and the rest are byte-identical, then set it back and confirm the file
   returns to its pre-tweak bytes.
6. **Print output exact** — re-run both scripts: **25 pages byte-identical**, 30 sheets,
   tiling and scale checks pass, tracked PDF unchanged. This is the load-bearing check,
   and the only one that is exact.
7. **Editing loop works** — nudge one node deliberately; confirm the tool reports exactly
   that one frame changed; confirm `--apply` then restores agreement; revert.

## 6. Risks

| risk | containment |
|---|---|
| a transform composed in the wrong order | the composition is unit-tested against the current matrices, and the render diff in step 3 would show a displaced feather immediately |
| baking mangles a relative or elliptical command | the bakery converts every command to an absolute form before transforming and asserts the command sequence is unchanged; there are no `A` commands in this file, and the assertion refuses one if it appears |
| a `data-*` attribute is lost on a later save | measured to survive; the generator's assertion names the missing attribute loudly; the JSON sidecar is the fallback |
| the normalisation moves a feather enough to matter | step 3 measures the actual movement; §9 has the fallback |
| the catalog starts drawing the toplines | they now have exactly one placement, inside a `display:none` group; step 3's render diff would show 8 extra strokes |
| the B-group's print rotation is confused with its catalog rotation | both stay explicit and neither is derived from the other: `rotate90` in `SECTIONS`, the catalog angle in `data-rot`; they were never the same number |

## 7. If the render diff in step 3 is unacceptable

Two levers, in order of preference:

1. **Relax the rounding.** Keep each placement's exact column angle instead of rounding to
   whole degrees. That removes the rotation component of the shift and leaves only the
   scale change. (Whole degrees are confirmed as the default; this is the per-feather
   escape, and `--set-rot X=83.31` accepts a fractional angle when one is wanted.)
2. **Keep the scale.** Write `transform="translate(tx,ty) rotate(θ) scale(sx,sy)"` and
   record `data-scale`. The conversion is then render-exact, at the cost of two more
   numbers per feather and a slightly less obvious drawing.

The sync tool takes a `--preserve-scale` flag so this is a re-run, not a rewrite.

## 8. Commit sequence

The readers and the defs must change together — the moment the def groups go, every page
build fails. So:

1. `templates: add inline_feathers.py` (the tool, not yet run)
2. `templates+print: inline the feather geometry into the catalog, and read it there`
3. `templates: document the in-place editing loop in the aggregate`

## 9. Closed — the three items that were open

All three resolved above rather than deferred:

1. **Catalog outline weight** — keep the heavier default `stroke-width: 1`; validation
   step 3 compares against the old render at the same default, and one presentation
   attribute per path reverses it if the render reads badly. (§2a)
2. **`upper-outline`'s `class="outline"`** — delete the class, keep the inline style. It is
   dead: nothing defines `.outline` any more, and `read_placement()` emits its own class.
   (§2a)
3. **Toplines keep `data-wh`/`data-vb`** — they are not feather paths and never become
   one: `read_topline()` reads them, and their frame is not their bbox because the origin
   circles sit on it. The asymmetry with `data-frame` is deliberate. (§2b)

The only genuinely deferred item is the pre-existing `upper-outline` stroke-width
inconsistency in §2a, and it is deferred on purpose: fixing it would change the placement
page's output, which is exactly what this work is not allowed to do.

---

## Appendix — measurements taken for this plan

| probe | file | result |
|---|---|---|
| Inkscape attribute round-trip | `.tmp/attr-probe/in.svg` → `plain.svg` | `data-rot`, `data-scale`, `data-frame` preserved; `inkscape:label` dropped |
| placement decomposition | `.tmp/attr-probe/decompose.py` | 28 placements; 20 exact `rotate·scale(1,−1)`, 8 with scale ≈ (1.2, 1.0) |
| simple-form fitting | `.tmp/attr-probe/fit_simple.py` | `rotate·scale` alone is off by up to 24 mm on `S`/`B` at the current angles — the basis for the normalisation cost in §2 |
| frame recovery | `.tmp/attr-probe/frame_recovery.py` | the frame equals the placed path's bbox under the inverse placement, by construction |
