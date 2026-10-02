# Plan — bake the elongated aspect correction into the feather geometry

**Status: proposed, not implemented.**

An aspect-ratio correction applied by hand in `templates/feathers-elongated.svg`
is **invisible to the print pipeline**. This plan moves that correction down into
the geometry so it stops being droppable, establishes `feathers-elongated.svg`
as the single source, and retires the aggregate.

The decision context:

- **`feathers-elongated.svg` becomes the source.** The correction is the thing
  that was wanted; the aggregate is the thing that lost it.
- **The correction is applied by baking, not by re-applying a transform.** A
  transform that anyone can drop again is the bug, not the fix.
- **Baking must be render-neutral.** The geometry's *frame* changes; what is
  drawn must not move by a single pixel. That is the acceptance test.
- **Re-tuning `layout.yaml` is a separate, later step** (§5.5). The correction
  does not fit the current sheet dimensions, so it cannot be landed silently.

## 1. The bug

`assemble_sheets.py` resolves a `source-id` and emits **only the matched
element**, copied verbatim under the spec's own placement transform
(`assemble_sheets.py:254`, `serialize()` at `:215`):

```python
for e in els:
    tr = transform_str(el["position"], el.get("transform"))
    out.append(f'<g transform="{tr}">{serialize(e)}</g>')
```

Any transform on an **ancestor** of the matched element is silently discarded —
one level of it, or four.

### The references split into two classes

`layout.yaml` has 39 distinct `source-id`s. Resolving each against a source
(39/39 resolve in both files):

| class | count | example | consequence |
|---|---|---|---|
| **leaf-style** | **28** | `//g[@id="P1"]/path` → `path#path8` | the `path` has no transform, so `P`'s and `P1`'s transforms — *and the correction* — are **dropped** |
| **group-style** | **11** | `//g[@id="B-align"]/g` → `g#g154` | the matched node is a `g`, so **its own** transform *is* kept — but its ancestors are still dropped |

So the spec is inconsistent with itself: the alignment overlays keep a
transform, the feathers keep none. This is why the correction appears to work in
some contexts and vanishes in others.

### It fails silently

Both files produce **visually identical** sheets — `premise.py` renders
`sheet-001.svg` from each run and gets the same ink coverage to four decimal
places and bit-identical ink pixel bounds:

| source-file | sheet-001 ink | ink bbox (px) | emitted SVG |
|---|---|---|---|
| `feathers-aggregate.svg` | 0.9156 % | 76, 107, 4147, 3263 | — |
| `feathers-elongated.svg` | 0.9156 % | 76, 107, 4147, 3263 | differs in text only |

Two independent reasons, both quiet:

1. `layout.yaml:1` still names `feathers-aggregate.svg`, so the corrected file
   is never read.
2. Even if it were, every leaf-style reference drops the correction anyway.

Nothing warns. The bounds check only fires when ink falls *outside* the drawing
area, and the correction would push it *further* out — not into a new failure.

## 2. What was measured

Throwaway tooling lives in `.tmp/bake/`, consistent with the repo's `.tmp*`
convention (`.tmp/svg-clean/`, `.tmp-align/`). `.tmp*/` is gitignored, so those
scripts are reproducible-but-untracked; the numbers they produced are quoted
here so the conclusions survive without them.

| Question | Finding | Tool |
|---|---|---|
| Is `elongated` a derivative of `aggregate`? | Yes — same 321 ids, same 39 roots, same ruler groups, minus 5 stray `*-N` clone elements | `analyze.py`, `featcheck.py` |
| Did the feather **shapes** change? | **No.** 0 of 73 paths differ; every number in `d` is numerically identical | `two_questions.py` §Q2 |
| Then what changed? | A non-uniform canvas scale — **sx = 0.84501499, sy = 1.2249641** — applied through group transforms, plus repositioning | `analyze.py`, `tiebreak.py` |
| Proof it is a pure canvas scale | the two files' accumulated `P1` matrices have component ratios `0.845015 / 1.224964` | `tiebreak.py` |
| Corrections dropped here too? | 73/73 referenced paths sat under a transform in the pre-fix state | `check_referenced.py` |
| Do the `*-align` groups differ between the files? | No — `det(elo)/det(agg) = 1.000000` for all eight; each pairs the outer correction with a nested inverse | `det_check.py` |
| Transform inventory | **81** total: 64 on `<g>`, 17 on `<path>`, nested up to 4 deep | `featcheck.py` |
| Arc commands in any `d` | **zero** | `featcheck.py` |

The root carrier is one group:

```xml
<g id="g2" transform="matrix(0.84501499,0,0,1.2249641,0.05113768,-0.05432029)">
```

**Wording that matters:** the shapes are identical *as authored*, but the
elongated file is not "just a stretch" of the aggregate. Each feather sits under
a different local transform, so the correction is applied anisotropically with
respect to each feather's own axis. Baking preserves that; "the geometry is
unchanged" and "the feathers are not stretched" are different claims, and only
the first is true.

## 3. Why not Inkscape's `transform-remove`

Tried it. It runs clean and is pixel-identical:

```
inkscape --actions="select-all;transform-remove;export-filename:baked.svg;export-plain-svg;export-do"
  → 81 transforms become 64;  rendered diff vs original: max channel diff 0
```

But it only un-nests the outer `g2`. Afterwards **all 73 referenced paths still
sit under a transform**, including under their own id groups:

```
B1  -> path5  transforms above: g2/B/B1/B1
P1  -> path8  transforms above: g2/P/P1/P1
```

It appears to need roughly one pass per nesting level, it rewrites the whole
document, and it weakens the id-scoped guarantees the spec's selectors depend
on. A local, deterministic bake is smaller, reviewable as a diff, and preserves
the group/class structure.

## 4. The rule to implement

**Local bake**: for every element that carries a `transform`, map *that
element's own geometry* through *that element's own matrix*, then delete the
attribute.

```
T_cumulative(path) = T(root) · … · T(parent) · T(path)
```

Baking each element's own matrix applies every ancestor's transform exactly once
at the leaf, and the composition telescopes to exactly `T_cumulative`. Group
nesting, ids and classes are untouched, so `//g[@id="P1"]/path` still resolves
and the engine's slicer keeps working unchanged.

Properties: render-neutral by construction; idempotent (a transform-free file
passes through unchanged); local (element-level matrices are small — `scale`,
`translate`, `rotate`, and a rotation-carrying shear on the `*-align` groups).

### Constraints the evidence forces

| Constraint | Why |
|---|---|
| Only `M m L l H h V v C c S s Q q T t Z z` need handling | zero arcs in the corpus |
| Output forced absolute | relative commands cannot survive a coordinate change |
| Scale `stroke-width` for non-uniform transforms | the `*-align` groups carry a real shear + anisotropic scale; without this the bake is **not** pixel-identical. Use `sqrt(abs(det))` as the uniform equivalent and confirm with §5.3 check 3 rather than trusting the approximation |
| `<line>`/`<circle>` → `<path>` if a non-uniform transform hits one | they distort otherwise. Only the 5 stray clone groups contain these, and those are deleted |
| Strip `data-rot90="1"` | Inkscape metadata that goes stale after baking and would mislead later tooling |

## 5. Steps

### 5.1 Build the baker — `.tmp/bake/bake.py`

Throwaway tool. Reuse the already-proven transform and path machinery in
`.tmp/bake/` (`_mul`, `_ops`, path parsing) rather than reimplementing it.

### 5.2 Bake `templates/feathers-elongated.svg` in place

Keep `viewBox="0 0 250 700"` — the frame the correction was authored in.

### 5.3 Verify

1. **No droppable transforms left.** Zero `transform=` on any of the 39
   referenced roots or anything beneath them. This is the bug being fixed, so it
   is the primary check.
2. **Whole-canvas render is identical.** Before vs after, both at 250 × 700, max
   channel diff **0**.
3. **Per-element slices are identical.** Slice each of the 39 referenced
   elements the way the engine does and render the slice alone, before vs after.
   Catches a `stroke-width` shift that a whole-canvas check can hide.

> Checks 1–3 prove the bake itself is faithful. They do **not** prove the
> correction reached the paper, because the pre-bake and post-bake *source* files
> draw the same thing. That is step 5.5's job.

### 5.4 Point the spec at the new source

`templates/layout.yaml:1` → `source-file: feathers-elongated.svg`.

### 5.5 Re-tune `layout.yaml` — the step that actually carries the correction

Baking changes each feather's local coordinates and therefore its ink bbox.
Measured, for P1 (`sheet` is 260 × 348.884):

| | x span | feather height |
|---|---|---|
| as emitted today (raw, correction dropped) | 18.30 … 124.00 and 136.00 … 241.70 | 347.88 |
| **corrected** (raw pushed through sx/sy) | 15.46 … 104.78 and 114.92 … 204.24 | **426.14** |

The correction makes each feather **0.845× as wide and 1.225× as tall**. P1's
corrected height (426.14) **exceeds its sheet (348.884)** — so `layout.yaml`'s
`dimensions` are not merely stale, they are **incompatible** with the correction
as currently written. This is the step that needs a human eye.

Deliverable for this step: for all 22 sheets, the current `width`/`height`, the
ink bbox the baked source actually produces, each `*-left`/`*-right` label's
current vs correct position, and which sheets no longer fit.

### 5.6 Retire the aggregate

`git rm templates/feathers-aggregate.svg`, after grepping all scripts and docs
for the name. Note `templates/declarative-layout-plan.md` uses it in its schema
example and would need a touch-up.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Baking silently changes what is drawn | §5.3 checks 2 and 3, before anything tracked changes |
| `stroke-width` drifts on sheared groups | scale for the transform's non-uniformity; §5.3 check 3 detects it, so the approximation is never the last word |
| The correction lands but the sheets do not fit | §5.5 is a hard prerequisite for a usable PDF, not a follow-up |
| The bounds check under-reports | it reads the *selected* geometry, which for leaf references excludes ancestors. It is a weak check and must not be treated as sign-off |
| `B1` ink-bbox warning | **pre-existing in both files** (`y −6.98`; `199.13` vs a 192.155 sheet). Not caused by this work, but it needs attention when dimensions are recomputed |
| Baking is one-way | a single commit on a tracked file; `git diff` is the review surface and the pre-bake file is recoverable from history |

## 7. Honest scope of the win

Baking is render-neutral **by construction**, so steps 5.1–5.4 and 5.6 do not
change a single pixel of the print output. They make the correction
*un-droppable* and put it in the right file.

Step 5.5 is what actually gets the correction onto paper — and per §5.5 it is
not a tweak, it is a re-fit of every sheet, because a 1.225× taller feather no
longer fits the sheet dimensions the aggregate's uncorrected geometry was
measured for.

That split is deliberate: 5.1–5.4 and 5.6 are provably safe and reviewable as a
diff; 5.5 needs judgement.

## 8. Relationship to other plans

- **`templates/wysiwyg-editor-plan.md` §2 is the strongest independent evidence
  for §1 here.** It documents the defect as *intended* behaviour, as a parity
  constraint the editor must reproduce: *"selected element is copied verbatim …
  ancestor view-transforms are not copied (that is why `/path` XPaths exist)"*.
  That is the same mechanism, recorded from the editor's side, and it means an
  editor built to match today's engine would faithfully reproduce the bug.
  Baking removes the constraint: once no transform is on an ancestor, "the whole
  group carries its own frame" and both the engine and the editor get the same
  answer. It also lets the palette offer group ids (`//g[@id="P1"]`) rather than
  the transform-losing `/path` forms.
- **The editor plan's auto-fit `dimensions` feature** ("auto-fit to the union of
  element bounds", §3.1) is exactly the tool §5.5 needs. Worth building §5.5's
  re-fit with that in mind, rather than hand-tuning 22 sheets twice.

## 9. Corrections to earlier claims

Two statements made while investigating this were wrong. They are recorded here
because the second one shaped the scope decision and should not be inherited.

1. **"The elongated file's `g2` scale is uniform, so the align groups were
   distorted by mistake."** Wrong. For every one of the eight `*-align` groups,
   `det(elo) / det(agg) = 1.000000` exactly (`det_check.py`) — each group carries
   a compensating nested inverse that leaves its own net transform identical to
   the aggregate's. Being precise about what that does and does not say: it means
   the correction is *not* baked into the align groups ourselves; the correction
   still rides on `g2` above them, so it is dropped at a leaf reference exactly
   like everywhere else. The `group-style` references only survive because the
   matched node is a `g` and the engine keeps that one node's transform.

2. **"P1's placed ink span moves from x 143–249 to x 18–242 when switching
   source."** Wrong — that came from the engine's own bounds-check report, which
   reads the *selected* geometry and therefore excludes ancestor transforms. The
   true figures are in §5.5: both files emit the same x span (18.30 … 241.70),
   and the corrected span would be 15.46 … 204.24 with a 426.14 height. Sheet
   dimensions are therefore **incompatible** with the correction, which is a
   stronger and more concrete finding than the one it replaced.
