# Feather aggregate — end state structure

**Status: rectified.** `feathers-aggregate - Copy.svg` now matches this document
(2026-09-28, 187 ids → 60). §9 records the verification. `feathers-aggregate.svg`
is untouched and still speaks the old grammar.

**Scope:** the aggregate SVG and the pipeline couplings in `make_logical_pages.py`.
`pages_to_pdf.py` is untouched — it only ever sees `page-NNN.svg`.

**The rule everything follows:** identity comes from **nesting**, role from the
**class**, human reading from the **label** — and an id exists only where a script
looks one up.

## 1. Document tree

```xml
<svg id="…">                                  plumbing ids: not part of the contract
  <namedview/>                                Inkscape page setup
  <defs/>                                     one shared <marker id="diamond">
  <style/>                                    presentation only; no id selectors

  <g id="B" class="family b">                 8 family containers: B P PC A SC MC LC S
    <g id="B1" class="feather" data-wh="…" data-vb="…" data-rot90="1">
      <path class="outline" d="…"/>           exactly one <path> — the outline
      <circle class="mark" cx="…" cy="…" r="0.5"/>   zero or more marks
    </g>
    …                                         B2, B3
  </g>
  …                                           P PC A SC MC LC S, same shape

  <g id="outline-toplines">                   the one placement container
    <g id="B-topline" class="topline" data-wh="…" data-vb="…" transform="rotate(…)">
      <path class="guide" d="…"/>             source-space geometry, unrotated
      <circle class="mark" cx="…" cy="…" r="0.5"/>
    </g>
    …                                         8 guide groups, A-topline … S-topline
    <g id="upper-outline" transform="matrix(…)">
      <path class="outline" d="…"/>           source-space; the whole-wing silhouette
    </g>
  </g>

  <g id="align" style="display:none">         diagnostic overlay: hidden, never read
    <g id="B-align" class="align">
      <path class="outline" …/>               the family silhouette
      <path class="arrow" …/>                 one per member, carrying the arrowhead
    </g>
    …                                         one per family
  </g>
</svg>
```

### The guide invariant — read this before editing the placement group

A guide group is read **twice, with two different meanings**, and one
representation has to satisfy both:

| reader | uses the group transform? | wants |
|---|---|---|
| `read_topline()` (the guide strip page) | **no** — ignored | the guide in its **own frame, unrotated** |
| `read_placement()` (the placement drawing) | **yes** — wrapped around the children | the guide **arranged** on the wing |

So the children are drawn in the guide's own frame, and the arrangement lives on
the **group transform**. Baking the rotation into the path data — which is what the
copy had — satisfies the placement page and quietly breaks the strip page: the
guide prints rotated, and the origin circles, whose own `rotate(…)` transforms
`_group_content()` drops, print at coordinates far outside the guide's frame
(`_frame`'s sibling assertion in `verify_body()` catches the second one, not the
first). `upper-outline` follows the same rule; `read_placement()` uses its
transform, and nothing reads its id.

## 2. Identifier grammar

| # | kind | id form | example | read by |
|---|---|---|---|---|
| 1 | family container | `<FAMILY>` | `PC` | nothing — the class carries it |
| 2 | item group | `<FAMILY><n>` | `PC1` | `_def_group()` by manifest name |
| 3 | guide group | `<FAMILY>-topline` | `PC-topline` | `_def_group()` by manifest name |
| 4 | placement container | `outline-toplines` | — | `PLACEMENT_GROUP` (line 63) |
| 5 | silhouette group | `upper-outline` | — | nothing by id; kept for reading |

Rules, all four of them:

1. **One token per level.** The family token appears exactly once in an id — never
   `PC-alignment-PC1-origin`.
2. **No leaf ids.** An outline path is the item group's `<path>`; a guide line is the
   guide group's `<path>`; an origin is a `<circle>`. Nothing below a group is named.
3. **Containers are role words, never numbers.** A family's alignment geometry lives
   in `<FAMILY>-align`, inside the `align` layer.
4. **No `-def` spelling.** One grammar, one spelling, no dual lookup.

Outside the contract, and free to be named however you like: the `align` layer, its
eight `<FAMILY>-align` groups, `diamond`, and the plumbing ids (`svg42`,
`namedview1`, `defs1`, `style1`). Nothing reads them.

## 3. Classes

| class | on | meaning |
|---|---|---|
| `family` | family container | a prefix group |
| `feather` | item group | a printed component |
| `topline` | guide group | an alignment guide slot |
| `outline` | `<path>` | a silhouette / feather outline |
| `guide` | `<path>` | a guide line |
| `mark` | `<circle>` | an origin dot — **filled** |
| `arrow` | `<path>` | an overlay origin arrow — **stroked, with the arrowhead** |
| `align` | overlay group | diagnostic geometry |

`mark` and `arrow` are deliberately separate: one class cannot mean both a filled dot
and a stroked hairline. The overlay's arrows are re-classed from `mark` for exactly
that reason.

Only one id selector survives, and on purpose: `#diamond` styles the single shared
marker def. The rule about classes exists so no *family* rule depends on an ancestor
id, not to ban id selectors outright.

Plus one colour token per family (`b p pc a sc mc lc s`) on the family container,
so the eight fill rules stop depending on an ancestor id. Every element in the file
carries its presentation in a class rule; the only inline `style` left is
`display:none` on the overlay layer, which is a visibility state rather than styling:

```css
.outline { stroke: #000000; }

/* a guide line and an overlay origin arrow are the same kind of stroke */
.guide,
.arrow {
  fill: none;
  stroke: #000000;
  stroke-width: 0.264583;
  stroke-linecap: butt;
  stroke-linejoin: miter;
}
.arrow { marker-start: url(#diamond); }

/* one marker, not twenty-eight; the head takes the path's stroke colour */
#diamond { overflow: visible; }
#diamond path { fill: context-stroke; fill-rule: evenodd; stroke: none; }

.mark { fill: #000000; stroke: none; }

.align { opacity: 0.5; }
.align .outline { fill: none; stroke: #000000; }

.p .outline { fill: #1f77b4 }      /* was  #P .outline */
```

**Classes are authoring-side, not contract.** Neither script reads `class`; the
pipeline writes its own (`class="outline"` at line 411, `class="guide"` at line 540).
The aggregate's stylesheet must also stay out of the print CSS: it uses `px`-free
unitless widths by convention, but the pipeline's own CSS is the only one that
matters for print, and `make_logical_pages.py` lines 70–73 documents why it keeps
those unitless.

## 4. Attributes

| attribute | on | replaces |
|---|---|---|
| `data-wh` | item group, guide group | — (already used) |
| `data-vb` | item group, guide group | — (already used) |
| `data-rot90` | item group | `rotate90 = name.startswith("B")` (line 368) |

`data-rot90` is written on the three B items but is still inert: the pipeline keeps
its name-prefix rule until someone changes it.

## 5. What the rectification removed

| gone | was |
|---|---|
| 28 `X1-outline` ids | the parent group already named the item |
| 16 `X-topline-outline` / `-origin` ids | found by tag; the group names the slot |
| 28 `X-alignment-X1-origin` ids | nesting + `class="arrow"` says it |
| 8 `X-alignment-outline` ids | nothing read them |
| 27 of 28 `<marker>` defs + all 28 child ids | one shared `#diamond` |
| `all-alignment` + `feather-group-placement` | one `align` layer, one `outline-toplines` |
| 8 `#<FAMILY> .outline` selectors | `.` + family class |
| `A-toplines` (plural) | the group id equals the manifest name |
| 29 inline `style` attributes on overlay paths | class rules |
| 2 inline `style` attributes on the marker and its head | `#diamond` rules |

Kept deliberately: **`outline-toplines`** — renaming it changes the placement page's
`<title>` and so the page hashes. The misnomer is cheaper than the churn.

## 6. Why this stays simple

- **Nothing unique is hand-typed twice.** Every copy/paste duplicates a *class*,
  which is allowed — so Inkscape cannot mint `-8`, `-81`, `-82` again.
- **No name carries geometry.** The B-group rotation, the plural `s`, and the `-def`
  suffix were all syntax smuggled into identity.
- **A lookup cannot be satisfied by the wrong thing.** `_def_group()` matches *any*
  element by id. That is not theoretical: while rectifying, the guide groups renamed
  to the singular spelling made `{c.get("id")[:-1]: c}` miss, and because
  `_def_group("A-topline")` then found the guide *group*, `main()` silently built all
  eight guides through `read_feather()` — pages that render, with every origin circle
  missing, instead of an error. With leaves unnamed and one grammar, that near-miss
  cannot recur (§7, item 2).
- **Adding an object costs no new names.** A mark is a classed `<circle>` inside an
  existing group.

## 7. Consumer agreement

| # | location | change | state |
|---|---|---|---|
| 1 | `read_feather()` line 368 | `rotate90` from `data-rot90`, not the name | **todo** |
| 2 | `main()` line 730 | key guides by manifest name, not by slicing one character | **done** |
| 3 | `_def_group()` 337–350 | drop the `{name}-def` fallback | todo |
| 4 | `_path_d()` 353–356 | first **direct-child** `<path>`, so a nested mark can't shadow the outline | todo |

Item 2 landed as a tolerant rewrite (`re.sub(r"-toplines?$", "-topline", …)`) rather
than a plain rename, so the old aggregate and the rectified one both work while the
two files coexist. Items 1, 3 and 4 are inert until someone edits the pipeline.

Unchanged: `PLACEMENT_GROUP` (63), `_frame()` (320–334), `topline_children()`
(378–385, direct-child `<g>` carrying `data-wh`), `_group_content()` (533–544),
`read_topline()` (547–556), `read_placement()` (559–590), the manifest (255–282).

## 8. Inventory

Measured before and after the rectification.

| | before | after |
|---|---|---|
| id attributes | **187** | **60** |
| marker defs + child paths | 28 + 28 | 1 + 0 |
| family containers | 8 | 8 |
| item groups | 28 | 28 |
| item outline leaf ids | 28 | 0 |
| guide groups | 0 (16 bare leaves) | 8 |
| topline leaf ids | 16 | 0 |
| alignment origin leaf ids | 28 | 0 |
| alignment outline leaf ids | 8 | 0 |
| silhouette | 1 bare leaf | 1 group |
| overlay groups | 9 (incl. `all-alignment`) | 8 + 1 layer |
| CSS rules keyed on an id | 8 | 0 |

The 60 that remain: 8 families + 28 items + 8 guides + `outline-toplines` +
`upper-outline` + `align` + 8 `<FAMILY>-align` + `diamond` + 4 plumbing.

## 9. Verification

The rectification is structure-only; the test is that the pipeline's output does not
move. `make_logical_pages.py` was run against both aggregates into throw-away
directories and every page hashed.

| check | result |
|---|---|
| logical pages | 25 vs 25, **24 byte-identical** |
| the one difference | `page-015` = `PC1/PC2` — those two outlines were **redrawn in the copy** (the only geometry difference; 26 of 28 outlines are byte-identical) |
| `topline_children()` | 8, all found |
| feathers | 8 families / 28 items, `mirror_check` and `verify_body` clean |
| guides | 8 read, `verify_body` clean (was: `placement_group()` assert, no guides found) |
| placement | 249.4 × 195.9 mm, `verify_body` clean |
| guide geometry | all 8 groups byte-identical to the tracked file's source-space form (baked form matched to ≤ 0.0001 mm before adoption) |
| silhouette | path and transform byte-identical |
| CSS roll-up | the whole document rendered with the overlay forced visible, before and after: **0 differing pixels** of 4 929 288 |
| marker from CSS | Inkscape 1.4 render of an inline-style marker vs a class-rule marker: **0 differing pixels** — the arrowhead resolves from `.arrow { marker-start: … }` |

Two things the rectification did **not** decide:

- **PC1/PC2** are redrawn in this copy. That is a content change, and it is why one
  page differs; the structural rework is output-neutral apart from it.
- The copy is still untracked and `feathers-aggregate.svg` is still what the pipeline
  reads by default. Switching `AGG_SVG` is a separate, deliberate step.
