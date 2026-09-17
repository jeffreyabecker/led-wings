# Feather Design — Physical Templating

> **Sizes (2026-08, current):** all feather sizes are **measured from the physical wing
> templates** — [feather-record.csv](feather-record.csv) is **authoritative** (left wing, mm;
> converted to cm here). The × 0.9085 projection is superseded: the real templates are smaller
> (longest ≈ P5/P4 ≈ 43.5/43.0 cm).
>
> **Rule: physical templating only.** This folder carries the *mechanical* feather geometry —
> outlines, arrangement, and the generator that draws them. **No electronics/lighting content
> lives here**: which feathers are lit, chunk counts, LED maps, and wiring all live in
> [boards/](../boards/README.md) (lighting doc:
> [boards/lighting-and-boards.md](../boards/lighting-and-boards.md)).

## Terminology

| Code | Group |
|------|-------|
| P | primaries P1–P10 |
| S | secondaries S1–S10 |
| A | alula A1–A4 |
| PC | primary coverts PC1–PC6 |
| SC | secondary coverts SC1–SC10 |
| MC | median coverts MC1–MC5 |
| L | lesser coverts L1–L6 |
| U | underwing coverts U1–U10 |
| B | body feathers (scapulars, etc.) — **not yet in the cut list** |

## Measured reference data

- [Golden eagle feather measurements](golden-eagle-feather-data.md) — pulled totals + vane
  lengths per feather (primaries, secondaries, rectrices) from the USFWS Feather Atlas and
  Jenni et al. 2020; alula + covert groups have **no published data** (working estimates only).
  **Sizing authority for the generator once covert gaps are validated.**
- **Quill wire cut list — inline below.** Wire length per feather = costume total + 4 cm mount
  tail (embed below the skin line into the frame).

## Quill wire — cut list

Wire length per feather for the costume quills (the wire backbone running the full feather,
base of calamus → tip).

> **Source:** measured totals from [feather-record.csv](feather-record.csv) (left wing, mm →
> cm). **Wire cut = measured total + 4 cm mount tail** (adjust the +4 to your mount;
> recompute = total + tail).
>
> **Note:** the templates are **~4 cm shorter** than the 55 cm envelope projection — primaries'
> tips land at **~51 cm** below the shoulder line (see
> [wing-structure-plan.md](../structural/wing-structure-plan.md)).
>
> **Confidence:** all rows are **measured from the physical templates** (authoritative). The
> templates are **mirrored** — the same sizes serve both wings.
>
> **Feather substrate:** **deferred to Phase 2** (foam trials) — this phase builds the feathers
> from **various packing foams** (see [PROJECT_PLAN](../../PROJECT_PLAN.md), Phase 2).

### Primaries — P1–P10 ✅ measured (physical templates)

| Feather | Real eagle (cm) | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|--------------------:|----------------------:|
| P1 | 39.0 | 30.7 | 34.7 |
| P2 | 40.4 | 39.5 | 43.5 |
| P3 | 43.3 | 41.5 | 45.5 |
| P4 | 47.4 | 43.0 | 47.0 |
| P5 | 53.3 | 43.5 | 47.5 |
| P6 | 54.0 | 42.5 | 46.5 |
| P7 | 53.7 | 37.0 | 41.0 |
| P8 | 51.4 | 33.0 | 37.0 |
| P9 | 46.3 | 31.1 | 35.1 |
| P10 | 33.4 | 29.0 | 33.0 |

### Secondaries — S1–S10 ✅ measured (physical templates)

| Feather | Real eagle (cm) | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|--------------------:|----------------------:|
| S1 | 37.0 | 24.8 | 28.8 |
| S2 | 36.9 | 29.3 | 33.3 |
| S3 | 35.3 | 27.8 | 31.8 |
| S4 | 32.5 | 27.0 | 31.0 |
| S5 | 31.6 | 26.2 | 30.2 |
| S6 | 30.6 | 25.0 | 29.0 |
| S7 | 28.3 | 23.2 | 27.2 |
| S8 | 27.6 | 22.0 | 26.0 |
| S9 | 27.0 | 18.6 | 22.6 |
| S10 | 26.4 | 15.0 | 19.0 |

### Alula — A1–A4 ✅ measured (4 per wing)

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| A1 | 15.6 | 19.6 |
| A2 | 14.8 | 18.8 |
| A3 | 12.6 | 16.6 |
| A4 | 9.2 | 13.2 |

### Primary coverts — PC1–PC6 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| PC1 | 10.2 | 14.2 |
| PC2 | 15.5 | 19.5 |
| PC3 | 17.6 | 21.6 |
| PC4 | 17.1 | 21.1 |
| PC5 | 15.7 | 19.7 |
| PC6 | 13.4 | 17.4 |

### Secondary coverts — SC1–SC10 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| SC1 | 12.5 | 16.5 |
| SC2 | 16.3 | 20.3 |
| SC3 | 17.3 | 21.3 |
| SC4 | 15.5 | 19.5 |
| SC5 | 15.7 | 19.7 |
| SC6 | 16.0 | 20.0 |
| SC7 | 17.0 | 21.0 |
| SC8 | 17.7 | 21.7 |
| SC9 | 13.2 | 17.2 |
| SC10 | 16.1 | 20.1 |

### Median coverts — MC1–MC5 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| MC1 | 11.0 | 15.0 |
| MC2 | 11.7 | 15.7 |
| MC3 | 11.7 | 15.7 |
| MC4 | 11.7 | 15.7 |
| MC5 | 9.8 | 13.8 |

### Lesser coverts — L1–L6 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| L1 | 6.5 | 10.5 |
| L2 | 7.0 | 11.0 |
| L3 | 8.4 | 12.4 |
| L4 | 8.7 | 12.7 |
| L5 | 9.0 | 13.0 |
| L6 | 7.7 | 11.7 |

### Marginal coverts — MG ⚠️ (removed — not in the user's templates)

None — the wearer's actual template set has **no marginal coverts** (see
[feather-record.csv](feather-record.csv)).

### Underwing coverts — U1–U10 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| U1 | 8.7 | 12.7 |
| U2 | 9.2 | 13.2 |
| U3 | 11.5 | 15.5 |
| U4 | 14.0 | 18.0 |
| U5 | 15.0 | 19.0 |
| U6 | 20.6 | 24.6 |
| U7 | 11.5 | 15.5 |
| U8 | 20.6 | 24.6 |
| U9 | 15.6 | 19.6 |
| U10 | 11.5 | 15.5 |

### Per-wing wire budget

| Group | Count | Wire sum (total, cm) | Wire sum (+4 cm tail, cm) |
|-------|------:|---------------------:|--------------------------:|
| Primaries P1–P10 | 10 | 370.8 | 410.8 |
| Secondaries S1–S10 | 10 | 238.9 | 278.9 |
| Alula A1–A4 | 4 | 52.2 | 68.2 |
| PC1–PC6 | 6 | 89.5 | 113.5 |
| SC1–SC10 | 10 | 157.3 | 197.3 |
| MC1–MC5 | 5 | 55.9 | 75.9 |
| L1–L6 | 6 | 47.3 | 71.3 |
| U1–U10 | 10 | 138.2 | 178.2 |
| **One wing** | **61 feathers** | **~11.5 m** | **~13.9 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 20 feathers, safe to cut in bulk
> (~6.9 m). Estimated groups = 41 feathers (~7.0 m) — cut one per type (A, PC, SC, MC, L,
> U) first and validate against the frame/mockup before committing the rest.

## Regions needed

The build groups and what they need (one archetype per group, graduated across
the group's feathers):

| Region | Build group(s) |
|--------|----------------|
| Primaries | P1–P10 |
| Secondaries | S1–S10 |
| Secondary coverts | SC1–SC10 |
| Primary coverts | PC1–PC6 |
| Median coverts | MC1–MC5 |
| Lesser coverts | L1-L6 |
| Alula | A1–A4 |
| Underwing coverts | U1-U10|
| Body feathers | B (scapulars, etc.) — not yet in the cut list |


## Source Images
our source template images are at 7px/cm. the largest primary measures 
375px tall and is 54cm according to feather atlas

## As-built template outlines (photos → measurements)

[find-template-outlines.py](find-template-outlines.py) reads the de-skewed photos of the
as-built templates in [as-built/source-images/unskewed/](as-built/source-images/unskewed/)
and extracts one outline + physical measurement per template.

```bash
python find-template-outlines.py                     # all images
python find-template-outlines.py --images "S1-6.jpg"
python find-template-outlines.py --px-per-inch 100   # skip auto-calibration
```

### Layout

```
mechanical/templates/
  find-template-outlines.py     the photo -> outline/measurement tool
  build-feather-aggregate.py    aggregate the individual feather SVGs into one catalog
  split-feather-aggregate.py    and back: the aggregate -> straightened individual files
  as-built/
    source-images/              photos: raw/ = camera originals, unskewed/ = de-skewed
    labels.csv                  image,index -> feather label, transcribed from the marks
    outlines/                   TRACKED   geometry + measurements (309 KB)
      <stem>.svg                 1:1 mm outline, path ids are feather labels
      <stem>.json                full polygon set, px and cm
      outlines.json              all images combined
      calibration.json           per-image px/inch for X and Y
      templates-measured.csv     one row per feather: length/width/area/aspect/position
    vectors/                    TRACKED   hand-editable vector set
      individuals/               one SVG per feather — SOURCE OF TRUTH for the aggregate
      feathers-aggregate.svg     all 42, one <g> per prefix, 1:1 mm
    scratch/                    IGNORED   QC rasters (~110 MB, fully regenerable)
      <stem>.overlay.png         outlines drawn on the photo, labelled
      <stem>.gridcheck.png       fitted 1" grid over the photo — verify calibration by eye
      <stem>.mask.png            the binary detection mask
      feathers-aggregate.png     aggregate QC raster (--png)
```

Geometry is small, textual and diffable, so it is committed. The rasters are ~15 MB each and
regenerate in seconds, so they stay in `scratch/`. `--out` and `--scratch` relocate either.

### Smoothed outline

Each SVG has one black outline path per template in `<g id="outlines">` (stroke 0.5, path
ids are the feather codes: `P1`, `SC3`, …), plus a `<g id="labels">` group. The outline is a
**smooth cubic-Bézier idealisation** of the detected edge, not a faithful trace of it —
`--fit-mm` (default **1.0 mm**) is the smoothing lever.

> **The measurements are NOT taken from the smooth curve.** `templates-measured.csv` and the
> JSON still derive length/width/area from the RDP polygon, so the drawn outline can sit up
> to ~1.5 mm from the reported width (median length difference 0.32 mm). This is deliberate:
> switching the measurement source would change the values, and because detection indices
> are assigned by **area**, a near-tie could renumber templates and invalidate
> [as-built/labels.csv](as-built/labels.csv). If you want the measurements taken from the
> smooth curve, that is a separate change and the anchor check would flag any remapping.

`--fit-mm` is the dial. Larger = flatter flanks, fewer segments:

| `--fit-mm` | median segments | deviation from the detected edge | length change |
|---|---:|---:|---:|
| 0.25 (unsmoothed-faithful) | 32 | 0.44 mm | 0.34 mm |
| 0.5 | 18 | 0.59 mm | 0.30 mm |
| **1.0 (default)** | **12** | **0.95 mm** | **0.32 mm** |
| 2.5 | 8 | 1.85 mm | 0.40 mm |

> **Do not use `--smooth-mm` as the smoothing lever.** Measured across all 42 templates, at
> the same resulting segment count, raising pre-smoothing to 3–6 mm cut the tip so hard the
> feather lost **1.5–4.0 mm of length**, whereas raising the tolerance lost **0.3 mm**. Keep
> `--smooth-mm` near 1 mm (the hand-cut roughness scale) and turn `--fit-mm` instead.

`--no-smooth` falls back to emitting the raw RDP polyline (the pre-smoothing output).

### Per-feather SVGs for hand-tweaking

```bash
python find-template-outlines.py --feathers
```

Writes one **self-contained** SVG per feather to `as-built/scratch/feathers/<label>.svg`
(42 files, ~3.4 MB, ~24 s). Each holds:

- the source photo cropped around that feather (base64 JPEG, embedded — no sibling file to
  lose if you move or copy the SVG), with an 8 mm margin (`--feather-margin-mm`)
- the smooth outline path with id = the feather code
- the code as a red label

Two properties make these safe to edit:

- **They share the sheet's mm frame.** `viewBox` is the crop's rectangle in absolute sheet
  coordinates, with `width`/`height` trimmed to it — so each file opens zoomed on its
  feather at 1:1, yet coordinates stay meaningful across all 42 files. A path tweaked in one
  keeps its absolute position.
- The photo is placed with `preserveAspectRatio="none"` across its calibrated mm rectangle.
  The scan is anisotropic (X and Y px/inch differ by ~10%), so stretching the crop to the
  mm box is exactly what makes it register with the path.

> **Hand edits are protected.** An existing file whose content differs is *left alone* and
> reported, so re-running cannot silently regenerate over your tweaked paths. Pass
> `--feather-force` when you do want to regenerate them.

> **Not tracked.** They live in `scratch/` (git-ignored) because they are large and
> regenerable. If your hand-tweaked versions become the source of truth, point
> `--feather-out` at a tracked folder instead — but note the generator will then be writing
> into it, so keep the no-clobber behaviour in mind.

### Aggregate SVG — all feathers, grouped by prefix

```bash
python build-feather-aggregate.py                 # -> as-built/vectors/feathers-aggregate.svg
python build-feather-aggregate.py --png           # + scratch/feathers-aggregate.png (QC raster)
python build-feather-aggregate.py --check         # verify only, write nothing
python build-feather-aggregate.py --flip none     # default: the files carry their own orientation
```

[build-feather-aggregate.py](build-feather-aggregate.py) reads the feather sources in
[as-built/vectors/individuals/](as-built/vectors/individuals/) — **those files are the source of
truth and the photo-detection tool above is not involved** — and writes one catalog holding all 42
feathers, 1:1 mm (user units = mm):

```xml
<g id="catalog">
  <g id="P">                      one group per prefix (P, S, A, PC, SC, MC, LC, B)
    <g id="P1" transform="matrix(...)" data-source="individuals/P1.svg">
      <path id="P1-outline" .../>    verbatim from individuals/P1.svg — d and transform
      <text ...>P1</text>            the source's own label
```

Every feather keeps its own group, and the **group** carries the whole transform — the placement,
the optional flip, *and the source file's own group transform* (the split files carry a real one) —
so the `<path>` inside is untouched and a group can be selected, hidden, moved or exported by id in
a vector editor without disturbing the geometry. No text is emitted for the document or for the
groups: the only labels in the output are the ones the individual SVGs already carry.

> **Why repositioning is required.** The individual files sit in frames of their own, and those
> frames overlap in absolute coordinates, so feathers would stack if the files were merely
> concatenated. The aggregate lays out one row per prefix instead, with `--align base|top|center`
> choosing the edge the row lines up on (default `base`).
>
> **Flip.** `--flip none|vertical|horizontal|both` (default **`none`**: the files already carry the
> orientation they were split out with) mirrors each outline about its own bounding-box centre,
> which leaves that box — and therefore every row and slot — unchanged. The mirror is on the
> feather's group, never on the path, and the label rides the group with a local counter-transform
> (a mirror would reverse the glyphs; the counter-transform makes the net effect on a label a pure
> translation, so it renders exactly as authored). Because a mirror on top of a file that already
> has its own group transform would need that transform folded into the label solution, asking for
> a flip while sources carry one is refused with an explanation rather than drawn wrong.
>
> **Self-checks** on every build: each written outline must equal the placement applied to the
> source outline (same points, to 0.01 mm), paths must be byte-identical, each label must keep its
> glyph orientation and anchored position and still lie on its own feather, no two feathers may
> overlap, and no non-source label text may appear. `--check` runs that without writing.

### Splitting the aggregate back into individual files

```bash
python split-feather-aggregate.py                  # -> individuals/*.svg, straightened
python split-feather-aggregate.py --check          # verify only, write nothing
python split-feather-aggregate.py --no-straighten  # exactly as drawn in the aggregate
python split-feather-aggregate.py --no-ancestors   # size from the feather's own transform
```

[split-feather-aggregate.py](split-feather-aggregate.py) is the inverse of the builder, for when the
aggregate has become the authority (hand edits, and the arrangement: per-prefix-group rotation and
scale, per-feather transforms). For every feather group it writes `individuals/<LABEL>.svg`:

- the feather **upright** — rotated so its long axis (the minimum-area box's long side, not a PCA
  axis, which leaves a curved feather slightly tilted) runs down the page with the tip at the
  bottom, at the size the aggregate gives it. So a group scale such as P's 1.2001x length survives,
  the arrangement's rotation does not, and the shape is never re-fitted;
- **`<g id="feather">` carries that transform and the `<path>` is copied verbatim** (d, transform,
  style, `sodipodi:nodetypes`), so an outline is bit-for-bit the aggregate's;
- the **label stays level**: it is re-anchored onto the straightened feather and its own transform
  solved so the net effect is the authored `rotate(180)` — level and unstretched whatever the
  group's rotation or scale;
- the `viewBox` is `0 0 w h` with the feather `--margin-mm` from the corner, so each file opens 1:1
  on its own feather. A shared sheet frame is meaningless once feathers are rotated upright, so
  files get their own local frame.

> The two flags are independent: `--no-ancestors` drops the *prefix group's* arrangement (its
> rotation and its ~1.2x length scale) and keeps only the feather's own transform; `--no-straighten`
> keeps the arrangement rotation, i.e. writes the geometry exactly as it lies in the aggregate (a
> lossless dump, but most files then open rotated).
>
> Self-checks on every run: each outline must equal the aggregate's put through the same
> straightening (point-for-point), the feather must come out axis-aligned and keep the aggregate's
> minimum-area size, the label must end up level, verbatim in text and on its own feather, and the
> file must read back through `build-feather-aggregate.py` as the same geometry.

### Calibration — X and Y must be scaled separately

These photos are **not metrically rectified**. Measured against the printed 1" grid they
carry a different pixels-per-inch in X and Y, in different directions per photo:

| Image | px/in X | px/in Y | Y/X |
|-------|--------:|--------:|----:|
| `P1-6_B1-5.jpg` | 101.54 | 112.10 | **+10.4%** |
| `S1-6.jpg` | 104.13 | 94.03 | **−9.7%** |
| `SC1-8_A1-4_PC1-3_MC1-5_LC1-5.jpg` | 106.82 | 105.83 | −0.9% |

A single px/inch figure would therefore corrupt every across-feather width by up to 10%,
so the script measures the two axes independently and does all geometry in physical units.

Calibration is automatic: it fits the printed 1" grid lines (per-band, least-squares on
~30 lines) and independently checks the result against the printed **1/4" dot grid**,
which must be 4.00 dot cells per inch (measured: 4.02 / 4.00 / 3.99). Because the de-skew
is purely affine (X pitch is constant top-to-bottom and Y pitch constant left-to-right),
one scale per axis is sufficient. `--px-per-inch X,Y` overrides everything.

> **If the source photos are ever re-exported**, map the sheet's grid to a fixed isotropic
> scale (e.g. exactly 3600 × 2400 px = 100 px/inch for the full 36 × 24" sheet). That
> removes the per-image scale *and* the aspect error, puts all three photos in one shared
> sheet coordinate frame (so the groups can be stitched), and makes `--px-per-inch 100`
> exact. Not required — the current photos calibrate fine.

### Detection

Templates are saturated (cardboard sat ≈ 91, blue tape sat ≈ 129) against a near-neutral
printed sheet (sat 15–22), so a saturation threshold separates them without picking up the
dark checkerboard patch or the printed ink. Tan templates, blue-taped templates and the
cardboard tips of part-taped templates are all found.

**Material matters.** Detection needs the template to be saturated. Kraft cardboard,
blue tape, and the cardboard tips of part-taped templates all read 60–130 saturation and
are found reliably. A **white paper** template has the same saturation as the sheet (~15)
and is not found at all — the original B5 was like this, which is what the
detected-vs-expected count check exists to catch. The fix that worked was remaking B5 in
cardboard and photographing it alone (`B5.jpg`). If you must use pale stock, mark it with
tape or a marker first; `--pale` adds a best-effort brightness pass, but it also returns
false positives (20 blobs on `P1-6_B1-5.jpg` where 11 are expected).

### Feather labels

[as-built/labels.csv](as-built/labels.csv) is the **labelling authority**:
it maps each photo's detection index to a feather code, and the script applies it to the
CSV `label` column, the overlay labels and the SVG path ids.

**The labels are transcribed from the hand-written marks on the templates themselves, and a
mark beats every other source.** Marks ride on the physical part; detection indices are
*derived*. Indices are assigned by **area**, so they are position-blind and can renumber if
segmentation changes — so each row carries the `length_cm` and `x_cm` the template had when
the mapping was made, and the script warns if a labelled index no longer matches its anchor
instead of silently mislabelling a feather.

It also prints each series in physical reading order, which is what catches a scrambled
mapping:

```
label order: B1 B2 B3 B4 | P1 P2 P3 P4 P5 P6
label order: A1 A2 A3 A4 | LC1 LC2 LC3 LC4 LC5 | MC1 MC2 MC3 MC4 MC5 | PC1 PC2 PC3 | SC1…SC8
```

Current mapping (label → photo), 42 templates:

| Photo | Labels |
|-------|--------|
| `B5.jpg` | `#1` = B5 (solo re-shoot in cardboard) |
| `P1-6_B1-5.jpg` | `#1` P2, `#2` P3, `#3` P4, `#4` P1, `#5` P5, `#6` P6, `#7`–`#10` = B1–B4 |
| `S1-6.jpg` | `#1`–`#6` = S1–S6 |
| `SC1-8_A1-4_PC1-3_MC1-5_LC1-5.jpg` | `#1` PC1, `#2` SC3, `#3` SC6, `#4` SC5, `#5` SC4, `#6` SC8, `#7` PC2, `#8` SC2, `#9` A2, `#10` A1, `#11` SC7, `#12` PC3, `#13` A3, `#14` SC1, `#15` MC2, `#16` MC4, `#17` MC3, `#18` A4, `#19` MC5, `#20` MC1, `#21` LC4, `#22` LC5, `#23` LC3, `#24` LC2, `#25` LC1 |

> **Why the P group is not index-ordered.** Detection index order for the primaries is
> 43.4, 42.2, 41.3, 39.4 cm, but the templates are *marked* P2, P3, P4, P1 — so `#4`
> (39.4 cm) is **P1** and `#1` (43.4 cm) is **P2**. Read off the sheet in physical order the
> series is a clean P1…P6 left to right (39.4, 43.4, 42.2, 41.3, 34.5, 30.2 cm). All four
> photos were re-read against the marks; only these four indices changed.

> `P1-6_B1-5.jpg` reports "10 detected vs 11 expected" on every run. That warning is correct:
> B5 has been re-shot on its own, so the filename still claims five B templates but only four
> remain in that photo. Rename it `P1-6_B1-4.jpg` to silence it.

> Neither P reading matches `feather-record.csv` for the P group (record: P1 30.7, P2 39.5,
> P3 41.5, P4 43.0, P5 43.5, P6 42.5 cm). Five of the six measured values match record values
> to within 0.5 cm but in a different order, and the photo's 34.5 cm template has no
> counterpart — the templates and the record look to have drifted apart (relabelled or
> re-cut) after the record was written. The measurement itself is verified independently by
> `*.gridcheck.png`, so this is a record question, not a measurement one.

### B series (graduated)

| | B1 | B2 | B3 | B4 | B5 |
|---|---:|---:|---:|---:|---:|
| length (cm) | 25.33 | 24.26 | 21.32 | 17.97 | 12.80 |
| width (cm) | 7.86 | 7.27 | 6.34 | 5.40 | 3.64 |

Measured from `P1-6_B1-5.jpg` (B1–B4) and the solo `B5.jpg`.

> **⚠️ Open question — the P group.** The handwritten marks on the photo read
> **left to right as P1 (39.4 cm), P2 (43.4 cm), P3 (42.2 cm), P4 (41.3 cm), P5 (34.5 cm),
> P6 (30.2 cm)** — i.e. the physical template marked `P1` is detection **#4**, and `#1` is
> marked `P2`. The table above instead labels `#1`–`#6` as P1–P6, i.e. in descending-length
> order. Both readings are recorded here so the discrepancy is not lost; confirm which is
> intended, since it moves 43.4 cm from P2 to P1 and 39.4 cm from P1 to P4.
>
> Note also that neither reading matches `feather-record.csv` for the P group
> (record: P1 30.7, P2 39.5, P3 41.5, P4 43.0, P5 43.5, P6 42.5 cm). Five of the six
> measured values match record values to within 0.5 cm but in a different order, and the
> photo's 34.5 cm template has no counterpart — which suggests the templates and the record
> drifted apart (relabelled or re-cut) after the record was written.