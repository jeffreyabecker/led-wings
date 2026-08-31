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

### Greater primary coverts — GPC1–GPC6 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| GPC1 | 10.2 | 14.2 |
| GPC2 | 15.5 | 19.5 |
| GPC3 | 17.6 | 21.6 |
| GPC4 | 17.1 | 21.1 |
| GPC5 | 15.7 | 19.7 |
| GPC6 | 13.4 | 17.4 |

### Greater secondary coverts — GSC1–GSC10 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| GSC1 | 12.5 | 16.5 |
| GSC2 | 16.3 | 20.3 |
| GSC3 | 17.3 | 21.3 |
| GSC4 | 15.5 | 19.5 |
| GSC5 | 15.7 | 19.7 |
| GSC6 | 16.0 | 20.0 |
| GSC7 | 17.0 | 21.0 |
| GSC8 | 17.7 | 21.7 |
| GSC9 | 13.2 | 17.2 |
| GSC10 | 16.1 | 20.1 |

### Median secondary coverts — MD1–MD5 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| MD1 | 11.0 | 15.0 |
| MD2 | 11.7 | 15.7 |
| MD3 | 11.7 | 15.7 |
| MD4 | 11.7 | 15.7 |
| MD5 | 9.8 | 13.8 |

### Lesser secondary coverts — LC1–LC6 ✅ measured

| Feather | Measured total (cm) | Wire cut = +4 cm (cm) |
|---------|--------------------:|----------------------:|
| LC1 | 6.5 | 10.5 |
| LC2 | 7.0 | 11.0 |
| LC3 | 8.4 | 12.4 |
| LC4 | 8.7 | 12.7 |
| LC5 | 9.0 | 13.0 |
| LC6 | 7.7 | 11.7 |

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
| GPC1–GPC6 | 6 | 89.5 | 113.5 |
| GSC1–GSC10 | 10 | 157.3 | 197.3 |
| MD1–MD5 | 5 | 55.9 | 75.9 |
| LC1–LC6 | 6 | 47.3 | 71.3 |
| U1–U10 | 10 | 138.2 | 178.2 |
| **One wing** | **61 feathers** | **~11.5 m** | **~13.9 m** |

> **Cut plan:** measured groups (primaries + secondaries) = 20 feathers, safe to cut in bulk
> (~6.9 m). Estimated groups = 41 feathers (~7.0 m) — cut one per type (alula, GPC, GSC, MD,
> LC, U) first and validate against the frame/mockup before committing the rest.

## Regions needed

The build groups and what they need (one archetype per group, graduated across
the group's feathers):

| Region | Build group(s) |
|--------|----------------|
| Primaries | P1–P10 |
| Secondaries | S1–S10 |
| Greater secondary coverts | GSC1–GSC10 |
| Greater primary coverts | GPC1–GPC6 |
| Median secondary coverts | MD1–MD5 |
| Lesser secondary coverts | LC1-LC6 |
| Alula | A1–A4 |
| Underwing Coverts | U1-U10|


## Source Images
our source template images are at 7px/cm. the largest primary measures 
375px tall and is 54cm according to feather atlas