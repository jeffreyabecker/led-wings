# Board inventory — panelized FPC subset (from feather-record.csv)

> **Basis (2026-08): recomputed from the authoritative measured totals**
> [`mechanical/templates/feather-record.csv`](../../../mechanical/templates/feather-record.csv)
> (left wing, cm). The earlier **× 1.024 / 55 cm projection is superseded** — the CSV says
> P4 = 43.0 cm, not 55.0. **Boards are sized to TOTAL feather length** (the CSV carries
> `total_cm` only — no vane column; vane lengths exist only for flight feathers in
> `golden-eagle-feather-data.md`).
>
> Model: **30/m (33.3 mm pitch), LEDs = ceil(total_cm × 0.3)**, boards chained from the
> {B7, B4, B3} SKUs to cover each feather's LED count (minimizing boards, then dark-LED
> excess). Reproducible from [`tools/recompute_boards.py`](../../../tools/recompute_boards.py).

Assembly panels are capped at **250 × 250 mm** (stencil/reflow guideline), so the max
board length is **233 mm = 7 LEDs** @ 33.3 mm pitch. **Material: FR-4 thin core
(0.6–0.8 mm) baseline; FPC fallback.**

## SKU subset (all with per-LED score lines)

| SKU | Length | LEDs | Role |
|---|---|---|---|
| B7 | 233 mm | 7 | largest primaries, structure |
| B4 | 133 mm | 4 | mid feathers, 12-LED chains (B4+B4+B4) |
| B3 | 100 mm | 3 | the **workhorse** here — most coverts are small |

> ⚠️ **SKU mix flipped vs the old plan:** the measured set has many small feathers (coverts,
> alula, underwing), so **B3-dominant (63/wing)** — the old "B7-dominant" assumption came from
> the superseded × 1.024 set.

## Per-feather board map (per wing, from CSV) ✅

### Primaries P1–P10 (25 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| P1 | 30.7 | 10 | B7+B3 | 2 |
| P2 | 39.5 | 12 | B4+B4+B4 | 3 |
| P3 | 41.5 | 13 | B7+B3+B3 | 3 |
| P4 | 43.0 | 13 | B7+B3+B3 | 3 |
| P5 | 43.5 | 14 | B7+B7 | 2 |
| P6 | 42.5 | 13 | B7+B3+B3 | 3 |
| P7 | 37.0 | 12 | B4+B4+B4 | 3 |
| P8 | 33.0 | 10 | B7+B3 | 2 |
| P9 | 31.1 | 10 | B7+B3 | 2 |
| P10 | 29.0 | 9 | B7+B3 | 2 |

### Secondaries S1–S10 (18 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| S1 | 24.8 | 8 | B4+B4 | 2 |
| S2 | 29.3 | 9 | B7+B3 | 2 |
| S3 | 27.8 | 9 | B7+B3 | 2 |
| S4 | 27.0 | 9 | B7+B3 | 2 |
| S5 | 26.2 | 8 | B4+B4 | 2 |
| S6 | 25.0 | 8 | B4+B4 | 2 |
| S7 | 23.2 | 7 | B7 | 1 |
| S8 | 22.0 | 7 | B7 | 1 |
| S9 | 18.6 | 6 | B3+B3 | 2 |
| S10 | 15.0 | 5 | B3+B3 | 2 |

### Alula A1–A4 (6 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| A1 | 15.6 | 5 | B3+B3 | 2 |
| A2 | 14.8 | 5 | B3+B3 | 2 |
| A3 | 12.6 | 4 | B4 | 1 |
| A4 | 9.2 | 3 | B3 | 1 |

### Primary coverts PC1–PC6 (11 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| PC1 | 10.2 | 4 | B4 | 1 |
| PC2 | 15.5 | 5 | B3+B3 | 2 |
| PC3 | 17.6 | 6 | B3+B3 | 2 |
| PC4 | 17.1 | 6 | B3+B3 | 2 |
| PC5 | 15.7 | 5 | B3+B3 | 2 |
| PC6 | 13.4 | 5 | B3+B3 | 2 |

### Secondary coverts SC1–SC10 (18 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| SC1 | 12.5 | 4 | B4 | 1 |
| SC2 | 16.3 | 5 | B3+B3 | 2 |
| SC3 | 17.3 | 6 | B3+B3 | 2 |
| SC4 | 15.5 | 5 | B3+B3 | 2 |
| SC5 | 15.7 | 5 | B3+B3 | 2 |
| SC6 | 16.0 | 5 | B3+B3 | 2 |
| SC7 | 17.0 | 6 | B3+B3 | 2 |
| SC8 | 17.7 | 6 | B3+B3 | 2 |
| SC9 | 13.2 | 4 | B4 | 1 |
| SC10 | 16.1 | 5 | B3+B3 | 2 |

### Median coverts MC1–MC5 (5 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| MC1 | 11.0 | 4 | B4 | 1 |
| MC2 | 11.7 | 4 | B4 | 1 |
| MC3 | 11.7 | 4 | B4 | 1 |
| MC4 | 11.7 | 4 | B4 | 1 |
| MC5 | 9.8 | 3 | B3 | 1 |

### Lesser coverts L1–L6 (6 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| L1 | 6.5 | 2 | B3 (1 dark) | 1 |
| L2 | 7.0 | 3 | B3 | 1 |
| L3 | 8.4 | 3 | B3 | 1 |
| L4 | 8.7 | 3 | B3 | 1 |
| L5 | 9.0 | 3 | B3 | 1 |
| L6 | 7.7 | 3 | B3 | 1 |

### Underwing U1–U10 (13 boards)

| Feather | total (cm) | LEDs | Chain | Boards |
|---|---|---|---|---|
| U1 | 8.7 | 3 | B3 | 1 |
| U2 | 9.2 | 3 | B3 | 1 |
| U3 | 11.5 | 4 | B4 | 1 |
| U4 | 14.0 | 5 | B3+B3 | 2 |
| U5 | 15.0 | 5 | B3+B3 | 2 |
| U6 | 20.6 | 7 | B7 | 1 |
| U7 | 11.5 | 4 | B4 | 1 |
| U8 | 20.6 | 7 | B7 | 1 |
| U9 | 15.6 | 5 | B3+B3 | 2 |
| U10 | 11.5 | 4 | B4 | 1 |

## Counts (per wing / both wings) ✅

| | Per wing | Both wings |
|---|---:|---:|
| Feathers | 61 | 122 |
| Lit LEDs | 374 | 748 |
| LED positions (incl. 19/wing dark) | 393 | 786 |
| Boards (feather) | 102 | 204 |
| — B7 / B4 / B3 | 16 / 23 / 63 | 32 / 46 / 126 |
| Strip length (LED pitch) | 12.45 m | 24.91 m |
| Feather total (CSV sums) | 11.50 m | 23.00 m |
| Full white (40 mA) | 15.0 A / 75 W | **29.9 A / 150 W** |

> Structure strips (3 × 0.8 m/wing, 72 LEDs/wing) are **not feathers** — unchanged from the
> earlier plan (24 boards both wings, add 2.9 A full white/wing).

## Panels

- **5 × 250 × 250 mm** for both wings (204 feather + 24 structure = 228 boards; 50 × 5 mm
  strips per panel → capacity 250, **22 spare** ≈ 9 % margin for rounding + cutting waste).
- Feather boards alone: 204 → still 5 panels (46 spare).

## Chain links

- **41 feather-internal board links per wing** (102 boards − 61 chains) → **82 both wings**,
  each a JST-PH 4-pin cable (VDD/VSS/DI/CI) — coincidentally the same 82 as the old plan.
- Longest chains: P3/P4/P6 (B7+B3+B3, 3 boards); P5 (B7+B7, 2); P2/P7 (B4+B4+B4, 3).
