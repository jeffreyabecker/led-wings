# LED Segment — Design Readiness

> Decision tracker for the LED segment board family (~70 unique boards, parameterized).
>
> **Toolchain:** KiCad 10 · `pcbnew` Python scripting.
> **Board type:** flexible PCB (FPC) — target · bends realized as arcs.
> **Varies per board:** geometry (length mm + bend points) · LED offsets from top.
> **Fixed per board:** width 10 mm · top = 0 mm · connectors at top.
>
> Topology: data daisy-chains feather-to-feather; power fans out from local power-hubs. See
> [topology](../../investigations/topology/) and [connector pinout](../../docs/connector-pinout.md).

## Locked

| Decision | Value |
|----------|-------|
| Tool | KiCad 10 + `pcbnew` Python |
| Board type | flexible PCB (FPC) — target |
| Varies per board | geometry (length + bend points), LED offsets from top |
| Fixed per board | connectors at top (0 mm) |
| Board width | 10 mm (fixed) |
| "Top" | 0 mm = start of board length |
| Geometry spec | overall length (mm) + bend points `(offset, deg)` |
| Bend realization | arcs (curved), not sharp corners — goal |
| LED placement | offset (mm) from top to chip center |
| Topology | data daisy-chain feather→feather; power from local power-hub |
| LED | SK9822-EC20 (C2909059), 5 V, ~40 mA/LED @ full white, 2020 |
| Connectors (SMD side-entry) | `J_PWR` 2-pin + `J_IN` 3-pin + `J_OUT` 3-pin (part numbers TBD) |
| Pinout | shared [contract](../../docs/connector-pinout.md): PWR GND/+5V · DATA-IN GND/DI/CI · DATA-OUT GND/DO/CO |
| Data path | `DI`/`CI` → first LED; last LED's `DO`/`CO` → `DATA OUT` → next feather |
| Reverse polarity | MDD `SS34` (C8678) in series with VCC — required |
| Decoupling | Yageo `CC0603KRX7R9BB104` (C14663), 100 nF |
| Bulk | Samsung `CL31A476MPHNNNE` (C96123), 47 µF 10V, per board |
| Deferred | series R + ESD/TVS + level shifter → controller; fuse + buck → power-hub |
| Current limit | 2 A per JST-PH circuit (per-feather power run is far under) |

## Open decisions

### Parameterization (block scripting)
- [ ] Bend **sign convention** for `deg` (clockwise vs counterclockwise)
- [ ] Bend **radius**: sharp polyline vs radiused bends (flex minimum bend radius)
- [ ] LED **lateral** position across the 10 mm width (centered? fixed offset?)
- [ ] Connector placement: `J_PWR`/`J_IN`/`J_OUT` at top (feather base) — confirm orientation
- [ ] LED orientation follows local strip direction (DI toward top)?
- [ ] Schematic approach: one parameterized schematic vs PCB-only generation

### Power (per-board, from power-hub)
- [ ] Trace width / copper weight for the per-board 5 V path (single board's current)
- [ ] Max LEDs per board at target brightness (per-board power budget)
- [ ] Decoupling density: 1×100 nF per LED vs per 2–4

### Layout / mechanical
- [ ] LED orientation (DI toward input) + silkscreen data-direction arrow
- [ ] Connector orientation + cable-exit direction (`DATA OUT` toward next feather, `PWR` toward power-hub)
- [ ] Keep DI/CI and DO/CO pairs matched; avoid loop area
- [ ] Termination: last feather's `DATA OUT` is unused (end of chain)
- [ ] Flex specifics: stiffener under SMD connector, bend radius, coverlay vs soldermask
- [ ] Thermal: copper pours as heat spreaders

### Manufacturing / test
- [ ] Panelization + fiducials
- [ ] Test points (GND/VCC/DI/CI/DO/CO, pogo pads)
- [ ] Silkscreen set (pin-1, polarity, data direction)

### KiCad libraries
- [ ] SK9822-EC20 `.kicad_sym` + `.kicad_mod` (convert from EasyEDA JSON/SVG)
- [ ] 2-pin + 3-pin JST-PH footprints (`S2B`/`S3B`-PH-SM4-TB) — confirm in stock lib or create

### Controller / power-hub (parallel)
- [ ] Controller: MCU, level shifter (one pair), series R, ESD/TVS; N chain outputs
- [ ] Power-hub: fuse per feed, 12 V→5 V buck (if 12 V bus), fan-out count
- [ ] Chain segmentation (N) + power-hub placement
- [ ] Chain timing / clock budget (~1400 LEDs cumulative regen delay)

## Constraints (why)

- 5 V has almost no headroom: 0.5 V drop = 10% = color shift/flicker (blue dies first). Each
  power run carries only its own board's current, so per-board drop is small; the power-hub
  owns distribution.
- 2 A per JST-PH circuit; one feather per power feed, so per-feed current is far below the limit.
- X5R/X7R derate ~40–60% under DC bias → think effective µF, not nominal.
- 2020 package: fine pads, pick-and-place + reflow only.
- Side-entry SMD connector on flex needs a stiffener for solder reliability + mating.
- SK9822 regenerates DATA+CLK per LED; the chain is serial, so `DO`/`CO` feed the next
  feather (daisy chain), and the last feather's `DATA OUT` is unused.
- ~1400 LEDs of cumulative regen delay → segment into several chains and keep the SPI clock
  conservative.

## References

- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html)
