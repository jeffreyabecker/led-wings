# Feather Boards — One Board per Group (8 per wing)

> **Status: working ✅** — topology locked (user decision): **one board per feather GROUP**
> (P, S, A, PC, SC, MC, L, U), not one per feather. Boards are **full-length custom 5 mm
> strips** (SK9822-EC20 2020) at **31 mm/LED** pitch, fed from the 6 A hub boards.
> Feather sizes = measured templates ([feather-record.csv](../mechanical/templates/feather-record.csv)).
>
> **Locked decisions:**
> - **8 group boards per wing** (both wings mirrored): P, S, A, PC, SC, MC, L, U.
> - **Full length at custom pitch** — each group board runs the group's feathers'
>   measured total lengths contiguously; LEDs = round(total length ÷ 31 mm).
> - **Segment split** — any board > ~390 mm breaks into chained segments (≤ 390 mm,
>   400 − 2×5 mm rails), joined by the 4-pin ZH1.5-4P data connector.
> - **Only the strips are panelized** — one panel per wing carries all 35 segments
>   (400 × ~185 mm V-cut). The **hub boards are individual PCBs, not panelized**
>   (see [hub-board.md](hub-board.md)).
> - **MOQ 5 panels** = 2 wings + 3 spare wings.

## 1. Group boards (per wing)

| Board | Feathers | Total len (mm) | LEDs | Board len (mm) | Segments | A @100 % |
|-------|----------|---------------:|-----:|---------------:|---------:|---------:|
| P | P1–P10 | 3708 | **120** | 3720 | 10 | 4.80 |
| S | S1–S10 | 2389 | **77** | 2387 | 7 | 3.08 |
| A | A1–A4 | 522 | **17** | 527 | 2 | 0.68 |
| PC | PC1–PC6 | 895 | **29** | 899 | 3 | 1.16 |
| SC | SC1–SC10 | 1573 | **51** | 1581 | 5 | 2.04 |
| MC | MC1–MC5 | 559 | **18** | 558 | 2 | 0.72 |
| L | L1–L6 | 473 | **15** | 465 | 2 | 0.60 |
| U | U1–U10 | 1382 | **45** | 1395 | 4 | 1.80 |
| **Wing** | **61** | **11 501** | **372** | **11 532** | **35** | **14.88** |

- Both wings: **744 LEDs**, ~23.1 m of strip, **29.76 A** @ 100 %.
- LEDs per board = `round(total mm ÷ 31)`; board length = `LEDs × 31` mm.
- Segment splits: P 12-LED ×10 · S 11 ×7 · A 9+8 · PC 10+10+9 · SC 11+10×4 ·
  MC 9×2 · L 8+7 · U 12+11×3.

## 2. Panelization — one 400 × ~185 mm panel per wing

- **35 segments** × 5 mm strip height = 175 mm + tooling → **400 × ~185 mm** V-cut panel
  (within JLCPCB rigid 400 × 400 / PCBA 470 × 500 limits). ✅
- Segment length rule: ≤ **390 mm** (400 − 2×5 mm rails); split via chained 4-pin links.
- MOQ 5 panels = 5 wings (2 build + 3 spare).

## 3. SKU collapse — one master strip, cut at score lines

| LEDs/segment | len (mm) | qty/wing |
|---:|---:|---:|
| 12 | 372 | 11 |
| 11 | 341 | 11 |
| 10 | 310 | 6 |
| 9 | 279 | 4 |
| 8 | 248 | 2 |
| 7 | 217 | 1 |

6 distinct segment lengths · one 5 mm-wide strip cell (LED + pads + score lines — the
**SK9822-EC20 has an internal decoupling capacitor**, so no external bypass caps) → one
master strip design, cut at score lines, panels break out per-group boards.

## 4. Power injection — 100 % full-white safe (≤ 1.5 A per 2 A tap)

| Board | A @100 % | Taps | Segments per tap | Max tap A |
|-------|---------:|-----:|-----------------|----------:|
| P | 4.80 | **4** | 30/30/30/30 | 1.20 |
| S | 3.08 | **3** | 26/26/25 | 1.04 |
| A | 0.68 | 1 | 17 | 0.68 |
| PC | 1.16 | 1 | 29 | 1.16 |
| SC | 2.04 | 2 | 26/25 | 1.04 |
| MC | 0.72 | 1 | 18 | 0.72 |
| L | 0.60 | 1 | 15 | 0.60 |
| U | 1.80 | 2 | 23/22 | 0.92 |
| **Wing** | **14.88** | **15** | | ≤ 1.20 |

- 15 taps/wing (30 both wings), every tap ≤ 1.20 A on a 2 A `PH2.0-2PWB` (1.5 A derate
  respected). Data daisy-chains through the segments (ZH1.5-4P), one chain per wing.

## 5. Bucks — 4 × 6 A hub boards per wing (TPS56628)

| Hub board | Feeds | A @100 % | 6 A load |
|-----------|-------|---------:|---------:|
| H-P | P | 4.80 | 80 % |
| H-S | S | 3.08 | 51 % |
| H-R1 | SC + U | 3.84 | 64 % |
| H-R2 | PC + MC + L + A | 3.16 | 53 % |
| **Wing** | **8 boards** | **14.88** | |

- Both wings: **8 × 6 A hub boards** (the same 5-tap board design, populated per group).
- Tap positions/wing: 4 × 5 = 20, **15 used**, 5 spare.
- Runtime: 100 % is a safety ceiling, not usage — 29.76 A × 2 wings… (battery sizing
  assumes a brightness cap; hardware survives full white).

## 6. Open decisions

- **Mid-segment link connector** for the splits — same ZH1.5-4P as the inter-segment
  links (no new part).
- **Score-line pitch** on the master strip (per-LED, per-segment, or per-SKU).
- **Tap connector** — PH2.0-2PWB confirmed (2 A, 1.5 A derate) for all taps ≤ 1.20 A.

## References

- [Templates (feather inventory, authoritative)](../mechanical/templates/README.md) — measured sizes
- [Hub boards](hub-board.md) — 6 A buck + power distribution
- [Hub modules](hub-modules.md) — power, cluster currents
- [Boards](README.md) — build plan
- [2020-leds project](2020-leds/) — SK9822-EC20 strip, connector libs (C145992, C2909059, C145954, C47647, C146050)
- [JLCPCB capabilities](https://jlcpcb.com/capabilities) — board/panel/PCBA size limits
