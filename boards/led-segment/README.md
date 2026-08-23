# LED Segment Board

Daisy-chainable addressable LED segment (SK9822-EC20).

## Idea

- SK9822-EC20 LEDs on a (possibly flex) PCB.
- Chain many segments together; each LED regenerates DATA + CLK.

## Connectors (SMD side-entry, flex-compatible)

- `J_IN` — IN role, 4-pin, white — JST `S4B-PH-SM4-TB`
- `J_OUT` — OUT role, 4-pin, distinct color — hanxia `HX PH2.0-4PWT`
- `J_PWR` — PWR role, 2-pin, white — JST `S2B-PH-SM4-TB`

Pin maps are the shared [connector pinout](../../docs/connector-pinout.md); exact part numbers in [selected-parts](selected-parts.md).

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
