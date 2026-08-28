# Feather Design — Physical Templating

> **Scale (2026-08, current):** wing tips at mid-butt → P4 = **55 cm** → **× 1.024** (55 ÷ 53.7)
> applied to all real totals — the tables below are **current at × 1.024** (were × 1.40).
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

> **Scale:** costume P4 = **55 cm** quill-to-tip (design-readiness) ÷ real adult-♂ P4 53.7 cm
> (Feather Atlas) = **× 1.024** applied to all real totals (was × 1.40). Measured groups
> (primaries, secondaries) are rescaled from the real totals; estimate groups from their
> documented basis (alula, GPC, GSC, MD) or rescaled by 55/75 from the previous graduated
> values (LC, MG, U). If the design envelope changes, rescale every row by `new_P4 ÷ 53.7`.
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

| Feather | Real total (cm) | Costume total @1.024× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|---------------------------:|----------------------:|
| P1 | 33.4 | 34 | 38 |
| P2 | 46.3 | 47 | 51 |
| P3 | 51.4 | 53 | 57 |
| P4 | 53.7 | **55** | 59 |
| P5 | 54.0 | 55 | 59 |
| P6 | 53.3 | 55 | 59 |
| P7 | 47.4 | 49 | 53 |
| P8 | 43.3 | 44 | 48 |
| P9 | 40.4 | 41 | 45 |
| P10 | 39.0 | 40 | 44 |

### Secondaries — S1–S11 ✅ measured (S9–S11 trend-extrapolated ⚠️)

| Feather | Real total (cm) | Costume total @1.024× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|---------------------------:|----------------------:|
| S1 | 37.0 | 38 | 42 |
| S2 | 36.9 | 38 | 42 |
| S3 | 35.3 | 36 | 40 |
| S4 | 32.5 | 33 | 37 |
| S5 | 31.6 | 32 | 36 |
| S6 | 30.6 | 31 | 35 |
| S7 | 28.3 | 29 | 33 |
| S8 | 27.6 | 28 | 32 |
| S9 | 27.0 ⚠️ | 28 | 32 |
| S10 | 26.4 ⚠️ | 27 | 31 |
| S11 | 26.0 ⚠️ | 27 | 31 |

### Alula ⚠️ estimate

| Feather | Basis | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------|-------------------:|----------------------:|
| A-B (longer) | ≈ 0.30 × P1 total | 10 | 14 |
| A-T (shorter) | ≈ 0.22 × P1 total | 8 | 12 |

### Greater primary coverts — GPC1–GPC6 ⚠️ estimate (≈ 0.5 × primary covered)

| Feather | Over primary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------:|-------------------:|----------------------:|
| GPC1 | P1 | 17 | 21 |
| GPC2 | P2 | 24 | 28 |
| GPC3 | P3 | 26 | 30 |
| GPC4 | P4 | 28 | 32 |
| GPC5 | P5 | 28 | 32 |
| GPC6 | P6 | 27 | 31 |

### Greater secondary coverts — GSC1–GSC10 ⚠️ estimate (≈ 0.5 × secondary covered)

| Feather | Over secondary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|---------------:|-------------------:|----------------------:|
| GSC1 | S1 | 19 | 23 |
| GSC2 | S2 | 19 | 23 |
| GSC3 | S3 | 18 | 22 |
| GSC4 | S4 | 17 | 21 |
| GSC5 | S5 | 16 | 20 |
| GSC6 | S6 | 16 | 20 |
| GSC7 | S7 | 14 | 18 |
| GSC8 | S8 | 14 | 18 |
| GSC9 | S9 | 14 | 18 |
| GSC10 | S10 | 14 | 18 |

### Median secondary coverts — MD1–MD4 ⚠️ estimate (≈ 0.6 × GSC)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MD1 | 11 | 15 |
| MD2 | 11 | 15 |
| MD3 | 11 | 15 |
| MD4 | 10 | 14 |

### Lesser secondary coverts — LC1–LC8 ⚠️ estimate (≈ 0.55 × median)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| LC1 | 7 | 11 |
| LC2 | 7 | 11 |
| LC3 | 7 | 11 |
| LC4 | 7 | 11 |
| LC5 | 7 | 11 |
| LC6 | 6 | 10 |
| LC7 | 6 | 10 |
| LC8 | 6 | 10 |

### Marginal coverts — MG1–MG12 ⚠️ estimate (smallest row, graduating)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MG1 | 6 | 10 |
| MG2 | 6 | 10 |
| MG3 | 5 | 9 |
| MG4 | 5 | 9 |
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
| U1 | 18 | 22 |
| U2 | 18 | 22 |
| U3 | 17 | 21 |
| U4 | 16 | 20 |
| U5 | 15 | 19 |
| U6 | 15 | 19 |
| U7 | 14 | 18 |
| U8 | 13 | 17 |
| U9 | 13 | 17 |
| U10 | 12 | 16 |

### Per-wing wire budget

| Group | Count | Wire sum (total, cm) | Wire sum (+4 cm tail, cm) |
|-------|------:|---------------------:|--------------------------:|
| Primaries P1–P10 | 10 | 473 | 513 |
| Secondaries S1–S11 | 11 | 347 | 391 |
| Alula A-B, A-T | 2 | 18 | 26 |
| GPC1–GPC6 | 6 | 150 | 174 |
| GSC1–GSC10 | 10 | 161 | 201 |
| MD1–MD4 | 4 | 43 | 59 |
| LC1–LC8 | 8 | 53 | 85 |
| MG1–MG12 | 12 | 52 | 100 |
| U1–U10 | 10 | 151 | 191 |
| **One wing** | **73 feathers** | **~14.5 m** | **~17.4 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 21 feathers, safe to cut in bulk
> (~9.0 m). Estimated groups = 52 feathers (~8.4 m) — cut one per type (GPC, GSC, MD, LC, MG,
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