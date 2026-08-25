# Parts List — COTS (battery excluded)

> Brief sourcing summary. Full detail: [boards/README.md](README.md) (settled parts) and
> [pigtail crimping](../docs/pigtail-crimping.md). Connectors: **JST PNI** (2.0 mm pitch,
> wire-to-wire, crimp both ends) — vendors TBD (not yet researched). **All pigtails are
> hand-made** (no pre-made).
> **Current plan:** wiring organized so no single run exceeds ~2–3 A (PNI class rating —
> confirm exact value in the [ePNI-WW datasheet](http://www.jst-india.com/downloads/series/ePNI-WW_(21-08-25).pdf)).

| # | Part | Spec | Qty | Potential vendors |
|---|------|------|-----|-------------------|
| 1 | LED strip | SK9822 96 LED/m, 10 mm, 5050, 5 V | ~15 m (3×5 m) | [Alibaba 30/60/96/144](https://www.alibaba.com/product-detail/Individually-Addressable-APA102-SK9822-30-60_1601370513576.html) (96 option) · [JAD-LEDS 96/m](https://jad-leds.com/dc5v-ic-external-led-strip/467.html) |
| 2 | Controller | Pixelblaze V3 Standard | 1 | [ElectroMage (Tindie)](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) |
| 3 | Level shifter | 74AHCT125 Quad, 3.3→5 V (2 of 4 gates) | 1 | [Adafruit 1787](https://www.adafruit.com/product/1787) |
| 4 | Buck modules | MP1584EN 3 A (practical ~2–2.5 A, **no heatsink**) — cluster ≤ ~2 A full-white | ~6–8 | [DollaTek 5-pk](https://www.amazon.co.uk/DollaTek-MP1584EN-Step-Down-Adjustable-Converter/dp/B07DJ5HZ7G) — bench-test each (counterfeits common) |
| 5 | Fuses | ATO inline holders (alt: polyfuse) | ~10 | [Youngneer ATO kit](https://www.amazon.sg/Youngneer-Holders-Standard-Harness-Waterproof/dp/B07YY6KWSY) |
| 6 | Reverse polarity | MDD SS34, 3 A 40 V SMA | 1/hub | [LCSC C8678](https://www.lcsc.com/product-detail/C8678.html) |
| 7 | PNI receptacle 2-pin | JST `PNIRR-02VF` | ~300 | TBD |
| 8 | PNI plug 2-pin | JST `PNIRP-02V-S` | ~300 | TBD |
| 9 | PNI contacts | Socket `SPNI-001T-P0.5` + pin `BPNI-001T-P0.5` | ~650 + ~650 | TBD |
| 10 | Crimp tool | JST PN-family tool or ratchet + PN dies (**SN-28B does NOT fit**) | 1 | TBD |
| 11 | Wire | Silicone — 20–22 AWG red/black (power), 24 AWG yellow (data) + green (clock) | ~15 m each | TBD |

**Strip caveat:** 96/m SK9822 is niche — confirm **10 mm wide, open (non-waterproof) PCB, 96/m**
with the vendor and validate one reel before bulk.

**Pigtails:** all hand-crimped (no pre-made) — rows 7–10 quantities assume the full hand-crimp.
⚠️ PNI is 2.0 mm class: keep any single run ≤ ~2–3 A (wiring plan), power 20–22 AWG, data 24 AWG.
