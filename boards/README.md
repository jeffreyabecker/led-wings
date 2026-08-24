# Boards — Strip-Module Build Plan (one-off)

> **Strategy (settled ✅):** one-off build — the LED medium is **two standard strip-module
> designs** (custom PCBs, panelized, JLCPCB PCBA) chained tip-to-tail with 4-pin JST-GH
> connectors; controller and power hubs are off-the-shelf modules. Fully parameterized custom
> feather boards (KiCad + `pcbnew`) stay deferred.
>
> Status: ✅ settled · ⚠️ to confirm · ⬜ TBD.

| Role | Status | Implementation |
|------|--------|----------------|
| Feather lighting | ✅ | Chained standard modules (4-LED + 6-LED), 4-pin JST-GH each end |
| Covert strip rows | ✅ | Chained 4-LED modules (7 per row) |
| Controller | ✅ | Pixelblaze V3 + 74AHCT125 level shifter (COTS modules) |
| Power hub | ✅ | Buck modules + fuse blocks on perfboard |

## System (locked)

- **Split power/data.** Data daisy-chains module-to-module from one central Pixelblaze
  driving **both wings**; power fans out from hub clusters on a 12 V bus and is **injected
  into the module chains via harness pigtails**.
- **Controller:** Pixelblaze V3 Standard (ElectroMage) — ESP32, 8 data channels, 3.3 V logic.
  **Segmentation (settled ✅): N = 2 chains — one per wing.** No Output Expander.
- **Pixels:** ~1260 LEDs total both wings (see
  [feather lighting](../mechanical/feather/lighting-and-boards.md)). Chain budget ≈ 630
  LEDs/channel — a full frame at 8 MHz SPI ≈ 2.5 ms, well inside any pattern frame rate.
- **Routing:** the two chains (one per wing) run along the wing's **top edge** (the feather
  bases — the only cable entrance); hubs sit along the same edge.

## LED medium — standard strip modules

- **Two module designs (custom PCBs, panelized):**
  - **4-LED** — 42 × 12 mm, 4 × SK9822-EC20 at 10.4 mm pitch
  - **6-LED** — 62 × 12 mm, 6 × SK9822-EC20 at 10.4 mm pitch
  - 4-pin JST-GH SMD on **each end**; chained tip-to-tail with 4-wire jumpers.
  - **Designs:** [module design core](modules/README.md) · [4-LED](modules/4-led-module.md) ·
    [6-LED](modules/6-led-module.md) (shared architecture + per-variant specs).
- **Signal contract (settled ✅, "option b"):** power + data combined on the 4-pin —
  **IN:** `+5V`/`GND`/`DI`/`CI` · **OUT:** `+5V`/`GND`/`DO`/`CO`. Power rides the chain;
  injection via harness pigtails (below). Pin maps:
  [wiring legend](../docs/connector-pinout.md).
- **Power injection:** harness pigtails tap `+5V`/`GND` **every 4–6 modules**, fed from the
  power-hubs, **fused per injection feed**. **Brightness cap ≤ 20–25 % (policy)** — a 630-LED
  chain head carries ~5 A @ 20 %, so full white stays "never"; between injection points the
  connectors stay ≤ ~0.8 A (JST-GH rated 1 A/circuit).
- **Chain layout (lego counts):**

  | Group | Modules | LEDs | vs map |
  |-------|---------|-----:|--------|
  | Primaries P1–P10 | 6+6+4 | 16 | −1 |
  | Secondaries S1–S12 | 6+4+4 | 14 | ✓ |
  | Tertials T1–T4 | 4+4+4 | 12 | ✓ |
  | Greater coverts GC1–GC12 | 6+4 | 10 | ✓ |
  | Alula A-B/A-T | 6+4 | ~10 ⚠️ | ✓ |
  | Covert rows | 7 × 4-LED | 28 | ✓ |

- **Volume:** ~270 modules (92 × 6-LED, 176 × 4-LED), ~540 JST-GH 4-pin connectors, ~1260
  SK9822-EC20. Total ~1260 LEDs both wings — battery math effectively unchanged (~50 A full
  white, ~10 A @ 20 %).
- **Fab:** EasyEDA Pro (JLCPCB-native — their part lib already carries the SK9822-EC20
  footprint, C2909059, and JST-GH SMD parts). Two fixed designs — no script needed. **1-layer
  flex PCBs**, panelized + PCBA at JLCPCB flex.

### SK9822-EC20 pin arrangement (LCSC C2909059, package `LED-SMD_6P-L2.0-W2.0-P0.80-TL`)

Pin map from the datasheet + EasyEDA footprint:

| Pin | Signal | Function |
|-----|--------|----------|
| 1 | SDO | Data output |
| 2 | GND | Ground |
| 3 | SDI | Data input |
| 4 | CKI | Clock input |
| 5 | VDD | Power (+5 V) |
| 6 | CKO | Clock output |

Physical pad layout (top view, 2×3 grid, 0.8 mm row pitch):

```
          TOP
  [1 SDO]   [6 CKO]    ← outputs
  [2 GND]   [5 VDD]    ← power
  [3 SDI]   [4 CKI]    ← inputs
        BOTTOM
```

- Left column (top→bottom): 1 SDO · 2 GND · 3 SDI
- Right column (top→bottom): 6 CKO · 5 VDD · 4 CKI
- Inputs (SDI/CKI) sit on the bottom edge, outputs (SDO/CKO) on the top edge — data/clock
  flow straight through the package, which suits daisy-chain routing.

## Controller — Pixelblaze (COTS)

- **Pixelblaze V3 Standard** (ElectroMage) — ✅ settled. 8 channels, 3.3 V logic, web UI
  live-coding (patterns ride for free). **N = 2 chains (settled ✅) — one per wing; no
  Output Expander.**
- **Level shifting:** the Pixelblaze's 3.3 V outputs need 5 V logic per chain — a
  74AHCT125-class shifter module (2 of 4 gates used) at the controller.
- Series R (33–100 Ω) at each chain head only if bench testing shows ringing; ESD/TVS
  optional for a one-off.

## Power hubs — modules, not boards

- **Buck:** MP1584/LM2596-class buck module per cluster (⚠️ buy from a reputable vendor —
  counterfeit MP1584s are common; test each module before install). One hub serves a feather
  cluster: ~0.4 A/feather full white, ~0.08 A @ 20 %.
- **Injection feeds:** fused pigtails from each hub tap the module chains every 4–6 modules.
- **Protection:** fuse per injection feed (ATO inline holder or polyfuse), reverse-polarity
  MDD `SS34` ([C8678](https://www.lcsc.com/product-detail/C8678.html)) on the 12 V input.
- **Form:** perfboard — buck module + fuses + screw terminals. **No data** on the hub.
- **12 V bus:** daisy-chain hub-to-hub; drop-tolerant.
- **Why 12 V (settled):** a 5 V bus can't scale — on a 2 m / 12 AWG reference bus, full-white
  drops ~33 % (color shift; blue dies first) vs ~6 % on 12 V (~1 % @ 20 % brightness). One
  MP1584-class 3 A module covers a hub's cluster (~2–4 A full white).

## Settled parts (module BOM + COTS)

| Item | Choice | Qty | Status | Source |
|------|--------|-----|--------|--------|
| LED (module BOM) | SK9822-EC20, 2020 | ~1260 | ✅ | [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html) |
| Decoupling (module BOM) | Yageo `CC0603KRX7R9BB104`, 100 nF | ~1260 (1/LED) | ✅ | [LCSC C14663](https://www.lcsc.com/product-detail/C14663.html) |
| Connector (module BOM) | JST-GH 4-pin SMD `SM04B-GHS-TB(LF)(SN)` | ~540 | ✅ | [LCSC C189895](https://www.lcsc.com/product-detail/C189895.html) |
| Module PCBs | 4-LED 42×12 mm + 6-LED 62×12 mm, 1-layer flex, panelized | ~270 | ✅ | JLCPCB flex + PCBA |
| Controller | Pixelblaze V3 Standard | 1 | ✅ | [Tindie](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) |
| Level shifter | 74AHCT125-class module (2 channels) | 1 | ⚠️ | TBD |
| Buck | MP1584/LM2596-class module | ~6–8 | ⚠️ | TBD (reputable vendor) |
| Fuse | ATO inline / polyfuse per injection feed | ~10 | ⬜ | TBD |
| Reverse polarity | MDD `SS34`, 3A 40V SMA | 1/hub | ✅ | [LCSC C8678](https://www.lcsc.com/product-detail/C8678.html) |
| Wire | Silicone, colors per wiring legend | — | ⬜ | TBD |

## Open decisions (compact)

- EasyEDA layout + panel sign-off (two module designs) — specs in [modules/](modules/)
- Injection cadence (4 vs 6 modules) after bench test
- Brightness cap value (20 % vs 25 %), tied to the battery budget
- Level-shifter module brand; buck module brand + bench test; fuse rating per feed
- Alula module count (confirm mockup); covert row spans once the layout is drawn

## Deferred (if we ever build more than one)

- Fully parameterized custom feather boards (KiCad 10 + `pcbnew` geometry — 10 mm width,
  length + bend points).
- Custom power-hub PCB and controller carrier.
- Shelved idea: single 6-pin connector per feather with hub-routed data chaining.

## References

- [Module designs](modules/) — shared design core + per-variant specs (4-LED / 6-LED)
- [Connector pinout / wiring legend](../docs/connector-pinout.md) — 4-pin module chain maps + injection rules
- [Battery](../investigations/battery/) — 12 V source sizing
- [Feather lighting](../mechanical/feather/lighting-and-boards.md) — LED map + chain layout
- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
