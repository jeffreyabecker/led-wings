# Generated feather-strip schematics

Build artifacts — **do not hand-edit.** Regenerate with:

```
python tools/gen_schematic.py --all        # all 12 SKUs
python tools/gen_schematic.py --leds 6     # one SKU
```

Pipeline: `kiutils` (typed Python objects) → `.kicad_sch` (KiCad 6 format) →
`kicad-cli sch upgrade --force` (KiCad 10, v20260306) → `kicad-cli sch erc` (validate).

## Contents

| File | LEDs | Notes |
|---|---|---|
| feather-strip-1led … 12led.kicad_sch | 1–12 | one per SKU, from `boards/feather-boards.md` |

Each schematic: **J1** DATA-IN (ZH1.5-4P, +5V/GND/DI/CI) → **L1…LN** (SK9822-EC20
daisy-chained DI→DO, CI→CO) → **J2** DATA-OUT (+5V/GND/DO/CO), plus **J3** PWR-TAP
(PH2.0-2PWB). Power rails +5V/GND named by net labels.

## Verification

- `kicad-cli sch erc` clean of wiring errors (remaining: mechanical-anchor pins
  unconnected, footprint/lib-link warnings — benign).
- `kicad-cli sch export netlist` confirms the daisy chain and power nets per SKU.
