# LED Segment — Design Readiness

> Decision tracker for the LED segment board family (~70 unique boards, parameterized).
>
> **Toolchain:** KiCad 10 · `pcbnew` Python scripting.
> **Varies per board:** board geometry (unique shape) · LED count & positions (unique set).
> **Fixed per board:** power-injection points always at the board's "top".

## Locked

| Decision | Value |
|----------|-------|
| Tool | KiCad 10 + `pcbnew` Python |
| Varies per board | geometry (unique shape), LED count & positions |
| Fixed per board | injection at "top" |
| LED | SK9822-EC20 (C2909059), 5 V, ~40 mA/LED @ full white, 2020 |
| Connectors (SMD side-entry) | `J_IN` 4-pin JST `S4B-PH-SM4-TB` · `J_OUT` 4-pin hanxia `HX PH2.0-4PWT` · `J_PWR` 2-pin JST `S2B-PH-SM4-TB` |
| Pinout | shared [contract](../../docs/connector-pinout.md): data 4-pin GND/DATA/CLK/+5V, power 2-pin GND/+5V |
| Reverse polarity | MDD `SS34` (C8678) in series with VCC — required |
| Decoupling | Yageo `CC0603KRX7R9BB104` (C14663), 100 nF |
| Bulk | Samsung `CL31A476MPHNNNE` (C96123), 47 µF 10V, per injection point |
| Deferred to controller | series R, fuse, ESD/TVS, level shifter |
| Current limit | 2 A per JST-PH circuit |

## Open decisions

### Parameterization (block scripting)
- [ ] How is each board's **geometry** specified? (DXF / SVG / polygon / coordinate list)
- [ ] How are each board's **LED positions** specified? (per-board coordinate list / spacing rules)
- [ ] Define the **"top"** convention for injection points (relative to data direction / board origin)
- [ ] Schematic approach: one parameterized schematic vs PCB-only generation

### Power (highest risk — uncalculated)
- [ ] Trace width / copper weight for the 5 V bus (≤2 A per injection point)
- [ ] Max LEDs per injection point at target brightness (injection interval)
- [ ] Decoupling density: 1×100 nF per LED vs per 2–4

### Layout / mechanical
- [ ] LED orientation (DI toward input) + silkscreen data-direction arrow
- [ ] Connector orientation + cable-exit direction
- [ ] Keep DATA/CLK paired & matched; avoid loop area
- [ ] Termination: pull-down on last board's CO (optional, long chains)
- [ ] Flex specifics: stiffener under SMD connectors, bend radius, coverlay vs soldermask
- [ ] Thermal: copper pours as heat spreaders

### Manufacturing / test
- [ ] Panelization + fiducials
- [ ] Test points (GND/VCC/DATA/CLK, pogo pads)
- [ ] Silkscreen set (IN/OUT, pin-1, polarity, data direction)

### KiCad libraries
- [ ] SK9822-EC20 `.kicad_sym` + `.kicad_mod` (convert from EasyEDA JSON/SVG)
- [ ] hanxia `HX PH2.0-4PWT`: reuse JST 4-pin footprint or create
- [ ] Confirm JST SMD footprints in stock `Connector_JST` lib (present — verify)

### Controller board (parallel)
- [ ] MCU, level shifter, series R, fuse, ESD/TVS
- [ ] Power supply sizing (total current × strands)

## Constraints (why)

- 5 V has almost no headroom: 0.5 V drop = 10% = color shift/flicker (blue dies first). Power path is a bus, not a trace.
- 2 A per JST-PH circuit; ~50 SK9822 LEDs at full white ≈ 2 A → more injection points, not bigger connectors.
- X5R/X7R derate ~40–60% under DC bias → think effective µF, not nominal.
- 2020 package: fine pads, pick-and-place + reflow only.
- Side-entry SMD connectors on flex need a stiffener for solder reliability + mating.
- SK9822 regenerates DATA+CLK per LED; level shifting handled externally.

## References

- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html)
