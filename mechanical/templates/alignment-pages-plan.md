# Plan — swap the alignment-guides strip for pages of the overlay's alignment elements

**Status: proposal.** Nothing is changed yet. The aggregate and both print scripts
are as committed in `d0cf1eb`.

**Scope:** `make_logical_pages.py`. `pages_to_pdf.py` is untouched — it only ever
sees `page-NNN.svg`. `feathers-aggregate.svg` is a read-only input.

**The ask:** (1) drop the generated alignment-guides page; (2) add pages for the new
alignment elements in `feathers-aggregate.svg`.

**Verdict:** the drop is two pages and about ninety lines; the add is a second
`read_placement`-shaped reader plus eight pages. Two parts are *not* mechanical and
need a decision (§3b, §3d): the numbers, because the pipeline reads neither CSS nor
markers, and `measure_ink`'s harness, which is both too small and too slow for these
items.

## 1. What the source holds now (measured)

The corrected copy has become the source: `feathers-aggregate - Copy.svg` is gone and
`feathers-aggregate.svg` carries the overlay.

| | |
|---|---|
| root children | namedview, defs, style, 8 family groups, `outline-toplines`, `align` |
| markers | 5 — `num1` … `num5` |
| origin arrows | 28, each carrying `class="arrow numN"` |
| guide groups | 8 `X-topline` (singular), inside `outline-toplines` |
| overlay | `<g id="align">` holding 8 `<g id="X-align" class="align">` |

Each `X-align` group is one silhouette `<path class="outline">` plus its 1–5 numbered
origin `<path class="arrow numN">`.

Sizes from `inkscape --query-all` (px, converted at 3.7795 px/mm). Every group sits
**left of the page** — the whole layer spans x ≈ −920 … −427 mm, y ≈ 33 … 928 mm:

| group | bbox (mm) | | group | bbox (mm) |
|---|---|---|---|---|
| P-align | 182.0 × 424.4 | | MC-align | 106.9 × 128.1 |
| S-align | 185.0 × 313.3 | | LC-align | 99.1 × 78.4 |
| B-align | 112.5 × 301.5 | | PC-align | 74.7 × 131.5 |
| SC-align | 144.0 × 151.9 | | A-align | 58.7 × 139.3 |

For comparison, the placement group `outline-toplines` is 248.1 × 194.9 mm.

## 2. Part 1 — drop the guides strip

| line(s) | what | why it can go |
|---|---|---|
| 197–232 | `AlignmentGuides` class | the only producer of the strip |
| 280–281 | its `SECTIONS` entry | — |
| 53 | `TOP_LINE_PAD` | read only by `AlignmentGuides.pad` |
| 424–430 | `preflip()` | only the mirrored strip used it |
| 547–556 | `read_topline()` | only the strip read guides as items |
| 378–385 | `topline_children()` | only used to build the `guides` dict |
| 736–742 | the `guides` dict in `main()` | goes with the strip |
| 731 | the `-toplines` / `-topline` tolerance | dead once that dict goes — this is the one-line change from `d0cf1eb`, and it has no other caller |

**Kept:** `PLACEMENT_GROUP` (63) and `read_placement()` (559). The placement page
still needs the guide *geometry*: `read_placement()` iterates the placement group's
`<g>` children directly and never calls `topline_children()` — worth a grep before
deleting, since that is the one dependency that would bite.

`side_note()` (663) outlives the strip if the new pages use it for their label;
otherwise it goes too.

Two pages disappear: the `…-topline/…` strip pair (currently pages 24 and 25).

## 3. Part 2 — add the overlay pages

### 3a. Reader — `read_align(name, el)`, shaped like `read_placement`

```python
def read_align(name, el):
    """One alignment overlay as an Item: silhouette + origins, at true scale."""
    content = (f'<g transform="{el.get("transform") or ""}">'
               f'{_group_content(el)}</g>{origin_labels(el)}')
    # measure ink, then W, H = ink box + 2 mm and re-origin, exactly as read_placement does
    return Item(name, W, H, body, inside_label=False, mirror=False)
```

Same contract as `read_placement()`: wrap the group in its own transform, serially
copy its `path`/`circle` children, measure, re-origin into `[0,W]×[0,H]`.

### 3b. The numbers — the one part that is not mechanical

`_group_content()` (533–544) copies `path` and `circle` and nothing else: it drops
`class`, `style`, and every marker reference. Read that way, an overlay prints as
silhouettes and bare hairlines — **no digits**. Three options:

| | approach | cost |
|---|---|---|
| (a) | carry the aggregate's CSS and marker defs onto the page | every page gains a `<style>` in the source's units (the cairosvg 96-dpi trap at lines 70–73) and five marker defs; the script stops owning its presentation |
| (b) | **emit each digit as text** | needs the origin's anchor point: read `numN` off the class, take the path's first vertex (the marker anchor — `refX/refY = 0` against a centred viewBox puts the digit dead centre on it), map it through the child's and the group's transforms, emit `<text class="label">N</text>` |
| (c) | print the overlays without numbers | nothing to build; the origins stay bare hairlines |

**Recommended: (b).** It keeps the script's own CSS and its existing idiom — it
already emits text for every page label — and needs no marker or CSS support from
cairosvg.

(b) needs one helper upgrade: the existing `apply_transform()` (476–492) handles
translate/rotate/scale only **and ignores `rotate`'s centre arguments**, which these
groups use (`matrix(…)`, `rotate(angle, cx, cy)`). Swap it for a matrix-based
affine helper; `mirror_check()` only ever passes translate and centred rotate, so the
swap is behaviour-preserving there.

The digit itself is read verbatim from the class — the source decides what each
origin is called.

### 3c. Section and manifest

One page per element, so the section is thin:

```python
class AlignmentPage(Section):
    """One overlay element, one true-scale page. Emits 1 page."""

    def __init__(self, item):
        self.items = (item,)

    def pages(self, ctx):
        item = ctx.raw[self.items[0]]
        return [Page(item.name,
                     item.body + side_note(item.name, item.W),
                     item.W, item.H)]
```

Manifest: replace the `AlignmentGuides(…)` line where it sits, keeping cover-first
and the placement pages where they are:

```python
    MirroredWholePage("outline-toplines"),
    AlignmentPage("B-align"), AlignmentPage("P-align"), AlignmentPage("PC-align"),
    AlignmentPage("A-align"), AlignmentPage("SC-align"), AlignmentPage("MC-align"),
    AlignmentPage("LC-align"), AlignmentPage("S-align"),
```

Print order is the manifest order (§7.3).

No mirroring: these are single placement-space drawings. `placement_halves()` shows
the pattern if a mirrored copy is ever wanted.

### 3d. `measure_ink()` must change — two independent reasons

1. **The harness is too small.** It is a fixed 300 × 300 mm (`read_placement`,
   580–582). P-align is 182 × 424 mm, S-align 185 × 313, B-align 113 × 302 — all
   clipped in y. A clipped render does not fail; it returns a *smaller* ink box, so
   the page comes out short and the body keeps geometry outside `[0,W]×[0,H]`. The
   placement group fits at 248 × 195 mm purely by luck.
2. **It is too slow.** 150 dpi over 300 mm is 1772² = 3.1 M px, and lines 526–527
   walk every pixel twice in Python. Fitting the harness to P-align at the same dpi
   is 3543 × 8858 = 31 M px; eight of those items turn a half-second step into
   minutes.

Fix: fit the harness to the item (analytic bbox from the path data, plus margin) and
replace the pixel walk with a threshold plus `Image.getbbox()`, which is C-speed. Then
150 dpi stays affordable.

**Watch out:** the placement page's W and H come from this same function and are
pixel-quantized (0.169 mm per pixel at 150 dpi). Changing the harness or dpi can move
those two pages. Either leave the placement group on the existing 300 mm/150 dpi path
and use the new path only for overlays, or accept the placement pages changing and
record the delta. (§5, step 4.)

## 4. What must not move

`read_feather()`, `placed_size()`, `right_transform()`, `feather_item()`,
`guide_label()`, `build_pair()`, `mirror_check()`, `shelf()`, `placement_halves()`,
`cover_page()`, `page_svg()`, `rotated_bbox()`, `placed_transform()`, the twenty item
sections, `PLACEMENT_GROUP`, and `read_placement()`'s output.

## 5. Acceptance test

Baseline first (step 0): hash all 25 `logical-pages/page-*.svg` and record
`pages_to_pdf.py`'s sheet count.

1. the 23 retained pages are **byte-identical** to the baseline;
2. the two strip pages are gone — no page whose `<title>` contains `-topline`;
3. **eight new pages**, titled `B-align` … `S-align`, each sized as §1 (allow one
   pixel of quantization, 0.17 mm);
4. the placement pages (022, 023) are byte-identical **if** the harness decision
   keeps their code path; otherwise the new hashes are recorded and the size delta
   explained;
5. page total 25 → 31; `pages_to_pdf.py` still passes its tiling and scale checks,
   with the sheet count delta attributable to tiling the new pages;
6. no dangling code: grep shows zero references to `read_topline`,
   `topline_children`, `preflip`, `TOP_LINE_PAD`, `AlignmentGuides`.

## 6. Risks

| risk | containment |
|---|---|
| harness clips an overlay silently | §3d; a clipped item produces a page visibly smaller than §1's table |
| the placement page shifts | keep its code path unchanged, or record and explain the delta (§5.4) |
| a digit lands off its origin | the anchor is the path's first vertex; spot-check one family by rendering the page |
| overlay coordinates are negative and far off-page | harmless — the reader re-origins by ink box — but any code that assumes page-local coordinates would break |
| deleting `topline_children()` breaks the placement page | grep first; `read_placement()` does not call it |
| fewer pages than the stale-file cleanup expects | the cleanup only unlinks pages it is about to rewrite, so a smaller set is safe |

## 7. Open questions

1. **One page per family (8), or one page holding all eight overlays (1)?** The plan
   assumes per-family, which keeps each page true scale; a single page would be
   661 × 896 mm and tile across ~6 sheets.
2. **Print the numbers?** Recommended yes, as text (§3b), sized like the existing
   page labels unless a specific size is wanted.
3. **Print order** — the family order above, or the order the old strip used
   (A, PC, SC, LC, MC, B, P, S)?
4. **A page label on each overlay page**, via `side_note()`, or a bare drawing?
5. **Unnumbered arrows.** The source numbers all 28, so the rule can be "print the
   digit if the class has one, otherwise nothing". Keep the diamond as a fallback
   glyph, or drop the case?
6. **Mirrored copies.** One page per overlay, or an additional mirrored page as the
   feathers and the placement drawing get?

## Appendix — measurements taken for this plan

| probe | result |
|---|---|
| `feathers-aggregate.svg` structure | 150 ids, 8 families + `outline-toplines` + `align`, 5 markers, 28 numbered arrows, 8 `X-topline` guides |
| `inkscape --query-all` on each `X-align` | the table in §1; page box for scale is 937.9 px = 248 mm |
| overlay layer bbox | 661.2 × 895.6 mm at x = −919.6, y = 32.7 — entirely off-page |
| `measure_ink` harness | fixed 300 × 300 mm (line 580–582), 150 dpi, two full pixel walks (526–527) |
| baseline to take in step 0 | 25 page hashes, `pages_to_pdf.py` sheet count |
