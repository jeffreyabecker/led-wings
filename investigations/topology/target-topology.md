# Target Topology — Separate Power and Data

> **Status: target (decided).** Supersedes the 6-pin home-run topology. Power and data are
> split into independent distribution paths.

## Decision

- **Data** — daisy-chained feather-to-feather. The controller drives one (or a few) `DI`/`CI`
  pair into the first feather; each feather's `DO`/`CO` feeds the next feather's `DI`/`CI`.
- **Power** — separate **power-hubs** (distribution nodes) feed `+5V`/`GND` to nearby feathers
  over short 2-wire runs. Bus voltage into the hubs is TBD (5 V vs 12 V + local buck).
- **Per feather** — a power connector plus data-IN and data-OUT connectors, instead of one
  combined 6-pin home-run connector.

## Why split

- Data is serial (regenerated per LED); power is a fan-out. Splitting them lets each scale on
  its own terms: add a power-hub where a cluster needs it, keep the data chain thin and short.
- The controller shrinks from a 140-port chaining hub to MCU + level shifter + N data outputs.
- Long power runs can use a higher bus voltage (12 V) and buck at the hub, so 5 V only exists
  on the short hub→feather tails — removing the 5 V drop ceiling from long cables.

## Physical layout (drives the data routing)

- Feathers are **not** in a strict linear sequence — primaries, secondaries and greater
  coverts form a layered 2-D array.
- **Primaries / secondaries / greater coverts** — individual feather boards. Each has a
  logical **top** (base — the only cable entrance) and a **bottom** (tip). All connectors
  enter at the top.
- **Lesser coverts / leading-edge feathers** — may be practical to light **from underneath
  with a shared strip**: a different board type (continuous strip), not individual feathers.

## Consequences

- The data chain routes along the wing's **top edge** (the feather bases), entering each
  feather at its top. That is a 2-D "snake", so the wing is **segmented into several chains**
  (controller drives N `DATA`+`CLK` outputs) rather than one ~1400-LED chain.
- Power-hubs sit along the same top edge and feed short 5 V runs into feather clusters.
- The **shared strip** (lesser coverts / leading edge) is its own chain segment + its own
  power feed; it does not interleave with the individual-feather chain.

## Board-type implications

| Board | Role |
|-------|------|
| Feather (primaries/secondaries/greater coverts) | existing `led-segment` concept, now with 3 connectors: PWR + DATA-IN + DATA-OUT |
| Shared strip (lesser coverts / leading edge) | **new** — continuous under-lit strip |
| Power-hub | **new** — fuse/junction (5 V bus) or 12 V→5 V buck (12 V bus) |
| Controller | simplified — MCU + level shifter + N data outputs, no port array |

## Open sub-decisions

- [ ] Power-hub bus voltage: 5 V (hub = fuse/junction only) vs 12 V (hub = 12 V→5 V buck).
- [ ] Number of data chains / segmentation; how feathers are grouped.
- [ ] Connector scheme + pinouts: PWR (2-pin) · DATA-IN (GND/DI/CI) · DATA-OUT (GND/DO/CO).
- [ ] Failure handling: per-feather `DI`→`DO` bypass vs accept a segment going dark on one
      dead feather.
- [ ] Shared-strip board: its own `boards/` entry and how it joins the chain.
- [ ] Rewrite `docs/connector-pinout.md` for the split power/data contract (replaces the
      6-pin home-run contract).

## References

- [Battery](../battery/) — 12 V source, ~710 Wh @ 8 h / 20 % (2000 px).
- [Connector pinout](../../docs/connector-pinout.md) — current 6-pin home-run contract (to be
  replaced).
