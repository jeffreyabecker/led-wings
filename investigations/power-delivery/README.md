# 12 V → 5 V Power Delivery — Investigation

> Scope: given the pixel is locked to **SK9822-EC20** (5 V, 2-wire DATA+CLK, individually
> addressable) and the source is fixed at **12 V** (wall for dev, 12 V battery for mobility),
> decide how to get 5 V to ~140 feathers. This is the one new problem the SK9822 decision
> creates.

## What's here

- [Conversion options](conversion-options.md) — where the 12 V→5 V step lives (hub vs
  junction vs feather), and the 5 V home-run voltage-drop budget.

## Status

`investigation` — default leaning is **hub-side conversion (per-port buck) + 5 V home-run**,
keeping the feather passive; see [conversion-options.md](conversion-options.md).

## Coupling

- Pixel: locked to SK9822-EC20 (see
  [LED segment design-readiness](../../boards/led-segment/design-readiness.md)).
- Battery: [battery](../battery/) (12 V source, ~500 Wh @ 8 h / 20 %).
- Hub: [controller](../../boards/controller/).
