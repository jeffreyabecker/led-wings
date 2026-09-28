# Feather aggregate — end state structure

**Status: target specification. Not implemented.** `feathers-aggregate - Copy.svg` is
mid-reorganisation; this is what it settles to.

**Scope:** the aggregate SVG and the four identifier couplings in
`make_logical_pages.py`. `pages_to_pdf.py` is untouched — it only ever sees
`page-NNN.svg`. The generated logical pages are the acceptance test.

**The rule everything follows:** identity comes from **nesting**, role from the
**class**, human reading from the **label** — and an id exists only where a script
looks one up.

## 1. Document tree

```xml
<svg id="…">                                  plumbing ids: not part of the contract
  <namedview/>                                Inkscape page setup
  <defs/>                                     empty — no <marker> defs
  <style/>                                    presentation only

  <g id="B" class="family b">                 8 family containers: B P PC A SC MC LC S
    <g id="B1" class="feather" data-wh="…" data-vb="…" data-rot90="1">
      <path class="outline" d="…"/>           exactly one <path> — the outline
      <circle class="mark" cx="…" cy="…" r="0.5"/>   zero or more marks
    </g>
    …                                         B2, B3
  </g>
  …                                           P PC A SC MC LC S, same shape

  <g id="outline-toplines">                   the one placement container
    <g id="B-topline" class="topline" data-wh="…" data-vb="…">
      <path class="guide" d="…"/>             exactly one
      <circle class="mark" cx="…" cy="…" r="0.5"/>   exactly one — the origin
    </g>
    …                                         8 guide groups, A-topline … S-topline
    <g id="upper-outline">
      <path class="outline" d="…"/>           whole-wing silhouette
    </g>
  </g>

  <g id="align" style="display:none">         diagnostic overlay: hidden, never read
    <g id="B-align"><path class="outline" d="…"/>…</g>
    …                                         one per family
  </g>
</svg>
```

## 2. Identifier grammar — four kinds

| # | kind | id form | example | read by |
|---|---|---|---|---|
| 1 | family container | `<FAMILY>` | `PC` | nothing — the class carries it |
| 2 | item group | `<FAMILY><n>` | `PC1` | `_def_group()` by manifest name |
| 3 | guide group | `<FAMILY>-topline` | `PC-topline` | `_def_group()` by manifest name |
| 4 | placement container | `outline-toplines` | — | `PLACEMENT_GROUP` (line 63) |

Rules, all four of them:

1. **One token per level.** The family token appears exactly once in an id — never
   `PC-alignment-PC1-origin`.
2. **No leaf ids.** An outline path is found as the item group's `<path>`; a mark is
   found as a `<circle>`. Nothing below a group is named.
3. **Containers are role words, never numbers.** There is no `MC-7`; a family's
   alignment geometry lives in `<FAMILY>-align`.
4. **No `-def` spelling.** One aggregate, one grammar, no dual lookup in `_def_group()`.

## 3. Classes

| class | on | meaning |
|---|---|---|
| `family` | family container | a prefix group |
| `feather` | item group | a printed component |
| `topline` | guide group | an alignment guide slot |
| `outline` | `<path>` | a silhouette / feather outline |
| `guide` | `<path>` | a guide line |
| `mark` | `<circle>` | an origin point |
| `align` | the overlay layer's groups | diagnostic geometry |

Plus one colour token per family (`b p pc a sc mc lc s`) on the family container,
so the eight fill rules stop depending on an ancestor id:

```css
.outline { stroke: #000000; }
.guide   { fill: none; stroke: #000000; stroke-width: .264583; }
.mark    { fill: #000000; stroke: none; }
.align   { opacity: .5; }
.p .outline { fill: #1f77b4 }      /* was  #P .outline */
```

**Classes are authoring-side, not contract.** Neither script reads `class`; the
pipeline writes its own (`class="outline"` at line 411, `class="guide"` at line 540).
The aggregate's stylesheet must also stay out of the print CSS: it uses `px` units,
which `make_logical_pages.py` lines 70–73 documents as a cairosvg 96-dpi trap.

## 4. Attributes

| attribute | on | replaces |
|---|---|---|
| `data-wh` | item group, guide group | — (already used) |
| `data-vb` | item group, guide group | — (already used) |
| `data-rot90` | item group | `rotate90 = name.startswith("B")` (line 368) |

## 5. What disappears

| gone | why it existed |
|---|---|
| 28 `X1-outline` ids | the parent group already names the item |
| 16 `X-topline-outline` / `-origin` ids | found by tag; the group already names the slot |
| 21 `X-alignment-X1-origin` ids | nesting + `class="mark"` says it |
| 21 `<marker>` defs + 21 `path19*` children | origins are circles; `_group_content()` (533–544) drops `style` and `marker-start` anyway, and the tracked aggregate has zero markers |
| `all-alignment`, `MC-7`-style containers | one hidden `align` layer, role-named group per family |
| `A-toplines` (plural) | the group id now equals the manifest name, deleting `{c.get("id")[:-1]: c}` (line 730) |
| the `-def` lookup fallback | one grammar, one spelling (lines 337–350, 345) |

## 6. Why this stays simple

- **Nothing unique is hand-typed twice.** Every copy/paste duplicates a *class*,
  which is allowed — so Inkscape cannot mint `-8`, `-81`, `-82` again.
- **No name carries geometry.** The B-group rotation, the plural `s`, and the `-def`
  suffix were all syntax smuggled into identity.
- **A lookup cannot be satisfied by the wrong thing.** `_def_group()` matches *any*
  element by id, so today `A-topline-outline` (a `<path>`) satisfies a lookup for a
  guide group and fails later inside `_frame()`. With leaves unnamed, that near-miss
  does not exist.
- **Adding an object costs no new names.** A mark is a classed `<circle>` inside an
  existing group.

## 7. Consumer agreement

Four script touches, each output-neutral:

| # | location | change |
|---|---|---|
| 1 | `read_feather()` line 368 | `rotate90` from `data-rot90`, not the name |
| 2 | `main()` line 730 | index guides by id directly; delete `[:-1]` |
| 3 | `_def_group()` 337–350 | drop the `{name}-def` fallback |
| 4 | `_path_d()` 353–356 | first **direct-child** `<path>`, so a nested mark can't shadow the outline |

Unchanged: `PLACEMENT_GROUP` (63), `_frame()` (320–334), `topline_children()`
(378–385, direct-child `<g>` carrying `data-wh`), `_group_content()` (533–544),
`read_topline()` (547–556), `read_placement()` (559–590), the manifest (255–282).

Two names are kept deliberately:

- **`outline-toplines`** — renaming it changes the placement page's `<title>` and so
  the page hashes. The misnomer is cheaper than the churn.
- **`A-topline` (singular)** — matches the manifest exactly. Group ids never reach the
  output, so this rename is free.

## 8. Inventory

Measured on the copy at `sha256 AE9217B4…`, 2026-09-28 13:24 (the file is being
edited live; re-measure before acting).

| | copy | tracked `feathers-aggregate.svg` | end state |
|---|---|---|---|
| id attributes | **162** | 94 | **45** contract names |
| `<marker>` defs (+ children) | 21 (+21) | 0 | 0 |
| family containers | 8 | 8 | 8 |
| item groups | 28 | 28 | 28 |
| guide groups | 8 | 8 | 8 |
| placement container | 1 | 1 | 1 |
| leaf ids | 65 | 44 | 0 |
| colour rules keyed on an id | 8 | 8 | 0 |

Contract names in the end state: 8 families + 28 items + 8 guides + 1 placement.

Feather geometry is already sound: all 28 item groups carry `data-wh`/`data-vb`, and
the pipeline reads all 28 out of the copy with `mirror_check` and `verify_body`
passing. What the copy has lost is the guide contract — its placement group is not
called `outline-toplines`, and its eight guides are bare paths and circles with no
`data-wh`, so `topline_children()` finds nothing and `placement_group()` asserts.
