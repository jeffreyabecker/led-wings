# Feather Boards — Single Panelized Board Plan

> **Status: working ✅** — topology and panel decision locked (below); per-feather list is
> definitive from the **templates inventory** (authoritative) + the lighting model.
>
> **Locked decisions:**
> - **Each feather gets a board** (73 feathers/wing, both wings mirrored).
> - **Daisy-chain + power injection** topology: 4-pin data in/out per board (ZH1.5-4P
>   `C145992`), 2-pin power taps (1.0T-2P `C145954` / PH2.0-2PWB `C47647`); power
>   injected every N boards.
> - **Board width: 5 mm** (locked — the 2020-LED path).
> - **One panel per wing**, **P4–P9 split** into 2 chained boards each so every board
>   fits a **400 × 400 V-cut panel** (JLCPCB rigid max) — and the panel stays
>   **assembly-capable** (≤ 470 × 500 PCBA max).
> - **MOQ 5 panels** = 2 wings + 3 spare wings.

## 1. Panel feasibility (verified, rails + tooling included)

JLCPCB rigid limits: single board max **400 × 500** · V-cut panel max **400 × 400** ·
PCBA max **470 × 500**.

| | One-piece (no split) | **Chosen: split P4–P9** |
|---|---|---|
| Boards/wing | 73 | **79** |
| Longest board | 477 mm (P5–P8) | **377 mm** (P1–P3) |
| Panel | needs 500 × 146 (bare only, >470 PCBA) | **400 × 181 mm** (33 rows × 5 mm) |
| Assembly | ❌ (>470 mm PCBA cap) | ✅ (≤470×500) |
| MOQ 5 | 5 panels = 5 wings | 5 panels = 5 wings |

- **Split rule:** boards > **390 mm** (400 − 2×5 mm rails) split into 2 chained segments
  (P4–P9: 13/15 LEDs → 7+6 / 8+7).
- **Tooling:** +6 mm edge zone for tooling holes included in the 181 mm height; 5 mm
  rails each side.
- **Copper:** 8 mm would be more robust but **5 mm locked** — 1 oz copper at 5 mm carries
  the 0.60 A full-white P5–P8 max with margin (IPC-2221 external ≈ 1 A+ at that width).

## 2. Board list (per wing, definitive)

### Primaries (P4–P9 split into 2 chained boards; P1–P3, P10 one piece)

| Board | LEDs | len (mm) | | Board | LEDs | len (mm) | | Board | LEDs | len (mm) |
|---|---|---:|---|---|---:|---|---|---:|
| P1 | 11 | 343 | | P4a | 7 | 210 | | P7a | 8 | 243 |
| P2 | 12 | 377 | | P4b | 6 | 177 | | P7b | 7 | 210 |
| P3 | 12 | 377 | | P5a | 8 | 243 | | P8a | 8 | 243 |
| P10 | 10 | 310 | | P5b | 7 | 210 | | P8b | 7 | 210 |
| | | | | P6a | 8 | 243 | | P9a | 7 | 210 |
| | | | | P6b | 7 | 210 | | P9b | 6 | 177 |

### Secondaries (one piece each)

| Board | LEDs | len (mm) | | Board | LEDs | len (mm) | | Board | LEDs | len (mm) |
|---|---|---:|---|---|---:|---|---|---:|
| S1 | 11 | 343 | | S5 | 9 | 277 | | S9 | 8 | 243 |
| S2 | 11 | 343 | | S6 | 9 | 277 | | S10 | 8 | 243 |
| S3 | 10 | 310 | | S7 | 8 | 243 | | S11 | 8 | 243 |
| S4 | 10 | 310 | | S8 | 8 | 243 | | | | |

### Coverts, alula, underwing (one piece each)

| Board | LEDs | len (mm) | | Board | LEDs | len (mm) | | Board | LEDs | len (mm) |
|---|---|---:|---|---|---:|---|---|---:|
| A1 (A-B) | 3 | 77 | | GSC5 | 5 | 143 | | LC1–LC5 | 2 | 43 |
| A2 (A-T) | 3 | 77 | | GSC6 | 5 | 143 | | LC6–LC8 | 2 | 43 |
| GPC1 | 5 | 143 | | GSC7 | 4 | 110 | | MG1–MG10 | 2 | 43 |
| GPC2 | 7 | 210 | | GSC8 | 4 | 110 | | MG11 | 1 | 10 |
| GPC3 | 7 | 210 | | GSC9 | 4 | 110 | | MG12 | 1 | 10 |
| GPC4 | 8 | 243 | | GSC10 | 4 | 110 | | U1–U4 | 5 | 143 |
| GPC5 | 8 | 243 | | MD1–MD3 | 4 | 110 | | U5–U10 | 4 | 110 |
| GPC6 | 8 | 243 | | MD4 | 3 | 77 | | | | |
| GSC1 | 6 | 177 | | | | | | | | |
| GSC2 | 6 | 177 | | | | | | | | |
| GSC3 | 5 | 143 | | | | | | | | |
| GSC4 | 5 | 143 | | | | | | | | |

### Totals (per wing)

- **79 boards** (73 feathers; 6 split) · **425 LEDs** · **12 322 mm** total strip length
- **Full-white: 17.0 A/wing** (34 A both wings)

## 3. SKU collapse (distinct board lengths)

| LEDs | len (mm) | qty/wing | | LEDs | len (mm) | qty/wing |
|---|---:|---:|---|---|---:|---:|
| 1 | 10 | 2 | | 6 | 177 | 12 |
| 2 | 43 | 18 | | 7 | 210 | 10 |
| 3 | 77 | 4 | | 8 | 243 | 11 |
| 4 | 110 | 25 | | 10 | 310 | 2 |
| 5 | 143 | 16 | | 11 | 343 | 4 |
| | | | | 12 | 377 | 2 |

14 distinct lengths · all share the same 5 mm-wide strip cell (LED + pads + score lines)
→ **one master strip design, cut at score lines**; panels break out per-feather boards.

## 4. Power injection — 100 % full-white design (safe, no brightness cap) ✅

> **Design basis: worst case = full white (40 mA/LED), no firmware cap.** Sized so the
> system survives a bug that runs everything at 100 %. Blinding? Yes — but safe.
>
> Constraints used: connector derated to **1.5 A** (of 2 A `PH2.0-2PWB`), rail
> **2 mm 2 oz**, far-end drop budget **0.3 V**, worst verified segment drop **195 mV**.

### Per-wing injection map (17 taps/wing · 34 both wings)

| Group | LEDs | A @100 % | Taps | Segments (LEDs/tap) | Max tap A |
|---|---|---:|---:|---|---:|
| Primaries | 131 | 5.24 | **4** | 33/33/33/32 | 1.32 |
| Secondaries | 100 | 4.00 | **3** | 34/33/33 | 1.36 |
| GPC | 43 | 1.72 | 2 | 22/21 | 0.88 |
| GSC | 48 | 1.92 | 2 | 24/24 | 0.96 |
| MD median | 15 | 0.60 | 1 | 15 | 0.60 |
| LC lesser | 16 | 0.64 | 1 | 16 | 0.64 |
| MG marginal | 22 | 0.88 | 1 | 22 | 0.88 |
| Alula | 6 | 0.24 | 1 | 6 | 0.24 |
| Underwing | 44 | 1.76 | 2 | 22/22 | 0.88 |

- Every tap ≤ **1.36 A** (fits a 2 A `PH2.0-2PWB`, 1.5 A derate respected).
- Every segment far-end ≥ **4.81 V** (worst 195 mV drop @ 2 mm 2 oz).
- **MD/LC per-group injection: ✅** — one tap each at the group head, trivial
  (39–45 mV drop, 0.60–0.64 A).

### Buck assignment (per wing, 2.5 A class)

| Group | A @100 % | Bucks | Capacity | Margin |
|---|---:|---:|---:|---:|
| Primaries | 5.24 | **3 × 2.5 A** | 7.5 A | +43 % |
| Secondaries | 4.00 | **2 × 2.5 A** | 5.0 A | +25 % |
| Rest | 7.76 | **4 × 2.5 A** | 10.0 A | +29 % |
| **Total** | **17.0** | **9 × 2.5 A/wing** | | |

- Both wings: **18 × 2.5 A bucks**, 34 taps, **170 W LED @100 %** (≈189 W from the
  12 V bus @90 % eff, ~15.7 A).
- ⚠️ **Runtime consequence:** 100 % is for *safety*, not usage — 189 W × 8 h = **1.5 kWh**
  (absurd). Real runtimes come from the brightness cap; the hardware just *survives*
  full white. The battery side (investigations/battery) must assume the cap.

### Tap wiring (per wing)

- Primaries: 3 bucks → 4 taps (2+1+1)
- Secondaries: 2 bucks → 3 taps (2+1)
- Rest: 4 bucks → 10 taps (3+3+2+2)

## 5. Open decisions

- **Mid-feather link connector** for the P4–P9 splits — same 4-pin ZH1.5-4P as
  inter-feather links (no new part) or a slimmer option.
- **Score-line pitch** on the master strip (per-LED, per-board, or per-SKU).
- **Tap connector for primaries' 1.32 A** — PH2.0-2PWB confirmed; 1.0T-2P (1 A) is
  **not** sufficient at 100 %.

## 5. References

- [Templates (feather inventory, authoritative)](../mechanical/templates/README.md)
- [Hub modules](hub-modules.md) — power distribution, cluster currents
- [Boards](README.md) — build plan, settled COTS parts
- [2020-leds project](2020-leds/) — SK9822-EC20 strip, connector libs (C145992, C2909059, C145954, C47647, C146050)
- [JLCPCB capabilities](https://jlcpcb.com/capabilities) — board/panel/PCBA size limits
