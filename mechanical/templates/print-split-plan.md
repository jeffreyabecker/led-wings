# Split Plan — logical-page builder + tiling PDF assembler

Split the single `make_feather_sheets.py` into two scripts so that **layout**
(what content sits on each logical page, at what true-scale size) is separate from
**pagination** (how logical pages map onto physical Letter sheets, including
tiling).

Rationale: tiling was the historically bug-prone part. Isolating it in a small,
generic, testable script shrinks the blast radius, and the first script becomes
purely about the domain (feathers / templates / mirroring / packing) with no
knowledge of paper size.

---

## 1. The contract between the two scripts

- **Script 1** (`make_logical_pages.py`) writes one **logical page** per SVG file.
  Each page is self-contained, true scale (mm), with an explicit `width`/`height`
  and a `<title>` label. Pages are sized to their *content*: a lone pair is a page
  at its natural pair size (which may be bigger than a physical sheet — Script 2
  tiles it); a group of items shares one page sized to the group's bounding box.

- **Script 2** (`pages_to_pdf.py`) reads the logical pages **in filename order** and
  emits one PDF. For each page:
  - fits the printable area → one Letter sheet, page placed at the margin;
  - bigger than the printable area → **tiled** across `cols × rows` sheets with
    overlap and crop marks.

The two scripts only meet at the filesystem: a directory of `page-NNN.svg` files.

---

## 2. Script 1 — `make_logical_pages.py`

### Responsibility
Read feathers + guide templates, build mirrored pairs, verify them, and lay them
out into logical pages driven by a **manual grouping config**. **No knowledge of
Script 2's paper, margins, or tiling.**

### Config (the part you edit at the top)
```
MAX_WIDTH = 260.0   # mm — a grouped page wraps into a new row beyond this width
                    #       (260 leaves ~9 mm of wiggle room under Script 2's
                    #       269.4 mm printable width, so groups never tile)
PAD       = 8.0     # mm — space between items on a shared page (raise it if the
                    #       current packing feels too tight)

# Ordered pages. Each entry is ONE logical page: a list of item names.
#   ["P1"]           -> P1 alone on its page (its natural pair size)
#   ["S3","S4","A1"] -> those items grouped on one page, wrapped at MAX_WIDTH
# The cover is always page 1. Every item appears exactly once, below.
# Feathers and toplines are all just items here — group either however you like
# (e.g. split the topline line into several lines to spread them out).
PAGES = [
    ["P1"], ["P2"], ["P3"], ["P4"], ["P5"],
    ["S1"], ["S2"],
    ["S3", "S4", "A1", "A2", "A3"],
    ["PC1", "PC2", "SC1", "SC2", "SC3", "SC4"],
    ["MC1", "MC2", "MC3", "MC4", "LC1", "LC2", "LC3", "B1"],
    ["B2"], ["B3"],
    ["outline-toplines"],
    ["A-topline", "B-topline", "LC-topline", "MC-topline",
     "P-topline", "PC-topline", "S-topline", "SC-topline"],
]
```
(`GAP = 10` — the mirror gap inside a pair — stays a constant. `MAX_WIDTH` and
`PAD` are Script 1's own layout choices, independent of Script 2's paper.)

### What it moves over (from the current script)
`read_feathers`, `read_topline`, `read_placement`, `_group_content`, `measure_ink`,
`verify_body`, `placed_size`, `right_transform`, `feather_item`, `build_pair`,
`mirror_check`, `apply_transform`, `_bbox`, `fmt`, `parse_mm`, `label_size`, the
`Feather`/`Item` dataclasses, and the shared `CSS` block. The old automatic
`pack_small` is **dropped** — grouping is now the manual `PAGES` config.

### What it does
1. Read feathers → verify mirror (`mirror_check`) → `feather_item`.
2. Read templates → verify body (`verify_body`) → `Item`.
3. Build the cover (calibration bars) as page 1.
4. For each `PAGES` entry, `build_pair` each item, then lay the group out:
   - one item → page = that pair's natural size (`2W+GAP × H`);
   - several items → place pairs left-to-right with `PAD` gaps, wrapping to a
     new row when the next pair would exceed `MAX_WIDTH`; the page is sized to
     its content (width = widest row, height = sum of row heights + `PAD`).
5. Emit one SVG per page, sized to its content, with a `<title>` label.

### Page SVG format (exactly)
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="Wmm" height="Hmm" viewBox="0 0 W H">
  <title>LABEL</title>            <!-- e.g. "P1", "cover", "S3/S4/A1" -->
  <style>…shared CSS…</style>
  <rect width="W" height="H" fill="#ffffff"/>
  …content at absolute mm positions…
</svg>
```
`viewBox` origin is always `0 0`. The `<title>` is the human label Script 2 uses in
tile notes.

### Outputs
```
mechanical/templates/print/logical-pages/page-001.svg   # cover
mechanical/templates/print/logical-pages/page-002.svg   # P1 (oversized pair)
… (oversized feathers, packed feathers, oversized template, packed toplines)
```

---

## 3. Script 2 — `pages_to_pdf.py`

### Responsibility
Read logical pages in order, render each to a Letter sheet (tiling oversized
pages), concatenate, verify. **Knows nothing about feathers or templates.**

### Constants it owns
```
PAPER_W, PAPER_H = 279.4, 215.9   # US Letter, landscape (mm)
MARGIN           = 5.0            # unprintable border
OVERLAP          = 12.0           # printed twice on adjacent tiles
pw, ph           = PAPER_W-2*MARGIN, PAPER_H-2*MARGIN     # printable area
stride_x, stride_y = pw-OVERLAP, ph-OVERLAP
```
Script 2 makes **no assumption** about how big Script 1's pages are. Any page
bigger than the printable area is tiled — including a packed page, should
Script 1's layout ever produce one. The two scripts are independent; they only
happen to line up for the current run.

### What it moves over
`corner_ticks`, `render_sheets`, `contact_sheet`, `verify_scale`, `fmt`,
`parse_mm`, and the small CSS for crop marks / tile notes (`.crop`, `.note`).

### Tiling algorithm (moved from `tiled_sheets`, now page-based)
For an input page of size `W × H`:
```
cols = 1 if W <= pw else ceil((W - pw) / stride_x) + 1
rows = 1 if H <= ph else ceil((H - ph) / stride_y) + 1
```
Tile `(c, r)` shows page region `[c·stride_x, c·stride_x+pw] × [r·stride_y, r·stride_y+ph]`,
mapped to the sheet's printable area via:
```
sheet_x = page_x - c·stride_x + MARGIN
sheet_y = page_y - r·stride_y + MARGIN
```
Each tile is one Letter sheet: the page's inner content wrapped in
`<g transform="translate(MARGIN - c·stride_x, MARGIN - r·stride_y)">`, clipped to
the printable rect, with corner crop marks and a margin note
`"{title} · tile i/j · cols×rows"`.

Pages that fit are placed whole at `(MARGIN, MARGIN)` — no clip, no crop marks.

### Process (per page)
1. Parse `width`/`height` and the `<title>` from the SVG root.
2. Extract the root's children (the content — this is why Script 1 emits clean,
   prefix-free SVGs).
3. If it fits → one sheet; else → `cols × rows` sheets.
4. Render each sheet SVG → PDF (cairosvg), merge all (pypdf).

### Verification (in Script 2)
- **Tiling structural check**: re-derive `cols`/`rows` for every oversized page and
  assert the emitted tile transforms match (covers the "silent drift" failure mode).
- **Scale check** (`verify_scale`): rasterise the first page (the cover) at 300 dpi
  and measure the 100 mm and 4 in bars back (unchanged from today).

### Outputs
```
mechanical/templates/print/feathers-letter-landscape.pdf
mechanical/templates/print/sheets/            # per-sheet intermediates (gitignored)
mechanical/templates/print/contact-sheet.png
```

---

## 4. What moves where (mapping from the current script)

| current | goes to |
|---|---|
| `read_feathers`, `read_topline`, `read_placement`, `_group_content`, `measure_ink`, `verify_body` | Script 1 |
| `placed_size`, `right_transform`, `feather_item`, `build_pair`, `mirror_check`, `apply_transform`, `_bbox` | Script 1 |
| `Item`, `Feather`, `label_size`, `fmt`, `parse_mm` | both (duplicated, tiny) |
| `CSS` (outline/guide/label/…) | Script 1 (embedded in each page) |
| `pack_small` | dropped — replaced by the manual `PAGES` config in Script 1 |
| `cover_sheet` | Script 1 (emits the cover logical page) |
| `tiled_sheets` | Script 2, reworked to tile a whole page |
| `corner_ticks`, `sheet_svg` | Script 2 (physical-sheet wrapper) |
| `render_sheets`, `contact_sheet`, `verify_scale` | Script 2 |

---

## 5. Decisions — confirmed and open

### Confirmed
- **Independence.** Script 1 owns `MAX_WIDTH`/`PAD` (its own layout choices);
  Script 2 tiles any page bigger than a sheet, with no assumptions. No shared
  paper constants.
- **Manual grouping** in Script 1 via the `PAGES` config — no automatic
  shelf-packer.
- **`MAX_WIDTH` = 260 mm** (initial value), `PAD` configurable.
- **Grouped pages are sized to their content** (widest row × total row height),
  not a fixed page size.
- **Label via `<title>`**, used by Script 2 for tile notes.
- **Cover lives in Script 1** (the first logical page); its size stays ~269 ×
  206 mm, the same physical size as today.
- **Script 2 tiles by content size, no exceptions** — any page bigger than the
  printable area is tiled.

### Open
None — all decisions above are confirmed.

---

## 6. Definition of done

- [ ] `make_logical_pages.py` writes `print/logical-pages/page-NNN.svg` (cover first).
- [ ] `pages_to_pdf.py` turns those pages, in order, into the same output the
      single script produces today (cover + tiled big pairs + grouped small items),
      with no regression in sheet count or content.
- [ ] Oversized pages (P1–P5, S1, S2, B2, B3, outline-toplines) tile with overlap +
      crop marks; grouped pages that fit go on one sheet each.
- [ ] The `PAGES` config lets me regroup items and adjust `MAX_WIDTH`/`PAD` without
      touching any other code.
- [ ] Both scripts run standalone (`python make_logical_pages.py` then
      `python pages_to_pdf.py`).
- [ ] Scale check still passes (100 mm → ~100 mm, 4 in → ~101.6 mm).
- [ ] The old single script is removed once the split is verified equivalent.
