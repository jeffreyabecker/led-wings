# Board design — custom SK9822-EC20 strip

Target: **5 mm-wide boards, 33.3 mm LED pitch (30/m)**, per-feather segment lengths
(~0.3–0.5 m ⚠️), SK9822-EC20 (2020 package), 5 V SPI. **Baseline material: standard
FR-4, thin core (0.6–0.8 mm)** — rigid is cheaper, allows 2 oz copper, and has tighter
registration than FPC; the 233 mm × 5 mm sliver stays stiff enough with a thin core.
**FPC is the fallback** only if feather curvature rules out rigid boards.

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

- Per-LED max: 40 mA → **1.2 A/m full white** at 30/m; 0.3 A/m at the 25 % firmware
  cap; 0.12 A/m at the 10 % operating point.
- **Rigid FR-4 allows 2 oz copper** ✅ (the FPC 1 oz cap no longer applies) — 2.0 mm
  rail at 2 oz ≈ ~3–4 A ⚠️ (IPC-2221, external), comfortably above the buck-limited
  worst case.
- **Worst case per segment is set by the buck, not the wing**: each MP1584EN
  current-limits at ~2–3 A, so a rail segment only ever sees ~2–3 A even on a fault.
- Even at 1 oz, a single 2.0 mm rail (~2.0–2.6 A) covers it; 2 oz on rigid is free
  headroom. At the 10 % operating point (0.12 A/m) it's pure safety margin.
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
- **Connector: JST-PH 4-pin (2.0 mm pitch)** at each board end — pinout
  VDD/VSS/DI/CI. Chain links (structure strips, long primaries) and feather-to-bus
  connections become plug-in cables instead of solder joints. Boards carry a male
  header at each end so any two boards link with a female–female cable.
- ⚠️ Profile: JST-PH adds ~3 mm at the board end — plan the feather-root slot to clear
  it (or swap to the slimmer **JST-ZH 1.5 mm** if the 5–7 mm budget is tight).

## Fabrication constraints (rigid FR-4 baseline) ⚠️

- **Thin core: 0.6–0.8 mm** — keeps the 233 × 5 mm sliver stiff without bowing and
  fits the feather thickness budget (~3.7 mm angled at 25° incl. LED ⚠️).
- Min trace/space 4/4 mil ✅; registration ±0.1 mm (tighter than FPC's ±0.2 mm) ✅;
  copper up to 2 oz ✅ — none of the FPC caps constrain the design.
- **Break-out**: rigid panels use V-score/tab routing (no flex panelization rules).
- Sliver fragility: 5 mm-wide rigid boards are brittle at length — handle via the
  panel until break-out; consider 0.8 mm core if warping appears.
- Panel size limits and panelization rules for flex
  ([capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities),
  [flex panel design guide](https://jlcpcb.com/blog/design-guidelines-flex-pcb-panels)).
