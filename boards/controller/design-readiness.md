# Controller Board — Design Readiness

Drives the data chains; power distribution lives in the power-hub board. Scale: N chains.

## Locked

- Pixel: SK9822-EC20 (5 V) — locked in [LED segment design-readiness](../led-segment/design-readiness.md).
- Topology: split power/data — data daisy-chains, power from power-hubs (see
  [topology](../../investigations/topology/)).
- Controller drives N `DATA` + `CLK` pairs into the first feather of each chain; feathers
  chain the rest.

## Open decisions

- [ ] MCU choice
- [ ] Number of chain segments (N); grouping of feathers into chains
- [ ] Level shifter part (one per data output)
- [ ] Series R value (33–100 Ω)
- [ ] ESD/TVS per data output
- [ ] Chain timing / clock budget (~1400 LEDs total, ~1400/N per chain)

See [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
