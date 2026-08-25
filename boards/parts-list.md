# Parts List — COTS (battery excluded)

> Brief sourcing summary. Full detail: [boards/README.md](README.md) (settled parts) and
> [pigtail crimping](../docs/pigtail-crimping.md). Prices approximate — verify before ordering.

| # | Part | Spec | Qty | Potential vendors |
|---|------|------|-----|-------------------|
| 1 | LED strip | SK9822 96 LED/m, 10 mm, 5050, 5 V | ~15 m (3×5 m) | [Alibaba 30/60/96/144](https://www.alibaba.com/product-detail/Individually-Addressable-APA102-SK9822-30-60_1601370513576.html) (96 option) · [JAD-LEDS 96/m](https://jad-leds.com/dc5v-ic-external-led-strip/467.html) |
| 2 | Controller | Pixelblaze V3 Standard | 1 | [ElectroMage (Tindie)](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) |
| 3 | Level shifter | 74AHCT125 Quad, 3.3→5 V (2 of 4 gates) | 1 | [Adafruit 1787](https://www.adafruit.com/product/1787) |
| 4 | Buck modules | MP1584EN 3 A (alt: XL4015 5 A) | ~6–8 | [DollaTek 5-pk](https://www.amazon.co.uk/DollaTek-MP1584EN-Step-Down-Adjustable-Converter/dp/B07DJ5HZ7G) — bench-test each |
| 5 | Fuses | ATO inline holders (alt: polyfuse) | ~10 | [Youngneer ATO kit](https://www.amazon.sg/Youngneer-Holders-Standard-Harness-Waterproof/dp/B07YY6KWSY) |
| 6 | Reverse polarity | MDD SS34, 3 A 40 V SMA | 1/hub | [LCSC C8678](https://www.lcsc.com/product-detail/C8678.html) |
| 7 | PH contacts | JST `SPH-002T-P0.5` (24–28 AWG) | ~550 | [DigiKey](https://www.digikey.sg/en/products/detail/jst-sales-america-inc/SPH-002T-P0-5L/26218852) · AliExpress bulk |
| 8 | PH housings | JST `PHR-2`, 2-pin | ~280 | DigiKey · [PH2.0 kits](https://www.amazon.com/dp/B09DP9FZTX) |
| 9 | PH headers | JST `B2B-PH-K-S`, 2-pin | ~120 | DigiKey · PH2.0 kits |
| 10 | Crimp tool | IWISS/iCrimp SN-28B | 1 | Amazon (~$20–30) |
| 11 | Wire | Silicone — 24 AWG red/black + 26–28 AWG data colors | ~15 m each | Amazon spool kits (e.g. [24 AWG 7-color](https://www.amazon.com/dp/B07TJXRGXM)) |

**Strip caveat:** 96/m SK9822 is niche — confirm **10 mm wide, open (non-waterproof) PCB, 96/m**
with the vendor and validate one reel before bulk.
