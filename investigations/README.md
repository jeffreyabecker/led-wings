# Investigations

Non-board design investigations — architecture, part-selection, and cost questions that
don't yet have their own board folder. Each investigation keeps a `README.md` (scope +
decision context) plus one or more analysis notes.

| Investigation | Status | Question |
|---------------|--------|----------|
| [Battery](battery/) | investigation | Which 12 V battery (chemistry + size) powers 8 h @ 20 % for mobility? |
| [Diffuser halo](diffuser-halo/) | investigation | How to make a thin, directional, resin-free diffuser bent into a halo ring? |
| [Side-facing LED placement](side-facing-led-placement/) | investigation | Where do edge-lit strips sit (distance/angle/density) for ≤ 7 mm feathers with an opaque foam top? |
| [Wing bones](wing-bones/) | investigation | Bone-structure layout + backplate: angles, heights, humerus, harness geometry |

## Conventions

- Status: `investigation` (in progress) · `target` (decided direction) · `recommended` · `rejected` · `superseded`.
- Cite the source for every spec or price; mark estimates `⚠️` vs confirmed `✅`.
- A recommendation here is an *input* to the [boards doc](../boards/README.md), not a locked
  decision. Locking decisions still happens there.
