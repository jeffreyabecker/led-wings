# Selected Parts — Controller Board

> Brief on purpose — rationale in [design-concerns.md](design-concerns.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `U*` | Level shifter (3.3 V → 5 V) | TBD | TBD | ⬜ |
| `R*` | Series R on DATA + CLK output | 33–100 Ω | 2 | ⬜ |
| `F*` | Fuse / polyfuse | TBD | TBD | ⬜ |
| `TVS*` | ESD/TVS on DATA, CLK, VCC | TBD | TBD | ⬜ |
| `J*` | Output connector to first segment (4-pin PH, matches `J_IN`) | TBD | TBD | ⬜ |

## To confirm

- [ ] MCU / level-shifter choice.
- [ ] Strand count and fuse rating.
- [ ] Output connector part (same 4-pin PH as segment `J_IN`).
