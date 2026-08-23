# Selected Parts — LED Segment

> Brief on purpose — rationale in [design-concerns.md](design-concerns.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

## LED

| Ref | Part | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-----|-----|------|-----|--------|
| `LED*` | SK9822 addressable RGB, 5 V, 2020 | OPSCO | `SK9822-EC20` | [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | TBD | ✅ |

## Board headers (SMD, side-entry — parallel to board, flex-compatible)

| Ref | Port | Color | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-------|-----|-----|------|-----|--------|
| `J_IN` | input, 4-pin | white | JST | `S4B-PH-SM4-TB` | [C265102](https://www.lcsc.com/product-detail/C265102.html) | 1 | ✅ |
| `J_OUT` | output, 4-pin | distinct (≠ white) | hanxia | `HX PH2.0-4PWT` | [C22461287](https://www.lcsc.com/product-detail/C22461287.html) | 1 | ✅ |
| `J_PWR` | power, 2-pin | white | JST | `S2B-PH-SM4-TB` | [C295747](https://www.lcsc.com/product-detail/C295747.html) | 1+ | ✅ |
| (alt) | 4-pin white | white | Boomele | `2.0-4P卧贴` | [C53041](https://www.lcsc.com/product-detail/C53041.html) | — | ✅ |

> Side-entry SMD so the cable exits **parallel** to the board (flex PCB: no through-hole).
> `J_OUT` uses a distinct (non-white) color so it stays visually separate from the white input.

## Cables (off-the-shelf)

| Use | Cable | Source |
|-----|-------|--------|
| OUT → IN daisy chain | JST-PH 4-pin female-to-female | MakerSheet, Adafruit STEMMA |
| Controller feed | JST-PH 4-pin female-to-tinned pigtail | The Pi Hut, Adafruit |
| Power injection | JST-PH 2-pin red/black pigtail | generic |

> Off-the-shelf wire colors may differ — verify pin-1 → color per vendor before wiring.

## On-board passives & protection (per segment)

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `C*` | Bulk cap, per injection point | 100–470 µF | TBD | ⬜ |
| `C*` | Decoupling, per LED (or 1–4 LEDs) | 100 nF | TBD | ⬜ |
| `D*`/`Q*` | Reverse-polarity protection (**required**) | Schottky / P-MOSFET | TBD | ⬜ |

## Footprints / symbols

- LED `SK9822-EC20`: JLCPCB EasyEDA footprint — [OPSCO SK9822-EC20 / C2909059](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK9822EC20/C2909059)
- Connectors: TBD (JST `S4B-PH-SM4-TB` / `S2B-PH-SM4-TB`, hanxia `HX PH2.0-4PWT`)

## To confirm

- [ ] Confirm SMD side-entry footprints match between JST (white) and the hanxia `J_OUT` header.
