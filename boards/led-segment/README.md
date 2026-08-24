# LED Segment Board

Single-connector addressable LED board (SK9822-EC20) — one "feather" of a wing. Home-runs
one 6-pin cable to the central hub; no board-to-board chaining.

## Idea

- SK9822-EC20 LEDs on a flexible PCB; each LED regenerates DATA + CLK.
- Every board has **one 6-pin port** carrying power + data/clock in + data/clock out back
  to the hub. The hub owns the serial chain (see [controller](../controller/)).

## Connector (SMD side-entry, flex-compatible)

- `J1` — single 6-pin port to hub — JST `S6B-PH-SM4-TB` ([C54582918](https://www.lcsc.com/product-detail/C54582918.html))

Pin map is the shared [connector pinout](../../docs/connector-pinout.md); exact part numbers
in [selected-parts](selected-parts.md).

## On-board

- SK9822-EC20 LEDs (`DI`/`CI` → first LED; last LED's `DO`/`CO` → connector return)
- Bulk cap + 100 nF decoupling (per-board power)
- Reverse-polarity protection (required)

## Deferred to hub (controller board)

- Series R (DATA/CLK), fuse (per port), ESD/TVS, level shifter (one DATA+CLK pair)

## Parameterization

- Flexible PCB (target); bends realized as arcs (curved), not sharp corners.
- Fixed width 10 mm; "top" = 0 mm (start of length).
- Per board: overall length (mm) + bend points `(offset, deg)`.
- LEDs: offset (mm) from top to chip center.
- Single 6-pin port at the top.

## Open questions

- Bend sign/radius conventions
- Max LEDs per board at target brightness (per-board power budget)

See [design readiness](design-readiness.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
