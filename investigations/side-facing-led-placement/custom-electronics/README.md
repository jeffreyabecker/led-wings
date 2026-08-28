# Custom electronics — FPC LED strip (Option B)

> Scope: design and build the wing's LED strips ourselves as **custom boards**:
> **SK9822-EC20** (2020-package, SPI) LEDs at **30/m (33.3 mm pitch)** on **5 mm-wide
> boards** cut to per-feather segments. **Baseline material: standard FR-4, thin core
> (0.6–0.8 mm)** — FPC is the fallback if feather curvature requires conformance.
> This is the "Route B" option from the strip-availability investigation.
>
> Why custom instead of stock 144–200/m minis (Route C): **Route C rejected on safety
> grounds** — a dense stock strip keeps its full current capability (worst case ~33 A @ 5 V
> on a firmware bug) on unknown, unverifiable trace sizing; custom boards let us size
> copper, add fusing, and cap brightness with known margins. Custom also delivers the
> exact **5 mm × 30/m** geometry at **0.2 W/LED** (vs 5050's 0.3 W), which drops the
> power budget ~33 %.

## Notes

- [fpc-design.md](fpc-design.md) — FPC layout: trace/routing plan, copper sizing,
  bypass caps, panelization, connectors.
- [assembly-and-cost.md](assembly-and-cost.md) — component BOM, assembly process
  (stencil/reflow), cost estimate, risks.
- [board-inventory.md](board-inventory.md) — panelized SKU subset (B7/B4/B3),
  board counts, panels, JST chain links.

## Key decisions

1. **Component: SK9822-EC20** — the 2020 (2 × 2 mm) package version of SK9822,
   SPI clock+data, 5 V, **0.2 W max (40 mA)** ⚠️ (vs 5050's 0.3 W/60 mA).
   Available at [LCSC (C2909059)](https://www.lcsc.com/product-detail/C2909059.html)
   and [OPSCO](https://www.opsco.com); datasheet from
   [Normand](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf).
   → Full-white power drops 249 W → **~166 W**; 8 h @ 10 % needs **~146 Wh** →
   a single 4S 10000 mAh pack (~800 g) instead of 4S 16000.
2. **Custom board over stock strip** — controlled trace sizing (safety), exact 5 mm
   width × 30/m (2020 part makes the narrow strip unnecessary), per-feather segment
   lengths with test pads. **Material: FR-4 thin core (0.6–0.8 mm) baseline; FPC
   fallback** (see [fpc-design.md](fpc-design.md)).
3. **JST-PH 4-pin connectors at board ends** — chain links and feather-to-bus wiring
   are plug-in cables (VDD/VSS/DI/CI), no solder joints; slim JST-ZH fallback if the
   feather-root profile is tight.
4. **Power safety baked in** — traces sized for full-white current with margin, per-wing
   fusing, firmware brightness cap (see [power-architecture.md](../power-architecture.md)).

## Open items

**Blocking — resolve before layout/ordering:**

- Verify SK9822-EC20 **pinout/pad layout** from the datasheet before starting the
  footprint (QFN-style 2020 pads) — a wrong footprint bricks the panel.
- Confirm EC20 reel price/MOQ at LCSC for ~830 chips.

**Confirm-at-quote — low risk, no design impact:**

- Rigid FR-4 panelization/array rules for our exact boards (V-score break-out) —
  quote/DFM formality; standard rigid tolerances apply (min trace/space 4/4 mil ✅,
  registration ±0.1 mm, copper up to 2 oz ✅ — the FPC 1 oz cap and ±0.2 mm
  registration no longer constrain the design).

## Status

`investigation` — default direction: **custom FR-4 thin-core (0.6–0.8 mm) boards with
SK9822-EC20, reflow-assembled in-house**; 5 mm width, B7/B4/B3 SKU subset, JST-PH 4-pin
at board ends; EC20 pinout + pricing verification pending.
