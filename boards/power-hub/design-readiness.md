# Power-Hub Board — Design Readiness

Local power node: 12 V in → 5 V out, one buck per feather cluster.

## Locked

- Topology: split power/data — the power-hub is the 12 V→5 V buck node (see
  [topology](../../investigations/topology/)).
- Pixel: SK9822-EC20 (5 V), passive feathers — no buck on the feather.
- Power-hub: **12 V in → 5 V out, integrated buck**.

## Open decisions

- [ ] Buck part (12 V→5 V) + current rating → determines feathers per hub
- [ ] Feathers per hub (N) — 0.4 A/feather full white, 0.08 A @ 20 %
- [ ] Fuse rating per 5 V output
- [ ] 12 V input connector + reverse-polarity/ESD protection
- [ ] 12 V bus topology (hub-to-hub daisy chain vs star from source)
- [ ] Placement along the wing's top edge

## Constraints (why)

- 12 V bus is drop-tolerant; 5 V only on short hub→feather tails.
- Passive feather stays LED + caps only (no inductor on the 10 mm flex).
- Buck efficiency ~90 %; idle/quiescent draw × hub count matters on battery.

See [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
