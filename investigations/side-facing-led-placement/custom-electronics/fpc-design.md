# FPC design — custom SK9822-EC20 strip

Target: **2 mm-wide flex PCB, 33.3 mm LED pitch (30/m)**, per-feather segment lengths
(~0.3–0.5 m ⚠️), SK9822-EC20 (2020 package), 5 V SPI.

## Routing plan (2-layer FPC)

SK9822 needs six connections per LED: **VDD, VSS, DI, CI, DO, CO**. DO/CO are short
pass-throughs to the *next* LED, so only four traces run the full length:

| Trace | Layer | Width ⚠️ | Notes |
|---|---|---|---|
| VDD (power rail) | top | 0.6–0.8 mm | widest trace — carries all LED current |
| DI (data) | top | 0.2–0.3 mm | single-ended, 5 V logic |
| VSS (ground) | bottom | 0.6–0.8 mm | full return path |
| CI (clock) | bottom | 0.2–0.3 mm | single-ended, 5 V logic |

DO→next-DI and CO→next-CI jumpers run **between adjacent LED footprints** (~10–15 mm
long per 33 mm pitch) — short, no length concern at SPI clock speeds.

2020 (2 × 2 mm) pads sit on the LED's underside (QFN-style) ⚠️ — **confirm exact pad
layout from the [SK9822-EC20 datasheet](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
before starting the footprint**; the LCSC [pinout image](https://www.lcsc.com/product-image/C2909059.html)
is the cross-check.

## Copper / current sizing (safety-critical)

- **FPC copper is capped at 1 oz (35 µm)** ✅ — no 2 oz on flex; all sizing uses
  1 oz cross-sections ([copper weight guide](https://jlcpcb.com/help/article/jlcpcb-copper-weight)).
- Per-LED max: 40 mA → **1.2 A/m full white** at 30/m; 0.3 A/m at the 25 % firmware
  cap; 0.12 A/m at the 10 % operating point.
- 1 oz trace capacity (IPC-2221, external) ⚠️: 0.8 mm ≈ ~1.0–1.3 A; 1.2 mm ≈ ~1.8 A
  (10–20 °C rise).
- **Worst case per segment is set by the buck, not the wing**: each MP1584EN
  current-limits at ~2–3 A, so a rail segment only ever sees ~2–3 A even on a fault —
  but that still exceeds a single 0.8 mm trace.
- **Plan for ~3 A worst case**: widen VDD/GND to ~1.2 mm **and** run VDD on both
  layers (top + bottom, via-stitched at each LED) → ~3.5 A combined ⚠️. At the 10 %
  operating point (0.12 A/m) this is pure safety margin, and it keeps the 2 mm strip
  width feasible.
- Power injection: feed VDD/VSS **every segment** (per-feather ~0.3–0.5 m) — segments
  are short, so voltage drop stays negligible; never chain power through feathers.
- **Fusing**: per-wing fuse on the 5 V bus (e.g. ~8 A — above the 25 % cap draw of
  ~6 A/wing, below the bus wiring limit); the per-cluster bucks self-limit their own
  segments. Firmware cap stays as the final layer of defense.

## Bypass capacitors

- One **0402 100 nF** across VDD/VSS per LED ⚠️ (APA102/SK9822 family recommend local
  decoupling; cheap insurance against clock/data glitches on long chains).
- Adds 830 components to place — include in the assembly plan.

## Panelization & connectors

- Panelize strips **side by side** with V-score/mouse-bites for clean break-off at
  feather lengths; add **test pads** (VDD/VSS/DI/CI) at each segment end for the
  post-reflow SPI test.
- Connectorization: **tinned solder pads** (2.54 mm pitch) at each end rather than JST —
  keeps the 2 mm profile and lets us solder thin magnet wire per feather. ⚠️ If JST-PH
  (4-pin) is preferred for field service, it adds ~4 mm of thickness at the feather root.

## JLCPCB constraints to verify ⚠️

- Minimum FPC board **width** (2 mm may be below their floor — if so, accept 3 mm).
- Min trace/space (their rigid PCB floor is ~0.1 mm; FPC similar).
- Copper weight: **max 1 oz (35 µm) on flex — confirmed** ✅; sizing assumes 1 oz
  (dual-layer parallel VDD where more capacity is needed).
- Panel size limits and panelization rules for flex
  ([capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities),
  [flex panel design guide](https://jlcpcb.com/blog/design-guidelines-flex-pcb-panels)).
