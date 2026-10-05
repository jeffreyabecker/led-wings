# Plan: label the geometry core

**Status:** proposed, not executed.
**Scope:** add `inkscape:label` attributes to the elements of
`templates/aggregate.svg` so the core is navigable in Inkscape's Objects and XML
panels. **No ids are renamed** — every existing `id` stays byte-identical, so the
sheets masters' `../aggregate.svg#<id>` hrefs keep resolving and nothing needs
rewriting.

Verified against the working tree after the reorg landed (`templates/aggregate.svg`,
769 lines, 129 elements, 134 ids, **0 duplicate ids**, **0 elements without an id**).
The reorg is mid-flight in the worktree: the two sheets documents and the core are
currently not well-formed XML, which is why the mechanics below are stated as
"by hand in Inkscape" rather than as a script step.

## 1. Why labels at all

Inkscape's Objects panel and the XML editor's element list show `inkscape:label`
when an element has one, and the raw `id` otherwise. The core's ids are either terse
by design (`P1-outline`) or Inkscape-generated noise (`path5-8`, `path13-2`,
`path55`-style dividers), so a maintainer opening the file today reads a list of
`path1 … path66` with no way to tell a divider from a wing profile. A label is the
only fix that does not rename anything, and renaming is exactly what we are avoiding
so the sheets masters keep working.

Labels are **maintainer metadata, not product data**: `inkscape:` is a
non-standard namespace, so the flattener strips every label on the way out. A
shipped CAM file must not carry them.

## 2. What gets a label

Counted from the current file, by class:

| count | element | role |
|---|---|---|
| 28 | `<path class="outline">` in a `<g class="feather">` | the catalog parts |
| 28 | `<path class="divider">` | the dividers between the feathers of one family |
| 8 | `<g class="align">` + 8 `<path class="outline">` inside them | the diagnostic overlays |
| 8 | `<path class="guide">` | the `*-topline` guides in `assembly-template` |
| 1 | `<path class="outline" id="path5-8">` in `<g id="full-outline">` | whole-wing profile |
| 1 | `<path class="outline" id="upper-outline">` in `<g id="assembly-template">` | upper cover of the assembly |
| 8 | `<g class="family …">` | the family groups |
| 6 | calibration `<line>`/`<text>` | the scale reference |
| 3 | misc `<g>` wrappers (`full-outline`, `align`, `assembly-template`, `calibration`) | containers |

That is ~91 elements. The eight `<g class="family …">` groups are worth doing
because the Objects panel nests by group, so the family is the first thing a
maintainer sees and the label is what names it.

## 3. Label text

One rule: **the label names the element in the maintainer's vocabulary, and repeats
the id only when the id is the identity a person would search for.** No id is ever
encoded into a label that does not already contain it.

| element | label | why |
|---|---|---|
| `<g class="feather" id="P1">` | `P1 right feather` | the id is the part identity |
| `<path class="outline" id="P1-outline">` | `P1 outline` | confirms which path in the group is the cut profile |
| `<g class="family p">` | `P family` | family letter + kind |
| `<path class="divider" id="path1">` | `P divider` | the generated id says nothing; the role does |
| `<g class="align" id="P-align">` | `P align overlay` | distinguishes the overlay from the family |
| `<path class="outline" id="path8-1">` | `P align outline` | the overlay's outer boundary |
| `<path class="guide" id="P-topline">` | `P topline guide` | assembly alignment line |
| `<path id="path5-8">` | `wing outline` | whole-wing profile; **needs your confirmation** |
| `<path id="upper-outline">` | `upper cover outline` | **needs your confirmation** |
| `<line id="calibration-centerline">` | `calibration centreline` | — |
| `<line id="calibratin-zero-line">` | `calibration zero line` | id keeps its typo; the label does not |
| `<line id="metric-50mm-line">` | `calibration 50 mm` | — |
| `<line id="us-2in-line">` | `calibration 2 in` | — |
| `<text id="metric-50mm-label">` | `50 mm text` | — |
| `<text id="us-2in-label">` | `2 in text` | — |

Two open questions in that table, both because I am inferring from id, path length
and parent transform rather than from knowing what the path draws:

- `path5-8`, the single path inside `<g id="full-outline">`, whose parent carries
  `translate(-1317.2834,-272.68523)`, and whose `d` is the longest in the file
  (~2300 chars). I read it as an exported whole-wing profile.
- `upper-outline`, the single `<path class="outline">` in `assembly-template`,
  sitting above eight `*-topline` guides. It is referenced nowhere else in the tree,
  so what it depicts is not recoverable from the file.

## 4. Label uniqueness

The flattener's manifest keys rows on a name, so labels must be unique even though
Inkscape does not enforce that. Two families of near-collision, both already avoided
by the table above:

- **The overlay vs. its family.** `<g id="P-align">` is `P align overlay`, and the
  family group `<g class="family p">` is `P family` — the letter alone would collide.
- **The overlay's outline vs. the part outline.** `P align outline` vs `P outline`.

Verification must therefore include a duplicate-label check (§6), not just a
coverage check.

## 5. Mechanics

Do it **by hand in Inkscape**, not by script:

1. Open `templates/aggregate.svg`. Saving from Inkscape repairs the current
   well-formedness breakage as a side effect, which a scripted edit cannot do (a
   script would have to parse the broken file first).
2. Select an element, open Object Properties (`Ctrl+Shift+O`), type the label. The
   Objects panel (`Ctrl+Shift+L`) shows the same labels and is the fastest way to
   walk a family and its dividers in order.
3. For the divider paths and the two unknown outlines, the canvas is the only
   reliable way to find them: their generated ids are unique, so `Edit → Find`
   (or the XML editor's element list) can select by id when the drawing position is
   ambiguous.
4. Save with Inkscape's default SVG 1.1 output.

No script, no `id` attribute is touched, and no other file changes. Git will show a
single-file diff of added label attributes (plus whatever Inkscape normalises on
save, which is why this should land as its own commit).

## 6. Verification

- Every element in §2 carries a non-empty `inkscape:label`: count labels against the
  element census (28 parts, 28 dividers, 8 align groups, 8 align outlines, 8 guides,
  8 families, 6 calibration, the two unknowns, the wrappers).
- **No duplicate labels** across the whole file.
- **No `id` changed**: `git diff` shows only added `inkscape:label` attributes on
  those lines, and the id set before and after is identical.
- `templates/feathers/sheets.svg` and `templates/alignment/sheets.svg` still resolve
  their `../aggregate.svg#<id>` hrefs — they were never edited, so this is a check
  that the "no renames" promise held, not a repair.
- Open the core in Inkscape's Objects panel: families nest, and every leaf reads as
  a name rather than `path42`.

## 7. Out of scope

- Renaming any id (deliberately deferred; it would break the two sheets masters).
- Labels in the shipped CAM output — the flattener removes the `inkscape:` namespace
  entirely.
- The current well-formedness breakage in the three SVGs, beyond Inkscape repairing
  the core on save. If the sheets masters are still malformed when this lands, that
  is a separate fix.
- A convention entry in `templates/AGENTS.md` recording "new core geometry gets a
  label, and label text follows §3" — worth adding, but it belongs with whatever
  edits that file next.
