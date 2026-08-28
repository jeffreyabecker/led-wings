# Placement geometry — side-facing strips

## Light-cone model ⚠️ (estimates, not measured)

- SK9822 (5050 package) emits in a ~120° cone → **60° half-angle**.
- At a gap `h` above the LED, each LED lights a circle of radius **r = h·tan 60° ≈ 1.7h**.
- **Continuity along the strip**: adjacent LEDs (pitch `p`) need `2r ≥ p`. For 30/m
  (p = 33 mm) that means **h ≥ ~10 mm**.
- **Setback from the edge**: the edge stays lit while **d ≤ 1.7h**.
- Design sweet spot: **h ≈ 12 mm gap, d ≈ 10–15 mm setback**.

| Gap height h | Patch radius r | Max useful setback d | Result |
|---|---|---|---|
| 10 mm | 17 mm | ~15 mm | just continuous, edge clearly lit |
| 12 mm | 21 mm | ~20 mm | sweet spot — comfortable overlap |
| 15 mm | 26 mm | ~25 mm | best continuity, dimmer overall |

## Bubble-wrap behavior

- Each air bubble is a **convex lens** → it *focuses* light into a dot pattern; it does
  not spread sideways.
- It does **not pipe light** along its plane — light travelling sideways through it dies
  within ~10–20 mm ⚠️.
- Therefore: **air does the spreading, bubble wrap only finishes the exit** — a thin
  bubble-wrap strip at the edge only, never filling the setback gap.
- Bigger bubbles (20–25 mm) spread better than small ones; two layers offset by half a
  bubble pitch kill the dot pattern.

## Angled mount — the thickness fix

Vertical footprint of a strip mounted at angle θ: **thickness ≈ W·sin θ + 2 mm**
(2 mm = LED height above the PCB).

| Strip width | Angle θ | Total thickness |
|---|---|---|
| 10 mm standard | 15° | ~4.6 mm |
| 10 mm standard | 20° | ~5.4 mm |
| 10 mm standard | 25° | **~6.0 mm ✓** |
| 5 mm mini (5050, 2 mm LED) | 30° | ~4.3 mm |
| **5 mm FPC + SK9822-EC20 (2020, ~1 mm LED)** | 25° | **~3.0 mm ✓✓** |
| **5 mm FPC + SK9822-EC20** | 40° | **~4.0 mm ✓** |

The 2020 package's ~1 mm height (vs 5050's ~2 mm) makes the 5 mm strip even thinner
than the 10 mm plan — **5 mm wide + EC20 is the chosen configuration** (see
[custom-electronics/](custom-electronics/)).

- The ±60° beam is so wide that angling barely changes *coverage* — it mainly aims the
  beam center at the edge exit.
- **LED face must tilt TOWARD the edge** — a 180° flip is the classic assembly mistake.
- **White reflector wedge** behind the strip's back recovers the below-axis beam lobe →
  +30–40 % apparent edge brightness ⚠️, costs nothing.

## Strip width / density availability

- SK9822 exists only in the **5050 (5 mm) package** → a strip can't be narrower than its
  own LED; standard 30/m strips are **10 mm wide** ✅ ([Adafruit 30/m](https://core-electronics.com.au/adafruit-dotstar-led-strip-apa102-warm-white-30-led-m-3000k.html),
  [Pimoroni](https://shop.pimoroni.com/products/flexible-rgb-led-strip-dotstar-apa102-sk9822-compatible),
  [Volition 30/m](https://www.govolition.com/product/V102-3086)).
- **5 mm mini** APA102C/SK9822-compatible strips exist, but only at **144–200/m** ✅
  ([like-light 5 mm mini](https://www.like-light.com/nl/5mm-mini-dc5v-apa102c-sk9822-200-pixel-addressable-flex-led-strip.htm)).
- **2020-package SK9822** exists as bare chips ([rose-lighting](https://www.rose-lighting.com/products/addressable-digital-smart-mini-2020-pixel-led-chip-sk9822/))
  and dense strips ([xuananlighting 200/m](https://www.xuananlighting.com/DC5V-200LEDs-SK9822-APA102C-2020-RGB-digital-led-strip-XXA-200D2020RGB-APA102CSK9822-5V-p6858913.html))
  — but **not at 30/m**.
- **A 2 mm × 30/m SK9822 strip does not exist** ⚠️ — physically impossible with the
  5050 package; only hand-placed 2020 chips or custom orders approach it.

## Getting 30/m at 5 mm width — the firmware trick

- Buy **5 mm mini @ 144/m** (LED pitch 6.9 mm) and **light every 5th LED** → effective
  **~29/m ≈ 30/m** ✅; every 4th → ~36/m if denser is wanted.
- Unlit LEDs draw **zero current** and are invisible when off (black packages).
- Implementation: skip non-multiples of 5 in the FastLED render loop.
- Verify the listing's actual PCB width before ordering (some "5 mm" listings ship
  6–7 mm) ⚠️, and confirm clock+data (SK9822/APA102C) protocol, not one-wire.

## Recommended layout

1. **10 mm SK9822 @ 30/m** in a slot at the feather edge, **~20–25° tilt**, LED face
   toward the edge, set back **~10–15 mm** (LED-to-exit path ≥ ~10 mm).
2. Bubble wrap: **thin strip at the edge exit only**.
3. White reflector wedge behind the strip's back.
4. If 5 mm width is mandatory: **144/m mini + every-5th-LED** trick, same geometry.
