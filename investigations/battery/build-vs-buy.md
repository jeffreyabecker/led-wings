# Battery Pack — Build vs Buy & Constructability

> Decide how to source the pack: buy a complete pack with integrated BMS vs assemble cells +
> a bought BMS board. Two things actually drive the choice: **constructability** (LiPo pouch
> vs 18650) and the **backpack-worn weight ceiling**.
>
> Legend: ✅ = sourced · ⚠️ = estimate.

## Constructability: LiPo pouch vs 18650 — "are pouches actually easier?"

Short answer: **pouches are easier to *fit*, harder to *terminate*; 18650s are the reverse.**

| | LiPo pouch (raw cell) | 18650 cylinder |
|---|---|---|
| Shape / fit | flat, thin — a few pouches replace ~50 cylinders | rigid rounds, bulky, many cells |
| Cell connection | solder/weld tabs — heat-damages the cell, delicate | **spring holders (zero welding)** or spot-weld strip |
| Mechanical | soft — puncture/swell risk, needs compression + hard case | steel can + vent — robust |
| Safety (near body) | higher fire risk if punctured | safer |
| Easiest DIY route | buy a pre-built RC pack (skip DIY) | **holders + bought BMS** |

The "pouches are easier" feeling conflates two things: **pre-built RC LiPo packs** are
buy-and-plug (easy, but no BMS and pricey per Wh), and the flat form factor. Building from
**raw** pouch cells is actually the *harder* path (tab termination + fragile pouch). For a DIY
build with a bought BMS, **18650 in spring holders is the most hobbyist-friendly** — no
welding, no soldering to cells, just drop cells into holders and wire the holders.

## Build vs buy — cost

Cell/BMS ballparks: 18650 Samsung 35E (3500 mAh) ~$4–6/cell ⚠️ · 3S 60 A BMS board ~$5–15 ✅ ·
raw LiPo pouch ~$0.3–0.5/Wh one-off ⚠️.

| Approach | Energy | Cost | $/Wh | BMS | Weight | Size (L×W×H) |
|---|---|---|---|---|---|---|
| **Buy** LiFePO4 100 Ah drop-in | 1280 Wh | ~$200–350 ✅ | $0.16–0.27 | built-in ✅ | ~10–12 kg | ~330×172×214 ⚠️ |
| **Buy** LiFePO4 50 Ah drop-in | 640 Wh | ~$120–200 ⚠️ | $0.19–0.31 | built-in ✅ | ~5.5–6.5 kg | ~195×166×172 ⚠️ |
| **Buy** NMC 12 V portable | 640–1280 Wh | ~$150–400 ⚠️ | $0.23–0.31 | built-in ✅ | ~3.5–8 kg | varies |
| **Buy** RC 3S LiPo (pre-built) | 244 Wh/pk | ~$100–150 ✅ | $0.4–0.6 | ❌ add $5–15 | ~1.2 kg/pk | ~180×60×45 ⚠️ |
| **Build** 18650 (holders) | 640 Wh | ~$300–375 ⚠️ | $0.47–0.59 | ✅ bought | ~3.2–3.5 kg | custom |
| **Build** LiPo pouch (raw) | 640 Wh | ~$370–500 ⚠️ | $0.58–0.78 | ✅ bought | ~3.5–4 kg | custom |

**Finding: buying is cheaper per Wh than building from retail cells.** Pack makers buy cells
wholesale (~$0.1–0.2/Wh) while you pay retail (~$0.35–0.5/Wh), so a complete pack undercuts a
DIY build on $/Wh *and* includes the BMS. The "cheaper to buy off-the-shelf" assumption holds
— for integrated packs. The reasons to build are form factor, shaving weight below a generic
box, or a cheap cell source, not cost.

## Proposed off-the-shelf pack — dimensions

The 2000-px / 8 h / 20 % target needs ~710 Wh at ≤ 5 kg. The single pack that clears *both* is
**Rebelcell 12V70 AV** (Li-ion NMC, 70 Ah, built-in BMS + charge indicator):

| Model | Energy | Weight | Size (L×W×H) | Fits ~710 Wh? | ≤ 5 kg? |
|---|---|---|---|---|---|
| **Rebelcell 12V70 AV** ✅ | **836 Wh** | **4.9 kg** | **195 × 130 × 155 mm** | ✅ | ✅ |
| Rebelcell 12V50 AV | 634 Wh | 3.9 kg | 195 × 130 × 155 mm | ~11 % short ⚠️ | ✅ |
| MANLY 12V60 LiFePO4 | 768 Wh | 5.8 kg | 195 × 166 × 170 mm | ✅ | ❌ (5.8) |
| ProPow 12V60 LiFePO4 | 768 Wh | 8.0 kg | 198 × 166 × 186 mm | ✅ | ❌ (8.0) |
| Redodo 12V50 LiFePO4 | 640 Wh | 5.3 kg | 195 × 166 × 172 mm | ~10 % short ⚠️ | ❌ (5.3) |

- **Only the Rebelcell 12V70 AV meets the target**: 836 Wh > 710 Wh needed (≈18 % headroom)
  **and** 4.9 kg < 5 kg hard max. The runner-up (12V50, 3.9 kg) is lighter but ~11 % short on
  energy; the LiFePO4 60 Ah packs have the energy but bust the weight cap.
- Note: an older Rebelcell manual lists the 12V70 AV at 260 × 167 × 210 mm / 6.1 kg; the
  current official site + SMG Europe + Anglers World + valciucentras all give **195 × 130 ×
  155 mm / 4.9 kg**, which is what this table uses (the bigger figure is a superseded/boxed
  variant). ⚠️ Confirm at purchase.

## Weight ceiling — backpack-worn, ~2 kg rest of project

For 8 h of wear, keep **total** (structure + battery) ≤ ~6 kg comfortable / ~7 kg hard max →
**battery ≤ ~4 kg comfortable, ~5 kg hard max** (rest ≈ 2 kg).

| Battery | Energy (18650 ~200 Wh/kg) | Pixels @ 8 h / 20 % |
|---|---|---|
| 3 kg | ~600 Wh | ~1690 |
| **4 kg (comfortable ceiling)** | **~800 Wh** | **~2250** |
| 5 kg (hard max) | ~1000 Wh | ~2810 |

(Wh ≈ pixels × 0.356; LiPo ~170 Wh/kg gives ~1910 px @ 4 kg.)

**Consequence: the target is now 2000 px → ~710 Wh → ~4 kg of lithium at the comfortable
ceiling (LiPo ~4.2 kg / 18650 ~3.6 kg), and fits within the 5 kg hard max.** The proposed
off-the-shelf **Rebelcell 12V70 AV (836 Wh / 4.9 kg)** sits right at the hard ceiling with ~18 %
energy headroom. 2800 px would have needed ~5 kg+ (hard/tiring).

## Synthesis

- **Cheapest + no DIY BMS = buy LiFePO4**, but ~5.5–6.5 kg at 640 Wh — over the 5 kg hard max
  for the 2000-px target (and the ~60 Ah packs bust the cap on weight).
- **Recommended off-the-shelf = Rebelcell 12V70 AV** (NMC, 836 Wh / 4.9 kg / 195×130×155 mm) —
  the only pack found that clears *both* the ~710 Wh energy and the 5 kg hard max, with a
  built-in BMS and charge indicator.
- **At the 4 kg comfortable ceiling**, buyable options are NMC "portable lithium" (~50–60 Ah)
  or **RC 3S LiPo + a bought BMS** (lightest, ~2.4–2.8 kg for 488 Wh, but pricey/Wh and bare).
- **Build (18650 holders + bought BMS)** is the lightest *sensible* DIY and needs no welding,
  but ~2× the $/Wh of buying and still ~3.2–3.5 kg.
- Bottom line: **"no DIY BMS + cheap + light enough" → buy Rebelcell 12V70 AV (or an NMC
  portable); "lightest, willing to assemble but not design a BMS" → RC LiPo + bought BMS, or
  18650 holders.** All paths reach the 2000-px target (~710 Wh); the choice is cost vs weight
  vs assembly effort.

## Open questions

- [ ] Confirm actual brightness — the pixel ceiling is a direct function of it.
- [ ] Pixel target set to **2000 px** (~710 Wh) — fits within the 5 kg hard max.
- [x] **Proposed off-the-shelf battery sized**: Rebelcell 12V70 AV, **836 Wh / 4.9 kg /
      195×130×155 mm** — only pack clearing ~710 Wh at ≤ 5 kg (⚠️ confirm the current,
      non-superseded spec at purchase).
- [ ] Verify NMC 12 V portable packs at ~50–60 Ah retail (the ~4 kg sweet spot).
- [ ] If building: 18650 holders (no welding) vs spot-weld vs pre-built RC LiPo + BMS.

## References

- 3S 60 A BMS board (~$5–15): https://shehzadelectronics.com/product/3s-60a-bms-li-ion-lithium-battery-charger-protection-board-18650-bms-11-1v-12v/
- Samsung 35E 18650 (3500 mAh, ~$4–6/cell): https://www.unemetech.com/sale-48206548-samsung-35e-18650-battery-3500mah-8a-3-6v-cylindrical-lithium-ion-cell-inr18650-35e.html
- RC 3S LiPo 22000 mAh: https://maxamps.com/products/lipo-22000-3s-11-1v-battery-pack
- 12 V LiFePO4 100 Ah (LiTime): https://www.amazon.com/dp/B084DB36KW
- 12 V Li-ion NMC portable: https://www.amazon.ca/dp/B0D2NQ1DZD
- **Rebelcell 12V70 AV (836 Wh / 4.9 kg / 195×130×155 mm)** — [official (Dec-2023)](https://web.archive.org/web/20231207230358/https://www.rebel-cell.com/product/12v70-av-battery/), [SMG Europe](https://www.smgeurope.com/automotive/rebelcell-12v70-av-li-ion-battery-12v-70a-836wh.html), [Anglers World](https://www.anglersworld.ie/en-gb/collections/rebelcell/products/rebelcell-12v70-av-li-ion-battery-12v-70a-836wh), [valciucentras](https://www.valciucentras.lt/akumuliatoriai-valtims/rebelcell-li-ion-12v-70ah-battery)
- Rebelcell 12V50 AV (634 Wh / 3.9 kg): [valciucentras](https://www.valciucentras.lt/Elektriniai-valciu-varikliai-akumuliatoriai-ikrovejai-dalys/Akumuliatoriai/rebelcell-li-ion-12v-50ah-battery)
- LiFePO4 60 Ah (energy but over weight): [MANLY 768 Wh / 5.8 kg](https://manlybattery.com/product-item/12v-60ah-lifepo4-battery/) · [ProPow 768 Wh / 8.0 kg](https://www.propowenergy.com/12v-60ah-lifepo4-battery-cp12060-battery-product/)
- LiFePO4 50 Ah (light-ish but short on energy): [Redodo 640 Wh / 5.3 kg](https://ca.redodopower.com/products/redodo-12v-50ah-lifepo4-battery-640wh-640w)
- Project context: [battery options](options.md)
