# Structural Design — Design Readiness

> Decision tracker for the wing structure. Locked decisions live here; open items below.
> Legend: ✅ = decided/locked · ⚠️ = estimate to confirm.

## Locked

| Decision | Value |
|----------|-------|
| Wing "bones" | cross-laminated cardboard, covered in foam pipe-wrap insulation |
| Fold / transport | fixed closed; **not** disassemblable |
| Total weight budget | **5 kg** (whole piece: frame + feathers + electronics + battery) |
| Electronics mounting | backplate/harness carries battery, power-hubs, controller (see [README](README.md#electronics-bay--backplate)) |

## Constraints (why)

### Frame — cross-laminated cardboard + foam pipe wrap

- Cross-laminated cardboard = alternating-grain layers (like plywood) → stiff, cheap, light
  "bones" for the ribs/spars.
- Foam pipe-wrap insulation pads the bones and rounds the profile the feathers sit on.
- ⚠️ Consequences to design around:
  - **Not waterproof** — sweat/rain soften cardboard; needs a seal or kept dry.
  - **Flammable** near LEDs/connectors/wiring — keep heat sources and any fault current clear
    of direct contact.
  - Foam faces the wearer (no sharp internal fasteners); cardboard carries the load.

### Fixed closed, not disassemblable

- The piece is one rigid unit → wingspan is capped by the smallest passage it must clear
  (a standard door ≈ 0.8–0.9 m).
- All service happens in place: removable electronics-bay lid (back coverts) + feather-level
  access, never frame disassembly.

### 5 kg total budget

- The **battery dominates** the budget:
  - 2000 px → ~710 Wh → ~4.2 kg (LiPo) — nearly exhausts 5 kg by itself. ❌
  - 1400 px → ~500 Wh → ~2.9 kg (LiPo) / ~2.5 kg (18650). ⚠️
- Holding 5 kg forces the pixel count/runtime down (or 18650 + shorter runtime). See below.

## Weight budget (first pass — ⚠️ order-of-magnitude)

| Item | Est. mass | Notes |
|------|----------:|-------|
| Battery (3S Li-ion) | 2.5–2.9 kg | 1400 px @ 8 h @ 20 % — dominant lever |
| Frame (cardboard + foam) | ~0.9 kg | both wings, ribs + spars |
| Feathers / diffusers | ~0.6 kg | substrate TBD (feather README) |
| LEDs + flex boards + connectors | ~0.3 kg | ~1400 px, ~76 boards |
| Power-hubs + controller + wiring | ~0.6 kg | bucks + MCU + cabling |
| **Total** | **~4.9–5.3 kg** | tight against the 5 kg cap |

> ⚠️ Only the battery line has a sourced basis
> ([battery options](../../investigations/battery/options.md)); the rest are order-of-magnitude
> and must be weighed once the frame + feather materials are locked.

## Open decisions

- [ ] Pixel count / runtime vs 5 kg — the 2000 px battery alone (~4.2 kg) breaks the budget;
      reconcile to ~1400 px (or accept less runtime) to hold 5 kg.
- [ ] Wingspan vs door clearance (fixed, non-disassemblable unit) — confirm max span.
- [ ] Frame lamination + seal: cardboard layup, adhesive, and a moisture/flame barrier.
- [ ] Backplate material + how it integrates with the wing frame and shoulder straps.
- [ ] Bay sealing vs access: dust/sweat protection against a hinge/latch/magnet lid.
- [ ] Does the back-coverts lid carry any electronics, or is it purely a cover?
