# Controller Board

External, one per strand.

## Idea

- Level-shifts controller logic to 5 V, drives DATA + CLK into the first segment's `J_IN`.

## Holds (deferred from segments)

- Level shifter (3.3 V → 5 V)
- Series R on DATA + CLK output (33–100 Ω)
- Fuse / polyfuse (one per strand / injection feed)
- ESD/TVS on DATA, CLK, VCC

## Open questions

- Controller MCU choice
- Number of strands / outputs per controller

See [design concerns](design-concerns.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
