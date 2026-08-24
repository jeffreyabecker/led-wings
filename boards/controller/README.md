# Controller / Hub Board

Central hub — one per wing (or a modular spine across many). Every LED board home-runs a
single 6-pin cable here; the hub owns routing, chaining, power distribution, and protection.

## Idea

- One 6-pin port per LED board. Chains port N's `DO`/`CO` → port N+1's `DI`/`CI` in copper,
  so one `DATA` + one `CLK` (level-shifted 3.3 → 5 V) drives the whole chain (140+ boards).
- Distributes 5 V to every port through a per-port fuse.

## Holds (deferred from boards)

- Level shifter (3.3 V → 5 V) on the single DATA + CLK pair into port 1
- Series R (33–100 Ω) on the DATA + CLK output
- Fuse / polyfuse per port
- ESD/TVS per port (DI, CI, DO, CO, VCC)
- Per-hop bypass jumper (port N `DO` → port N+1 `DI`) for field repair

## Connectors

- One 6-pin port per board (matches the board's `J1`), plus MCU + power inputs.

## Open questions

- MCU choice
- Port count per hub (140+ boards → modular spine / multiple hubs?)
- Connector density + topology: 6-pin JST-PH home-run vs RJ45/Cat5e snowflake (48 V + buck) — undecided
- Power distribution sizing (total current, heavy copper, multiple 5 V inputs)
- Chain order: fixed in copper vs reconfigurable; bypass jumper scheme
- Chain timing / clock budget (~1400 LEDs cumulative regen delay)

See [design readiness](design-readiness.md) · [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
