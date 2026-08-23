# Controller Board — Design Readiness

External, one per strand. Drives DATA + CLK into the first segment's `J_IN`.

## Locked

- Deferred here from segments: level shifter (3.3 V → 5 V), series R, fuse, ESD/TVS.

## Open decisions

- [ ] MCU choice
- [ ] Level shifter part
- [ ] Series R value (33–100 Ω)
- [ ] Fuse rating (one per strand / injection feed)
- [ ] ESD/TVS part
- [ ] Output connector (4-pin PH, matches segment `J_IN`)
- [ ] Number of strands / outputs per controller

See [parts](selected-parts.md) · [connector pinout](../../docs/connector-pinout.md).
