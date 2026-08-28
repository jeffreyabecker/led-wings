# Feather Design — Physical Templating

> **Scale (2026-08, current):** wing tips at mid-butt → envelope 55 cm → **× 0.9085** applied
> to all real totals — rescaled so the primaries mount in **anatomical order P1→P10** within
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
> in anatomical order (longest ≈ P5/P6, tips at 55; see
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
| P1 | 33.4 | 30 | 34 |
| P2 | 46.3 | 42 | 46 |
| P3 | 51.4 | 47 | 51 |
| P4 | 53.7 | 49 | 53 |
| P5 | 54.0 | 49 | 53 |
| P6 | 53.3 | 48 | 52 |
| P7 | 47.4 | 43 | 47 |
| P8 | 43.3 | 39 | 43 |
| P9 | 40.4 | 37 | 41 |
| P10 | 39.0 | 35 | 39 |

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

### Alula ⚠️ estimate

| Feather | Basis | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------|-------------------:|----------------------:|
| A-B (longer) | ≈ 0.30 × P1 total | 9 | 13 |
| A-T (shorter) | ≈ 0.22 × P1 total | 7 | 11 |

### Greater primary coverts — GPC1–GPC6 ⚠️ estimate (≈ 0.5 × primary covered)

| Feather | Over primary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------:|-------------------:|----------------------:|
| GPC1 | P1 | 15 | 19 |
| GPC2 | P2 | 21 | 25 |
| GPC3 | P3 | 23 | 27 |
| GPC4 | P4 | 24 | 28 |
| GPC5 | P5 | 25 | 29 |
| GPC6 | P6 | 24 | 28 |

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

### Median secondary coverts — MD1–MD4 ⚠️ estimate (≈ 0.6 × GSC)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MD1 | 10 | 14 |
| MD2 | 10 | 14 |
| MD3 | 10 | 14 |
| MD4 | 9 | 13 |

### Lesser secondary coverts — LC1–LC8 ⚠️ estimate (≈ 0.55 × median)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| LC1 | 6 | 10 |
| LC2 | 6 | 10 |
| LC3 | 6 | 10 |
| LC4 | 6 | 10 |
| LC5 | 6 | 10 |
| LC6 | 5 | 9 |
| LC7 | 5 | 9 |
| LC8 | 5 | 9 |

### Marginal coverts — MG1–MG12 ⚠️ estimate (smallest row, graduating)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MG1 | 5 | 9 |
| MG2 | 5 | 9 |
| MG3 | 4 | 8 |
| MG4 | 4 | 8 |
| MG5 | 4 | 8 |
| MG6 | 4 | 8 |
| MG7 | 4 | 8 |
| MG8 | 4 | 8 |
| MG9 | 4 | 8 |
| MG10 | 4 | 8 |
| MG11 | 3 | 7 |
| MG12 | 3 | 7 |

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
| Alula A-B, A-T | 2 | 16 | 24 |
| GPC1–GPC6 | 6 | 132 | 156 |
| GSC1–GSC10 | 10 | 143 | 183 |
| MD1–MD4 | 4 | 39 | 55 |
| LC1–LC8 | 8 | 45 | 77 |
| MG1–MG12 | 12 | 48 | 96 |
| U1–U10 | 10 | 134 | 174 |
| **One wing** | **73 feathers** | **~12.9 m** | **~15.8 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 21 feathers, safe to cut in bulk
> (~8.1 m). Estimated groups = 52 feathers (~7.7 m) — cut one per type (GPC, GSC, MD, LC, MG,
> U, alula) first and validate against the frame/mockup before committing the rest.

## Regions needed

The build groups and what they need (one archetype per group, graduated across
the group's feathers):

| Region | Build group(s) |
|--------|----------------|
| Primaries | P1–P10 |
| Secondaries | S1–S11 |
| Greater secondary coverts | GSC1–GSC10 |
| Greater primary coverts | GPC1–GPC6 |
| Median secondary coverts | MD1–MD4 |
| Lesser secondary coverts | LC1-LC8 |
| Marginal coverts | MG1–MG12 |
| Alula | A-B, A-T |
| Underwing Coverts | U1-U10|


## Source Images
our source template images are at 7px/cm. the largest primary measures 
375px tall and is 54cm according to feather atlas