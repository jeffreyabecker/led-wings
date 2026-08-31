# Feather Design — Physical Templating

> **Scale (2026-08, current):** wing tips at mid-butt → envelope 55 cm → **× 0.9085** applied
> to all real totals — rescaled so the primaries mount in **Atlas order P1→P10 (P1 = wing
> tip)** within
> the 55 cm envelope (longest ≈ P5/P6 ≈ 49/48 cm, tips peak at 55; was × 1.024 → × 1.40).
> The tables below are **current at × 0.9085**.
>
> **Rule: physical templating only.** This folder carries the *mechanical* feather geometry —
> outlines, arrangement, and the generator that draws them. **No electronics/lighting content
> lives here**: which feathers are lit, chunk counts, LED maps, and wiring all live in
> [boards/](../boards/README.md) (lighting doc:
> [boards/lighting-and-boards.md](../boards/lighting-and-boards.md)).

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

> **Scale:** costume **× 0.9085** — the folded wing fits the 55 cm envelope with the primaries
> in Atlas order (P1 = wing tip; longest ≈ P5/P6, tips at 55; see
> [wing-structure-plan.md](../structural/wing-structure-plan.md)). Measured groups
> (primaries, secondaries) are rescaled from the real totals; estimate groups from their
> documented basis (alula, GPC, GSC, MD) or scaled from the previous values (LC, MG, U).
> If the envelope changes, rescale every row by the new factor.
>
> **Wire cut = costume total + 4 cm mount tail** (adjust the +4 to your mount;
> recompute = total + tail).
>
> **Confidence:** primaries/secondaries = **measured** (Feather Atlas adult ♂ BRD 901 +
> Jenni et al. 2020 cross-check). Alula + all covert groups = **⚠️ graduated estimates**
> (no published data — see [golden-eagle-feather-data.md](golden-eagle-feather-data.md)).
> Cut measured groups freely; for estimated groups cut **one of each type first**, dry-fit on
> the frame, then commit. Trimming beats recutting too-short.

### Primaries — P1–P10 ✅ measured

| Feather | Real total (cm) | Costume total @0.9085× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|----------------------------:|----------------------:|
| P1 | 39.0 | 35 | 39 |
| P2 | 40.4 | 37 | 41 |
| P3 | 43.3 | 39 | 43 |
| P4 | 47.4 | 43 | 47 |
| P5 | 53.3 | 48 | 52 |
| P6 | 54.0 | 49 | 53 |
| P7 | 53.7 | 49 | 53 |
| P8 | 51.4 | 47 | 51 |
| P9 | 46.3 | 42 | 46 |
| P10 | 33.4 | 30 | 34 |

### Secondaries — S1–S11 ✅ measured (S9–S11 trend-extrapolated ⚠️)

| Feather | Real total (cm) | Costume total @0.9085× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|----------------------------:|----------------------:|
| S1 | 37.0 | 34 | 38 |
| S2 | 36.9 | 34 | 38 |
| S3 | 35.3 | 32 | 36 |
| S4 | 32.5 | 30 | 34 |
| S5 | 31.6 | 29 | 33 |
| S6 | 30.6 | 28 | 32 |
| S7 | 28.3 | 26 | 30 |
| S8 | 27.6 | 25 | 29 |
| S9 | 27.0 ⚠️ | 25 | 29 |
| S10 | 26.4 ⚠️ | 24 | 28 |
| S11 | 26.0 ⚠️ | 24 | 28 |

### Alula ⚠️ estimate (4 per wing — user's templates)

| Feather | Basis | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------|-------------------:|----------------------:|
| A1 (longest) | ≈ 0.30 × innermost primary (P10 real) | 9 | 13 |
| A2 | graduated | 8 | 12 |
| A3 | graduated | 8 | 12 |
| A4 (shortest) | ≈ 0.22 × innermost primary | 7 | 11 |

### Greater primary coverts — GPC1–GPC6 ⚠️ estimate (≈ 0.5 × primary covered)

| Feather | Over primary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------:|-------------------:|----------------------:|
| GPC1 | P10 | 15 | 19 |
| GPC2 | P9 | 21 | 25 |
| GPC3 | P8 | 23 | 27 |
| GPC4 | P7 | 24 | 28 |
| GPC5 | P6 | 25 | 29 |
| GPC6 | P5 | 24 | 28 |

### Greater secondary coverts — GSC1–GSC10 ⚠️ estimate (≈ 0.5 × secondary covered)

| Feather | Over secondary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|---------------:|-------------------:|----------------------:|
| GSC1 | S1 | 17 | 21 |
| GSC2 | S2 | 17 | 21 |
| GSC3 | S3 | 16 | 20 |
| GSC4 | S4 | 15 | 19 |
| GSC5 | S5 | 14 | 18 |
| GSC6 | S6 | 14 | 18 |
| GSC7 | S7 | 13 | 17 |
| GSC8 | S8 | 13 | 17 |
| GSC9 | S9 | 12 | 16 |
| GSC10 | S10 | 12 | 16 |

### Median secondary coverts — MD1–MD5 ⚠️ estimate (≈ 0.6 × GSC)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MD1 | 10 | 14 |
| MD2 | 10 | 14 |
| MD3 | 10 | 14 |
| MD4 | 9 | 13 |
| MD5 | 8 | 12 |

### Lesser secondary coverts — LC1–LC6 ⚠️ estimate (≈ 0.55 × median)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| LC1 | 6 | 10 |
| LC2 | 6 | 10 |
| LC3 | 6 | 10 |
| LC4 | 6 | 10 |
| LC5 | 6 | 10 |
| LC6 | 5 | 9 |

### Marginal coverts — MG1–MG12 ⚠️ (removed — not in the user's templates)

None — the wearer's actual template set has **no marginal coverts** (see
[feather-record.csv](feather-record.csv)).

### Underwing coverts — U1–U10 ⚠️ estimate (≈ 0.85 × upperwing equivalents)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| U1 | 16 | 20 |
| U2 | 16 | 20 |
| U3 | 15 | 19 |
| U4 | 14 | 18 |
| U5 | 13 | 17 |
| U6 | 13 | 17 |
| U7 | 12 | 16 |
| U8 | 12 | 16 |
| U9 | 12 | 16 |
| U10 | 11 | 15 |

### Per-wing wire budget

| Group | Count | Wire sum (total, cm) | Wire sum (+4 cm tail, cm) |
|-------|------:|---------------------:|--------------------------:|
| Primaries P1–P10 | 10 | 419 | 459 |
| Secondaries S1–S11 | 11 | 311 | 355 |
| Alula A1–A4 | 4 | 32 | 48 |
| GPC1–GPC6 | 6 | 132 | 156 |
| GSC1–GSC10 | 10 | 143 | 183 |
| MD1–MD5 | 5 | 47 | 67 |
| LC1–LC6 | 6 | 35 | 59 |
| U1–U10 | 10 | 134 | 174 |
| **One wing** | **62 feathers** | **~12.5 m** | **~15.0 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 21 feathers, safe to cut in bulk
> (~8.1 m). Estimated groups = 41 feathers (~6.9 m) — cut one per type (alula, GPC, GSC, MD,
> LC, U) first and validate against the frame/mockup before committing the rest.

## Regions needed

The build groups and what they need (one archetype per group, graduated across
the group's feathers):

| Region | Build group(s) |
|--------|----------------|
| Primaries | P1–P10 |
| Secondaries | S1–S11 |
| Greater secondary coverts | GSC1–GSC10 |
| Greater primary coverts | GPC1–GPC6 |
| Median secondary coverts | MD1–MD5 |
| Lesser secondary coverts | LC1-LC6 |
| Alula | A1–A4 |
| Underwing Coverts | U1-U10|


## Source Images
our source template images are at 7px/cm. the largest primary measures 
375px tall and is 54cm according to feather atlas