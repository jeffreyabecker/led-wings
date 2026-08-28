# Structural Design — Design Readiness

> Decision tracker for the wing structure. Locked decisions live here; open items below.
> Legend: ✅ = decided/locked · ⚠️ = estimate to confirm.
>
> ⚠️ **Feather sizing authority:** every feather size below (envelope height/vane, widths,
> stagger) is a **provisional placeholder**. The authoritative sizing lives in
> [`mechanical/templates/`](../templates/) and **has not yet
> been finalized** — re-check these values once feather sizing is locked.

## Locked

| Decision | Value |
|----------|-------|
| Wing "bones" | cross-laminated cardboard, covered in foam pipe-wrap insulation ⚠️ covering under review — see [pipe-foam alternative](../../investigations/wing-bones/README.md#pipe-foam-alternatives--anchoring--color-new-track) |
| Wing members | **Option C** — straight radius/ulna + fanned carpal; **no humerus** (wing root blends into the backplate); θ1 ≈ 0–5° vs spine, θ2 ≈ 20–25° vs radius (⚠️ angles to refine via anatomy research) |
| Fold / transport | fixed closed; **not** disassemblable |
| Total weight budget | **battery excluded from structural weight** — externally carried (side pack); worn structure (frame + feathers + electronics) ≈ **~2.1 kg** ⚠️ — the old 5 kg whole-piece cap no longer binds the worn piece |
| Electronics mounting | backplate carries power-hubs + controller; **battery deferred — side pack if needed** (see [README](README.md#electronics-bay--backplate)) |
| Physical envelope | 50 cm wide × **~55 cm** tall (⚠️ P4 = 55 cm — D1 mid-butt decision; feather sizing not finalized, see note above), folded flat on the back |
| Width clearance | ✅ **no passage narrower than 50 cm exists** — the 50 cm envelope is the hard limit |

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

### Physical envelope (measured)

- **Width:** 50 cm — shoulder-to-shoulder, measured with a tailor's tape. Hard limit: both wings
  + center back covers must sit inside it.
- **Height:** **~55 cm**, folded flat on the back — set by the longest primary (**P4 = 55 cm**
  quill-to-tip, ~41 cm vane @ mockup ratio 0.75), tips landing **mid-butt** (D1 decision,
  [wing-bones](../../investigations/wing-bones/README.md)) — ≈ 62 cm above the floor for a
  167 cm wearer (13 cm above the knee); nearly real-eagle scale (**× 1.024**, was × 1.40).
- **Form:** a **folded** wing laid flat on the back (not an extended, outspread wing) — feathers
  point down/back and overlap shingle-style; primaries reach the hem, coverts stack up toward the
  shoulders.
- Feather scaling lives with the template list: [`mechanical/templates/`](../templates/) — ⚠️ sizing not yet finalized (see note above).

### Weight budget — battery excluded (external)

- The **battery is not worn on the structure** — it rides in an external side pack, so the
  pixel count/runtime decision sizes the *pack*, not the frame (see the battery investigation;
  the 5 kg whole-piece ceiling no longer applies to the worn piece).
- Worn structure = **frame + feathers + electronics only** ≈ **~2.1 kg** ⚠️ (table below).

## Weight budget — worn structure only (first pass — ⚠️ order-of-magnitude)

| Item | Est. mass | Notes |
|------|----------:|-------|
| Frame (cardboard + foam) | ~0.9 kg | both wings, ribs + spars |
| Feathers / diffusers | ~0.3 kg | ⚠️ scales with P4² — envelope 75→55 cm cut feather area ~46 %; substrate TBD (feather README) |
| LEDs + strips + connectors | ~0.3 kg | ~1400 px, ~88 strip chunks |
| Power-hubs + controller + wiring | ~0.6 kg | bucks + MCU + cabling |
| **Total (worn)** | **~2.1 kg** | ⚠️ no battery — see below |

> Battery (**not worn** — external side pack): ~2.5–2.9 kg @ 1400 px / ~4.2 kg @ 2000 px
> ([battery options](../../investigations/battery/options.md)). All worn-structure lines are
> order-of-magnitude and must be weighed once the frame + feather materials are locked.

## Open decisions

- [ ] **Bone-structure geometry** — structure decided (Option C, no humerus); **θ1/θ2 angle
      values to refine** via anatomy research — see
      [`investigations/wing-bones/`](../../investigations/wing-bones/README.md).
- [ ] **Pipe-foam alternative** — covering/anchor material available in **multiple colors** —
      under investigation ([wing-bones](../../investigations/wing-bones/README.md#pipe-foam-alternatives--anchoring--color-new-track)).
- [ ] **Backplate geometry** — shape (angular-shield?), overall height, top-edge offset below
      the trapezius, wing-fold rise above the shoulders (wearer-measured; checklist in the
      wing-bones investigation).
- [ ] Pixel count / runtime — battery is **external** (side pack) → sizes the pack only, no
      longer a structural-weight constraint (worn piece ≈ 2.1 kg ⚠️).
- [ ] Frame lamination + seal: cardboard layup, adhesive, and a moisture/flame barrier.
- [ ] Backplate material + how it integrates with the wing frame and shoulder straps.
- [ ] Bay sealing vs access: dust/sweat protection against a hinge/latch/magnet lid.
- [ ] Does the back-coverts lid carry any electronics, or is it purely a cover?
- [ ] Feather width: **keep per-feather vane ratios**, adjusted globally by the generator's
  `--vane-ratio-adjustment` (no hand-editing) — see [mechanical/templates/](../templates/).
