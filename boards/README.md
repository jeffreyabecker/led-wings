# Boards — Off-the-Shelf Build Plan (one-off)

> **Strategy (settled ✅):** this is a **one-off build** — the electrical system is assembled
> from off-the-shelf SK9822 strips and modules. **No custom PCBs for this build**; the
> parameterized custom-board plan (KiCad + `pcbnew`) and the 6-pin hub-routed idea are
> **deferred** to "if we ever build more than one".
>
> Status: ✅ settled · ⚠️ to confirm · ⬜ TBD.

| Role | Status | Implementation |
|------|--------|----------------|
| Feather lighting | ✅ | SK9822 strip chunks (96 LED/m), one cut per lit feather |
| Covert strip rows | ✅ | Continuous SK9822 strip spans, one cut per row |
| Controller | ✅ | Pixelblaze V3 + 74AHCT125 level shifter (COTS modules) |
| Power hub | ✅ | Buck modules + fuse blocks on perfboard |

## System (locked)

- **Split power/data.** Data daisy-chains feather→feather (pigtails) from one central
  Pixelblaze driving **both wings**; power fans out from hub clusters on a 12 V bus. 5 V
  exists only on the short hub→feather runs.
- **Controller:** Pixelblaze V3 Standard (ElectroMage) — ESP32, 8 data channels, 3.3 V logic.
  **Segmentation (settled ✅): N = 2 chains — one per wing** (all feathers + covert rows of
  that wing). No Output Expander.
- **Pixels:** ~1270 LEDs total both wings (see
  [feather lighting](../feather/lighting-and-boards.md)). Chain budget ≈ 635
  LEDs/channel on 2 channels — a full frame at 8 MHz SPI ≈ 2.5 ms, well inside any pattern
  frame rate.
- **Routing:** the two chains (one per wing) run along the wing's **top edge** (the feather
  bases — the only cable entrance); hubs sit along the same edge feeding short 5 V runs into
  clusters.

## LED medium — SK9822 strip

- **Strip:** SK9822 **96 LED/m** (≈10.4 mm pitch), **10 mm wide**, 5050 — the near-exact
  match to the 10 mm-pitch map. ⚠️ Source TBD (AliExpress/Alibaba 96/m listings; validate one
  reel before ordering the rest). **Fallback:** 144/m with a ~7 mm diffuser gap (spacing ≤ 2×
  gap keeps the glow smooth).
- **Feather = cut chunk.** One chunk per lit feather, cut per-LED (every LED carries its own
  chip). LED count = exposed-tip map + 2-LED bleed, at 10.4 mm pitch — same counts as the
  10 mm-pitch map:

  | Group | Exposed (cm) | Bleed | Chunk LEDs | Chunk length |
  |-------|-------------:|------:|-----------:|-------------:|
  | Primaries P1–P10 | 15 | +2 | 17 | ~17.7 cm |
  | Secondaries S1–S12 | 12 | +2 | 14 | ~14.6 cm |
  | Tertials T1–T4 | 10 | +2 | 12 | ~12.5 cm |
  | Greater coverts GC1–GC12 | 8 | +2 | 10 | ~10.4 cm |
  | Alula A-B/A-T | ~8 ⚠️ | +2 | ~10 ⚠️ | ~10.4 cm |

- **Chunk termination (settled ✅):** 6 stub wires soldered per chunk — `+5V`/`GND` (power,
  from a hub), `DI`/`CI` (data in), `DO`/`CO` (data out to the next feather) — then
  **2-pin JST-PH crimped pigtails**: female `PHR-2` on power-in and data-in, a male plug
  (PH header) on data-out, so every jumper is female–female. Wire pairs + colors are the
  [wiring legend](../docs/connector-pinout.md); parts + crimp procedure in
  [pigtail crimping](../docs/pigtail-crimping.md). Epoxy/glue strain relief over every pad
  set; bench-test each chunk before mounting (a bad joint darkens the whole downstream chain).
- **Covered base:** no strip at all — only the exposed tip + bleed is lit, so there are no
  hidden LEDs (and no idle-current waste).
- **Limits:** a 17-LED chunk ≈ 0.68 A full white — strip copper handles it easily; power
  pigtails budgeted at 2 A.

## Covert strip rows

- One **continuous strip span per row** (median / lesser / marginal) — no cuts except row
  length, one common LED orientation by construction. The scallop silhouette lives in the
  overlay/diffuser, **not** in the strip.
- **Wiring per row:** `PWR` + `DI`/`CI` at the row head; `DO`/`CO` at the tail → next row's
  head (or its own chain).
- **Rows (working ⚠️):** median ~28 cm (~27 LEDs), lesser ×2 ~28 cm, marginal ~28 cm.
  Full-white per row ≈ 1.1 A — feed at the row head; mid-span power injection only if the
  bench shows drop.

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
- **Protection:** fuse per 5 V feed (ATO inline holder or polyfuse), reverse-polarity MDD
  `SS34` ([C8678](https://www.lcsc.com/product-detail/C8678.html)) on the 12 V input.
- **Form:** perfboard — buck module + fuses + screw terminals. **No data** on the hub.
- **12 V bus:** daisy-chain hub-to-hub; drop-tolerant.
- **Why 12 V (settled):** a 5 V bus can't scale — on a 2 m / 12 AWG reference bus, full-white
  drops ~33 % (color shift; blue dies first) vs ~6 % on 12 V (~1 % @ 20 % brightness). One
  MP1584-class 3 A module covers a hub's cluster (~2–4 A full white).

## Settled parts (COTS)

| Item | Choice | Qty | Status | Source |
|------|--------|-----|--------|--------|
| LED strip | SK9822 96 LED/m, 10 mm wide, 5050 | ~15 m (3×5 m reels) | ⚠️ | [Alibaba 30/60/96/144 listing](https://www.alibaba.com/product-detail/Individually-Addressable-APA102-SK9822-30-60_1601370513576.html) |
| Controller | Pixelblaze V3 Standard | 1 | ✅ | [Tindie](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) |
| Level shifter | 74AHCT125-class module (3.3 V → 5 V, 2 channels) | 1 | ⚠️ | TBD |
| Buck | MP1584/LM2596-class module | ~6–8 | ⚠️ | TBD (reputable vendor) |
| Fuse | ATO inline / polyfuse per 5 V feed | ~10 | ⬜ | TBD |
| Reverse polarity | MDD `SS34`, 3A 40V SMA | 1/hub | ✅ | [LCSC C8678](https://www.lcsc.com/product-detail/C8678.html) |
| PH contact (pigtails) | JST `SPH-002T-P0.5`, 24–28 AWG | ~550 | ⬜ | DigiKey / Mouser / AliExpress |
| PH housing (pigtails) | JST `PHR-2`, 2-pin | ~280 | ⬜ | same |
| PH header (pigtails) | JST `B2B-PH-K-S`, 2-pin | ~120 | ⬜ | same |
| Crimp tool | IWISS/iCrimp SN-28B (JST PH/XH/VH) | 1 | ⬜ | Amazon |
| Wire | Silicone — 24 AWG red/black (power), 26–28 AWG yellow/green/orange/blue (data) | ~15 m each | ⬜ | TBD |

## Open decisions (compact)

- Strip vendor + 96/m sourcing; fallback 144/m + 7 mm gap
- Diffuser gap validation on 5050 emitters (prototype with the first reel)
- Level-shifter module brand (74AHCT125-class)
- Buck module brand + bench test; fuse rating per feed
- Alula chunk size (confirm mockup); covert row spans once the layout is drawn

## Deferred (if we ever build more than one)

- Custom feather boards — 2020 SK9822 (`SK9822-EC20`, C2909059), JST connectors,
  parameterized KiCad 10 + `pcbnew` geometry (10 mm width, length + bend points).
- Custom power-hub PCB and controller carrier.
- Shelved idea: single 6-pin power+data connector per feather with hub-routed data chaining.

## References

- [Connector pinout / wiring legend](../docs/connector-pinout.md) — PWR / DATA-IN / DATA-OUT wire pairs + colors
- [Pigtail crimping](../docs/pigtail-crimping.md) — JST-PH parts, counts, crimp procedure
- [Battery](../investigations/battery/) — 12 V source sizing
- [Feather lighting](../feather/lighting-and-boards.md) — LED map + chunk counts
- [SK9822 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
