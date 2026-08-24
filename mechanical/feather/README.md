# Feather Design

Physical feather geometry — the mechanical feathers that carry the LED boards and
shape/diffuse the light.

## Scope

- Feather outline + curvature for the ~70 unique feather shapes, mirroring the
  `boards/led-segment/` parameterization (overall length + bend points).
- The enumerated, first-principles template list lives in
  [outline-templates.md](outline-templates.md) — 70 individual wing feathers (52 flight + 18
  greater coverts), shared covert strips, plus scapular + back-cover templates over the
  electronics.
- Diffuser integration — see [`investigations/diffuser-halo/`](../../investigations/diffuser-halo/).
- LED-board mounting: how the flexible PCB attaches to and follows each feather.
- Overlap/stacking: feather-to-feather layering for a natural wing silhouette.

## Open questions

- Feather substrate — flex PCB as the structural skin vs a separate carrier with the PCB
  attached?
- Diffuser geometry per feather size.
- Attachment/removal for service (dead-LED replacement).
