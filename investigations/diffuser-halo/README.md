# Diffuser (LED halo) — Material investigation

> Scope: a **thin** light diffuser for an LED halo that (1) looks good, (2) has a
> **distinct emission direction** — radially *outward*, not omnidirectional like an
> off-the-shelf silicone tube — and (3) can be **bent into a circle**, all **without
> casting resin**. Driving criterion: **workability** (easy to cut, form, and finish).

## Core idea

A silicone tube is a *volumetric scatterer*: light bounces inside the bulk and leaves in
every direction, which is exactly the "no direction" look. To get a distinct direction,
switch from a scattering volume to an **edge-lit light guide** — the same physics as an
LCD backlight or an edge-lit sign:

1. **Clear guide** (PETG — preferred for workability) carries light by total internal
   reflection (TIR), so the material itself stays dark and light only leaves where we
   want it.
2. **One-sided extraction** — a texture (laser-engraved dots/lines, or a sanded frost) on
   *one* face breaks TIR and ejects light out the *opposite* face.
3. **Reflective backing** over the textured face recycles any back-scatter toward the emit
   face.

Net result: light exits predominantly one face/rim → **directional**, **thin (1.5–3 mm)**,
and resin-free.

## Why PETG

PETG is chosen for **workability**, and it carries almost all of acrylic's light-guide
behavior:

- **Forms far more easily** — bends at ~120 °C ⚠️ (becomes pliable around 70 °C) vs
  acrylic's ~150–170 °C, and it stays ductile rather than snapping when cooled too fast.
- **Doesn't crack or craze** — drills, cuts, and bends without the hairline fractures
  acrylic is prone to; forgiving to hand-work.
- **Machines and glues well** — easy to sand, polish, and solvent/structural bond.
- **Laser-cuts cleanly**; engraving leaves a slightly meltier finish than acrylic but is
  still fine for extraction dots.

The one real tradeoff: PETG is a touch less optically clear (≈88 % vs ≈92 % transmission
⚠️) and faintly warmer in tint. Irrelevant here — we frost/diffuse the emit face anyway.

## Fabrication (no casting)

Two physical forms, chosen by which "out" you mean:

| Form | Emission "out" | How to make it | Bending? |
|------|----------------|----------------|----------|
| **Flat annulus (donut)** | radially, in the plane, out the outer rim | laser-cut an annulus from sheet | none |
| **Ring wall (cylinder)** | radially, out the outer cylindrical face | laser-cut a strip → thermoform around a mandrel | yes |

### Directionality recipe (applies to both forms)

1. Laser-cut **PETG**, ~1.5–3 mm ⚠️ (thickness is a trade: thinner = more flexible/easier
   bend, but less light-carrying and more LED hot-spots).
2. **Emit face/rim** — fine *satin* frost: wet-sand 800 → 1200 grit, or a light laser
   raster. Keeps the direction while smoothing hot-spots.
3. **Back (inner) face** — laser-engrave a **dot or line** extraction pattern. Increase
   dot density with distance from the LED so brightness stays even across the ring.
4. **Backing** — white reflective film/tape (or silver mirror film) over the engraved face.
5. Optional: a thin **opal diffuser film** on the emit face if individual LEDs still read
   through.

### Bending into a circle (ring-wall form)

- Heat PETG to ~120 °C ⚠️ (oven, strip heater, or heat-gun line-bend) and wrap it around a
  wood/metal **mandrel** of the target diameter; hold until cooled. Much more forgiving
  than acrylic — no annealing step needed to avoid crazing.
- Keep the bend gentle; PETG tolerates far tighter radii than acrylic before it kinks.

## Alternatives

- **Cast acrylic (PMMA)** — slightly clearer and engraves with a crisper frost, but
  thermoforms ~40 °C hotter, is brittle, and crazes/cracks under stress. Chosen only if
  maximum clarity matters more than workability.
- **Opal / prismatic cast acrylic** — some inherent direction, but the prism pattern is
  destroyed by thermoforming.
- **Polycarbonate (PC)** — tougher still, but needs higher temperature and burns/off-gasses
  on a laser cutter (CNC or careful cutting instead).
- **3D-printed translucent ring** (clear/white PETG) with a textured inner wall + reflective
  back — doable, but milky and hotspot-prone; hard to make it "look good."
- **Diffuser film** (opal PET, e.g. 3M) laminated onto a clear strip — great hot-spot
  hiding with zero engraving, adds a film layer.

## Recommendation

**PETG edge-lit guide**, laser-cut + (optionally) thermoformed, with a **one-sided
laser-engraved extraction pattern** and a **white reflective backing**. Thin, directional,
resin-free, and the most workable material in the light-guide family — the same
construction as an edge-lit sign, just bent into a ring.

## Sources

- [Simply Plastics — PETG: The Fabricator's Material of Choice](https://www.simplyplastics.com/ideas-and-advice/petg-the-fabricators-material-of-choice)
- [P&M Plastics — PETG vs Acrylic](https://www.pmplastics.com.au/blog/petg-vs-acrylic)
- [Daei Pet Sheet — At what temperature will PETG sheet bend?](https://www.daeipetsheet.com/news/at-what-temperature-will-petg-sheet-bend)
- [AML — Acrylic Light Guide Panel Design Guide (dot patterns + uniformity)](https://www.aml-acrylic.com/blog/acrylic-light-guide-panel-design-guide-uniformity-dot-patterns-and-led-integration.html)
- [CandlePowerForums — LGP: laser-etched dots vs V-grooves](https://www.candlepowerforums.com/threads/lgp-laser-etched-dots-or-v-grooves.441461/)
- [Hexatron — What is a Light Guide Plate (LGP)](https://hexatrontech.com/he/blog/2025/05/what-is-a-light-guide-plate-lgp/08/#main-content)

## Status

`investigation` — default direction: **PETG edge-lit guide with one-sided extraction +
reflective backing**, chosen for workability.
