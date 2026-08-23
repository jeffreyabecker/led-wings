# LED Segment Board

Daisy-chainable addressable LED segment (SK9822-EC20).

## Idea

- SK9822-EC20 LEDs on a (possibly flex) PCB.
- Chain many segments together; each LED regenerates DATA + CLK.

## Connectors (all SMD side-entry, flex-compatible)

- `J_IN` — 4-pin white (GND / DATA / CLK / +5V)
- `J_OUT` — 4-pin distinct color (GND / DATA / CLK / +5V)
- `J_PWR` — 2-pin white (GND / +5V), power injection

## On-board

- SK9822-EC20 LEDs
- Bulk cap per injection point + 100 nF decoupling
- Reverse-polarity protection (required)

## Deferred to controller board

- Series R (DATA/CLK), fuse, ESD/TVS, level shifter

## Open questions

- LEDs per segment
- Power injection interval

See [design concerns](design-concerns.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
