# Battery Options — Wearable Mobility Power

> Pick the battery that feeds the fixed 12 V rail (wall supply for dev, battery for
> mobility). The pixel is locked to the SK9822-EC20 (5 V), powered through a 12 V→5 V buck,
> so the battery only has to stay above the buck's input dropout (~6–7 V). **Wearable →
> weight is a first-class constraint.**
>
> Legend: ✅ = sourced · ⚠️ = estimate, to confirm.

## Requirements recap

- Fixed **12 V** system; battery must hold the rail above the 12 V→5 V buck's input dropout
  across its full discharge.
- Runtime target: **8 h at 20 % brightness** (typical animated look, not full-white).
- Pixel target: **2000 px** (set after the weight analysis; pixel count is the dominant
  weight lever).
- Energy needed: SK9822 @ 5 V via a 12 V→5 V buck (~90 %): **~710 Wh**.

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

- **Weight is the wearable's hard constraint → Li-ion/LiPo wins.** LiFePO4 is the safest and
  longest-lived but ~1.5–2× heavier per Wh — it is *rejected* here despite being the best
  cycle-life/safety choice.
- **Li-ion (NMC/LiPo) is the lightest**, but it *must* have a BMS and is the fire-risk option;
  3S and 4S differ only in voltage (4S is what "12 V automotive replacement" packs are).
- **3S LiFePO4 is too low** (9.6 V nominal) — rejects itself as a "12 V" rail.
- Lead-acid is cheapest but ~4–5× heavier — static installs only, not wearable.

Sources: [LiFePO4 vs Li-ion vs lead-acid](https://walkingsolar.com/lifepo4-vs-lithium-ion-vs-lead-acid-which-battery-is-best-for-solar/),
[lead-acid vs lithium energy density](https://eszoneo.com/info-detail/lead-acid-vs-lithium-battery-energy-density-a-comprehensive-comparison-for-modern-power-systems),
[3S LiPo guide](https://www.ufinebattery.com/blog/an-ultimate-guide-about-3s-lipo-batteries/),
[12 V LiFePO4 voltage range](https://www.redwayess.com/what-is-the-voltage-range-of-a-12v-lifepo4-battery/),
[voltage charts (12 V)](https://jetraybattery.com/battery-voltage-soc-complete-chart-guide-12v-24v-48v/).

## Voltage-floor fit vs the buck's input dropout

With the SK9822 (5 V) fed by a 12 V→5 V buck, the rail only needs to stay above the buck's
minimum input — ~6–7 V for a typical buck (5 V out + ~1–2 V dropout). Every "12 V" chemistry
clears this comfortably, which is what **frees us to use 3S Li-ion** (the lightest option)
rather than being forced to 4S:

| Chemistry | Empty voltage | Clears ~6–7 V floor? |
|---|---|---|
| Lead-acid (50 % DoD) | ~10.5 V | ✅ |
| 3S Li-ion | 9.0 V | ✅ |
| 4S Li-ion | 12.0 V | ✅ |
| 4S LiFePO4 | 10.0 V | ✅ |
| 3S LiFePO4 | 7.5 V | ✅ (tight) |

- The buck absorbs the sag, so LED color stays flat down to the buck's dropout.
- Practical guardrail: set the low-voltage disconnect above the dropout with margin
  (~9–10 V) to avoid brown-out at end of charge.

## Sizing (2000 px target)

| | Full white | 20 % brightness |
|---|---|---|
| Rail power (2000 × 0.2 W) | 400 W (80 A @ 5 V) | **80 W** |
| Battery draw (÷ 90 % buck) | ~444 W | **~89 W** |
| 8 h energy | ~3.6 kWh | **~710 Wh** |

Scaling (linear in pixel count — the main lever):

> **Battery Wh ≈ pixels × 0.356** (8 h @ 20 %, battery-side) · **LiPo weight ≈ Wh ÷ 170 kg**

| Pixels | Battery energy | LiPo weight (~170 Wh/kg) |
|---|---|---|
| 2800 | ~1000 Wh | ~5.9 kg |
| **2000 (target)** | **~710 Wh** | **~4.2 kg** |
| 1400 | ~500 Wh | ~2.9 kg |
| 700 | ~250 Wh | ~1.5 kg |
| 350 | ~125 Wh | ~0.73 kg |

> ⚠️ Weights are pack-level (≈ energy ÷ ~170 Wh/kg for LiPo with enclosure + BMS). Cells are
> usually rated at C/5–C/10; a high-C load or cold weather shaves usable capacity, so pad
> 20–30 % above the table for a real build.

## Recommendation

- **Default: 3S Li-ion — LiPo pouch or 18650 — ~11.1 V nominal, ~64 Ah / ~710 Wh for the
  2000-px target.** This is the weight-optimal chemistry for a wearable, and 3S (not 4S) is
  now usable because the 12 V→5 V buck absorbs the voltage sag.
- **LiPo pouch** is the lightest and most formable, but needs a hard enclosure + BMS (puncture
  → fire, and this sits near the body). **18650 (3S ~18P)** is slightly heavier but inherently
  robust — safer for a bumpable wearable. Pick on form-factor/safety, not chemistry.
- **LiFePO4 is rejected for wearable** (1.5–2× heavier); lead-acid is rejected (4–5× heavier).
- Reality check: ~710 Wh ≈ **~4 kg** — right at the comfortable backpack ceiling (LiPo
  ~4.2 kg, 18650 ~3.6 kg). Charging + thermal management are real but manageable at this
  scale.

## Next step — off-the-shelf pack (before specifying cells)

Do **not** spec a custom cell configuration yet. First investigate buying an off-the-shelf
pack — RC/hobby 3S LiPo packs, "12 V" Li-ion/LiFePO4 power-station/e-bike packs, and 12 V
replacement packs — for availability, included BMS, capacity, weight, and cost. A purchased
pack with an integrated BMS and enclosure is strongly preferred over a DIY cell build at
~710 Wh (safety + certification).

## Open questions

- [ ] **Off-the-shelf pack survey (next).** RC 3S LiPo vs "12 V" Li-ion/LiFePO4 packs vs
      e-bike packs: capacity, weight, BMS included, discharge rating, cost.
- [ ] Confirm the actual average brightness — "20 %" is an assumption and scales linearly.
- [ ] Pixel target is **2000 px** (locked); the scaling table gives the cost of any change.
- [ ] Set the low-voltage disconnect (~9–10 V) above the buck's dropout.
- [ ] Charging: a ~710 Wh pack needs a real charger (~0.5 C ≈ 350 W) and thermal management.
- [ ] Safety: enclosure, BMS, fusing, and thermal monitoring are non-negotiable at ~710 Wh.

## References

- LiFePO4 vs Li-ion vs lead-acid: https://walkingsolar.com/lifepo4-vs-lithium-ion-vs-lead-acid-which-battery-is-best-for-solar/
- Lead-acid vs lithium energy density: https://eszoneo.com/info-detail/lead-acid-vs-lithium-battery-energy-density-a-comprehensive-comparison-for-modern-power-systems
- 12 V LiFePO4 voltage range: https://www.redwayess.com/what-is-the-voltage-range-of-a-12v-lifepo4-battery/
- LiFePO4 voltage chart (SOC): https://www.lifepo4batteryshop.com/blogs/lifepo4-battery-voltage-chart-guide.html
- 12 V voltage/SOC charts: https://jetraybattery.com/battery-voltage-soc-complete-chart-guide-12v-24v-48v/
- 3S LiPo guide: https://www.ufinebattery.com/blog/an-ultimate-guide-about-3s-lipo-batteries/
- Lead-acid (flooded/AGM/gel) deep-cycle: https://howtostoreelectricity.com/lead-acid-batteries-for-solar/
- Project context: [controller design readiness](../../boards/controller/design-readiness.md)
