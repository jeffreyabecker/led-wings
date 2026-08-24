# Feather Lighting & Boards

> Status: **ideation** · nothing locked · pairs with [outline-templates.md](outline-templates.md).
> Legend: ✅ = anatomy/selected fact · ⚠️ = design estimate (to be locked later).

How the mechanical feather outlines map to LED strip modules. [outline-templates.md](outline-templates.md)
carries the geometry + arrangement; this file carries **which feathers are lit, how** (individual
module chain vs shared row chain vs unlit structural), and the module count / LED budget.

## 1. Module-chain model

- **One lit feather = one chain of standard modules** — 4-LED (42 mm) and 6-LED (62 mm)
  modules at 10.4 mm pitch, chained tip-to-tail with 4-pin JST connectors, mounted along the
  exposed tip; the covered base carries no modules. Chain layout in
  [boards/README.md](../../boards/README.md).
- **Single LED line per feather (locked).** One module chain along the rachis lights the whole
  vane; brightness falls off toward the vane edges. The **bright-rachis → dim-edge gradient
  is the accepted aesthetic** — the alternatives were analyzed and rejected: two staggered
  lines (2× modules + wiring) and edge-lit PETG guides (rigid + too heavy for the feather
  weight budget).
- **Vane floor.** Every *lit individual* feather needs a **vane ≥ ~14 mm wide** at the
  module's widest point (10 mm module + diffuser margin). The chord ratios in the outline
  tables already respect this floor.
- **Pigtails + chain jumpers enter at the feather base (top)** — the only cable entrance.
  Data daisy-chains module→module; power is injected into the chain via harness pigtails from
  local power-hubs. See [boards/README.md](../../boards/README.md).
- **Shared rows are module chains too** (§4), not one chain per covert feather.

## 2. Lighting map

| Group | Lighting | Form |
|-------|----------|------|
| Primaries P1–P10 | lit | individual module chain each |
| Secondaries S1–S12 | lit | individual chunk each |
| Tertials T1–T4 | lit | individual chunk each |
| Greater coverts GC1–GC12 | **lit** | individual chunk each — incl. inner GC10–GC12 |
| Alula A-B + A-T (bottom + top) | lit | individual chunk each — 2 per wing |
| Median coverts | lit | shared strip |
| Lesser coverts | lit | shared strip |
| Marginal coverts | lit | shared strip |
| Scapulars SC1–SC6 | unlit (default) ⚠️ | structural covers |
| Back coverts BC1–BC8 | unlit (default) ⚠️ | structural cover / removable lid |

## 3. Decision — greater inner coverts get lights

The three innermost greater coverts (**GC10–GC12**) get their own lights as individual chunks,
instead of folding into a shared covert strip. **All 12 greater coverts are therefore lit
individually** (one per secondary). This drops the `inner-greater-covert-strip` from the shared
strips (§4).

## 4. Shared rows — chained 4-LED modules

The dense covert rows (median / lesser / marginal) are **one chain of seven 4-LED modules per
row**, so each row keeps one common LED orientation for the animation.

### Row chain

- **LEDs:** 7 × 4-LED modules = 28 per ~29 cm row (10.4 mm pitch). ⚠️ Row spans are
  placeholders until the wing layout is drawn.
- **Wiring:** standard 4-pin chain — `DI`/`CI` in at the row head, `DO`/`CO` out the tail →
  next row's head; power injected via pigtails every 4–6 modules (wiring legend:
  [pinout](../../docs/connector-pinout.md)).
- **Common orientation:** the chain keeps one orientation by construction: `DI` in at the
  head → LEDs in order → `DO` out the tail. The row then behaves as one logical strip, so
  animations map 1:1 to row position.
- **Scallop edge:** the scallop silhouette lives in the mechanical overlay/diffuser above the
  modules; the chain itself stays straight.

### Rows (per wing, working ⚠️)

| Row | Modules (4-LED) | LEDs |
|-----|----------------:|-----:|
| Median coverts | 7 | 28 |
| Lesser coverts ×2 rows | 7 + 7 | 56 |
| Marginal coverts (leading edge) | 7 | 28 |
| **Per wing** | **28** | **112** |

- Both wings: **56 modules across 8 row chains, ~224 LEDs**.
- ⚠️ Row spans (~28 cm) are placeholders until the wing layout is drawn — modules per row =
  span ÷ 4.16 cm, rounded.
- Power: ~28 LEDs ≈ 1.1 A full-white per row — inject at the row head and mid-row via the
  standard pigtail cadence.

## 5. Count reconciliation

Earlier board notes carried a **~70 unique LED board shapes** placeholder.
Lighting all 12 greater coverts + the bottom/top alula shifts it to **~80 individual module
chains** (per-feather LED counts are derived in §6):

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries (P1–P10) | 10 | 20 |
| Secondaries (S1–S12) | 12 | 24 |
| Tertials (T1–T4) | 4 | 8 |
| Greater coverts (GC1–GC12) | 12 | 24 |
| Alula (A-B + A-T) | 2 | 4 |
| **Individual lit chains** | **40** | **80** |

- **80 individual lit feathers = 52 flight (P+S+T) + 24 greater coverts + 4 alula** ✅
- **Alula:** the bottom + top alula are lit individually — 2 per wing, 4 total. ✅
- **Shared rows (median/lesser/marginal)** are module chains (§4), not part of the 80.
- **Scapulars + back coverts** default to unlit structural covers; if lit they add chains on
  top of the 80. ⚠️

## 6. LED map per feather (first-principles rough pass)

> Derived from the stacking geometry. All assumptions ⚠️ — knobs at the end.

### Model

- **Light only what shows.** In the folded shingle stack, each feather's base is covered by the
  feathers in front of it — hidden length needs no strong lighting. Only the exposed tip is lit.
- **Exposure is a fixed tip stagger, not a % of vane.** In a shingle stack each feather shows
  roughly the same *length* of tip beyond the feather covering it, whatever its total length —
  which is why the draft primaries all show ~10–20 cm regardless of size. (% of vane was the
  earlier wrong model: it gave long feathers more exposure than they actually get.)
- **Working stagger (⚠️, anchored to the drafts):** primaries **~15 cm** (draft range 10–20) ·
  secondaries **~12 cm** · tertials **~10 cm** · greater coverts **~8 cm**.
- **Pitch:** ~10 mm across the exposed tip — smooth glow needs spacing ≤ ~2× the LED-to-diffuser
  gap (~5 mm gap on the 10 mm module). The modules keep the 10.4 mm pitch — the same map.
- **Bleed:** +2 LEDs extending ~20 mm under the cover edge, so the visible boundary glows evenly
  despite flex/register shifts.
- **Covered base:** 0 LEDs (hidden). A dim under-glow through the cover would be extra — not
  counted.
- **Uneven spacing:** the map is two-zone (10 mm on the exposed tip, none on the covered base).
  If tips should read brighter, tighten the last ~5 cm to ~8 mm (+1 LED each) — not in this pass.

### Primaries (exposed ~15 cm — draft range 10–20 cm → 12–22 LEDs)

| ID | Vane (cm) | Exposed (cm) | LEDs (modules) |
|----|----------:|-------------:|---------------:|
| P1–P10 | 41–56 | 15 | 16 (6+6+4) |

### Secondaries (exposed ~12 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs (modules) |
|----|----------:|-------------:|---------------:|
| S1–S12 | 34–44 | 12 | 14 (6+4+4) |

### Tertials (exposed ~10 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs (modules) |
|----|----------:|-------------:|---------------:|
| T1–T4 | 42–46 | 10 | 12 (4+4+4) |

### Greater coverts (exposed ~8 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs (modules) |
|----|----------:|-------------:|---------------:|
| GC1–GC12 | 17–22 | 8 | 10 (6+4) |

### Totals

| Group | Chains | LEDs (both wings) |
|-------|-------:|------------------:|
| Individual feathers (P/S/T/GC) | 76 | ~990 |
| Alula — bottom + top (2 per wing) | 4 | ~40 |
| Shared covert rows (4 rows/wing) | 8 | ~224 |
| **Total** | **~88** | **~1260** |

### What this costs (power → battery → weight)

- Full white: 1260 × 40 mA ≈ **50 A @ 5 V** — never run full white.
- 20 % brightness: ≈ 10 A @ 5 V = 50 W → ÷ 90 % buck ≈ **56 W** from the battery.
- 8 h @ 20 %: ≈ **445 Wh** → ≈ **2.6 kg** LiPo (~170 Wh/kg).
- Total: frame ~0.9 + feathers ~0.6 + electronics ~0.6 + battery ~2.6 ≈ **~4.7 kg** — inside
  the 5 kg cap with a slim margin.

### Knobs (tunable ⚠️)

- **Tip stagger per group** — take the real values from the draft mockups (primaries 10–20 cm);
  each ±1 cm of stagger ≈ ±1 LED per feather (±76 total).
- **Module mix** — P: 6+6+4 = 16 LEDs vs 6+6+6 = 18; module pitch is fixed at 10.4 mm.
- **Row spans** — modules per row = span ÷ 4.16 cm, once the layout is drawn.
- **Runtime/brightness** — the ≤ 20–25 % brightness cap pairs with the injection cadence
  (battery sizing).

## 7. Open decisions

- [ ] Confirm the per-group tip stagger from the draft mockups (primaries 10–20 cm; S/T/GC
      working 12/10/8 cm).
- [ ] Brightness cap + runtime: ≤ 20–25 % @ 8 h → ~2.6 kg battery fits the 5 kg cap (slim
      margin).
- [ ] Confirm alula sizes from the mockup (working ~11 cm total / ~8 cm vane).
- [ ] Back feathers: unlit structural covers (default) vs accent-lit chains.
- [ ] Module design sign-off + panel order (see [boards/README.md](../../boards/README.md)).
- [ ] Power-hub placement (chain segmentation settled: N = 2, one chain per wing — see
      [boards/README.md](../../boards/README.md)).

## References

- [Boards](../../boards/README.md) — strip-module build plan, incl. the chain layout.
- [Diffuser halo](../../investigations/diffuser-halo/) — light shaping/diffusion.
- [Connector pinout](../../docs/connector-pinout.md) — wiring legend (4-pin module chains + injection).
- [Feather outlines](outline-templates.md) — geometry + arrangement this file maps from.
