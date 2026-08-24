# Structural Design

Physical wing structure — the frame the feather boards and power-hubs attach to.

## Scope

- Wing frame/skeleton: spars, ribs, load path from wing tip to body.
- Mounting points for the boards: led-segment feathers, power-hubs, controller.
- Harness/cable routing for the daisy-chain data lines and hub power feeds.
- Body attachment: how the wings mount to the wearer/back and stay balanced in motion.
- Materials + weight budget (mobility target: 8 h wear).

## Electronics bay / backplate

The battery, power-hubs, and controller mount to a **backplate** (or directly to the harness),
and the back coverts ([BC1–BC8](../feather/outline-templates.md#37-back-coverts--bc1bc8-8-center-back))
form a removable feathered lid over them.

- Backplate/harness carries the battery (heaviest item), the power-hubs, and the controller.
- Electronics bay: a recessed, shielded area on the upper back, sized to the selected parts.
- Removable/hinged lid: the back-coverts panel detaches or swings open for battery swap + service.
- Cable egress: data + power runs leave the bay toward each wing with strain relief.
- Cooling/venting: buck converters + battery need airflow — don't let the bay trap heat.
- Centre of mass: battery placement dominates balance — keep it low and close to the spine.

## Open questions

- Frame material — carbon/glass-fibre rod vs 3D-printed skeleton vs hybrid?
- Fold/transport — do the wings need to collapse, fold, or disassemble for storage?
- Weight budget and centre of mass vs battery/hub placement.
- Backplate material + how it integrates with the wing frame and shoulder straps.
- Bay sealing vs access: dust/sweat protection against a hinge/latch/magnet lid.
- Does the back-coverts lid carry any electronics, or is it purely a cover?
