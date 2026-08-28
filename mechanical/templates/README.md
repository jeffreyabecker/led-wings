# Feather Design — Physical Templating

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

> **Scale:** costume P4 = 75 cm quill-to-tip (design-readiness) ÷ real adult-♂ P4 53.7 cm
> (Feather Atlas) = **× 1.40** applied to all real totals. If the design envelope changes,
> rescale every row by `new_P4 ÷ 53.7`.
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

| Feather | Real total (cm) | Costume total @1.40× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|--------------------------:|----------------------:|
| P1 | 33.4 | 47 | 51 |
| P2 | 46.3 | 65 | 69 |
| P3 | 51.4 | 72 | 76 |
| P4 | 53.7 | **75** | 79 |
| P5 | 54.0 | 76 | 80 |
| P6 | 53.3 | 75 | 79 |
| P7 | 47.4 | 66 | 70 |
| P8 | 43.3 | 61 | 65 |
| P9 | 40.4 | 57 | 61 |
| P10 | 39.0 | 55 | 59 |

### Secondaries — S1–S11 ✅ measured (S9–S11 trend-extrapolated ⚠️)

| Feather | Real total (cm) | Costume total @1.40× (cm) | Wire cut = +4 cm (cm) |
|---------|----------------:|--------------------------:|----------------------:|
| S1 | 37.0 | 52 | 56 |
| S2 | 36.9 | 52 | 56 |
| S3 | 35.3 | 49 | 53 |
| S4 | 32.5 | 46 | 50 |
| S5 | 31.6 | 44 | 48 |
| S6 | 30.6 | 43 | 47 |
| S7 | 28.3 | 40 | 44 |
| S8 | 27.6 | 39 | 43 |
| S9 | 27.0 ⚠️ | 38 | 42 |
| S10 | 26.4 ⚠️ | 37 | 41 |
| S11 | 26.0 ⚠️ | 36 | 40 |

### Alula ⚠️ estimate

| Feather | Basis | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------|-------------------:|----------------------:|
| A-B (longer) | ≈ 0.30 × P1 total | 14 | 18 |
| A-T (shorter) | ≈ 0.22 × P1 total | 10 | 14 |

### Greater primary coverts — GPC1–GPC6 ⚠️ estimate (≈ 0.5 × primary covered)

| Feather | Over primary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------:|-------------------:|----------------------:|
| GPC1 | P1 | 23 | 27 |
| GPC2 | P2 | 32 | 36 |
| GPC3 | P3 | 36 | 40 |
| GPC4 | P4 | 38 | 42 |
| GPC5 | P5 | 38 | 42 |
| GPC6 | P6 | 37 | 41 |

### Greater secondary coverts — GSC1–GSC10 ⚠️ estimate (≈ 0.5 × secondary covered)

| Feather | Over secondary | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|---------------:|-------------------:|----------------------:|
| GSC1 | S1 | 26 | 30 |
| GSC2 | S2 | 26 | 30 |
| GSC3 | S3 | 25 | 29 |
| GSC4 | S4 | 23 | 27 |
| GSC5 | S5 | 22 | 26 |
| GSC6 | S6 | 21 | 25 |
| GSC7 | S7 | 20 | 24 |
| GSC8 | S8 | 19 | 23 |
| GSC9 | S9 | 19 | 23 |
| GSC10 | S10 | 18 | 22 |

### Median secondary coverts — MD1–MD4 ⚠️ estimate (≈ 0.6 × GSC)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MD1 | 16 | 20 |
| MD2 | 16 | 20 |
| MD3 | 15 | 19 |
| MD4 | 14 | 18 |

### Lesser secondary coverts — LC1–LC8 ⚠️ estimate (≈ 0.55 × median)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| LC1 | 10 | 14 |
| LC2 | 10 | 14 |
| LC3 | 9 | 13 |
| LC4 | 9 | 13 |
| LC5 | 9 | 13 |
| LC6 | 8 | 12 |
| LC7 | 8 | 12 |
| LC8 | 8 | 12 |

### Marginal coverts — MG1–MG12 ⚠️ estimate (smallest row, graduating)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| MG1 | 8 | 12 |
| MG2 | 8 | 12 |
| MG3 | 7 | 11 |
| MG4 | 7 | 11 |
| MG5 | 6 | 10 |
| MG6 | 6 | 10 |
| MG7 | 6 | 10 |
| MG8 | 5 | 9 |
| MG9 | 5 | 9 |
| MG10 | 5 | 9 |
| MG11 | 4 | 8 |
| MG12 | 4 | 8 |

### Underwing coverts — U1–U10 ⚠️ estimate (≈ 0.85 × upperwing equivalents)

| Feather | Costume total (cm) | Wire cut = +4 cm (cm) |
|---------|-------------------:|----------------------:|
| U1 | 25 | 29 |
| U2 | 24 | 28 |
| U3 | 23 | 27 |
| U4 | 22 | 26 |
| U5 | 21 | 25 |
| U6 | 20 | 24 |
| U7 | 19 | 23 |
| U8 | 18 | 22 |
| U9 | 18 | 22 |
| U10 | 17 | 21 |

### Per-wing wire budget

| Group | Count | Wire sum (total, cm) | Wire sum (+4 cm tail, cm) |
|-------|------:|---------------------:|--------------------------:|
| Primaries P1–P10 | 10 | 649 | 689 |
| Secondaries S1–S11 | 11 | 476 | 520 |
| Alula A-B, A-T | 2 | 24 | 32 |
| GPC1–GPC6 | 6 | 204 | 228 |
| GSC1–GSC10 | 10 | 219 | 259 |
| MD1–MD4 | 4 | 61 | 77 |
| LC1–LC8 | 8 | 71 | 103 |
| MG1–MG12 | 12 | 71 | 119 |
| U1–U10 | 10 | 207 | 247 |
| **One wing** | **73 feathers** | **~19.8 m** | **~22.7 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 21 feathers, safe to cut in bulk
> (~12.1 m). Estimated groups = 52 feathers (~10.6 m) — cut one per type (GPC, GSC, MD, LC, MG,
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
