# Hub Board — Buck + Power Distribution (TPS56628DDA)

> **Status: design ⚠️** — chip adopted ✅, reference values verified from the TI
> EVM guide/datasheet. Board = **pure buck + power distribution**: 12 V in → 5 V out
> → fused taps. **No data, no control logic, no LED drive on this board.**
>
> **Chip: TPS56628DDA** (LCSC [C2877989](https://www.lcsc.com/product-detail/C2877989.html))
> — 6 A sync buck, 4.5–18 V in, 0.6–5.5 V out, 650 kHz D-CAP2 (no external
> compensation), SO-8 (PowerPAD). Pulled into `libs/` ✅ (symbol, footprint, 3D).

## 1. Role & boundary

| In | Out |
|---|---|
| 12 V bus (12–16.8 V, 4S Li-ion) | one fused 5 V tap per LED-group chain segment |
| Reverse-polarity protected (SS34) | taps ≤ 1.36 A each @100 % (2 A PH2.0-2PWB conn) |

- **Purely power.** The hub does NOT carry data — the LED boards daisy-chain data
  independently. This board is buck + fusing + terminals only.
- **Count:** 4 boards/wing (P: 1×6 A, S: 1×6 A, R: 2×6 A) → **8 total both wings**.

## 2. Reference design (from TI EVM TPS56628EVM-534 + datasheet Table 3-1)

EVM is 1.05 V out; **our target is 5.0 V** → use the datasheet's 5 V column:

| Value | 5 V output (datasheet T3-1) | EVM example (1.05 V) |
|---|---|---|
| **R1 (top FB)** | **124 kΩ** | 8.25 kΩ |
| **R2 (bottom FB)** | **22.1 kΩ** | 22.1 kΩ |
| **L1** | **2.5–3.3 µH** (6 A) | 1.5 µH |
| **Cout (C9+C10+C11)** | **4.7–68 µF** (ceramic) | 2 × 22 µF |
| C4 (feedforward) | optional (2 pF) | open |
| C5 (VREG5) | 1 µF 0603 | 1 µF |
| C3/C7 (boot + ?) | 0.1 µF 0603 | 0.1 µF |
| Cin (C1/C2) | 2 × 10 µF 1210, 35 V X7R | 2 × 10 µF |

**EVM schematic essentials (verified):**
- EN → enable (pull to VIN via 100 kΩ; EN = 10 V/div in the app)
- PG → power-good, open-drain (100 kΩ pull-up if used)
- SW node, VBST bootstrap cap (C3, 0.1 µF), VREG5 (C5, 1 µF)
- AGND/PGND single-point tie (net-tie on EVM)
- 650 kHz fixed; D-CAP2 → no compensation parts

## 3. Design decisions for OUR board (5 V, 6 A)

- **L1: 3.3 µH, ≥ 6–7 A Isat, low DCR** (EVM used 1.5 µH/11 A — ours at 5 V wants the
  upper end of the 2.5–3.3 µH range; pick a shielded 3.3 µH ≥ 6 A).
- **Cout: 2 × 22 µF 1206 (10 V X5R)** — inside the 4.7–68 µF window; D-CAP2 wants
  low-ESR ceramic. (Add a 3rd if transient tests need it.)
- **Cin: 2 × 10 µF 1210, 35 V X7R** — the 12 V bus can see 16.8 V + spikes; 35 V rating
  gives headroom. Place tight to VIN/PGND (the critical loop).
- **Feedback:** R1 124 kΩ / R2 22.1 kΩ (5.0 V). Route VFB away from SW.
- **EN:** pull to VIN (always-on when bus is live); no sequencing needed.
- **PG:** tie to VIN through 100 kΩ (or NC) — not used for now.
- **Outputs:** 1–4 fused taps. Fuse per tap (ATO inline holder or polyfuse) sized to the
  tap's chain (≤ 1.36 A at 100 % → **2 A fuse**, matches the PH2.0-2PWB).
- **Reverse polarity:** SS34 on 12 V in (existing C8678 plan) — keep.
- **Input protection:** TVS clamp on the 12 V bus (TPS56628 is 18 V max — see §4).

## 4. ⚠️ The 18 V input limit — must handle

TPS56628 Vin max = **18 V**. The 4S bus is 12–16.8 V nominal, but a charge spike or
hot-plug transient can exceed 18 V. **Add a TVS (e.g., SMBJ18A-class) + the SS34**
on the bus input, and keep the bus wiring clean. This is the one real constraint the
AOZ/SY8205 (30 V) parts didn't have — acceptable trade for 6 A at $0.72, but
non-negotiable to design in.

## 5. Board spec (pure distribution)

| Item | Value |
|---|---|
| Stackup | 2-layer, 2 oz outer (current + thermal) |
| Input | 12 V bus, SS34 reverse-protect, TVS clamp, 2×10 µF 1210 |
| Buck | TPS56628DDA, 5.0 V, 6 A, 650 kHz |
| Output | fused taps → PH2.0-2PWB (C47647) 2-pin power taps |
| Fuse | 2 A per tap (ATO/polyfuse), or per-board input fuse + per-tap |
| Terminals | push-in spring-clamp (Wago 2060-class) for bus + tap wiring |
| Size | ~30 × 25 mm (4 taps) — one panelized part |
| No | data, no MCU, no LED drive — power only |

## 6. Per-wing deployment (4 boards/wing)

| Board | Group | Taps | Tap currents @100% |
|---|---|---|---|
| H-P | Primaries (131 LED, 5.24 A) | 4 | 1.32/1.32/1.32/1.28 A |
| H-S | Secondaries (100 LED, 4.0 A) | 3 | 1.36/1.32/1.32 A |
| H-R1 | Rest half 1 | 3 | ≤ 0.96 A |
| H-R2 | Rest half 2 | 2 | ≤ 0.88 A |

## 7. BOM — JLCPCB part numbers (verified via jlcsearch, 2026)

> **Basic = JLCPCB "basic part"** (in-stock, no extended-part fee — the cheap path).
> 🔴 = not basic (extended part — adds a per-kind setup fee; prefer basic where possible).

| Ref | Value | Pkg | LCSC | Basic? | Stock | ~Price |
|---|---|---|---|---|---|---|
| U1 | TPS56628DDA | SO-8 EP | [C2877989](https://www.lcsc.com/product-detail/C2877989.html) | — | 150 | $0.72 |
| C1, C2 (Cin) | 10 µF 35 V X7R | 1210 | [C97973](https://www.lcsc.com/product-detail/C97973.html) | 🔴 | 7,882 | $0.87 |
| C3 (boot) | 0.1 µF 50 V X7R | 0603 | [C14663](https://www.lcsc.com/product-detail/C14663.html) | **BASIC** | 12.6 M | $0.011 |
| C5 (VREG5) | 1 µF 50 V X5R | 0603 | [C15849](https://www.lcsc.com/product-detail/C15849.html) | **BASIC** | 6.0 M | $0.030 |
| C9, C10 (Cout) | 22 µF 25 V X5R | 1206 | [C12891](https://www.lcsc.com/product-detail/C12891.html) | **BASIC** | 574 k | $0.18 |
| L1 | 3.3 µH 5.5/6 A | 5.4×5.2 | [C475518](https://www.lcsc.com/product-detail/C475518.html) (FXL0530) | 🔴 | 17 k | $0.18 |
| R1 (FB top) | 124 kΩ 1 % | 0603 | [C2933136](https://www.lcsc.com/product-detail/C2933136.html) | 🔴 | 181 k | $0.001 |
| R2 (FB bot) | 22.1 kΩ 1 % | 0603 | [C2960862](https://www.lcsc.com/product-detail/C2960862.html) | 🔴 | 262 k | $0.001 |
| R5 (EN↑) | 100 kΩ 1 % | 0603 | [C25803](https://www.lcsc.com/product-detail/C25803.html) | **BASIC** | 8.0 M | $0.002 |
| D1 (TVS) | SMBJ18A (18 V, 600 W) | SMB | [C353379](https://www.lcsc.com/product-detail/C353379.html) | 🔴 | 55 k | $0.038 |
| D2 (rev-pol) | SS34 | SMA | [C8678](https://www.lcsc.com/product-detail/C8678.html) | — | — | — |

**Per-board BOM ≈ $1.90** (buck $0.72 + caps $0.30 + L $0.18 + R $0.01 + TVS $0.04 + SS34) —
× 8 boards ≈ **$15 total** for all hub power, vs ~$40+ for 18 × MP1584EN modules.

> ⚠️ **Only 4 of 10 passives are BASIC** (C3, C5, C9/10, R5). The extended-part fee
> (~$3/kind × ~6 kinds ≈ $18 one-time) erodes the savings on an 8-board run. Options:
> (a) accept the fee (still ~$33 vs $40 modules, and the boards are better); (b) substitute
> basic-value parts where tolerance allows (e.g. R1 120 kΩ basic — recompute Vout;
> C1 10 µF 1206 basic) — review item before ordering; (c) hand-solder the hub boards
> (no PCBA fee at all — 8 boards × ~20 parts is a manageable bench job).

## 8. References

- TI TPS56628 datasheet (SLVSC94) — 5 V column Table 3-1
- TI EVM user's guide [SLVU988A](https://www.ti.com/lit/ug/slvu988a/slvu988a.pdf) — schematic + BOM (verified above)
- [Feather boards](feather-boards.md) — 100 % injection map, 17 taps/wing
- [Hub modules](hub-modules.md) — group currents, buck sizing
- [2020-leds project](2020-leds/) — libs: C2877989, C47647, C145954, C145992, C2909059
