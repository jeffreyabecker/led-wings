# Generated feather-strip schematics

Build artifacts — **do not hand-edit.** Regenerate with:

```
python tools/gen_schematic.py --all        # all 6 SKUs (7–12 LEDs)
python tools/gen_schematic.py --leds 8     # one SKU
```

Pipeline: `kiutils` (typed Python objects) → `.kicad_sch` (KiCad 6 format) →
`kicad-cli sch upgrade --force` (KiCad 10, v20260306) → `kicad-cli sch erc` (validate).

## Contents

| File | LEDs | Notes |
|---|---|---|
| feather-strip-7led … 12led.kicad_sch | 7–12 | one per SKU — the 6 group-board segment lengths (`boards/feather-boards.md` §3) |

Each schematic: **J1** DATA-IN (ZH1.5-4P, +5V/GND/DI/CI) → **L1…LN** (SK9822-EC20
daisy-chained DI→DO, CI→CO) → **J2** DATA-OUT (+5V/GND/DO/CO), plus **J3** PWR-TAP
(PH2.0-2PWB) and **C1** (bulk decoupling). Power rails +5V/GND named by net labels.

> **Decoupling:** the SK9822-EC20 has **no internal decoupling capacitor** (datasheet).
> Each schematic includes **C1** — one bulk **22 µF 25 V X5R 1206** (`C12891`, BASIC)
> across +5V/GND at the power-tap end (joined by net name); data lines route under it
> on the back copper.

## Verification

- `kicad-cli sch erc` clean of wiring errors (remaining: mechanical-anchor pins
  unconnected, footprint/lib-link warnings — benign).
- `kicad-cli sch export netlist` confirms the daisy chain and power nets per SKU.
