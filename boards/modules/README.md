# Strip Modules — Design Core (shared by 4-LED & 6-LED)

> Status legend: ✅ settled · ⚠️ to confirm at layout · ⬜ TBD.
>
> This file is the **common architecture** both module variants share. Variant-specific numbers
> live in the two design files:
> - [4-LED module](4-led-module.md) — 42 × 12 mm
> - [6-LED module](6-led-module.md) — 62 × 12 mm

## What a module is

A single-row LED strip module: SK9822-EC20 pixels at **10.4 mm pitch** on a **12 mm-wide,
1-layer flex PCB**, with a **4-pin JST-GH SMD connector on each end**. Power + data both ride
the 4-pin;
modules chain tip-to-tail, and power is injected every 4–6 modules from the power-hubs.
(System plan: [boards/README](../README.md) · pinout legend:
[connector-pinout](../../docs/connector-pinout.md).)

## Block diagram

```
IN (JST-GH 4)                                  OUT (JST-GH 4)
┌────────┐                                     ┌────────┐
│ 1 GND  ├── GND rail ────────────────────────┤ 4 GND  │
│ 2 SDI  ├─▶ SDI ─▶ LED1 ─▶ LED2 ─▶ … ─▶ LEDn ─┴─▶ SDO ─┤ 3 SDO
│ 3 CLK  ├─▶ CLK ─▶ LED1 ─▶ LED2 ─▶ … ─▶ LEDn ─┴─▶ CKO ─┤ 2 CKO
│ 4 +5V  ├── +5V rail ────────────────────────┤ 1 +5V  │
└────────┘                                     └────────┘
```

- **Power rails** run the full strip length; both connectors wired through with **crossed pin
  order** (IN pin 4 `+5V` ↔ OUT pin 1 `+5V`; IN pin 1 `GND` ↔ OUT pin 4 `GND`).
- **Data daisy-chains LED→LED** — each SK9822 re-buffers `SDO`/`CKO`, so hops stay short and
  clean. No termination and **no series R on the module** (optional chain-head R stays at the
  controller, per plan).

## Settled architecture

| Item | Choice | Status |
|------|--------|--------|
| LED | SK9822-EC20, 2020 pkg (2.0 × 2.0 mm) — [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | ✅ |
| Pitch | 10.4 mm center-to-center, single row | ✅ |
| Board | **1-layer flex PCB, 12 mm wide** | ✅ |
| Connector | JST-GH 4-pin SMD `SM04B-GHS-TB`, **top-entry**, footprint 8.25 × 4.13 mm — [C189895](https://www.lcsc.com/product-detail/C189895.html) | ✅ |
| Signal contract | IN: `GND`/`SDI`/`CLK`/`+5V` · OUT: `+5V`/`CKO`/`SDO`/`GND` | ✅ |
| Decoupling | 100 nF 0603 **per LED** — [C14663](https://www.lcsc.com/product-detail/C14663.html) | ✅ |
| Fab | EasyEDA Pro → JLCPCB flex + PCBA | ✅ |
| Stackup | 1-layer flex, **1 oz copper, 4 mil**; coverlay **default** (amber) | ✅ |
| Stiffener | **Under the two connectors only** (rest stays flexible) | ✅ |
| Panelization | **We supply a panelized file** (tab-routed, not V-scored) | ✅ |

## Routing topology

- **Single layer:** everything — power rails, data/clock, pads, decoupling — lives on one
  copper layer (flex base, 1 oz copper). No vias, no back side.
- **Power:** +5V / GND rails run the strip's full length and **fill the available width** (wide
  edge traces/pours), sized for the inter-injection budget (≤ ~0.8 A, see current math). Both
  connectors pass the rails straight through.
- **Data:** `SDI`/`CLK` enter at IN, hop LED→LED, exit as `SDO`/`CKO` at OUT. Clocked protocol +
  per-LED re-buffering → no termination needed on the module.
- **Decoupling:** one 100 nF 0603 per LED, placed directly beside its pixel between `+5V` and
  `GND`, for the per-LED current spikes.
- **Placement:** connector footprint is **8.25 × 4.13 mm**. Orient the **8.25 mm axis across
  the 12 mm board width** (1.875 mm margin each side) and the **4.13 mm axis along the strip**
  into the end margin. LED row centered. The end-margin math fits exactly:
  - 4-LED: 42 mm = 2 × 5.4 + 3 × 10.4 → 5.4 − 4.13 = 1.27 mm clearance ✅
  - 6-LED: 62 mm = 2 × 5.0 + 5 × 10.4 → 5.0 − 4.13 = 0.87 mm clearance ✅
- **Direction:** modules are directional. Chain head at the feather base → `IN`; tail toward the
  tip → `OUT`; the last module's OUT is unused. (JST-GH here is the top-entry type — jumpers
  plug in from above and fold flat along the feather.)

## Current math (per module)

- Full-white per LED ≈ **40 mA** (project budget, from battery sizing).
- Connector design budget between injection points: **≤ ~0.8 A** (JST-GH rated 1 A/circuit).
- Module draw (drives injection cadence):

| Module | Full white | @ 20 % |
|--------|-----------:|-------:|
| 4-LED | 0.16 A | ~0.03 A |
| 6-LED | 0.24 A | ~0.05 A |

## Panelization & fab notes

- Two fixed designs (no scripting), 1-layer flex, 1 oz copper, 4 mil, **default coverlay**.
- **Stiffener under the two connectors only** (FR-4/PI stiffener pads at each end; the LED span
  stays flexible).
- **We supply a panelized file** — tab-routed (mouse-bites) between boards, not V-scored.
- **Workflow: schematic first** in EasyEDA Pro (clean BOM/CPL), then PCB layout; Gerber/BOM/CPL
  export decided at handoff.
- Silkscreen: module ID (`4LED` / `6LED`), `IN`/`OUT` marks, pin numbers, LED indices.

### Panel plan (mixed, ×5 minimum order)

- **One mixed panel** of both module types, ordered **5×** (JLCPCB flex min. order).
- **Per panel:** 37 × 4-LED + 20 × 6-LED (57 modules) → totals **185 × 4-LED + 100 × 6-LED**
  vs. 176 / 92 required (~5 % spares as assembly-loss + repair stock).
- **Layout:** both boards share the 12 mm width → stacked in 12 mm-wide columns along the
  490 mm panel length. 7 columns hold everything (worst column ≈ 438 mm of 490 mm); total
  width ≈ 84 mm of 234 mm.
- **Panel max:** 234 × 490 mm (JLCPCB flex).

## Open decisions (shared)

- Mounting: **adhesive-only** (VHB/tape) to the feather substrate — no holes.
- Final column/rail placement + edge keep-out against JLCPCB flex panel rules (at layout).

## KiCad library references

Symbols + footprints (official [KiCad libraries](https://gitlab.com/kicad/libraries), v8/v9):

| Part | Symbol (lib:name) | Footprint (lib:name) | Notes |
|------|--------------------|----------------------|-------|
| Decoupling cap | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | standard 0603 |
| Connector (IN/OUT) | `Connector_Generic:Conn_01x04` | `Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal` | GH top-entry SMD, 4-pin + 2 mount pads |
| LED | `LED:APA102-2020` | `LED_SMD:LED-APA102-2020` | APA102-2020 = SK9822-EC20 package/pin-compatible |

### LED pin-map caveat ⚠️

The KiCad `LED:APA102-2020` symbol uses **APA102 pin numbers**, which do **not** match the
SK9822-EC20 datasheet numbering — same six signals, different pin numbers:

| Signal | APA102-2020 (KiCad) | SK9822-EC20 (datasheet) |
|--------|:---:|:---:|
| VDD | 1 | 5 |
| CKO | 2 | 6 |
| SDO | 3 | 1 |
| SDI | 4 | 3 |
| CKI | 5 | 4 |
| GND | 6 | 2 |

**Consequence:** when drawing the schematic with `LED:APA102-2020`, map wires by **signal name**
(SDI/SDO/CKI/CKO/VDD/GND), not by pin number. The footprint `LED_SMD:LED-APA102-2020` lands
the signals on the physically-correct pads; only the symbol's pin *numbers* differ from the
datasheet. Flagged for the schematic step.

## References

- [Connector pinout / wiring legend](../../docs/connector-pinout.md) — canonical 4-pin maps
- [Boards plan](../README.md) — chain layout, injection cadence, BOM status
- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [JST SM04B-GHS-TB datasheet](https://pdf.datasheet.live/f55f35a7/jst-mfg.com/SM04B-GHS-TB%28LF%29%28SN%29.html)
