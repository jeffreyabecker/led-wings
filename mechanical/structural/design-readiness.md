# Structural Design — Design Readiness

> Decision tracker for the wing structure. Locked decisions live here; open items below.
> Legend: ✅ = decided/locked · ⚠️ = estimate to confirm.
>
> ⚠️ **Feather sizing authority:** the global scale is **locked at × 0.9085** — the primaries
> mount in **Atlas order P1→P10 (P1 = wing tip)** within the 55 cm envelope (longest ≈ P5/P6 ≈
> 49/48 cm, tips peak at 55); the tables in [`mechanical/templates/`](../templates/) are
> **current** at that scale. ⚠️ Covert/alula/underwing sizes are still **working estimates**
> (no published data) — validate before locking templates.

## Locked

| Decision | Value |
|----------|-------|
| Wing "bones" | cross-laminated cardboard, covered in foam pipe-wrap insulation ⚠️ covering under review — see [pipe-foam alternative](../../investigations/wing-bones/README.md#pipe-foam-alternatives--anchoring--color-new-track) |
| Wing members | **Option C** — straight radius/ulna + fanned carpal; **no humerus** (wing root blends into the backplate); θ1 = 0° vs spine, θ2 = 20° (15–25° range) — short upper spars (~13–14 cm), feathers dominate the lower wing (⚠️ layout working — see wing-bones) |
| Fold / transport | fixed closed; **not** disassemblable |
| Total weight budget | **battery excluded from structural weight** — externally carried (side pack); worn structure (frame + feathers + electronics) ≈ **~2.1 kg** ⚠️ — the old 5 kg whole-piece cap no longer binds the worn piece |
| Electronics mounting | backplate carries power-hubs + controller; **battery deferred — side pack if needed** (see [README](README.md#electronics-bay--backplate)) |
| Physical envelope | 50 cm wide × **~55 cm** tall (⚠️ longest ≈ P5/P6 ≈ 49/48 cm — D1 mid-butt decision; feather sizing not finalized, see note above), folded flat on the back |
| Width clearance | ✅ **no passage narrower than 50 cm exists** — the 50 cm envelope is the hard limit |
| Harness | **over-the-shoulder straps + cross-chest (sternum) strap** — no load-bearing waist belt (battery is off-back) |
| Plate top + fold | plate top ≈ **shoulder line** (3–4 cm below C7, ⚠️ Q5) · **fold rise = 0 cm** (✅ Q4) — nothing above the shoulders |

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
- **Height:** **~55 cm**, folded flat on the back — set by the longest primaries (**P5/P6 ≈
  49/48 cm** quill-to-tip; tips peak at 55 cm at the envelope), mounted in **Atlas order
  (P1 = wing tip) P1→P10**, tips landing **mid-butt** (D1 decision,
  [wing-bones](../../investigations/wing-bones/README.md)) — ≈ 62 cm above the floor for a
  167 cm wearer (13 cm above the knee); scale **× 0.9085** (was × 1.024 → × 1.40).
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
| Feathers / diffusers | ~0.25 kg | ⚠️ scales with length² — ×1.40 → ×0.9085 cut feather area ~58 %; substrate TBD (feather README) |
| LEDs + strips + connectors | ~0.3 kg | ~1400 px, ~88 strip chunks |
| Power-hubs + controller + wiring | ~0.6 kg | bucks + MCU + cabling |
| **Total (worn)** | **~2.1 kg** | ⚠️ no battery — see below |

> Battery (**not worn** — external side pack): ~2.5–2.9 kg @ 1400 px / ~4.2 kg @ 2000 px
> ([battery options](../../investigations/battery/options.md)). All worn-structure lines are
> order-of-magnitude and must be weighed once the frame + feather materials are locked.

## Open decisions

- [ ] **Bone-structure geometry** — structure + angles decided (Option C, no humerus, θ1 = 0°,
      θ2 = 20°); **feather-root layout computed (working ⚠️)** — primaries/secondaries root
      tables in the wing-bones investigation; validate on the mockup before committing.
- [ ] **Pipe-foam alternative** — covering/anchor material available in **multiple colors** —
      under investigation ([wing-bones](../../investigations/wing-bones/README.md#pipe-foam-alternatives--anchoring--color-new-track)).
- [ ] **Backplate geometry** — shape (angular-shield?), overall height, top-edge offset below
      the trapezius, wing-fold rise above the shoulders. **Working values:** angular-shield,
      straight taper 44 → ~37 cm, height ~30–32 cm (bottom ~6–8 cm above waist) · plate top ≈
      shoulder line (3–4 cm below C7, ⚠️ Q5) · **fold rise = 0 cm (✅ Q4)** · roots + straps
      co-located at the top corners (±20) · bay ~15 × 12 cm at y≈14–26 — see the wing-bones
      investigation.
- [ ] Pixel count / runtime — battery is **external** (side pack) → sizes the pack only, no
      longer a structural-weight constraint (worn piece ≈ 2.1 kg ⚠️).
- [ ] Frame lamination + seal: cardboard layup, adhesive, and a moisture/flame barrier.
- [ ] Backplate material + how it integrates with the wing frame and shoulder straps.
- [ ] Bay sealing vs access: dust/sweat protection against a hinge/latch/magnet lid.
- [ ] Does the back-coverts lid carry any electronics, or is it purely a cover?
- [ ] Feather width: **keep per-feather vane ratios**, adjusted globally by the generator's
  `--vane-ratio-adjustment` (no hand-editing) — target vane ratio **~0.80–0.82** (real eagle;
  the mockup's 0.75 ran low) — see [mechanical/templates/](../templates/).
