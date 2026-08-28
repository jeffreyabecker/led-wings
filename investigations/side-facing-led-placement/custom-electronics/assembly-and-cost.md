# Assembly & cost — custom SK9822-EC20 strip

## Bill of materials ⚠️ (estimates; ~830 LEDs, 2 wings)

| Item | Qty | ~Cost | Source |
|---|---|---|---|
| SK9822-EC20 (2020) | 830 | $50–100 | [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html) / [OPSCO](https://www.opsco.com) — verify reel price/MOQ |
| 0402 100 nF bypass caps | 830 | ~$5 | LCSC/any |
| FPC fab (2-layer, panelized) | ~23 m | $10–40 ⚠️ | JLCPCB flex / PCBWay — depends on width & panel |
| Stencil (laser-cut PET) | 1 | $10–20 | JLCPCB stencil or DIY |
| Solder paste | 1 | ~$10 | — |
| Hot plate / reflow oven | 1 | $40–60 (one-time) | — |
| Magnet wire, fuses, XT60 | — | ~$15 | — |
| **Total (excl. one-time tools)** | | **~$90–165** | |

Compare: Route A (custom-order from a strip maker) ≈ $1.5–4/m × 23 m + setup ⚠️ —
competitively priced *if* the MOQ/lead time is acceptable, but zero control over trace
sizing and no test-pad design.

## Assembly process

1. **Stencil** the panel, apply solder paste.
2. **Place** 2020 chips + 0402 caps — tweezers or vacuum pen; 2020 (2 mm) is small but
   manageable; expect ~50–100 placements/hour ⚠️ (≈ 8–16 h for 1660 placements).
3. **Reflow** in batches on a hot plate (or oven) — QFN-style 2020 packages reflow
   without issue; watch paste volume (tombstoning on tiny caps).
4. **Break out** segments at score lines, solder magnet-wire leads to the end pads.
5. **Test every segment** with an ESP32 SPI jig (FastLED count + color sweep) before
   installation — cheap insurance that pays for itself during feather assembly.

## Risks ⚠️

- **EC20 availability/lead** — confirm stock before designing around it; OPSCO/LCSC
  carry it, but reel pricing needs a quote.
- **Footprint errors** — the 2020 pad layout must match the datasheet; a wrong footprint
  bricks 23 m of FPC. Build one 5-chip test coupon first.
- **FPC width floor** — if JLCPCB won't do 2 mm, 3 mm is still fine for the 5–7 mm
  feather budget.
- **Assembly tedium/yield** — 1660 placements is a slog; a bad reflow batch wastes chips
  (~$0.10 each) more than time. Consider a cheap pick-and-place or a friend with a
  stencil printer if the volume hurts.
- **2020 thermal** — at the 0.2 W max the tiny package runs warm; fine at the ≤25 %
  cap, but don't run test patterns at 100 % white for long.

## Next steps

1. Download the EC20 datasheet, confirm pinout + bypass-cap recommendation.
2. Quote FPC at JLCPCB for 2 mm and 3 mm widths (panel of ~0.5 m strips).
3. Order a 5-chip **test coupon** + stencil → reflow → SPI test → then commit to the
   full panel.
