# Controller Board

The wing's brain — drives the data chains. It does **not** distribute power (that's the
power-hub's job). One per wing.

## Idea

- MCU + level shifter (3.3 V → 5 V) drives N `DATA` + `CLK` pairs, each into the first
  feather of a chain segment.
- Feathers daisy-chain data between themselves; the controller only feeds the chain heads.

## Holds (deferred from feathers)

- Level shifter (3.3 V → 5 V) per data output
- Series R (33–100 Ω) per data output
- ESD/TVS per data output

## Connectors

- N data outputs (DATA + CLK + GND), plus MCU + power input.

## Open questions

- MCU choice
- Number of chain segments (N) and how feathers are grouped
- Chain timing / clock budget (~1400 LEDs total, ~1400/N per chain)

See [design readiness](design-readiness.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
