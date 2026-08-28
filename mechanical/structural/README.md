# Structural Design

Physical wing structure — the frame the strip chunks and power-hubs attach to.

> **Build plan:** [wing-structure-plan.md](wing-structure-plan.md) — the concrete,
> buildable wing structure (bones + backplate + feather mounting). Locked decisions —
> frame material, transport, weight budget — are tracked in
> [design-readiness.md](design-readiness.md).

## Scope

- Wing frame/skeleton: spars, ribs, load path from wing tip to body.
- Mounting points for strip chunks, power-hubs, controller.
- Harness/cable routing for the daisy-chain data lines and hub power feeds.
- Body attachment: how the wings mount to the wearer/back and stay balanced in motion.
- Materials + weight budget (mobility target: 8 h wear).

## Electronics bay / backplate

The power-hubs and controller mount to a **backplate** (or directly to the harness), and the
back coverts ([BC1–BC8](../templates/)) form a removable feathered lid over them.

- **Battery (deferred ✅):** if a mobility battery is needed it lives in a **side pack** — NOT
  on the backplate. The bay carries electronics only (hubs + controller + wiring); bay sizing
  no longer depends on pack footprint (see
  [wing-bones investigation](../../investigations/wing-bones/README.md)).
- Electronics bay: a recessed, shielded area on the upper back, sized to the selected parts.
- Removable/hinged lid: the back-coverts panel detaches or swings open for service.
- Cable egress: data + power runs leave the bay toward each wing with strain relief; a feed
  run to the side pack (if fitted).
- Cooling/venting: buck converters need airflow — don't let the bay trap heat.
- Centre of mass: with the battery off-back, the back load is the wings + light electronics;
  the side pack (if fitted) sits at the waist — balance is better than a back-mounted pack.

## Open questions

- **Bone-structure layout + backplate geometry** — being investigated in
  [`investigations/wing-bones/`](../../investigations/wing-bones/README.md):
  - Member chain: **no humerus — wing root blends into the backplate** (decided ✅); straight
    radius/ulna + fanned carpal (Option C); θ1 = 0° vs spine, θ2 = 20° (15–25° range) — short
    upper spars (~13–14 cm), feathers dominate the lower wing (⚠️ layout working, see
    wing-bones).
  - Backplate shape (angular-shield?), overall height, top-edge offset below the trapezius,
    wing-fold rise above the shoulders, allowable total width (50 cm — locked).
- Width clearance: ✅ resolved — no passage narrower than the 50 cm wings exists (see design-readiness).
- Frame lamination + seal: cardboard layup, adhesive, and a moisture/flame barrier.
- Backplate material + how it integrates with the wing frame and shoulder straps.
- Bay sealing vs access: dust/sweat protection against a hinge/latch/magnet lid.
- Does the back-coverts lid carry any electronics, or is it purely a cover?

Full open-decision list (including the battery sizing trade — now external, side pack) is in
[design-readiness.md](design-readiness.md).
