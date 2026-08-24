# Wings PCBs

LED lighting PCB project — addressable RGB (SK9822) "feather" boards that home-run a single
6-pin cable to a central hub.

## Toolchain

- KiCad 10, parameterized via `pcbnew` Python scripting (~70 unique LED board shapes).
- Varies per board: geometry + LED count/positions. Fixed: single 6-pin port at "top".

## Boards

- [LED segment](boards/led-segment/) — single-connector SK9822 feather board
- [Controller](boards/controller/) — central hub: chaining, power distribution, protection

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — canonical 6-pin home-run pinout for all boards

Per-board design readiness + part lists live in each board folder.

## Investigations

- [Battery](investigations/battery/) — 12 V chemistry + sizing for 8 h @ 20 % mobility
- [Power delivery](investigations/power-delivery/) — 12 V→5 V conversion and distribution to
  ~140 SK9822-EC20 feathers

## Adding a board

Create `boards/<name>/` with a `README.md` — see [boards/README.md](boards/README.md).
