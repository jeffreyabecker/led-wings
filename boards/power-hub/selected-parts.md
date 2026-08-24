# Selected Parts — Power-Hub Board

> Brief on purpose — rationale in [design-readiness.md](design-readiness.md),
> pinout in [../../docs/connector-pinout.md](../../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD

| Ref | Part | Value | Qty | Status |
|-----|------|-------|-----|--------|
| `U*` | Buck (12 V→5 V), MP2315 / MP1584-class | 2–3 A | 1 | ⚠️ |
| `L*` | Inductor | per buck datasheet | 1 | ⚠️ |
| `C*` | Bulk + decoupling | TBD | TBD | ⬜ |
| `F*` | Fuse / polyfuse per 5 V output | TBD | 1/output | ⬜ |
| `D*` | Reverse-polarity (12 V input) | SS34-class | 1 | ⚠️ |
| `TVS*` | ESD/TVS (12 V input) | TBD | 1 | ⬜ |
| `J*` | 12 V input (bus) | TBD | 1 | ⬜ |
| `J*` | 5 V output (matches feather `J_PWR`) | `S2B-PH-SM4-TB` | N | ⚠️ |

## To confirm

- [ ] Buck part + current rating (feathers per hub).
- [ ] Fuse rating per 5 V output.
- [ ] 12 V input connector family + protection parts.
- [ ] 12 V bus topology (hub-to-hub vs star).
