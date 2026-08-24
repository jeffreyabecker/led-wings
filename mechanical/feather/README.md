# Feather Design

Physical feather geometry — the mechanical feathers that carry the LED boards and
shape/diffuse the light.

## Documents

- [outline-templates.md](outline-templates.md) — the feather **outlines + arrangement** only:
  every individual feather template (geometry) and how they layer/stack.
- [lighting-and-boards.md](lighting-and-boards.md) — **lighting & board concerns**: which
  feathers are lit, individual boards vs shared strips vs unlit covers, and the board count /
  LED budget.

## Scope

- Feather outline + curvature for the ~76 unique lit feather shapes, mirroring the
  `boards/led-segment/` parameterization (overall length + bend points).
- The enumerated, first-principles template list lives in
  [outline-templates.md](outline-templates.md) — 76 individual wing feathers (52 flight + 24
  greater coverts), shared covert strips, plus scapular + back-cover templates over the
  electronics.
- Diffuser integration — see [`investigations/diffuser-halo/`](../../investigations/diffuser-halo/).
- LED-board mounting: how the flexible PCB attaches to and follows each feather — see
  [lighting-and-boards.md](lighting-and-boards.md).
- Overlap/stacking: feather-to-feather layering for a natural wing silhouette — see
  [outline-templates.md](outline-templates.md).

## Open questions

- Feather substrate — flex PCB as the structural skin vs a separate carrier with the PCB
  attached?
- Diffuser geometry per feather size.
- Attachment/removal for service (dead-LED replacement).
