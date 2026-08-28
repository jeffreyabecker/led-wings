# Power architecture (from the same design conversation)

Context: 5 V **SK9822** addressable strips (SPI, clock + data), single ESP32 controller,
4S LiPo battery with distributed buck converters. Earlier 12 V strip assumptions were
superseded once the available part turned out to be 5 V addressable.

## LED counts ⚠️ (2 m wingspan assumption)

- Vanes @ 30/m (area 0.3 m²/wing, strips ~one LED-pitch apart): ~9.1 m strip/wing →
  ~273 LEDs/wing (~546 total)
- Radius + carpal @ 60/m, 3 strips × 0.8 m: ~2.4 m/wing → ~144 LEDs/wing (~288 total)
- **~830 LEDs total ≈ 22.8 m of strip**
- Density is a *mounting* decision for addressable strips — "15/m" is achievable by
  spacing segments or, for the mini strip, by lighting every Nth LED.

## Power at 5 V (SK9822 = 60 mA/LED full white → 0.3 W/LED) ✅

| Brightness | Power | Current @ 5 V |
|---|---|---|
| 100 % | ~249 W | ~50 A |
| 50 % | ~125 W | ~25 A |
| 25 % | ~62 W | ~12.4 A |
| 10 % | ~25 W | ~5 A |
| 5 % | ~12.5 W | ~2.5 A |

- 8 h runtime target needs **~220 Wh @ 10 % brightness** (incl. ~10 % buck loss) ⚠️.
- Set a **firmware brightness cap ≤ 40 %** (target 25–33 %) so a bug can't command 50 A.

## Distribution: 4S → 5 V buck converters

- **MP1584EN**: ~1.5–2 A continuous ≈ 7.5–10 W @ 5 V ⚠️ (the 3 A rating is peak).
- Rule: **~1 buck per 10 feathers** — ~4 per wing for vanes (≈35 feathers/wing ⚠️:
  ~10 primaries + ~10 secondaries + ~10 greater coverts + ~4 alula) and 3 per wing for
  structure strips (1 per strip, 48 LEDs each) → **~14 MP1584EN total** (~$25).
- Each buck feeds ≤ 0.4 m of strip → short 5 V runs, negligible voltage drop — the
  right topology for 5 V.
- 4S input (12–16.8 V) → regulated 5 V = constant brightness across discharge.

## Battery

- **4S 16000 mAh** (237 Wh, ~17 × 7 × 4.5 cm, ~1.1–1.2 kg) → ~8.6 h @ 10 % ⚠️
  ([Tattu 16000 30C](https://www.nextfpv.com.au/collections/lipo-battery/products/tattu-16000mah-30c-14-8v-4s-lipo-battery-pack-with-xt90-s-plug),
  [Lumenier 16000 4S 20C](https://www.lumenier.com/products/lumenier-16000mah-4s-20c-lipo-battery)).
- Prefer **2× 4S 8000 mAh** for weight balance (one per wing, ~600 g each) and pack
  redundancy.
- **Low-C packs are the value pick**: 10C "high capacity" packs ≈ $0.42/Wh vs 30C
  ≈ $0.75/Wh ✅ ([Multistar 10000 10C](https://hobbyking.com/en_us/multistar-high-capacity-4s-10000mah-multi-rotor-lipo-pack.html),
  [Multistar 16000 10C](https://hobbyking.com/en_us/multistar-high-capacity-4s-16000mah-multi-rotor-lipo-pack.html),
  [Gens Ace G-Tech 8000 10C](https://www.gearrc.com/gens-ace-g-tech-8000mah-14-8v-10c-4s-lipo-battery-ec5-plug-gea8k4s10e5gt-1-97860)).
  Draw is only ~1–2 C, so 10 C is 5–10× headroom.
- Fits a standard hip bag; needs a LiPo safety pouch + XT60 quick-disconnect loom to the
  wings (strain relief at bag exit).

## Controller

- Single **ESP32**: all ~830 LEDs on one SPI daisy chain (SK9822 = clock + data, no
  one-wire timing constraints).
- 2 MHz clock → ~13 ms/frame ≈ **75 fps** ✅; 5 MHz → ~190 fps if wanted.
- **Level shifter required**: SK9822 logic-high ≈ 0.7·VDD ≈ 3.5 V > ESP32's 3.3 V ⚠️ —
  74HCT245 + 330 Ω series resistors on data/clock.

## USB-C power bank — rejected

- 100 W banks deliver 20 V/5 A peak, but the 12 V rail is typically capped at 3 A
  (36 W); a PD-trigger + buck would be needed anyway.
- Capacity kills it: 8 h @ 10 % needs ~220 Wh ≈ **3× 27,000 mAh (100 Wh) banks**; only
  5 % brightness was single-bank-viable, and that ran the bank near its continuous max
  (thermal throttle risk).

## Open items

- Confirm real feather count per wing (assumed ~35) — vane buck count scales 1 per 10
  feathers.
- Confirm per-feather edge length for the LED-to-exit continuity number (≥ ~10 mm path).
- Verify the 5 mm mini listing's actual PCB width and protocol (SK9822/APA102C, not
  one-wire).
