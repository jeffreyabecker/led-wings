# Power architecture (from the same design conversation)

Context: 5 V **SK9822** addressable strips (SPI, clock + data), single ESP32 controller,
4S LiPo battery with distributed buck converters. Earlier 12 V strip assumptions were
superseded once the available part turned out to be 5 V addressable.

## LED counts ✅ (measured totals — feather-record.csv, no scaling)

> **Basis (2026-08):** per-feather **measured totals** from
> [`mechanical/templates/feather-record.csv`](../../mechanical/templates/feather-record.csv)
> (authoritative). The × 1.024 / P4 = 55 cm projection is **superseded** (CSV: P4 = 43.0 cm).
> **Basis = total feather length** (the CSV carries no vane column).

Per wing, strip length = measured feather total (cm), density 30/m (33.3 mm pitch),
LEDs = ceil(total × 0.3):

| Group | Feathers | Total (m) | LEDs (ceil) |
|---|---|---:|---:|
| Primaries P1–P10 | 10 | 3.71 | 116 |
| Secondaries S1–S10 | 10 | 2.39 | 76 |
| Alula A1–A4 | 4 | 0.52 | 17 |
| Primary coverts PC1–PC6 | 6 | 0.90 | 31 |
| Secondary coverts SC1–SC10 | 10 | 1.57 | 51 |
| Median coverts MC1–MC5 | 5 | 0.56 | 19 |
| Lesser coverts L1–L6 | 6 | 0.47 | 17 |
| Underwing U1–U10 | 10 | 1.38 | 47 |
| **Feathers per wing** | **61** | **11.50** | **374** |
| Structure (3 × 0.8 m) | 3 | 2.40 | 72 |
| **Per wing** | **64** | **13.90** | **446** |
| **Both wings** | **128** | **27.80** | **892** |

Feathers only: 11.50 m/wing, 374 LEDs/wing → 748 both wings. LED positions incl. 19
dark/wing (board-chain rounding): 393/wing → 786 both wings
([board-inventory](custom-electronics/board-inventory.md)).

## Power at 5 V (SK9822-EC20 = 40 mA/LED full white → 0.2 W/LED) ✅

| Brightness | Power (892 LEDs) | Current @ 5 V |
|---|---|---|
| 100 % | ~178 W | ~36 A |
| 50 % | ~89 W | ~18 A |
| 25 % | ~45 W | ~9 A |
| 10 % | ~18 W | ~3.6 A |
| 5 % | ~9 W | ~1.8 A |

(Feathers only, 748 LEDs: subtract ~16 %.)

- 8 h runtime: **~158 Wh @ 10 %** (incl. ~10 % buck loss) → 4S 10000 ≈ 7.5 h;
  4S 16000 ≈ 12 h ⚠️. At 5 %: ~79 Wh → 4S 5000 ≈ 7.4 h.
- Set a **firmware brightness cap ≤ 40 %** (target 25–33 %) so a bug can't command 36 A.

## Distribution: 4S → 5 V buck converters

- **MP1584EN**: ~1.5–2 A continuous ≈ 7.5–10 W @ 5 V ⚠️ (the 3 A rating is peak).
- Rule: **~1 buck per 10 feathers** — ~6 per wing for vanes (61 feathers/wing) and 3 per
  wing for structure strips (1 per strip, 48 LEDs each) → **~18 MP1584EN total** (~$32).
- Each buck feeds ≤ 0.4 m of strip → short 5 V runs, negligible voltage drop — the
  right topology for 5 V.
- 4S input (12–16.8 V) → regulated 5 V = constant brightness across discharge.

## Battery

- **4S 16000 mAh** (237 Wh, ~17 × 7 × 4.5 cm, ~1.1–1.2 kg) → ~12 h @ 10 % ⚠️
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

- Single **ESP32**: all ~890 LEDs on one SPI daisy chain (SK9822 = clock + data, no
  one-wire timing constraints).
- 2 MHz clock → ~13 ms/frame ≈ **75 fps** ✅; 5 MHz → ~190 fps if wanted.
- **Level shifter required**: SK9822 logic-high ≈ 0.7·VDD ≈ 3.5 V > ESP32's 3.3 V ⚠️ —
  74HCT245 + 330 Ω series resistors on data/clock.

## USB-C power bank — rejected

- 100 W banks deliver 20 V/5 A peak, but the 12 V rail is typically capped at 3 A
  (36 W); a PD-trigger + buck would be needed anyway.
- Capacity kills it: 8 h @ 10 % needs ~158 Wh ≈ **2× 27,000 mAh (100 Wh) banks**; only
  5 % brightness was single-bank-viable, and that ran the bank near its continuous max
  (thermal throttle risk).

## Open items

- Confirm per-feather edge length for the LED-to-exit continuity number (≥ ~10 mm path).
- Verify the 5 mm mini listing's actual PCB width and protocol (SK9822/APA102C, not
  one-wire).
