# Boards

One folder per board concept. Each board keeps:
- `README.md` — idea/requirements
- `design-readiness.md` — board-specific decisions/readiness
- `selected-parts.md` — board-specific BOM

Shared cross-cutting stuff (e.g. the connector pinout) lives in [`docs/`](../docs/).

| Board | Status | Notes |
|-------|--------|-------|
| [led-segment](led-segment/) | ideation | SK9822 single-connector feather board |
| [controller](controller/) | ideation | central hub: chaining + power distribution |

Possible future boards: modular hub spine / power-distribution backplane.
