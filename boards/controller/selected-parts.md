# Selected Parts — Controller Board

> Brief on purpose — rationale in [design-readiness.md](design-readiness.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `U*` | MCU | TBD | 1 | ⬜ |
| `U*` | Level shifter (3.3 V → 5 V), one per data output | TBD | N | ⬜ |
| `R*` | Series R on DATA + CLK output | 33–100 Ω | 2N | ⬜ |
| `TVS*` | ESD/TVS per data output | TBD | TBD | ⬜ |
| `J*` | Data output (DATA + CLK) — 2-pin JST-GH 1.25 mm | TBD | N | ⬜ |

## To confirm

- [ ] MCU choice.
- [ ] Number of chain segments (N).
- [ ] Data output connector family.
- [ ] Chain timing / clock budget.
