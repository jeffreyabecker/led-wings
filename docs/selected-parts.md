# Selected Parts — Master BOM

> Single source of truth. Brief on purpose — rationale in [design-concerns.md](design-concerns.md),
> pinout in [connector-pinout.md](connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

## LED

| Ref | Part | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-----|-----|------|-----|--------|
| `LED*` | SK9822 addressable RGB, 5 V, 2020 | OPSCO | `SK9822-EC20` | [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | TBD | ✅ |

## Board headers (Boomele PH 2.0 mm, top-entry TH)

| Ref | Port | Color | MPN | LCSC | Qty | Status |
|-----|------|-------|-----|------|-----|--------|
| `J_IN` | input, 4-pin | white | `PH-4A` | [C2321](https://www.lcsc.com/product-detail/C2321.html) | 1 | ✅ |
| `J_OUT` | output, 4-pin | black | TBD | ⚠️ find C# | 1 | ⚠️ |
| `J_PWR` | power, 2-pin | white | `PH-2A` | [C2319](https://www.lcsc.com/product-detail/C2319.html) | 1+ | ✅ |
| (alt) | 4-pin SMD | — | `PH-4AWD` | [C49994](https://www.lcsc.com/product-detail/PH-Connectors_PH-4AWD_C49994.html) | — | ⚠️ orientation |

## Cables (off-the-shelf)

| Use | Cable | Source |
|-----|-------|--------|
| OUT → IN daisy chain | JST-PH 4-pin female-to-female | MakerSheet, Adafruit STEMMA |
| Controller feed | JST-PH 4-pin female-to-tinned pigtail | The Pi Hut, Adafruit |
| Power injection | JST-PH 2-pin red/black pigtail | generic |

> Off-the-shelf wire colors may differ — verify pin-1 → color per vendor before wiring.

## Passives & protection

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `C*` | Bulk cap, per injection point | 100–470 µF | TBD | ⬜ |
| `C*` | Decoupling, per LED (or 1–4 LEDs) | 100 nF | TBD | ⬜ |
| `R*` | Series R, DATA + CLK input | 33–100 Ω | TBD | ⬜ |
| `D*`/`Q*` | Reverse-polarity protection (**required**) | Schottky / P-MOSFET | TBD | ⬜ |
| `F*` | Input fuse / polyfuse | TBD | TBD | ⬜ |
| `TVS*` | ESD/TVS on DATA, CLK, VCC | TBD | TBD | ⬜ |

## Controller

External — level-shifted to 5 V; drives DATA + CLK into `J_IN`.

## To confirm

- [ ] Black 4-pin PH header C# for `J_OUT`.
- [ ] `PH-4AWD` orientation (if SMD).
