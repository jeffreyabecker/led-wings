# Controller / Hub Board — Design Readiness

Central hub. Every LED board home-runs one 6-pin cable here; the hub chains the boards in
copper and distributes power. Scale: 140+ boards.

## Locked

- Pixel: SK9822-EC20 (5 V) — locked in [LED segment design-readiness](../led-segment/design-readiness.md).
- Deferred here from boards: level shifter (3.3 V → 5 V), series R, fuse (per port),
  ESD/TVS (per port).
- Serial chain in hub copper: port N's `DO`/`CO` → port N+1's `DI`/`CI`; one DATA + one
  CLK into port 1.

## Open decisions

- [ ] MCU choice
- [ ] Level shifter part (one DATA + CLK pair)
- [ ] Series R value (33–100 Ω)
- [ ] Fuse rating (one per port)
- [ ] ESD/TVS part (per port: DI, CI, DO, CO, VCC)
- [ ] Hub connector family + topology (6-pin JST-PH home-run vs RJ45/Cat5e snowflake) — see below
- [ ] Port count per hub; modular spine vs single board (140+ boards)
- [ ] Power distribution sizing (total current, heavy copper, multiple 5 V inputs)
- [ ] Bypass jumper scheme (port N `DO` → port N+1 `DI`)
- [ ] Chain timing / clock budget (~1400 LEDs cumulative regen delay)

## Undecided — hub connector & topology

Home-run connector family, and whether to use a snowflake (tree) trunk instead of a
per-board home-run. Working assumption is the 6-pin JST-PH per-board home-run; RJ45/Cat5e +
snowflake is under investigation.

- **Cat5 at 5 V — rejected as a shared trunk.** ¼ of the LEDs (~35 boards ≈ 14 A @ full
  white, assuming ~10 LEDs/board) exceeds 24 AWG ampacity (~0.6–1 A/pair safe) and collapses
  on voltage drop (I × L ≤ ~6 A·m with 2 pairs on power). One Cat5 at 5 V ≈ 3–10 boards.
- **Cat5 at 48 V + local buck — viable.** 70 W ÷ 48 V ≈ 1.46 A over 2 pairs (~0.73 A/pair);
  drop ≈ 2.5 V over 20 m. 2 pairs = power, 2 pairs = data (`DI`/`CI`, `DO`/`CO`).
- **Open sub-options:** buck per feather vs per snowflake junction; trunk voltage (24 V vs
  48 V); feathers per trunk; LEDs/board (scales current linearly).

See [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
