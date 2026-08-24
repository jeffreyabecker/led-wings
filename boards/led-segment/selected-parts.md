# Selected Parts — LED Segment

> Brief on purpose — rationale in [design-readiness.md](design-readiness.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

## LED

| Ref | Part | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-----|-----|------|-----|--------|
| `LED*` | SK9822 addressable RGB, 5 V, 2020 | OPSCO | `SK9822-EC20` | [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | TBD | ✅ |

## Board connector (SMD, side-entry — parallel to board, flex-compatible)

| Ref | Port | Mfr | MPN | LCSC | Qty | Status |
|-----|------|-----|-----|------|-----|--------|
| `J1` | single 6-pin home-run port | JST | `S6B-PH-SM4-TB` | [C54582918](https://www.lcsc.com/product-detail/C54582918.html) | 1 | ✅ |

> Side-entry SMD so the cable exits **parallel** to the board (flex PCB: no through-hole).
> One connector per board; direction is by pin name (`DI` vs `DO`), not connector color.

## Cables (off-the-shelf)

| Use | Cable | Source |
|-----|-------|--------|
| Board → hub | 6-pin female-to-female (JST-PH) | TBD |
| (alt, hub density) | RJ45/Cat5e — 6 signals + 2 spare | open decision |

> Off-the-shelf wire colors may differ — verify pin-1 → color per vendor before wiring.

## On-board passives & protection (per board)

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `C*` | Bulk — Samsung `CL31A476MPHNNNE` ([C96123](https://www.lcsc.com/product-detail/C96123.html)) | 47 µF, 1206 X5R 10V | 1 | ✅ |
| `C*` | Decoupling — Yageo `CC0603KRX7R9BB104` ([C14663](https://www.lcsc.com/product-detail/C14663.html)) | 100 nF, 0603 X7R 50V | 1 per LED (or 1–4) | ✅ |
| `D*` | Reverse-polarity — MDD `SS34` ([C8678](https://www.lcsc.com/product-detail/C8678.html)) | 3A, 40V, SMA | 1 | ✅ |

## Footprints / symbols

- LED `SK9822-EC20`: JLCPCB EasyEDA footprint — [OPSCO SK9822-EC20 / C2909059](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK9822EC20/C2909059)
- Connector: 6-pin JST `S6B-PH-SM4-TB` footprint (confirm in `Connector_JST` lib or create)

## To confirm

- [ ] Confirm 6-pin side-entry SMD footprint for `S6B-PH-SM4-TB` (LCSC part confirmed: C54582918).
- [ ] Confirm hub connector family (JST-PH 6-pin vs RJ45/Cat5e) before freezing `J1`.
