# 12 V → 5 V Conversion Options — SK9822-EC20

> The pixel is locked: **SK9822-EC20, 5 V, individually addressable** (2-wire DATA+CLK). The
> source is fixed at **12 V**. That creates exactly one new problem: **the 12 V rail must be
> stepped to 5 V, and 5 V must reach ~140 feathers.**
>
> Legend: ✅ = sourced · ⚠️ = estimate, to confirm. Prices in ¥ (LCSC/module).

## Load model

| | Full white (worst case) | 20 % brightness (target) |
|---|---|---|
| Per pixel | 40 mA @ 5 V = 0.2 W | 8 mA avg = 0.04 W |
| Total (~1400 px) | **280 W / 56 A @ 5 V** | **56 W / 11 A @ 5 V** |
| Per board (~10 px) | 2 W / 0.4 A | 0.4 W / 0.08 A |
| Hub 12 V rail (buck input) | ~26 A | ~5.2 A |

> 20 % brightness is the operating point; full white is a brief ceiling. Everything below
> hangs on that distinction.

## The core fork: does the home-run carry 5 V or 12 V?

Every option is one of two families, and the fork is *which voltage rides the long cable*:

- **5 V home-run** → the buck lives at the hub; the feather stays **passive** (LEDs + caps
  only), but the cable is drop-sensitive (5 V has ~zero headroom).
- **12 V home-run** → the buck lives on (or near) the feather; the cable is drop-tolerant,
  but every feather becomes **active** (buck + inductor on a 10 mm flex board).

The existing 6-pin connector contract already carries **+5 V (VCC)**, so a 5 V home-run is a
drop-in; a 12 V home-run changes the power pin and adds a converter to every board.

## Option A — hub-side conversion, 5 V home-run

Convert once (or per-port) at the hub; the home-run keeps carrying 5 V.

- **A1 — one big hub buck (12 V→5 V, ~60 A / 300 W).** Simplest board; heaviest copper; the
  5 V bus is 56 A; the converter is hot and a single point of failure. ⚠️ A 12 V→5 V **DC-DC**
  at 60 A is *not* commodity (mains "5 V 60 A" supplies are, but that's AC→DC) — expect a
  parallel/custom converter or several modules (~¥100–300). Drop still lives on the 5 V
  home-run.
- **A2 — per-port (or per-2–4-ports) hub buck.** A small 12 V→5 V buck per port at the hub
  (MP1584-class, 0.5–3 A, ~¥1.5–3 ⚠️ × 140). No 56 A bus — the hub's *12 V* rail is the bus
  (~26 A full-white / ~5 A @ 20 %), far easier than 56 A @ 5 V. Each port gets its own fused
  5 V rail. The home-run still carries 5 V (drop analysis below), but the hub is simple to
  build/repair (no flex constraint).
- **A3 — per-junction hub buck.** One buck per cluster of ports (e.g. 8 ports = 8 × 0.4 A =
  3.2 A → a ~4 A 12 V→5 V buck, ~¥5–8 ⚠️, ~18 of them). Fewer parts than A2, still no 56 A
  bus, and each cluster's 5 V runs are short.

All A variants keep the feather passive and the 6-pin `+5 V` contract intact.

## Option B — feather-side conversion, 12 V home-run

Distribute 12 V (drop-tolerant) and put a small 12 V→5 V buck on each feather.

- Per board: 0.17 A @ 12 V full white (2 W) / 0.03 A @ 20 % → 12 V home-run drop is
  negligible (0.17 A × 168 mΩ/m × 10 m ≈ 0.29 V ≈ 2.4 % of 12 V, and the on-board buck
  regulates 5 V down to ~7 V input).
- Cost: 140 × (MP1584-class buck + inductor + caps, ~¥1.5–3 ⚠️) + placement + an inductor
  that doesn't sit well on a 10 mm flex feather + 140 new failure/EMI points.
- This turns the feather from a passive strip into an active converter board, and changes the
  power pin from +5 V to +12 V.

## Option C — junction buck, 12 V trunk + short 5 V tails

A 12 V trunk feeds a junction box that bucks to 5 V for a handful of nearby feathers.

- ~16–20 × 25 W 12 V→5 V bucks (~¥10–15 ⚠️) + junction enclosures + short 5 V tails.
- 12 V over the long trunk (tolerant), 5 V only over short tails (drop OK). But you add
  mechanical junctions and still run some 5 V. Best when feathers cluster tightly.

## Voltage-drop budget (the SK9822's Achilles heel)

5 V has no headroom: the project's own number is **0.5 V = 10 % = color shift (blue first)**.
For a home-run (VCC + GND, 24 AWG round-trip ≈ 168 mΩ/m):

| Current | 5 % (0.25 V) | 10 % (0.5 V) |
|---|---|---|
| 0.4 A (full white) | ~3.7 m | ~7.4 m |
| 0.08 A (20 % avg) | ~18 m | ~37 m |

> The 20 % row uses **average** current because the on-board bulk cap (47 µF) smooths the
> SK9822's PWM ripple; the cable sees the average, the cap covers the on-cycle peaks. At the
> realistic 20 % operating point, a 5 V home-run is fine to ~15–30 m; only *sustained* full
> white collapses it to ~4–7 m.

## Side-by-side

| | A1 hub bulk | A2 hub per-port | A3 hub per-junction | B feather buck | C junction |
|---|---|---|---|---|---|
| Home-run voltage | 5 V | 5 V | 5 V | **12 V** | 12 V + 5 V tail |
| Feather active? | passive | passive | passive | **active** | passive |
| Converter count | 1 | 140 | ~18 | 140 | ~16–20 |
| Converter cost | ~¥100–300 ⚠️ | ~¥210–420 ⚠️ | ~¥90–145 ⚠️ | ~¥210–420 ⚠️ | ~¥160–300 ⚠️ |
| Hub 5 V bus | 56 A ❌ | none (12 V bus) | none | none | none |
| Drop limit @ 20 % | ~18 m | ~18 m | ~18 m | ~none | short tail |
| Failure points | 1 (SPOF) | 140 (hub, repairable) | 18 (hub) | 140 (on flex) | 18 |
| Connector change | none | none | none | +5 V→+12 V | partial |

## Recommendation (leaning)

- **Default: A2 — hub-side per-port (or per-cluster) 12 V→5 V buck, 5 V home-run.** It keeps
  the feather passive (no buck/inductor on 10 mm flex), keeps the 6-pin `+5 V` contract, avoids
  the non-commodity 60 A 12 V→5 V converter and the 56 A 5 V bus (the hub's 12 V rail is only
  ~5 A @ 20 % / ~26 A full-white), and the 5 V home-run drop is acceptable at the 20 %
  operating point (~15–30 m). A3 (per-junction) is the same idea with fewer, larger bucks.
- **Escalate to B (12 V home-run + feather buck) only if** home-runs are long *and* full white
  must be sustained — that's the one case where 5 V's drop budget genuinely fails, and it is
  what forces an active feather.
- **A1 (one big hub buck) only if** minimizing part count beats everything else, and you accept
  a hot SPOF + a custom/parallel 60 A converter + heavy 5 V copper.

## Open questions

- [ ] Confirm the real max home-run length (geometry) and whether full white is ever sustained
      — these two determine A vs B.
- [ ] Confirm 20 % is the true average brightness (it scales current and drop ~linearly).
- [ ] Pick the A2/A3 buck part (MP1584-class) and cluster size (per-port vs per-4 vs per-8);
      confirm efficiency + idle draw (140 bucks idling drains the battery).
- [ ] Verify the 47 µF bulk cap actually smooths the 0.4 A PWM pulses at the chosen length
      (or bump it if ripple sags the rail mid-pulse).
- [ ] Per-port fuse rating for 5 V (0.4 A full-white → ~0.5 A), and whether a fuse + the buck
      are best co-located per port.
- [ ] Battery idle/pack size impact of the chosen converter count (quiescent current × 140).

## References

- MP1584-class 12 V→5 V buck module (~¥1.5–3): https://www.amazon.com/gp/product/B01MQGMOKI
- 5 V 60 A / 300 W supplies (AC→DC; note the DC-DC 12 V→5 V equivalent is less commodity):
  https://kuriosity.sg/products/power-supply-5v-60a-12v-29a-24v-14-6a
- Project context: [connector pinout](../../docs/connector-pinout.md) ·
  [controller](../../boards/controller/)
