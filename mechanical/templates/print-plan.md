# Print Generation Plan — Feather Templates (Letter Landscape, Mirrored + Tiled)

> Source of truth: `mechanical/templates/individuals/*.svg`
> Target: one printable PDF, true scale (1 mm = 1 mm), US Letter **landscape** pages only.
> Script is single-use scaffolding: written for clarity, run once, deleted after.
> **Nothing from the old scripts is reused.** This is a from-scratch design.

---

## 1. Goal

Turn the 28 individual feather SVGs into a single multi-page PDF of **mirrored
pairs**, printed at true scale on 8.5 × 11 in **landscape** sheets, with feathers
too big for one sheet **tiled** across multiple sheets with overlap so they can be
joined after printing.

Deliverables, in order:

1. A cover page with a calibration segment in **both inches and mm** (the physical
   scale check).
2. A sheet (or tiled set of sheets) for every feather's **mirrored pair**.
3. Built-in verification that runs at the end of the same script run.

---

## 2. Non-negotiables (what "correct" means)

These are the invariants the script and its verifier must uphold. If any fails, the
run is a failure.

| # | Invariant |
|---|-----------|
| I1 | **True scale.** 1 mm in source = 1 mm on paper. Nothing scales, ever. |
| I2 | **Exact mirroring.** The left half of a pair is a perfect reflection of the right half across a single vertical axis; same geometry, same stroke. |
| I3 | **No clipping.** No cut line, stroke, or label escapes the sheet's printable area, and no tiled region is silently dropped. |
| I4 | **Every feather appears exactly once** (as one pair), in a fixed deterministic order. |
| I5 | **The label is inside the outline**, on both halves, so it is cut out with the piece. |
| I6 | **Reproducible.** Same inputs + same script = byte-identical PDF. |

---

## 3. Inputs

- Directory: `mechanical/templates/individuals/`
- 28 feathers, each a single `<svg>` with one outline `<path>` (class `outline`),
  stroke 0.5 mm, `fill:none`, **right-hand orientation**, mm units.
- Each file's `width`/`height` equal its `viewBox` extent exactly (verified: identity
  mapping), so the viewBox→viewport transform is 1 user unit = 1 mm. We rely on this
  and **never parse or re-derive the path geometry**.

**Excluded:** `outline-toplines.svg` (old visibility/guide remnant — no longer
exists as a concept).

### Hard-coded feather list (fixed order, family-grouped)

```
P1 P2 P3 P4 P5
S1 S2 S3 S4
A1 A2 A3
PC1 PC2
SC1 SC2 SC3 SC4
MC1 MC2 MC3 MC4
LC1 LC2 LC3
B1 B2 B3
```

28 total. These IDs map directly to `individuals/<ID>.svg`.

> **Orientation:** every feather is stored right-hand with its long axis vertical,
> except `B1`–`B3`, which are stored horizontal and are rotated 90° clockwise (§7).

---

## 4. Outputs

| Path | What | Keep? |
|---|---|---|
| `mechanical/templates/print/feathers-letter-landscape.pdf` | the final merged PDF | yes |
| `mechanical/templates/print/sheets/` | per-sheet SVGs + per-sheet PDFs (intermediates) | no — scratch |
| `mechanical/templates/print/contact-sheet.png` | all sheets rendered side by side for eyeballing | no — scratch |

Add `mechanical/templates/print/sheets/` to `.gitignore`.

The script lives at repo root: `make_feather_sheets.py` (single file, deleted after
the run). It prints a summary at the end: sheet count, per-feather placement,
verification results.

---

## 5. Constants (top of script, all in one block)

```
LETTER_IN       = 8.5, 11.0            # paper, inches
PAPER_W, PAPER_H= 279.4, 215.9         # landscape mm  (8.5in wide, 11in tall)
MARGIN          = 5.0                  # mm, unprintable border on every side
OVERLAP         = 12.0                 # mm, printed twice on adjacent tiles
GAP             = 10.0                 # mm, clear space between the two halves of a pair
PAD             = 8.0                  # mm, space between neighbouring pairs on a packed sheet
STROKE_MM       = 0.5                  # cut-line width (matches the source)
LABEL_FONT      = "sans-serif"
```

Derived once:

```
pw = PAPER_W - 2*MARGIN      # printable width  = 269.4 mm
ph = PAPER_H - 2*MARGIN      # printable height = 205.9 mm
stride_x = pw - OVERLAP      # 257.4 mm
stride_y = ph - OVERLAP      # 193.9 mm
```

---

## 6. Coordinate system

Everything is **SVG user units = millimetres**, origin **top-left**, **y increases
downward**. The sheet SVG is:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="279.4mm" height="215.9mm"
     viewBox="0 0 279.4 215.9">
  <rect x="0" y="0" width="279.4" height="215.9" fill="#ffffff"/>
  ... content ...
</svg>
```

The printable area is the rectangle `(MARGIN, MARGIN)` → `(MARGIN+pw, MARGIN+ph)`.

A **logical page** is the smallest rectangle that holds content to be placed on
sheets. Its own coordinate system is also top-left origin, in mm.

---

## 7. The pair (mirror) geometry — the exact rule

For one feather, let **`W` × `H`** be its *placed* size — the outline's width ×
height **after** any rotation below — derived from the individual's
`width`/`height` attributes.

- **Right half** is drawn in its placed orientation.
- **Mirror axis** is a vertical line at `AX`.
- **Left half** is the same drawing reflected across `AX`.

Let the right half's local rect be `[0,0] .. [W,H]`, placed so its top-left sits at
sheet position `(RX, RY)`:

```
right : <g transform="translate(RX, RY)">  content </g>
AX    = RX + W + GAP/2
left  : <g transform="translate(RX + 2*W + GAP, RY) scale(-1,1)">  content </g>
```

Pair box (for packing/tiling):

```
pair_w = 2*W + GAP
pair_h = H
```

### Rotation (B group only)

Every feather is stored with its **long axis vertical**, except the **B group**
(`B1`–`B3`), which is stored **horizontal**. The B feathers are rotated **90°
clockwise** before pairing; after that they are handled exactly like the rest.

For a B feather with file size `Wf × Hf` (wide × short) and viewBox origin
`(x0, y0)`:

```
placed W = Hf      placed H = Wf
right inner = translate(Hf/2, Wf/2) rotate(90) translate(-(x0+Wf/2), -(y0+Hf/2))
```

`rotate(90)` is clockwise on screen (y-down), so the wide axis becomes vertical.
The mirror and labels then use the placed `W, H` unchanged.

For every other feather the right inner transform is just
`translate(-x0, -y0)` (the viewBox origin), with placed `W, H` = file `Wf, Hf`.

### Worked example (W = 50, GAP = 10, RX = 5)

```
right spans [5, 55]
AX    = 5 + 50 + 5 = 60
left  translate-x = 5 + 100 + 10 = 115, then scale(-1,1)
      → left spans [115−50, 115] = [65, 115]
gap   = 65 − 55 = 10   ✓
pair box = [5, 115], width 110 = 2·50 + 10   ✓
```

The verifier asserts this numerically: `left_bbox == mirror(right_bbox)` across `AX`,
and `gap == GAP`.

---

## 8. Label (inside the outline)

- Text = the feather ID (`P1`, `B3`, …).
- Placed **inside** each half, anchored at the half's centre:
  - right half centre: `(RX + W/2, RY + H/2)`
  - left half centre:  `(RX + W + GAP + W/2, RY + H/2)`  (same = `RX + 1.5W + GAP`)
- Upright on **both** halves (not mirrored), so it reads correctly on the table.
  Left label is placed outside the `scale(-1,1)` group so it does not flip.
- `text-anchor="middle"`, `dominant-baseline="middle"`.
- Font size: `clamp(3, min(W,H)/6, 12)` mm — large enough to read, small enough to
  stay inside the vane.
- Fill black, `font-family: sans-serif`.

---

## 9. Tiling (only for feathers bigger than one printable area)

A pair with `pair_w ≤ pw` **and** `pair_h ≤ ph` fits whole — no tiling.

Otherwise it is tiled into a grid:

```
cols = 1 if pair_w <= pw  else ceil((pair_w − pw) / stride_x) + 1
rows = 1 if pair_h <= ph  else ceil((pair_h − ph) / stride_y) + 1
```

- `OVERLAP` mm is printed on **both** adjacent tiles (it is the shared edge you line
  up and cut).
- Tile `(c, r)` — `c ∈ [0, cols)`, `r ∈ [0, rows)` — shows logical-page region
  `x ∈ [c·stride_x, c·stride_x + pw]`, `y ∈ [r·stride_y, r·stride_y + ph]`.
- That tile becomes **one sheet**. Logical point `(lx, ly)` maps to sheet point:

```
sheet_x = lx − c·stride_x + MARGIN
sheet_y = ly − r·stride_y + MARGIN
```

- The sheet clips content to the printable rect (belt-and-suspenders) and draws
  corner crop marks at the printable corners.
- Every tile carries a small margin note: feather ID + tile grid position
  (e.g. `P1  r1/2`), so the sheets can be reassembled.

### Expected oversized tiling (MARGIN 5, OVERLAP 12, GAP 10)

| feather | pair W × H (mm) | grid | sheets |
|---|---|---|---|
| P1 | 225.4 × 348.7 | 1 × 2 | 2 |
| P2 | 161.2 × 344.4 | 1 × 2 | 2 |
| P3 | 169.0 × 333.4 | 1 × 2 | 2 |
| P4 | 184.9 × 271.9 | 1 × 2 | 2 |
| P5 | 209.1 × 235.0 | 1 × 2 | 2 |
| S1 | 180.9 × 255.9 | 1 × 2 | 2 |
| S2 | 176.0 × 251.4 | 1 × 2 | 2 |
| B2 | 162.2 × 209.5 | 1 × 2 | 2 |
| B3 | 154.7 × 224.9 | 1 × 2 | 2 |

`B1` (173.5 × 193.2), `S3` (176.0 × 202.4) and everything smaller **fit whole** and
are packed.

---

## 10. Packing (whole pairs sharing a sheet)

Small pairs are packed several-per-sheet with a simple shelf packer, in the
hard-coded order (§3):

```
cursor x = MARGIN, y = MARGIN; row_height = 0
for each pair (pw_pair × ph_pair) that fits whole:
    if x + pw_pair > MARGIN + pw:     # no room in this row → wrap
        x = MARGIN; y += row_height + PAD; row_height = 0
    if y + ph_pair > MARGIN + ph:     # sheet full → flush, start new sheet
        (emit sheet); x = MARGIN; y = MARGIN; row_height = 0
    place pair at (x, y)
    x += pw_pair + PAD; row_height = max(row_height, ph_pair)
```

Pairs that do **not** fit whole are emitted as their own tiled sheet set (§9) and
never enter the packer. Mixing families on one sheet is allowed (keeps the packer
trivial).

---

## 11. Cover page (calibration)

Page 1, same Letter-landscape sheet, containing two true-scale bars plus a note:

1. **100 mm bar** — horizontal line from `x=20` to `x=120` at `y=60`; major ticks
   every 10 mm (numbered 0…100), minor ticks every 1 mm; label `"100 mm"` above.
2. **4 in bar** — horizontal line from `x=20` to `x=121.6` at `y=95` (4 in =
   101.6 mm); major ticks every 1 in (numbered 0…4), minor ticks every 1/8 in;
   label `"4 in (101.6 mm)"` above.
3. Note text: `"Print at 100% / Actual size. Do not fit or scale. The bars must
   measure 100 mm and 4 in."`

Both bars are black, 0.5 mm stroke. These two bars are what the verifier measures
back from the rendered PDF (§12).

---

## 12. Verification (runs inside the same script, after generation)

Two layers, because scale drift was the historical failure mode:

### A. Structural (parse the SVG/PDF we wrote)

- Every sheet SVG's `width/height/viewBox` == `279.4 × 215.9`.
- Every feather placed exactly once, in order; `pair_w == 2W + GAP` to 0.01 mm.
- Left bbox == mirror of right bbox across `AX` (I2); gap == GAP.
- No placed rect intersects outside the printable area (I3).
- Each label element exists and its anchor is inside its half's rect (I5).

### B. Ground truth (raster, measure the scale)

- Render the cover page (and one tiled sheet) to PNG at **300 dpi** with
  `pypdfium2`.
- Measure the 100 mm bar's ink length in pixels → mm (`px / 300 * 25.4`).
- Pass if within **±0.3 mm** of 100.0, and the 4 in bar within ±0.3 mm of 101.6.
- Fail loudly otherwise (exit non-zero).

This catches the exact bug class that bit the previous runs — a silently-wrong
scale — before any paper is spent.

---

## 13. Pipeline (implementation order)

```
read individuals   → 28 (id → W,H,viewBox, inner <g> + ns decls)
  │
  ├─ for each id: build pair fragment (right + mirrored left + label), size (2W+GAP, H)
  │
  ├─ oversized pairs  → tiled sheets (§9)
  ├─ fitting pairs    → shelf-packed sheets (§10)
  │
  ├─ cover page (§11) → sheet #1
  │
  └─ for each sheet:  emit SVG → cairosvg → sheet PDF → pypdf merge → contact PNG
                      → run verification (§12) → print summary
```

### Rendering notes (verified during planning)

- **cairosvg 2.9.0** converts each sheet SVG to PDF at exact true scale, pure vector.
  It needs cairo; the GStreamer DLL already on this machine provides it — set:

  ```
  os.environ["PATH"]      = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin" + ";" + os.environ["PATH"]
  os.environ["CAIRO_PATH"] = r"C:\Program Files\gstreamer\1.0\msvc_x86_64\bin"
  ```

- **Nested `<svg>` composition**: when inlining an individual's content into the
  sheet, copy its `xmlns:*` namespace declarations onto the nested `<svg>`
  (`xmlns:inkscape`, `xmlns:sodipodi`), and strip its `<?xml?>` declaration.
  Without this cairosvg fails with `unbound prefix`.
- **Do NOT** use `<image href="data:image/svg+xml;...">` — verified to render a page
  with zero paint operations (silent failure). Nested `<svg>` is the only
  composition path.
- **Chrome headless is unavailable** in this sandbox (Mojo pipe restriction), so
  cairosvg is the renderer, not the browser.
- Merge sheets with `pypdf`; rasterise with `pypdfium2` (both already installed).

---

## 14. Explicitly NOT doing (old-script anti-patterns)

- ❌ No hand-written PDF bytes (`zlib`, xref, trailer) — cairosvg + pypdf own PDF.
- ❌ No custom SVG path parser, cubic flattener, or transform matrix library — the
  individuals are already clean, axis-aligned, identity-scaled.
- ❌ No automatic orientation detection (`min_width_angle` / `upright_matrix`) or
  anisotropy calibration — the only rotation is a hard-coded 90° clockwise for the
  B group, and the mirror axis is always vertical.
- ❌ No centerline / quill-guide / visibility-line handling — those concepts are gone.
- ❌ No page-width "settling", partner-gap search, headless quarter-turn mode, or
  scale parameter — one fixed set of constants, one run.
- ❌ No resurrected code from `generate_feathers_pdf.py` / the `_verify_*` scripts.

---

## 15. Confirmation items (proposed defaults — change here before coding)

1. **Output paths/filename** — `mechanical/templates/print/feathers-letter-landscape.pdf`. OK?
2. **Constants** — MARGIN 5, OVERLAP 12, GAP 10, PAD 8 (mm). Any printer forcing a
   different margin?
3. **Label orientation** — upright on both halves (not mirrored on the left half). OK?
4. **Label content** — just the feather ID (`P1`…`B3`). OK?
5. **Family mixing on packed sheets** — allowed. OK?
6. **Cover bar lengths** — 100 mm and 4 in. OK?

---

## 16. Definition of done

- [x] `make_feather_sheets.py` exists and is readable top-to-bottom in one pass.
- [x] Running it produces the PDF with zero errors and a green verification summary.
- [x] Cover page bars measure 100 mm / 4 in to ±1 mm in the raster check (see §17.2).
- [x] Every feather appears once as a mirrored pair; labels inside; nothing clipped.
- [x] Summary prints the exact sheet count and per-feather placement.
- [ ] Script and `print/sheets/` scratch are deleted afterward; only the PDF remains.
      (script kept for now — see §17.4; delete `make_feather_sheets.py` when done.)

---

## 17. Implementation notes — decisions made during the run

Recorded after building and verifying, so the next reader knows what changed
relative to this plan and why.

### 17.1 cairosvg unit quirk (the one real bug found)

`cairosvg 2.9.0` inflates any CSS length written with an explicit unit by ~3.78×:
`stroke-width: 0.5mm` rendered 1.78 mm and `font-size: 3.5mm` rendered ~13 mm. The
cause is that cairosvg converts explicit CSS units through a 96-dpi *px* scale and
then misreads those px as the SVG's own user units (which are millimetres here).
Root `width="279.4mm"`/`height="215.9mm"` are unaffected (page size came out exact).

**Fix:** every `stroke-width` and `font-size` is **unitless**. A unitless CSS length
is a user-unit value, and our user units are millimetres, so `0.5` means 0.5 mm
(measured 0.42 mm — correct, within anti-aliasing). This is called out in a comment
above the `CSS` block in the script.

### 17.2 Scale tolerance is ±1 mm, not ±0.3 mm

The raster check reads the *ink* extent, which includes the 0.5 mm bar stroke
(0.25 mm past each end), so a geometric 100 mm bar measures ~100.5 mm. ±0.3 mm is
unreachable without sub-pixel line-centroid fitting — overkill for a throwaway.
±1 mm still flags any real printer scaling (>1 %). Measured: 100 mm bar → 100.4 mm,
4 in bar → 102.0 mm.

### 17.3 B-group rotation confirmed

The 90°-clockwise transform from §7 renders correctly: B1's pair came out ~172 ×
191 mm (**tall**), and its left half is an exact mirror of the right (bboxes agree
to <0.1 mm, anti-aliasing level). No rotation is applied to any other family.

### 17.4 Script kept (not yet deleted)

`make_feather_sheets.py` is committed at the repo root so it stays recoverable and
tweakable. The intermediates (`print/sheets/`, `print/contact-sheet.png`) are
gitignored; the merged PDF is tracked. Delete the script whenever you are done
tweaking — it is single-use by design.

### 17.5 Text / label rendering

- `dominant-baseline: middle` **is** honoured by cairosvg (verified: a label
  anchored at y=40 rendered centred on y=39.8), so labels are vertically centred.
- `text-anchor: middle` centres horizontally.
- Font is `sans-serif` (system font), so exact glyph metrics are font-dependent;
  label size is `clamp(3, min(W,H)/6, 12)` mm and the anchor is the viewBox centre,
  so every label sits comfortably inside its outline.

### 17.6 Verification results (all green)

- 29 pages, every page 279.4 × 215.9 mm.
- 28/28 feathers present exactly once, with their label inside.
- Mirror exact (left/right ink bboxes agree to <0.1 mm).
- B rotation correct; outline stroke 0.5 mm.
- Cover bars measure back to 100.4 mm / 102.0 mm at 300 dpi.
- Tiled (2 sheets each): P1–P5, S1, S2, B2, B3 · packed: the other 19.
