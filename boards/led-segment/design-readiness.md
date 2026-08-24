# LED Segment — Design Readiness

> Decision tracker for the LED segment board family (~70 unique boards, parameterized).
>
> **Toolchain:** KiCad 10 · `pcbnew` Python scripting.
> **Board type:** flexible PCB (FPC) — target · bends realized as arcs.
> **Varies per board:** geometry (length mm + bend points) · LED offsets from top.
> **Fixed per board:** width 10 mm · top = 0 mm · 6-pin port at top.
>
> Topology: every board home-runs one 6-pin cable to the central hub (no board-to-board
> chaining). See [connector pinout](../../docs/connector-pinout.md) and
> [controller](../controller/).

## Locked

| Decision | Value |
|----------|-------|
| Tool | KiCad 10 + `pcbnew` Python |
| Board type | flexible PCB (FPC) — target |
| Varies per board | geometry (length + bend points), LED offsets from top |
| Fixed per board | 6-pin port at top (0 mm) |
| Board width | 10 mm (fixed) |
| "Top" | 0 mm = start of board length |
| Geometry spec | overall length (mm) + bend points `(offset, deg)` |
| Bend realization | arcs (curved), not sharp corners — goal |
| LED placement | offset (mm) from top to chip center |
| Topology | one 6-pin port per board → central hub; hub chains in copper (140+ boards) |
| LED | SK9822-EC20 (C2909059), 5 V, ~40 mA/LED @ full white, 2020 |
| Connector (SMD side-entry) | `J1` 6-pin JST `S6B-PH-SM4-TB` ([C54582918](https://www.lcsc.com/product-detail/C54582918.html)) |
| Pinout | shared [contract](../../docs/connector-pinout.md): 6-pin GND/DI/CI/DO/CO/+5V |
| Data path | `DI`/`CI` → first LED; last LED's `DO`/`CO` → connector (return to hub) |
| Reverse polarity | MDD `SS34` (C8678) in series with VCC — required |
| Decoupling | Yageo `CC0603KRX7R9BB104` (C14663), 100 nF |
| Bulk | Samsung `CL31A476MPHNNNE` (C96123), 47 µF 10V, per board |
| Deferred to hub | series R, fuse (per port), ESD/TVS, level shifter (one DATA+CLK pair) |
| Current limit | 2 A per 6-pin circuit (one board per port — well under) |

## Open decisions

### Parameterization (block scripting)
- [ ] Bend **sign convention** for `deg` (clockwise vs counterclockwise)
- [ ] Bend **radius**: sharp polyline vs radiused bends (flex minimum bend radius)
- [ ] LED **lateral** position across the 10 mm width (centered? fixed offset?)
- [ ] Connector placement: single `J1` at top — confirm orientation
- [ ] LED orientation follows local strip direction (DI toward top)?
- [ ] Schematic approach: one parameterized schematic vs PCB-only generation

### Power (per-board, no injection)
- [ ] Trace width / copper weight for the per-board 5 V path (single board's current)
- [ ] Max LEDs per board at target brightness (per-board power budget)
- [ ] Decoupling density: 1×100 nF per LED vs per 2–4

### Layout / mechanical
- [ ] LED orientation (DI toward input) + silkscreen data-direction arrow
- [ ] Connector orientation + cable-exit direction (toward hub)
- [ ] Keep DI/CI and DO/CO pairs matched; avoid loop area
- [ ] Termination: hub terminates final port's `DO`/`CO` (optional)
- [ ] Flex specifics: stiffener under SMD connector, bend radius, coverlay vs soldermask
- [ ] Thermal: copper pours as heat spreaders

### Manufacturing / test
- [ ] Panelization + fiducials
- [ ] Test points (GND/VCC/DI/CI/DO/CO, pogo pads)
- [ ] Silkscreen set (pin-1, polarity, data direction)

### KiCad libraries
- [ ] SK9822-EC20 `.kicad_sym` + `.kicad_mod` (convert from EasyEDA JSON/SVG)
- [ ] 6-pin JST `S6B-PH-SM4-TB` footprint — confirm in stock `Connector_JST` lib or create

### Controller / hub (parallel)
- [ ] MCU, level shifter (one pair), series R, per-port fuse, ESD/TVS
- [ ] Hub port count (140+ boards → modular spine / multiple hubs)
- [ ] Power distribution sizing (total current × boards)
- [ ] Chain timing / clock budget (~1400 LEDs cumulative regen delay)

## Constraints (why)

- 5 V has almost no headroom: 0.5 V drop = 10% = color shift/flicker (blue dies first). Each
  home-run carries only its own board's current, so per-board drop is small; the hub owns
  distribution.
- 2 A per 6-pin circuit; one board per port, so per-port current is far below the limit.
- X5R/X7R derate ~40–60% under DC bias → think effective µF, not nominal.
- 2020 package: fine pads, pick-and-place + reflow only.
- Side-entry SMD connector on flex needs a stiffener for solder reliability + mating.
- SK9822 regenerates DATA+CLK per LED; the chain is serial and driven from the hub (one
  DATA + one CLK), so `DO`/`CO` must return to the hub.
- ~1400 LEDs of cumulative regen delay across the chain → keep the hub's SPI clock
  conservative.

## References

- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html)
