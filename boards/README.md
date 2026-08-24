# Boards

One folder per board concept. Each board keeps:
- `README.md` — idea/requirements
- `design-readiness.md` — board-specific decisions/readiness
- `selected-parts.md` — board-specific BOM

Shared cross-cutting stuff (e.g. the connector pinout) lives in [`docs/`](../docs/).

| Board | Status | Notes |
|-------|--------|-------|
| [led-segment](led-segment/) | ideation | SK9822 feather board — daisy-chain data + power connector |
| [controller](controller/) | ideation | data source: MCU + level shifter, N chain outputs |

Possible future boards: power-hub (fuse / 12 V→5 V buck + 5 V fan-out), shared under-lit strip
(lesser coverts / leading edge).
