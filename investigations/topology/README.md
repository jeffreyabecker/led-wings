# Topology — Investigation

> Scope: how data and power reach the ~140 feather boards across the wing. Recorded as the
> project's **target** topology (see [target-topology.md](target-topology.md)).

## What's here

- [Target topology](target-topology.md) — the decided split (daisy-chain data + power-hubs).
- [Power-hub bus voltage](power-hub.md) — why 12 V→5 V (drop budget + buck comparison).

## Status

`target` — power and data are split: **data daisy-chains** feather-to-feather, **power fans
out** from local power-hubs.

## Coupling

- [Power-hub](../../boards/power-hub/) — the 12 V→5 V buck node.
- [Battery](../battery/) — 12 V source.
