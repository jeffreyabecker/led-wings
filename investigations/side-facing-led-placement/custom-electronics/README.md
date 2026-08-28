# Custom electronics — FPC LED strip (Option B)

> Scope: design and build the wing's LED strips ourselves as a **custom flex-PCB strip**:
> **SK9822-EC20** (2020-package, SPI) LEDs on a **~2 mm wide FPC at 30/m (33.3 mm pitch)**,
> cut to per-feather segments. This is the "Route B" option from the strip-availability
> investigation.
>
> Why custom instead of stock 144–200/m minis (Route C): **Route C rejected on safety
> grounds** — a dense stock strip keeps its full current capability (worst case ~33 A @ 5 V
> on a firmware bug) on unknown, unverifiable trace sizing; a custom FPC lets us size
> copper, add fusing, and cap brightness with known margins. Custom also delivers the
> exact **2 mm × 30/m** geometry at **0.2 W/LED** (vs 5050's 0.3 W), which drops the
> power budget ~33 %.

## Notes

- [fpc-design.md](fpc-design.md) — FPC layout: trace/routing plan, copper sizing,
  bypass caps, panelization, connectors.
- [assembly-and-cost.md](assembly-and-cost.md) — component BOM, assembly process
  (stencil/reflow), cost estimate, risks.

## Key decisions

1. **Component: SK9822-EC20** — the 2020 (2 × 2 mm) package version of SK9822,
   SPI clock+data, 5 V, **0.2 W max (40 mA)** ⚠️ (vs 5050's 0.3 W/60 mA).
   Available at [LCSC (C2909059)](https://www.lcsc.com/product-detail/C2909059.html)
   and [OPSCO](https://www.opsco.com); datasheet from
   [Normand](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf).
   → Full-white power drops 249 W → **~166 W**; 8 h @ 10 % needs **~146 Wh** →
   a single 4S 10000 mAh pack (~800 g) instead of 4S 16000.
2. **Custom FPC over stock strip** — controlled trace sizing (safety), exact 2 mm
   width × 30/m, per-feather segment lengths with test pads.
3. **Power safety baked in** — traces sized for full-white current with margin, per-wing
   fusing, firmware brightness cap (see [power-architecture.md](../power-architecture.md)).

## Open items

- Verify SK9822-EC20 **pinout/pad layout** from the datasheet before layout (QFN-style
  2020 pads) ✅-pending.
- Verify JLCPCB **FPC capability**: minimum board width (~2 mm?), copper weight
  **capped at 1 oz on flex ✅ (no 2 oz)** — sizing uses dual-layer parallel rails,
  min trace/space, panelization rules
  ([capabilities](https://jlcpcb.com/capabilities/flex-pcb-capabilities),
  [panel design guide](https://jlcpcb.com/blog/design-guidelines-flex-pcb-panels)).
- Confirm EC20 reel price/MOQ at LCSC for ~830 chips.

## Status

`investigation` — default direction: **DIY FPC strip with SK9822-EC20, reflow-assembled
in-house**; parallel check on JLCPCB FPC limits before committing to 2 mm width.
