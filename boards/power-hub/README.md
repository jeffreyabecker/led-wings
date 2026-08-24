# Power-Hub Board

Local power-distribution node — **12 V in → 5 V out**, feeding a cluster of nearby feathers.

## Idea

- One 12 V→5 V buck converter per hub, sized for its cluster.
- Fans out `+5V`/`GND` to N feathers over short 2-pin runs (matches the feather `J_PWR`).
- 12 V bus in from the battery/wall source. No data — data is a separate daisy chain.

## Connectors

- 12 V input (bus) — 2-pin or terminal
- N × 2-pin 5 V output — JST `S2B-PH-SM4-TB` (matches feather `J_PWR`)

## Holds

- 12 V→5 V buck + inductor
- Fuse per 5 V output
- Reverse-polarity protection (12 V input)
- ESD/TVS (12 V input)
- Bulk + decoupling caps

## Open questions

- Feathers per hub (N) → buck current rating (0.4 A/feather full white, 0.08 A @ 20 %)
- Buck part (MP2315 / MP1584-class vs larger)
- 12 V bus topology: daisy-chain hub-to-hub vs star from the source
- Placement along the wing's top edge

See [design readiness](design-readiness.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
