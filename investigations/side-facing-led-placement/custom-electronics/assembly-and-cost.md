# Assembly & cost — custom SK9822-EC20 strip

## Bill of materials ⚠️ (estimates; ~930 LED positions = 892 lit + 38 dark, 2 wings)

| Item | Qty | ~Cost | Source |
|---|---|---|---|
| SK9822-EC20 (2020) | 930 | $50–100 | [LCSC C2909059](https://www.lcsc.com/product-detail/C2909059.html) / [OPSCO](https://www.opsco.com) — verify reel price/MOQ |
| 22 µF 25 V X5R decoupling (1206, **BASIC** — one per segment board) | 70 | ~$13 | [LCSC C12891](https://www.lcsc.com/product-detail/C12891.html) |
| FPC → **FR-4 thin-core fab** (0.6–0.8 mm, panelized) | ~30 m | $15–40 ⚠️ | JLCPCB rigid — cheaper than FPC, 2 oz copper, V-score break-out |
| Stencil (laser-cut PET) | 1 | $10–20 | JLCPCB stencil or DIY |
| Solder paste | 1 | ~$10 | — |
| Hot plate / reflow oven | 1 | $40–60 (one-time) | — |
| Magnet wire, fuses, XT60 | — | ~$15 | — |
| JST-PH 4-pin headers (×~270) + housings/contacts + crimp tool | — | ~$25–40 ⚠️ | — |
| **Total (excl. one-time tools)** | | **~$123–213** | |

Compare: Route A (custom-order from a strip maker) ≈ $1.5–4/m × 23 m + setup ⚠️ —
competitively priced *if* the MOQ/lead time is acceptable, but zero control over trace
sizing and no test-pad design.

## Assembly process

1. **Stencil** the panel, apply solder paste.
2. **Place** 2020 chips + the bulk 1206 decoupling caps — tweezers or vacuum
   pen; 2020 (2 mm) is small but manageable; expect ~50–100 placements/hour ⚠️
   (≈ 10–20 h for ~1000 placements).
3. **Reflow** in batches on a hot plate (or oven) — QFN-style 2020 packages reflow
   without issue (no tiny caps to tombstone).
4. **Break out** segments at score lines.
5. **Crimp** JST link cables (female–female, VDD/VSS/DI/CI).
6. **Test every segment** via its JST connector with an ESP32 SPI jig (FastLED count +
   color sweep) before installation — cheap insurance that pays for itself during
   feather assembly.

## Risks ⚠️

- **EC20 availability/lead** — confirm stock before designing around it; OPSCO/LCSC
  carry it, but reel pricing needs a quote.
- **Footprint errors** — the 2020 pad layout must match the datasheet; a wrong footprint
  bricks the whole panel. Build one 5-chip test coupon first.
- **Rigid sliver handling** — 233 × 5 mm FR-4 boards are brittle at length; keep them
  in the panel until break-out, and prefer 0.8 mm core if warping/bowing shows up.
- **Feather straightness** — rigid boards won't conform to curved feather edges; if the
  feathers aren't straight enough, fall back to FPC.
- **Assembly tedium/yield** — 930 placements is a slog; a bad reflow batch wastes chips
  (~$0.10 each) more than time. Consider a cheap pick-and-place or a friend with a
  stencil printer if the volume hurts.
- **2020 thermal** — at the 0.2 W max the tiny package runs warm; fine at the ≤25 %
  cap, but don't run test patterns at 100 % white for long.

## Next steps

1. EC20 datasheet — **no internal decoupling cap** (an earlier claim that it had one was
   wrong); use **bulk 22 µF 1206 per segment board**; re-check pinout against the 2020
   footprint.
2. Quote FPC at JLCPCB for 2 mm and 3 mm widths (panel of ~0.5 m strips).
3. Order a 5-chip **test coupon** + stencil → reflow → SPI test → then commit to the
   full panel.
