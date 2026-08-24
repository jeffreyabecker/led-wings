# Battery Options — 12 V Mobility Power

> Pick the battery that feeds the fixed 12 V rail (wall supply for dev, battery for
> mobility). The pixel is locked to the SK9822-EC20 (5 V), powered through a 12 V→5 V buck,
> so the battery only has to stay above the buck's input dropout (~6–7 V).
>
> Legend: ✅ = sourced · ⚠️ = estimate, to confirm.

## Requirements recap

- Fixed **12 V** system; battery must hold the rail above the 12 V→5 V buck's input dropout
  across its full discharge.
- Runtime target: **8 h at 20 % brightness** (typical animated look, not full-white).
- Energy needed: SK9822 @ 5 V (via 12 V→5 V buck, ~85 % end-to-end): **~500 Wh**.

## Chemistry comparison ("12 V")

| | Lead-acid (SLA/AGM) | 3S Li-ion/LiPo | 4S Li-ion | 4S LiFePO4 | 3S LiFePO4 |
|---|---|---|---|---|---|
| Nominal | 12.0 V | 11.1 V | 14.8 V | 12.8 V | 9.6 V |
| Range (empty→full) | 10.5–12.9 V ✅ | 9.0–12.6 V ✅ | 12.0–16.8 V ✅ | 10.0–14.6 V ✅ | 7.5–10.95 V ✅ |
| Energy density | 30–40 Wh/kg ✅ | 150–250 Wh/kg ✅ | 150–250 Wh/kg ✅ | 90–160 Wh/kg ✅ | 90–160 Wh/kg |
| Cycle life (to 80 %) | 200–500 ✅ | 300–1000 ✅ | 300–1000 ✅ | 2000–4000+ ✅ | 2000–4000+ |
| Upfront cost | lowest ⚠️ | mid ⚠️ | mid ⚠️ | higher ⚠️ | — |
| Safety | sealed, low fire risk | **thermal runaway risk** | **thermal runaway risk** | safest lithium ✅ | safest lithium |
| BMS / charger | charge controller only | **BMS required** | **BMS required** | BMS required | BMS required |
| Fits "12 V" name | yes | yes (11.1 V) | no (16.8 V max) | yes (12.8 V) | no |

Key points:

- **Lead-acid** is the cheapest and needs no BMS, but is heavy and dies fast when deeply
  cycled (keep above ~50 % DoD → effectively ~10.5 V floor).
- **Li-ion (NMC/LiPo)** is the lightest, but it *must* have a BMS and is the fire-risk
  option; 3S and 4S differ only in voltage (4S is what "12 V automotive replacement" packs
  actually are).
- **LiFePO4** trades ~1.5–2× the weight of Li-ion for the longest cycle life, the safest
  chemistry, and a famously flat discharge curve.
- **3S LiFePO4 is too low** (9.6 V nominal) — rejects itself as a "12 V" rail.

Sources: [LiFePO4 vs Li-ion vs lead-acid](https://walkingsolar.com/lifepo4-vs-lithium-ion-vs-lead-acid-which-battery-is-best-for-solar/),
[lead-acid vs lithium energy density](https://eszoneo.com/info-detail/lead-acid-vs-lithium-battery-energy-density-a-comprehensive-comparison-for-modern-power-systems),
[3S LiPo guide](https://www.ufinebattery.com/blog/an-ultimate-guide-about-3s-lipo-batteries/),
[12 V LiFePO4 voltage range](https://www.redwayess.com/what-is-the-voltage-range-of-a-12v-lifepo4-battery/),
[voltage charts (12 V)](https://jetraybattery.com/battery-voltage-soc-complete-chart-guide-12v-24v-48v/).

## Voltage-floor fit vs the buck's input dropout

With the SK9822 (5 V) fed by a 12 V→5 V buck, the rail only needs to stay above the buck's
minimum input — ~6–7 V for a typical buck (5 V out + ~1–2 V dropout). Every "12 V"
chemistry clears this comfortably:

| Chemistry | Empty voltage | Clears ~6–7 V floor? |
|---|---|---|
| Lead-acid (50 % DoD) | ~10.5 V | ✅ |
| 3S Li-ion | 9.0 V | ✅ |
| 4S Li-ion | 12.0 V | ✅ |
| 4S LiFePO4 | 10.0 V | ✅ |
| 3S LiFePO4 | 7.5 V | ✅ (tight) |

- The buck absorbs the sag, so the LED color stays flat down to the buck's dropout.
- Practical guardrail: set the low-voltage disconnect above the dropout with margin
  (~9–10 V) to avoid brown-out at end of charge.

## Sizing (8 h @ 20 %)

| Brightness | Rail power (5 V baseline) | Battery |
|---|---|---|
| 10 % | 28 W | ~250 Wh |
| **20 %** | 56 W | **~500 Wh** |
| 50 % | 140 W | ~1250 Wh |
| 100 % | 280 W | ~2500 Wh |

Ah at nominal and weight for the target energy:

| Chemistry | Nominal | Ah for 500 Wh | Weight (500 Wh) |
|---|---|---|---|
| Lead-acid (35 Wh/kg) | 12.0 V | ~42 Ah | ~14 kg |
| 4S LiFePO4 (125 Wh/kg) | 12.8 V | ~39 Ah | ~4 kg |
| 3S Li-ion (200 Wh/kg) | 11.1 V | ~45 Ah | ~2.5 kg |

> ⚠️ Weights are cell-level (≈ energy ÷ density); add pack enclosure, BMS, and derating for
> a real number. Li-ion/LiFePO4 cells are usually rated at C/5–C/10; a high-C load or cold
> weather shaves usable capacity, so pad 20–30 % above the table for the build.

## Recommendation

- **Default for mobility: 4S LiFePO4 (12.8 V nominal, 10.0–14.6 V).** Safest chemistry,
  2000+ cycles, flat discharge. For the 8 h/20 % target, ~39 Ah / ~4 kg. Slightly heavier and
  pricier than Li-ion, but the lowest lifecycle cost and zero thermal-runaway risk for a
  wearable/costume-scale light.
- **If weight is the hard constraint: 3S Li-ion (~2.5 kg).** Its empty voltage (9.0 V) sits
  comfortably above the buck's dropout, so there is no floor penalty.
- **Lead-acid only** if cost is the sole driver and weight/cycle-life don't matter (static
  installs, not mobility): ~14 kg for the same energy.

## Open questions

- [ ] Confirm the actual average brightness the show runs at — "20 %" is an assumption and
      scales the battery linearly.
- [ ] Confirm discharge rate (C-rate) and cold-weather operation → derating factor.
- [ ] Pick the 12 V→5 V buck (input range, dropout, efficiency) — its minimum input sets the
      real battery floor.
- [ ] Set the low-voltage disconnect: a ~9–10 V cut protects the cells and keeps the rail
      above the buck's dropout with margin.
- [ ] Choose pack form factor (prismatic vs 18650/21700 vs pouch) and a BMS with the right
      per-cell cut-offs for the chosen chemistry.

## References

- LiFePO4 vs Li-ion vs lead-acid: https://walkingsolar.com/lifepo4-vs-lithium-ion-vs-lead-acid-which-battery-is-best-for-solar/
- Lead-acid vs lithium energy density: https://eszoneo.com/info-detail/lead-acid-vs-lithium-battery-energy-density-a-comprehensive-comparison-for-modern-power-systems
- 12 V LiFePO4 voltage range: https://www.redwayess.com/what-is-the-voltage-range-of-a-12v-lifepo4-battery/
- LiFePO4 voltage chart (SOC): https://www.lifepo4batteryshop.com/blogs/lifepo4-battery-voltage-chart-guide.html
- 12 V voltage/SOC charts: https://jetraybattery.com/battery-voltage-soc-complete-chart-guide-12v-24v-48v/
- 3S LiPo guide: https://www.ufinebattery.com/blog/an-ultimate-guide-about-3s-lipo-batteries/
- Lead-acid (flooded/AGM/gel) deep-cycle: https://howtostoreelectricity.com/lead-acid-batteries-for-solar/
- Project context: [controller design readiness](../../boards/controller/design-readiness.md)
