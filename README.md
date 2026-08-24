# Wings PCBs

LED lighting PCB project — addressable RGB (SK9822) "feather" boards: data daisy-chained
feather-to-feather, power fed from local power-hubs.

## Toolchain

- KiCad 10, parameterized via `pcbnew` Python scripting (~70 unique LED board shapes).
- Varies per board: geometry + LED count/positions. Fixed: connectors at "top".

## Boards

- [LED segment](boards/led-segment/) — SK9822 feather board (daisy-chain data + power connector)
- [Controller](boards/controller/) — data source: MCU + level shifter, N chain outputs

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — canonical split power/data pinout for all boards

Per-board design readiness + part lists live in each board folder.

## Investigations

- [Battery](investigations/battery/) — 12 V chemistry + sizing for 8 h @ 20 % mobility
- [Topology](investigations/topology/) — target: split power (hubs) and data (daisy-chain)

## Adding a board

Create `boards/<name>/` with a `README.md` — see [boards/README.md](boards/README.md).
