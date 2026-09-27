# Plan — consolidate `individuals/` back into `feathers-aggregate-min.svg`

**Status: implemented.** See "Outcome" at the end for what actually happened, including
two things this plan got wrong.

**Scope:** `mechanical/templates/feathers-aggregate-min.svg`, the new
`mechanical/templates/consolidate_aggregate.py`, and the three readers in
`make_logical_pages.py`. `pages_to_pdf.py` is untouched. The 25 generated logical
pages must come out **byte-identical**.

This is the inverse of `775d311` ("break out feathers into individual files"). The
aggregate is currently a manifest of 29 external references —
`<use href="individuals/X.svg#X-def">` — and cannot be rendered by anything that does
not resolve external hrefs. After this, the aggregate is the source of truth and
`individuals/` is deleted.

---

## 0. Terminology

| name | means |
|---|---|
| **def group** | `<g id="X-def">` — one feather's or topline's geometry, copied verbatim |
| **placement** | the `<use>` in `<g id="P">`/`<g id="S">`/… that rotates and positions a def group |
| **frame** | the individual file's `viewBox` origin + extent (`x0 y0 W H`), which the scripts need |
| **internal item** | a def group the scripts read: 28 feathers + 8 toplines = 36 |
| **catalog items** | the internal items **plus** the two whole-wing outlines (`top-lines`, `total-outline`) |

---

## 1. What is actually true today

Measured, read-only, with Inkscape as the reference renderer.

| claim | evidence |
|---|---|
| The scripts never read the aggregate | `make_logical_pages.py` read `individuals/*.svg` directly before this change (`read_feathers`, `read_topline`, `read_placement`) |
| The aggregate could not render without the individuals | cairosvg renders it **empty**; Inkscape `--query-all` resolves the hrefs |
| The aggregate's 29 placements are the *only* place rotations live | 8 group `transform`s + 28 `<use>` matrices |
| Hoisting a def group and retargeting the `<use>` to `#X-def` changes nothing | `--query-all` gives **identical bboxes** for every id, and an Inkscape render at 96 dpi is **pixel-identical** (0 of 2,019,235 px) |
| The split **dropped each file's `viewBox` origin** | the `<use>` matrices already absorb it, so inlining needs **no compensating translate** — B1,B2,… all reproduce exactly |
| `outline-toplines.svg` never rendered inside the aggregate | its groups sit at y ≈ 1675–1900; the aggregate's `viewBox` is `0 0 247.95744 570.1775` |
| `<use>` `width`/`height` are inert here | they only size a reference to `<symbol>`/`<svg>`; these reference `<g>`. Kept verbatim anyway. |

**Consequence:** the consolidation is a pure re-homing of markup. No transform needs
recomputing, which is exactly why "keep everything rotated the same way" is achievable
without touching a single matrix.

> **Superseded in part.** §2 below proposes `<defs>`. The geometry now lives in a
> *hidden group* instead, because `<defs>` is awkward to edit in Inkscape. That change
> landed after the consolidation and is recorded in §11; the inlining rule itself is
> unaffected, since `<defs>` and the hidden group differ only in the container.

---

## 2. Target shape of the aggregate

```xml
<svg width="247.95744mm" height="570.17749mm" viewBox="0 0 247.95744 570.1775" …>
  <style>…</style>
  <defs>
    <!-- one per feather, copied verbatim, plus its frame as data attributes -->
    <g id="B1-def" class="group B"
       data-wh="193.15454 81.754908"
       data-vb="108.29541 44.994112 193.15454 81.754908">
      <path id="B1-outline" class="outline" d="…"/>
    </g>
    …
    <!-- one per topline -->
    <g id="A-topline-def" data-wh="2 89.629811"
       data-vb="190.064856 1723.540766 2 89.629811">
      <path …/><circle …/>
    </g>
    …
    <!-- the whole-wing placement template, re-homed -->
    <g id="placement-top-lines" transform="matrix(…)" style="display:inline">
      <use id="toplines-B" href="#B-topline-def" width="90.278854" height="89.806569"
           transform="rotate(-47.685529 47.679584 1789.868628)"/>
      … 8 of these …
    </g>
    <g id="placement-total-outline" transform="matrix(…)" style="display:inline">
      <g id="placement-upper-outline">
        <path …/>  <!-- upper-outline's geometry, translated to the aggregate frame -->
      </g>
    </g>
  </defs>

  <sodipodi:namedview …/>
  <title …/>
  <desc …>…</desc>

  <g id="B" transform="matrix(…)">
    <use id="B1" href="#B1-def" width="193.15454" height="81.754908"
         transform="matrix(0.034899…,1696.703…)" />
    …
  </g>
  …
  <use id="top-lines-ref" href="#placement-top-lines"
       transform="translate(-33.258665,-26.770171)" style="display:inline" />
  <metadata …/>
</svg>
```

### The inlining rule, stated exactly

For each `<use href="individuals/X.svg#X-def">`:

1. copy `<g id="X-def">` **verbatim** into `<defs>` — no transform added, no path touched;
2. add `data-wh` / `data-vb` from the source file's `width`/`height`/`viewBox`;
3. change **only** the `href` to `#X-def`.

`id`, `width`, `height`, `style` and `transform` on the `<use>` remain byte-for-byte.
That is what preserves all three rotation forms: the group wrappers, the per-`<use>`
matrices, and B1–B3's 90° inside the path data.

---

## 3. The two frames that do not fold in cleanly

### 3a. `outline-toplines.svg` — the placement template

Its root `viewBox` origin *is* the frame `read_placement()` measures against, and it
references the eight toplines. Three groups live in it:

| group | what it draws | disposition |
|---|---|---|
| `top-lines` | the eight toplines, each via `<use href="X-topline.svg#X-topline-def">` | inline into `<defs id="placement-top-lines">`, retarget each `<use>` to `#X-topline-def` |
| `total-outline` | same transform as `top-lines` | inline into `<defs id="placement-total-outline">` |
| `upper-outline` | referenced by `total-outline` from `upper-outline.svg` | inline into `<defs id="placement-upper-outline">` |

Two wrinkles, both benign:

- **`read_placement()` measures the union**, not just `top-lines`. Because
  `total-outline`/`upper-outline` carry the *same* `matrix(1.0060486,0.09641559,-0.01794757,1.1907292,78.158134,-1978.5147)`
  as `top-lines`, including both groups is geometrically a no-op versus including one.
  The plan keeps all three so `measure_ink()` sees exactly the same ink. **This is
  assertion-checked: if the measured `W`/`H` changes at all, the consolidation is wrong.**
- **The ids collide.** `top-lines`/`total-outline` live in two files and `upper-outline`
  in a third, so the defs copy is namespaced with a `placement-` prefix. The three
  in-document `<use>` ids (`top-lines-ref`, plus the two inner `upper-outline` uses) are
  renamed `toplines-B`, `toplines-P`, … and `placement-upper-outline-ref` to avoid
  clashing with the 36 def-group ids.

The existing `<use id="top-lines-ref" href="individuals/outline-toplines.svg#top-lines">`
in the document body keeps its `translate(-33.258665,-26.770171)` and simply points at
`#placement-top-lines`. Its (invisible) position in the drawing is unchanged.

### 3b. `upper-outline.svg` carries `inkscape:label`

`read_placement()` re-serialises each path with `_group_content()`, which emits bare
`<path class="guide" d="…"/>` and never copies `transform` on the path. The one
namespaced attribute that survives into a logical page would be `inkscape:label` on a
`<path>` — it appears in `B-topline`, `PC-topline`, `S3`, `S4`, `SC1`–`SC4` too.
The plan strips `inkscape:*` / `sodipodi:*` attributes from every def group at
consolidation time, in the writer, and asserts none survive.

---

## 4. Per-feather frame: option (a)

`read_feathers()` needs `W`, `H` **and** the `viewBox` origin `x0, y0`
(`right_transform()` and `mirror_check()` both use them). Those lived on each file's
root `<svg>`; a `<g>` cannot carry them, and the aggregate's own `viewBox`
(`0 0 247.95744 570.1775`) is the catalog's, not any feather's.

**Adopted: (a) data attributes on the def group.**

```xml
<g id="P1-def" class="group P"
   data-wh="107.70177 348.70091"
   data-vb="171.95 164.833 107.70177 348.70091">
```

Two attributes rather than three: `data-wh` is `W H`, `data-vb` is `x0 y0 W H`.
The reader asserts `data-wh == data-vb[2:]` and refuses a group missing either, so a
botched frame fails loudly instead of silently moving a feather. The `rotate90 = name
.startswith("B")` rule stays in the script, where it belongs — it is a pipeline fact,
not a property of the file.

*Rejected:* (b) a sidecar `<defs>` entry holding only the frames — adds a second place
to look and a second thing to keep in sync.

---

## 5. Code changes

### 5a. New: `mechanical/templates/consolidate_aggregate.py`

One-shot, idempotent, committed alongside the result (it is the inverse of the deleted
`break_out_feathers.py`, and it is the only record of how the file was assembled).

```
load aggregate
for each external <use>:
    resolve individuals/X.svg -> root width/height/viewBox + <g id="X-def">
    assert every id resolves, assert no duplicate target
    copy def group into defs, strip namespaces, add data-wh/data-vb
    rewrite only the href -> #X-def
special-case outline-toplines:
    re-home top-lines / total-outline / upper-outline into placement-* ids
    retarget the 8 inner uses and rename the inner use ids
insert one <defs> immediately after </style>
write, or refuse and change nothing
```

Guards: every `href` must resolve; no two sources may claim the same def id; the twelve
catalog items referenced by the body must all exist in defs.

### 5b. `make_logical_pages.py`

- `IND_DIR` → `AGG_SVG = ROOT / "mechanical" / "templates" / "feathers-aggregate-min.svg"`,
  plus one `load_aggregate()` that parses once and indexes `{id: element}`.
- `read_feathers()` — per name, take the `{name}-def` group's `data-wh`/`data-vb` and its
  path `d`; keep the `viewBox == W/H` assertion and the whitespace normalisation.
- `read_topline(name)` — same, from `{name}-topline-def`.
- `read_placement()` — walk the `placement-top-lines` / `placement-total-outline` groups,
  splicing each referenced `{name}-topline-def` in place of its `<use>`.
- The manifest assertion (`set(listed) == set(raw)`) is unchanged and still guards
  against a def group being dropped.

### 5c. Documentation

- The comment at line 80 and the `<desc>` at line 104 both still say the geometry lives
  in `individuals/`. Both are rewritten to describe the consolidated file.
- `mechanical/README.md` gains one line noting the aggregate is now the geometry source.

---

## 6. Validation

Every step is falsifiable and cheap:

1. **Baseline** — SHA-256 of the 25 `logical-pages/page-*.svg`.
   `pages_to_pdf.py` baseline: **30 sheets** (5 tiled, 20 fit).
2. **Consolidation is geometry-preserving** — Inkscape `--query-all` on the old and new
   aggregate: every surviving id must have an identical bbox (tolerance `1e-6`).
3. **Rendering** — Inkscape render of both at 96 dpi must be pixel-identical.
4. **`read_placement()` frame unchanged** — print `W`/`H` before and after; must match to
   3 decimals.
5. **Pipeline** — re-run `make_logical_pages.py`; all 25 pages byte-identical to step 1.
   `pages_to_pdf.py` still yields 30 sheets with the tiling and scale checks passing. The
   tracked PDF must not change.
6. **No stragglers** — `git grep individuals` returns nothing outside history and this
   plan; the scripts' assertions still fire if a def group is missing.
7. Commit the consolidation and the script change separately.

---

## 7. Risks

| risk | containment |
|---|---|
| A mistyped `href` silently drops a feather | writer asserts every reference resolved; the manifest assertion in `main()` and validation 5 both catch it |
| A frame is lost or wrong | `data-wh`/`data-vb` required, cross-checked against each other; `read_feathers` asserts `viewBox == W/H`; `mirror_check()` fails loudly |
| Def-group ids collide across the three outlines | defs copies are prefixed `placement-`; the writer asserts id uniqueness across the whole file |
| `outline-toplines` reframing shifts the placement page | validation 4 compares `W`/`H` numerically; the same-transform fact in §3a means it cannot move |
| The catalog starts showing the placement template | impossible by construction — inlining preserves the y ≈ 1700 offsets, so it stays off-canvas as it is today |
| Losing the ability to regenerate `individuals/` | `consolidate_aggregate.py` is committed; the inverse is mechanical and the file is in git history |

---

## 8. Commit sequence

1. `templates: add consolidate_aggregate.py` (the generator, not yet run)
2. `templates: inline the individuals back into feathers-aggregate-min.svg`
3. `print: read feather geometry from the aggregate`
4. `templates: delete individuals/`

Each commit leaves the tree consistent: (2) leaves the scripts working off the old
`individuals/`, (3) is the switch, (4) removes the now-dead directory.

---

## 9. Open question for review

**§3a** — the plan keeps all three placement outlines in `<defs>` so `measure_ink()`
sees identical ink and `read_placement()`'s frame is provably unchanged. The
alternative is to drop `total-outline`/`upper-outline` entirely (they are the built
wing's silhouette, not a template the script uses); that shrinks the file but changes
what `read_placement()` measures, and therefore the placement page's crop.
**Recommendation: keep all three.** *(Adopted.)*

---

## 10. Outcome

Four commits, as planned:

| commit | what |
|---|---|
| `ee418ee` | `templates: add the consolidator for individuals/ -> aggregate` |
| `2dc5346` | `templates: inline the individuals back into feathers-aggregate-min.svg` |
| `95f66b0` | `print: read feather geometry from the aggregate` |
| (this one) | `templates: delete individuals/` + stale-comment cleanup |

Every validation in §6 passed:

- `--query-all`: **38 ids, 0 bbox mismatches** (tol `1e-6`)
- Inkscape render at 96 dpi: **0 differing pixels** of 2,019,235
- `read_placement()`: identical `(W, H, body)` triple — `249.5653… × 192.6693…`
- **all 25 logical pages byte-identical** to the pre-change baseline
- `pages_to_pdf.py`: 30 sheets, tiling + scale checks pass, tracked PDF unchanged
- the whole pipeline runs with `individuals/` renamed away
- `git grep individuals` clean outside history and this plan

### Where the plan was wrong

1. **The sheet count is 30, not 29.** The plan said 29; the real baseline was 30 —
   5 tiled, 20 fit.
2. **§3a over-thought the placement template.** The plan worried that keeping only
   `top-lines` would shift `read_placement()`'s crop, and so carried all three groups
   defensively. In fact the three groups share one transform, so they measure the same
   ink; keeping all three was harmless but not load-bearing. Kept anyway — it is the
   literal inverse of the split, and the frames are now provably unchanged.

### Three bugs the verification caught during implementation

- `data-wh` initially carried `mm` suffixes (`"193.15454mm 81.754908mm"`). `parse_mm()`
  tolerates them, but the attribute should be bare numbers like `viewBox`. Fixed.
- Moved blocks were re-indented line-by-line, which reflowed Inkscape's attribute
  layout. Now each block is shifted as a whole, preserving its internal relative
  indentation (including the `<path>` continuation lines the editor left unindented).
- The writer originally wrote through `Path.write_text`, turning the file CRLF in a
  repository that `.gitattributes` pins to LF. All reads and writes now pass
  `newline=""`.

### Not done, deliberately

`consolidate_aggregate.py` stops working once `individuals/` is gone; it now exits with
a one-line message saying so. It is kept as the record of how the aggregate was
assembled — and because "make a change to the individual feathers and re-run it" is the
one workflow this consolidation removes. Editing geometry now means editing the def
group in the aggregate directly.

---

## 11. Follow-up: geometry moved out of `<defs>`

`<defs>` turned out to be awkward to edit in Inkscape — the outlines are buried in the
defs section rather than in the document tree. `hide_geometry_source.py` moved them into
a hidden group.

### Why the obvious hidden group does not work

`display` is **inherited into a `<use>`'s shadow tree**. Hiding the geometry container
with `display:none` therefore hides every placed copy as well, and the drawing
disappears. The override has to be re-stated on each `<use>`. Measured in Inkscape
against the `<defs>` build:

| technique | pixels differing |
|---|---|
| `display:none` on the group **+ `display:inline` on every `<use>`** | **0** of 2,019,235 |
| `visibility:hidden` on the group + `visibility:visible` on every `<use>` | 151,404 |
| bare `hidden` attribute | 151,404 |

So `display:inline` on the `<use>` elements is load-bearing, not belt-and-braces.
`hide_geometry_source.py` asserts every `<use>` carries it.

### Result

```xml
<defs id="defs1" />                        <!-- kept empty, as before -->
<g id="geometry-source" style="display:none">
  <g id="B1-def" data-wh="…" data-vb="…" class="group B">
    <path id="B1-outline" class="outline" d="…"/>
  </g>
  …
</g>
…
<use id="B1" href="#B1-def" width="…" height="…"
     transform="matrix(…)" style="display:inline" />
```

Verified: `--query-all` value-diffs against the original aggregate **0 of 38**, pixel
diff **0**, all **25 logical pages byte-identical**, PDF reproduces byte-for-byte.

### What this actually buys, and what it does not

- **It does not** put feathers back on the canvas. The container is hidden, so the
  geometry still does not draw — re-enabling `display` would double every feather,
  since the `<use>` elements already draw them.
- **It does** move 94 ids (the `-def` groups and their paths) out of the defs section
  and into the ordinary document tree, where Inkscape can reach them.
- **The editing path is `Shift+D`** (verified as `app.select-original` in this install's
  `keys/default.xml`): select any placed feather, press it, and Inkscape jumps to the
  source outline in `#geometry-source`. That is the practical way to edit geometry.


