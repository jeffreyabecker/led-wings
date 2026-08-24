# Selected Parts — Controller / Hub Board

> Brief on purpose — rationale in [design-readiness.md](design-readiness.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `U*` | MCU | TBD | 1 | ⬜ |
| `U*` | Level shifter (3.3 V → 5 V), one DATA + CLK pair | TBD | 1 | ⬜ |
| `R*` | Series R on DATA + CLK output | 33–100 Ω | 2 | ⬜ |
| `F*` | Fuse / polyfuse (per port) | TBD | 1/port | ⬜ |
| `TVS*` | ESD/TVS per port (DI, CI, DO, CO, VCC) | TBD | TBD | ⬜ |
| `J*` | 6-pin port per board (matches board `J1`) | TBD | 1/board | ⬜ |
| `JP*` | Bypass jumper (port N `DO` → port N+1 `DI`) | TBD | 1/hop | ⬜ |

## To confirm

- [ ] MCU choice.
- [ ] Port count per hub; modular spine vs single board.
- [ ] Connector family for density (JST-PH 6-pin vs RJ45/Cat5e).
- [ ] Power distribution sizing (total current, number of 5 V inputs).
- [ ] Chain timing / clock budget.
