# LED Segment (Feather) Board

Addressable LED feather board (SK9822-EC20) — one "feather" of a wing. Data daisy-chains
feather-to-feather; power comes from a local power-hub.

## Idea

- SK9822-EC20 LEDs on a flexible PCB; each LED regenerates DATA + CLK.
- **Data**: `DI`/`CI` in → first LED; last LED's `DO`/`CO` → `DATA OUT` connector to the next
  feather.
- **Power**: separate 2-pin `PWR` connector fed from a nearby power-hub (`+5V`/`GND`).

## Connectors (SMD side-entry, flex-compatible)

- `J_PWR` — 2-pin power in (JST-PH 2.0 mm) — GND / +5V
- `J_IN` — 2-pin data in (JST-GH 1.25 mm) — DI / CI
- `J_OUT` — 2-pin data out (JST-GH 1.25 mm) — DO / CO

Pin maps are the shared [connector pinout](../../docs/connector-pinout.md); exact part
numbers in [selected-parts](selected-parts.md).

## On-board

- SK9822-EC20 LEDs
- Bulk cap + 100 nF decoupling (per-board power)
- Reverse-polarity protection (required)

## Deferred to controller / power-hub

- Series R (DATA/CLK), ESD/TVS, level shifter → controller
- Fuse (per feed), 12 V→5 V buck → power-hub

## Parameterization

- Flexible PCB (target); bends realized as arcs (curved), not sharp corners.
- Fixed width 10 mm; "top" = 0 mm (start of length).
- Per board: overall length (mm) + bend points `(offset, deg)`.
- LEDs: offset (mm) from top to chip center.
- Connectors at the top (the feather base — the only entrance).

## Open questions

- Bend sign/radius conventions
- Max LEDs per board at target brightness (per-board power budget)

See [design readiness](design-readiness.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
