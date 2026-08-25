# Wings

One-off LED-lit wing costume — off-the-shelf SK9822 strips cut into per-feather chunks, data
daisy-chained chunk-to-chunk, power fed from buck-module power-hubs, driven by a Pixelblaze.

## Build strategy

- **Off-the-shelf electrical system** — no custom PCBs for this build. SK9822 96 LED/m strips
  cut to per-feather LED counts; Pixelblaze V3 controller; buck-module + fuse power-hubs.
- Custom boards (KiCad 10 + `pcbnew` parameterized feathers) are deferred to "if we build
  more than one".

## Boards

- [Boards](boards/README.md) — the build plan: strip-chunk cut table, covert rows, controller,
  power hubs, settled COTS parts

## Mechanical

- [Mechanical](mechanical/) — physical wing design: [structural](mechanical/structural/) frame + [feather](feather/) geometry

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — pigtail wiring legend (PWR / DATA-IN / DATA-OUT wire pairs + colors)

## Investigations

- [Battery](investigations/battery/) — 12 V chemistry + sizing for 8 h @ 20 % mobility

## Changing the plan

Update [boards/README.md](boards/README.md) — it is the single source of truth for the
electrical build.
