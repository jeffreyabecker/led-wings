# Side-facing LED placement — Investigation

> Scope: place SK9822 LED strips at the **edges** of wing feathers so light diffuses out
> the *sides* of the wing (glowing feather rims / wing outline) while the feathers stay
> **5–7 mm thick**, under an **opaque EVA foam** top that must remain dark.
>
> Question: where exactly do the strips go — how far from the edge, at what angle, at what
> density — and what strip part number makes that geometry possible?

## Decisions so far (from the design conversation)

1. **Side-facing, angled mount** — strips sit in a slot at the feather edge with the LED
   faces tilted ~20–25° up-and-out toward the edge. The angle is what fits a 10 mm-wide
   strip in a 5–7 mm feather (thickness ≈ W·sin θ + 2 mm).
2. **Air gap spreads; bubble wrap only finishes** — bubble wrap is a lens/finish layer,
   not a spreader, and it does not pipe light sideways. Keep the LED-to-edge path in air
   (≥ ~10 mm); put a thin bubble-wrap strip only at the edge exit.
3. **30/m effective density** — 33 mm LED pitch drives the continuity requirement
   (patch ≥ 33 mm). Standard 30/m SK9822 strips are 10 mm wide; the 5 mm mini ships only
   at 144–200/m, so the fallback for a 5 mm-wide strip is **144/m mini + light every 5th
   LED in firmware** (effective ~29/m, unlit LEDs draw nothing).
4. **Custom FPC strip chosen over stock dense strips (safety)** — de-densifying a stock
   144–200/m mini in firmware was **rejected on safety grounds** (full current capability
   ~33 A @ 5 V on a bug, unverifiable trace sizing). Instead we're building a **custom
   5 mm-wide FPC with SK9822-EC20 (2020) at 30/m**, which also drops power ~33 %
   (0.2 W/LED vs 0.3 W), fits the feather thickness budget at ~3 mm angled, and buys
   exact geometry + test pads → see [custom-electronics/](custom-electronics/).
5. **Power architecture (same conversation)** — 5 V SK9822, single ESP32 over SPI (clock +
   data daisy chain), 4S low-C LiPo → ~14× MP1584EN buck converters (~1 per 10 feathers).

## Notes

- [placement-geometry.md](placement-geometry.md) — cone math, setback/gap numbers,
  angle-fit table, bubble-wrap physics, strip width/density availability.
- [power-architecture.md](power-architecture.md) — LED counts, 5 V power budget,
  buck distribution, battery sizing, controller wiring, USB-C rejection.
- [custom-electronics/](custom-electronics/) — custom FPC strip (Option B): FPC design,
  assembly & cost, SK9822-EC20 component research.

## Status

`investigation` — default direction: **custom 5 mm FPC strip (SK9822-EC20 @ 30/m) in a
slot at the feather edge, tilted ~20–40°, set back ~10–15 mm, bubble wrap at the exit
only**; custom-electronics sub-investigation active (FPC capability + component
verification pending).
