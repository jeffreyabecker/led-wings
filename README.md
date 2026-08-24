# Wings PCBs

LED lighting PCB project — addressable RGB (SK9822) "feather" boards: data daisy-chained
feather-to-feather, power fed from local power-hubs.

## Toolchain

- KiCad 10, parameterized via `pcbnew` Python scripting (~76 unique LED board shapes).
- Varies per board: geometry + LED count/positions. Fixed: connectors at "top".

## Boards

- [Boards](boards/README.md) — one consolidated doc: core ideas + settled part numbers for the
  LED segment (feather), shared strip, controller, and power-hub boards

## Mechanical

- [Mechanical](mechanical/) — physical wing design: [structural](mechanical/structural/) frame + [feather](mechanical/feather/) geometry

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — canonical split power/data pinout for all boards

Board core ideas and settled part numbers live in [boards/README.md](boards/README.md).

## Investigations

- [Battery](investigations/battery/) — 12 V chemistry + sizing for 8 h @ 20 % mobility

## Adding a board

Add the new board's core idea to [boards/README.md](boards/README.md) and move parts into its
settled-parts table once they are locked.
