# Wings PCBs

LED lighting PCB project — addressable RGB (SK9822) segments with JST-PH daisy-chain connectors.

## Boards

- [LED segment](boards/led-segment/) — daisy-chainable SK9822 LED board
- [Controller](boards/controller/) — external per-strand driver/protection board

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — canonical JST-PH pinout for all boards

Per-board design concerns and part lists live in each board folder.

## Adding a board

Create `boards/<name>/` with a `README.md` — see [boards/README.md](boards/README.md).
