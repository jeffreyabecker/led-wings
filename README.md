# Wings

One-off LED-lit wing costume — two standard SK9822 strip-module PCBs (4-LED / 6-LED, 4-pin
JST each end) chained tip-to-tail, power injected from buck-module power-hubs, driven by a
Pixelblaze.

## Build strategy

- **Two strip-module PCBs, everything else off-the-shelf.** 4-LED (42 × 10 mm) and 6-LED
  (62 × 10 mm) SK9822 modules at 10.4 mm pitch, panelized + assembled at JLCPCB; Pixelblaze V3
  controller; buck-module + fuse power-hubs.
- Fully parameterized custom feather boards (KiCad 10 + `pcbnew`) are deferred to "if we build
  more than one".

## Boards

- [Boards](boards/README.md) — the build plan: module designs + chain layout, controller,
  power hubs, settled parts

## Mechanical

- [Mechanical](mechanical/) — physical wing design: [structural](mechanical/structural/) frame + [feather](mechanical/feather/) geometry

## Shared docs

- [Connector pinout](docs/connector-pinout.md) — pigtail wiring legend (PWR / DATA-IN / DATA-OUT wire pairs + colors)

## Investigations

- [Battery](investigations/battery/) — 12 V chemistry + sizing for 8 h @ 20 % mobility

## Changing the plan

Update [boards/README.md](boards/README.md) — it is the single source of truth for the
electrical build.
