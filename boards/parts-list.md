# Parts List — COTS (battery excluded)

> Brief sourcing summary. Full detail: [boards/README.md](README.md) (settled parts) and
> [pigtail crimping](../docs/pigtail-crimping.md). Connectors: **Molex Micro-Fit 3.0, 2-pin
> per function** (1×2, 2-circuit) — vendors TBD (not yet researched).

| # | Part | Spec | Qty | Potential vendors |
|---|------|------|-----|-------------------|
| 1 | LED strip | SK9822 96 LED/m, 10 mm, 5050, 5 V | ~15 m (3×5 m) | [Alibaba 30/60/96/144](https://www.alibaba.com/product-detail/Individually-Addressable-APA102-SK9822-30-60_1601370513576.html) (96 option) · [JAD-LEDS 96/m](https://jad-leds.com/dc5v-ic-external-led-strip/467.html) |
| 2 | Controller | Pixelblaze V3 Standard | 1 | [ElectroMage (Tindie)](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) |
| 3 | Level shifter | 74AHCT125 Quad, 3.3→5 V (2 of 4 gates) | 1 | [Adafruit 1787](https://www.adafruit.com/product/1787) |
| 4 | Buck modules | MP1584EN 3 A (alt: XL4015 5 A) | ~6–8 | [DollaTek 5-pk](https://www.amazon.co.uk/DollaTek-MP1584EN-Step-Down-Adjustable-Converter/dp/B07DJ5HZ7G) — bench-test each |
| 5 | Fuses | ATO inline holders (alt: polyfuse) | ~10 | [Youngneer ATO kit](https://www.amazon.sg/Youngneer-Holders-Standard-Harness-Waterproof/dp/B07YY6KWSY) |
| 6 | Reverse polarity | MDD SS34, 3 A 40 V SMA | 1/hub | [LCSC C8678](https://www.lcsc.com/product-detail/C8678.html) |
| 7 | Micro-Fit receptacle 2-pin | Molex `43025-0200`, 1×2 (2-circuit) | ~300 | TBD |
| 8 | Micro-Fit plug 2-pin | Molex `43645-0200`, 1×2 (2-circuit) | ~300 | TBD |
| 9 | Micro-Fit contacts | Socket `43031-xxxx` + pin `43030-xxxx` (20–24 AWG) | ~650 + ~650 | TBD |
| 10 | Crimp tool | Molex 63811-1000 (or ratchet + Micro-Fit dies) | 1 | TBD |
| 11 | Micro-Fit pigtails (pre-made) | 2-pin plug↔receptacle / female-to-pigtail, 10–30 cm | ~90 | [Molex OTS 214751-2022 (F-to-pigtail)](https://www.molex.com/ja-jp/products/series-chart/214751?sku=2147512022&description=Micro-Fit%203.0%20Female-to-Pigtail%20Off-the-Shelf%20(OTS)%20Cable%20Assembly,%20Single%20Row,%20300.00mm%20Length,%20Gold%20(Au)%20Plating,%202%20Circuits,%20Black&pageSize=25&page=0#1) · [RS 2-way F-to-pigtail](https://ph.rs-online.com/web/p/wire-to-board-cables/2044622) · [TME MX-214770-0220](https://www.tme.com/ph/en/details/mx-214770-0220/wire-to-board-cable-assemblies/molex/2147700220/) · [DigiKey](https://www.digikey.se/en/products/detail/molex/2147572023/12180315) |
| 12 | Wire | Silicone — 20–22 AWG red/black (power), 24 AWG data colors | ~15 m each | TBD |

**Strip caveat:** 96/m SK9822 is niche — confirm **10 mm wide, open (non-waterproof) PCB, 96/m**
with the vendor and validate one reel before bulk.

**Pigtails: pre-made vs hand-crimp.** Pre-made 2-pin pigtails (row 11) can replace hand
crimping — rows 9–10 then shrink to repair spares. ⚠️ Micro-Fit contacts are 20–24 AWG: power
20–22 AWG, data 24 AWG.
