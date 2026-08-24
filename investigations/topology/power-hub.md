# Power-Hub Bus Voltage — 5 V vs 12 V + Buck

> Analysis backing the **12 V in → 5 V out** hub decision (recorded in
> [target-topology.md](target-topology.md) and the [power-hub board](../../boards/power-hub/)).
> This is the useful part of the (deleted) power-delivery investigation, re-framed for the
> split topology: the power-hub bus carries **all** pixel power, so its voltage sets the
> current and the drop budget.
>
> Legend: ✅ = sourced · ⚠️ = estimate.

## Load model (2000 px)

| | Full white | 20 % brightness |
|---|---|---|
| Rail power (2000 × 0.2 W) | 400 W | 80 W |
| 5 V bus current | 80 A | 16 A |
| 12 V bus current (÷ ~90 % buck) | ~37 A | ~7.4 A |

## The fork: where does the 12 V→5 V step live?

| Option | Bus | Power-hub | Feather | Verdict |
|---|---|---|---|---|
| **A. 5 V bus** | 5 V | fuse/junction only (dumb) | passive | 5 V bus carries 80 A / 16 A → drop-limited |
| **B. 12 V bus + hub buck** | 12 V | **12 V→5 V buck per hub** | passive | 12 V bus ~2.4× lower current; 5 V only on short tails |
| **C. 12 V bus + feather buck** | 12 V | — | **active** (buck on flex) | ❌ rejected — active flex feather |

## Bus drop budget (the decider)

Reference: a 2 m bus, 12 AWG (round-trip ≈ 10.4 mΩ/m ≈ 21 mΩ total):

| | 20 % brightness | Full white |
|---|---|---|
| 5 V bus | 16 A → 0.33 V = **6.7 %** ⚠️ | 80 A → 1.66 V = **33 %** ❌ |
| 12 V bus | 7.4 A → 0.15 V = **1.3 %** ✅ | 37 A → 0.77 V = **6.4 %** ✅ |

- **5 V bus is the same drop problem, just moved to the bus.** It is only viable if the bus
  is short *and* thick *and* full white is never sustained. At 20 % it's borderline; at full
  white it collapses (33 %).
- **12 V bus keeps 5 V off the long run.** 5 V exists only on the short hub→feather tail
  (one feather's ~0.4 A @ full white / 0.08 A @ 20 % over ≤1 m → negligible drop even at
  24–26 AWG). The buck tolerates several volts of bus sag, so color stays flat.
- This is the quantitative backing for the "12 V + buck at the hub" direction already noted
  in [target-topology.md](target-topology.md).

## Hub buck sizing

Per-hub 12 V→5 V buck, sized for its cluster. Worked example: ~2000 px clustered into ~10–20
hubs → ~100–200 px/hub → each hub bucks ~2–4 A @ 5 V full white (~0.4–0.8 A @ 20 %). One
MP1584-class 3 A buck (~¥1.5–3 ⚠️) covers a hub — this is the "one buck per cluster" option,
**not** one per feather, so the converter count stays small and lives off-flex (easy thermal +
repair).

## Recommendation

**Option B — 12 V bus + per-hub 12 V→5 V buck.** The bus carries 12 V (~7 A @ 20 %), each
power-hub is a fuse + one small buck, and 5 V only exists on the short hub→feather tails.
Option A (5 V bus) is acceptable only if the wing is small enough that a thick, short bus
holds full-white drop under ~5 % — it does not for a wing-scale bus.

## Open items

- [ ] Hub count + cluster size (px/hub) → sets the buck count and the bus topology.
- [ ] Bus conductor: gauge and layout (single 12 V rail vs a loop/ring for redundancy).
- [ ] Per-hub part: fuse + buck (MP1584-class) and its idle draw (N hubs idling on battery).
- [ ] Full-white policy: brief ceiling vs sustained — this sets how hard the bus must be sized.

## References

- MP1584-class 12 V→5 V buck module (~¥1.5–3): https://www.amazon.com/gp/product/B01MQGMOKI
- Project context: [target-topology.md](target-topology.md) · [power-hub board](../../boards/power-hub/) · [battery](../battery/)
