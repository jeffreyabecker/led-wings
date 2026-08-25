# Feather Lighting & Boards

> Status: **ideation** · nothing locked · pairs with [outline-templates.md](../feather/outline-templates.md).
> Legend: ✅ = anatomy/selected fact · ⚠️ = design estimate (to be locked later).
>
> ⚠️ **Feather sizing authority:** all feather sizes below (vane floor, per-feather
> vane/exposed cm, row spans, and the LED counts derived from them) are **provisional
> placeholders**. The authoritative sizing lives in
> [`feather/outline-templates.md`](../feather/outline-templates.md) + `source-images/` and
> **has not yet been finalized** — re-derive the LED map once it is locked.

How the mechanical feather outlines map to LED strip chunks. [outline-templates.md](../feather/outline-templates.md)
carries the geometry + arrangement; this file carries **which feathers are lit, how** (individual
chunk vs shared strip vs unlit structural), and the chunk count / LED budget.

## 1. Chunk model

- **One lit feather = one strip chunk** — an SK9822 96 LED/m (10.4 mm pitch), 10 mm-wide strip
  cut to the feather's LED count and mounted along the exposed tip; the covered base carries
  no strip. Cut table in [boards/README.md](README.md).
- **Single LED line per feather (locked).** One strip line along the rachis lights the whole
  vane; brightness falls off toward the vane edges. The **bright-rachis → dim-edge gradient
  is the accepted aesthetic** — the alternatives were analyzed and rejected: two staggered
  lines (2× strips + wiring) and edge-lit PETG guides (rigid + too heavy for the feather
  weight budget).
- **Vane floor.** Every *lit individual* feather needs a **vane ≥ ~14 mm wide** at the strip's
  widest point (10 mm strip + diffuser margin). The chord ratios in the outline tables already
  respect this floor.
- **Pigtails enter at the feather base (top)** — the only cable entrance. Data daisy-chains
  feather→feather; power fans out from local power-hubs. See
  [boards/README.md](README.md).
- **Shared strips are continuous strip spans** with a scalloped overlay (§4), not one chunk
  per covert feather.

## 2. Lighting map

| Group | Lighting | Form |
|-------|----------|------|
| Primaries P1–P10 | lit | individual strip chunk each |
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

## 4. Shared strips — one continuous strip per row

The dense covert rows (median / lesser / marginal) are **one continuous off-the-shelf strip per
row** (no cuts except row length), so each row keeps one common LED orientation for the
animation.

### Row strip

- **LEDs:** ~27 per ~28 cm row at 96 LED/m (10.4 mm pitch). ⚠️ Row spans are placeholders
  until the wing layout is drawn.
- **Wiring:** `PWR` + `DI`/`CI` pigtails at the row head; `DO`/`CO` at the tail → next row's
  head (wiring legend: [pinout](../docs/connector-pinout.md)).
- **Common orientation:** a continuous strip keeps one orientation by construction: `DI` in at
  the head → LEDs in order → `DO` out the tail. The row then behaves as one logical strip, so
  animations map 1:1 to row position.
- **Scallop edge:** the scallop silhouette lives in the mechanical overlay/diffuser above the
  strip; the strip itself stays straight.

### Rows (per wing, working ⚠️)

| Row | Span (cm) ⚠️ | LEDs @96/m |
|-----|------------:|-----------:|
| Median coverts | 28 | 27 |
| Lesser coverts ×2 rows | 28 + 28 | 54 |
| Marginal coverts (leading edge) | 28 | 27 |
| **Per wing** | **112** | **~108** |

- Both wings: **8 continuous rows, ~216 LEDs**.
- ⚠️ Row spans (~28 cm) are placeholders until the wing layout is drawn — LEDs per row =
  span ÷ 1.04 cm.
- Power: ~27 LEDs ≈ 1.1 A full-white per row — feed at the row head from a power-hub; add
  mid-span injection only if the bench shows drop.

## 5. Count reconciliation

Earlier board notes carried a **~70 unique LED board shapes** placeholder.
Lighting all 12 greater coverts + the bottom/top alula shifts it to **~80 individual strip
chunks** (per-feather LED counts are derived in §6):

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries (P1–P10) | 10 | 20 |
| Secondaries (S1–S12) | 12 | 24 |
| Tertials (T1–T4) | 4 | 8 |
| Greater coverts (GC1–GC12) | 12 | 24 |
| Alula (A-B + A-T) | 2 | 4 |
| **Individual lit chunks** | **40** | **80** |

- **80 individual lit feathers = 52 flight (P+S+T) + 24 greater coverts + 4 alula** ✅
- **Alula:** the bottom + top alula are lit individually — 2 per wing, 4 total. ✅
- **Shared strips (median/lesser/marginal)** are continuous spans (§4), not part of the 80.
- **Scapulars + back coverts** default to unlit structural covers; if lit they add chunks on
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
  gap (~5 mm gap on the 10 mm strip). The 96/m strip's 10.4 mm pitch is the same map.
- **Bleed:** +2 LEDs extending ~20 mm under the cover edge, so the visible boundary glows evenly
  despite flex/register shifts.
- **Covered base:** 0 LEDs (hidden). A dim under-glow through the cover would be extra — not
  counted.
- **Uneven spacing:** the map is two-zone (10 mm on the exposed tip, none on the covered base).
  If tips should read brighter, tighten the last ~5 cm to ~8 mm (+1 LED each) — not in this pass.

### Primaries (exposed ~15 cm — draft range 10–20 cm → 12–22 LEDs)

| ID | Vane (cm) | Exposed (cm) | LEDs |
|----|----------:|-------------:|-----:|
| P1–P10 | 41–56 | 15 | 17 |

### Secondaries (exposed ~12 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs |
|----|----------:|-------------:|-----:|
| S1–S12 | 34–44 | 12 | 14 |

### Tertials (exposed ~10 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs |
|----|----------:|-------------:|-----:|
| T1–T4 | 42–46 | 10 | 12 |

### Greater coverts (exposed ~8 cm)

| ID | Vane (cm) | Exposed (cm) | LEDs |
|----|----------:|-------------:|-----:|
| GC1–GC12 | 17–22 | 8 | 10 |

### Totals

| Group | Chunks | LEDs (both wings) |
|-------|-------:|------------------:|
| Individual feathers (P/S/T/GC) | 76 | ~1010 |
| Alula — bottom + top (2 per wing) | 4 | ~40 |
| Shared covert strips (4 rows/wing) | 8 | ~216 |
| **Total** | **~88** | **~1270** |

### What this costs (power → battery → weight)

- Full white: 1270 × 40 mA ≈ **51 A @ 5 V** — never run full white.
- 20 % brightness: ≈ 10.2 A @ 5 V = 51 W → ÷ 90 % buck ≈ **56 W** from the battery.
- 8 h @ 20 %: ≈ **450 Wh** → ≈ **2.65 kg** LiPo (~170 Wh/kg).
- Total: frame ~0.9 + feathers ~0.6 + electronics ~0.6 + battery ~2.65 ≈ **~4.75 kg** — inside
  the 5 kg cap with a slim margin.

### Knobs (tunable ⚠️)

- **Tip stagger per group** — take the real values from the draft mockups (primaries 10–20 cm);
  each ±1 cm of stagger ≈ ±1 LED per feather (±76 total).
- **Density/pitch (locked):** 96 LED/m (10.4 mm) — no density fallback
  ([boards/README.md](README.md)).
- **Row spans** — LEDs per row = span ÷ 1.04 cm, once the layout is drawn.
- **Runtime/brightness** (battery sizing).

## 7. Open decisions

- [ ] Confirm the per-group tip stagger from the draft mockups (primaries 10–20 cm; S/T/GC
      working 12/10/8 cm).
- [ ] Runtime at 96/m: 8 h @ 20 % → ~2.65 kg battery fits the 5 kg cap (slim margin).
- [ ] Confirm alula sizes from the mockup (working ~11 cm total / ~8 cm vane).
- [ ] Back feathers: unlit structural covers (default) vs accent-lit chunks.
- [ ] Strip vendor: source + validate a 96 LED/m SK9822 reel before bulk (see
      [boards/README.md](README.md)).
- [ ] Power-hub placement (chain segmentation settled: N = 2, one chain per wing — see
      [boards/README.md](README.md)).

## References

- [Boards](README.md) — COTS build plan, incl. the strip-chunk cut table.
- [Diffuser halo](../investigations/diffuser-halo/) — light shaping/diffusion.
- [Connector pinout](../docs/connector-pinout.md) — pigtail wiring legend (PWR / DATA-IN / DATA-OUT).
- [Feather outlines](../feather/outline-templates.md) — geometry + arrangement this file maps from.
