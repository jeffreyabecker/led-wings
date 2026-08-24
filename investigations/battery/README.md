# Battery — Investigation

> Scope: pick the 12 V battery that powers the system for mobility, sized for the planned
> runtime, and matched to the 12 V→5 V buck that feeds the SK9822-EC20 pixels.

The system runs off a fixed **12 V** source — a wall supply for development, a **12 V
battery** for mobility. The pixel is locked to the SK9822-EC20 (5 V), fed through a
12 V→5 V buck, so the battery only needs to stay above the buck's input dropout (~6–7 V),
not a pixel-string voltage floor.

## What's under investigation

- [Battery options](options.md) — lead-acid vs 3S/4S Li-ion vs LiFePO4: voltage range,
  energy density, cycle life, cost, safety, and an 8 h @ 20 % sizing.

## Status

`investigation` — default recommendation is **4S LiFePO4 (12.8 V nominal)**; see
[options.md](options.md) for the bottom line and open items.
