# Selected Parts — LED Segment

> Brief on purpose — rationale in [design-readiness.md](design-readiness.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

## LED

| Ref | Part | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-----|-----|------|-----|--------|
| `LED*` | SK9822 addressable RGB, 5 V, 2020 | OPSCO | `SK9822-EC20` | [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | TBD | ✅ |

## Board connectors (SMD, side-entry — parallel to board, flex-compatible)

| Ref | Port | Pins | Mfr | MPN | LCSC | Qty | Status |
|-----|------|------|-----|-----|------|-----|--------|
| `J_PWR` | power in (GND/+5V) | 2 | JST | `S2B-PH-SM4-TB` | [C295747](https://www.lcsc.com/product-detail/C295747.html) | 1 | ⚠️ |
| `J_IN` | data in (DI/CI) | 2 | JST | `SM02B-GHS-TB(LF)(SN)` | [C189893](https://www.lcsc.com/product-detail/C189893.html) | 1 | ⚠️ |
| `J_OUT` | data out (DO/CO) | 2 | JST | `SM02B-GHS-TB(LF)(SN)` | [C189893](https://www.lcsc.com/product-detail/C189893.html) | 1 | ⚠️ |

> Side-entry SMD so cables exit **parallel** to the board (flex PCB: no through-hole).
> Direction is by pin name (`DI` vs `DO`), not connector color. Power uses 2.0 mm JST-PH;
> data uses 1.25 mm JST-GH so the data cable is a 2-wire `DI`/`CI` pair (`GND` lives on `J_PWR`).

## Cables (off-the-shelf)

| Use | Cable | Source |
|-----|-------|--------|
| Feather → feather (data) | 2-pin female-to-female (JST-GH 1.25 mm) | TBD |
| Power-hub → feather | 2-pin red/black pigtail (JST-PH 2.0 mm) | TBD |
| Controller → first feather | 2-pin female-to-female (JST-GH 1.25 mm) | TBD |

> Off-the-shelf wire colors may differ — verify pin-1 → color per vendor before wiring.

## On-board passives & protection (per board)

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `C*` | Bulk — Samsung `CL31A476MPHNNNE` ([C96123](https://www.lcsc.com/product-detail/C96123.html)) | 47 µF, 1206 X5R 10V | 1 | ✅ |
| `C*` | Decoupling — Yageo `CC0603KRX7R9BB104` ([C14663](https://www.lcsc.com/product-detail/C14663.html)) | 100 nF, 0603 X7R 50V | 1 per LED (or 1–4) | ✅ |
| `D*` | Reverse-polarity — MDD `SS34` ([C8678](https://www.lcsc.com/product-detail/C8678.html)) | 3A, 40V, SMA | 1 | ✅ |

## Footprints / symbols

- LED `SK9822-EC20`: JLCPCB EasyEDA footprint — [OPSCO SK9822-EC20 / C2909059](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK9822EC20/C2909059)
- Connectors: JST `S2B-PH-SM4-TB` (power) + `SM02B-GHS-TB` (data ×2) footprints (confirm in `Connector_JST` lib or create)

## To confirm

- [ ] Confirm `SM02B-GHS-TB` side-entry SMD part + footprint (data ×2).
- [ ] Confirm power-hub and controller connector families before freezing `J_PWR`/`J_IN`/`J_OUT`.
