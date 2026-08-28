# FPC design — custom SK9822-EC20 strip

Target: **5 mm-wide flex PCB, 33.3 mm LED pitch (30/m)**, per-feather segment lengths
(~0.3–0.5 m ⚠️), SK9822-EC20 (2020 package), 5 V SPI. **5 mm width** (not 2 mm) —
the 2020 part makes the narrow FPC unnecessary, and 5 mm removes every routing and
fabrication constraint while still fitting the feather thickness budget (~3 mm angled).

## Layer count

**2-layer — assumed throughout this design.** Rationale:

- The 2020 QFN pads (6 pads under a 2 mm square) leave no trustworthy room to route
  all four long signals (VDD, VSS, DI, CI) plus the DO/CO pass-throughs on one side —
  not with the 4/4 mil floor and ±0.2 mm registration.
- 2 layers give clean separation (power+data top, ground+clock bottom), room for the
  2.0 mm rails, and a bottom-side **ground pour** for SPI signal integrity on the long
  chain.
- Downsides (small cost premium, stiffer) don't matter: 5 mm × ~0.4 m segments mount
  straight in a feather slot, so little flex is needed.

## Routing plan (2-layer FPC)

SK9822 needs six connections per LED: **VDD, VSS, DI, CI, DO, CO**. DO/CO are short
pass-throughs to the *next* LED, so only four traces run the full length — on 5 mm
there is generous room for all of them:

| Trace | Layer | Width ⚠️ | Notes |
|---|---|---|---|
| VDD (power rail) | top | 1.5–2.0 mm | single wide rail carries all LED current |
| DI (data) | top | 0.3 mm | single-ended, 5 V logic |
| VSS (ground) | bottom | 1.5–2.0 mm | full return path |
| CI (clock) | bottom | 0.3 mm | single-ended, 5 V logic |

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
- 1 oz trace capacity (IPC-2221, external) ⚠️: 0.8 mm ≈ ~1.0–1.3 A; **2.0 mm ≈
  ~2.0–2.6 A** (10–20 °C rise).
- **Worst case per segment is set by the buck, not the wing**: each MP1584EN
  current-limits at ~2–3 A, so a rail segment only ever sees ~2–3 A even on a fault.
- **A single 2.0 mm VDD rail covers it** — no via-stitching or dual-layer tricks
  needed on the 5 mm strip; 5 mm width makes the ~2–3 A worst case a non-issue. At
  the 10 % operating point (0.12 A/m) it's pure safety margin.
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

## JLCPCB FPC constraints

- **Min trace / spacing: 4/4 mil (~0.1 mm) with ±0.20 mm positional tolerance —
  confirmed** ✅. Our 0.3 mm signals and 2.0 mm rails sit well above the width floor;
  the ±0.2 mm registration is looser than rigid PCB and drives the 2020 pad design
  (below).
- Minimum FPC board **width** — 5 mm is comfortably above any floor ✅ (the 2 mm
  width question is moot with the 2020 part).
- Copper weight: **max 1 oz (35 µm) on flex — confirmed** ✅; a single 2.0 mm rail
  provides the needed capacity, no dual-layer tricks.

### Design implications of the ±0.2 mm tolerance ⚠️

- The 2020 LED pads are the tightest feature (6 pads around a 2 mm square). With
  ±0.2 mm registration, keep **solder mask between adjacent pads** (mask-defined
  openings) to limit bridging, and size pads conservatively rather than at minimum.
- Stencil alignment for assembly must tolerate ±0.2 mm — plan slightly oversized paste
  apertures, or accept minor skew on the 2 mm parts.
- Panel size limits and panelization rules for flex
  ([capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities),
  [flex panel design guide](https://jlcpcb.com/blog/design-guidelines-flex-pcb-panels)).
