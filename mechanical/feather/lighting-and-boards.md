# Feather Lighting & Boards

> Status: **ideation** · nothing locked · pairs with [outline-templates.md](outline-templates.md).
> Legend: ✅ = anatomy/selected fact · ⚠️ = design estimate (to be locked later).

How the mechanical feather outlines map to LED boards. [outline-templates.md](outline-templates.md)
carries the geometry + arrangement; this file carries **which feathers are lit, how** (individual
board vs shared strip vs unlit structural), and the board count / LED budget.

## 1. Board model

- **One lit feather = one LED segment (feather) board** — see
  [boards/README.md](../../boards/README.md). A fixed 10 mm flexible ribbon that runs
  along the feather's rachis; its geometry comes from the outline template (length + bend points).
- **Single LED line per feather (locked).** One ribbon along the rachis lights the whole vane;
  brightness falls off toward the vane edges. The **bright-rachis → dim-edge gradient is the
  accepted aesthetic** — the alternatives were analyzed and rejected: two staggered lines (2×
  boards + connectors) and edge-lit PETG guides (rigid + too heavy for the feather weight
  budget).
- **Vane floor.** Every *lit individual* feather needs a **vane ≥ ~14 mm wide** at the ribbon's
  widest point (10 mm board + diffuser margin). The chord ratios in the outline tables already
  respect this floor.
- **Connectors enter at the feather base (top)** — the only cable entrance. Data daisy-chains
  feather→feather; power fans out from local power-hubs. See
  [boards/README.md](../../boards/README.md).
- **Shared strips are a different board type** — chains of short 3–4 cm boards with a scalloped
  overlay (§4), not one board per covert feather.

## 2. Lighting map

| Group | Lighting | Form |
|-------|----------|------|
| Primaries P1–P10 | lit | individual `led-segment` board each |
| Secondaries S1–S12 | lit | individual board each |
| Tertials T1–T4 | lit | individual board each |
| Greater coverts GC1–GC12 | **lit** | individual board each — incl. inner GC10–GC12 |
| Alula A-B + A-T (bottom + top) | lit | individual board each — 2 per wing |
| Median coverts | lit | shared strip |
| Lesser coverts | lit | shared strip |
| Marginal coverts | lit | shared strip |
| Scapulars SC1–SC6 | unlit (default) ⚠️ | structural covers |
| Back coverts BC1–BC8 | unlit (default) ⚠️ | structural cover / removable lid |

## 3. Decision — greater inner coverts get lights

The three innermost greater coverts (**GC10–GC12**) get their own lights as individual boards,
instead of folding into a shared covert strip. **All 12 greater coverts are therefore lit
individually** (one per secondary). This drops the `inner-greater-covert-strip` from the shared
strips (§4).

## 4. Shared strips — chains of short boards

The dense covert rows (median / lesser / marginal) are **not** one long ribbon: each row is a
**chain of short 3–4 cm boards**, so the whole row keeps one common LED orientation for the
animation.

### Strip board ("scallop segment")

- **Size:** 40 × 10 mm (working; a 30 × 10 mm / 3-LED variant for tighter rows).
- **LEDs:** 4 × SK9822-EC20 at 10 mm pitch.
- **Connectors:** **4-pin, power + data combined** (`+5V`/`GND`/`DI`/`CI` in,
  `+5V`/`GND`/`DO`/`CO` out) — not the feather's separate `J_PWR` + `J_IN`/`J_OUT`
  ([pinout](../../docs/connector-pinout.md)) — chained tip-to-tail.
- **Common orientation:** every board is identical and faces the same way along the chain:
  `DI` in at one end → LEDs in order → `DO` out the far end. The chain then behaves as one
  logical strip (N × 4 LEDs in chain order), so animations map 1:1 to chain position.
- **Scallop edge:** one board = one covert scallop. Keep the board rectangular (orientation
  stays trivial) and put the scallop silhouette in the mechanical overlay/diffuser above it;
  a scalloped board outline is optional.

### Rows (per wing, working ⚠️)

| Row | Boards (4 cm) | LEDs |
|-----|--------------:|-----:|
| Median coverts | 7 | 28 |
| Lesser coverts ×2 rows | 7 + 7 | 56 |
| Marginal coverts (leading edge) | 7 | 28 |
| **Per wing** | **28** | **112** |

- Both wings: **~56 boards, ~224 LEDs**.
- ⚠️ Row spans (~28 cm) are placeholders until the wing layout is drawn — boards per row =
  span ÷ 4 cm, rounded up.
- Power: 4 LEDs ≈ 0.16 A full-white per board — power rides the 4-pin chain, fed at the chain
  head from a power-hub feed (one feed can carry several strip boards).

## 5. Count reconciliation

Earlier board notes carried a **~70 unique LED board shapes** placeholder.
Lighting all 12 greater coverts + the bottom/top alula shifts it to **~80 individual board
shapes** (per-feather LED counts are derived in §6):

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries (P1–P10) | 10 | 20 |
| Secondaries (S1–S12) | 12 | 24 |
| Tertials (T1–T4) | 4 | 8 |
| Greater coverts (GC1–GC12) | 12 | 24 |
| Alula (A-B + A-T) | 2 | 4 |
| **Individual lit boards** | **40** | **80** |

- **80 individual lit feathers = 52 flight (P+S+T) + 24 greater coverts + 4 alula** ✅
- **Alula:** the bottom + top alula are lit individually — 2 per wing, 4 total. ✅
- **Shared strips (median/lesser/marginal)** are chains of short boards (§4), not part of the 80.
- **Scapulars + back coverts** default to unlit structural covers; if lit they add boards on
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
  gap (~5 mm gap on the 10 mm ribbon).
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

| Group | Boards | LEDs (both wings) |
|-------|-------:|------------------:|
| Individual feathers (P/S/T/GC) | 76 | ~1010 |
| Alula — bottom + top (2 per wing) | 4 | ~32 |
| Shared covert strips (4 rows/wing) | ~56 | ~224 |
| **Total** | **~136** | **~1270** |

### What this costs (power → battery → weight)

- Full white: 1270 × 40 mA ≈ **51 A @ 5 V** — never run full white.
- 20 % brightness: ≈ 10.2 A @ 5 V = 51 W → ÷ 90 % buck ≈ **56 W** from the battery.
- 8 h @ 20 %: ≈ **450 Wh** → ≈ **2.65 kg** LiPo (~170 Wh/kg).
- Total: frame ~0.9 + feathers ~0.6 + electronics ~0.6 + battery ~2.65 ≈ **~4.75 kg** — inside
  the 5 kg cap with a slim margin; the 3-LED strip variant saves ~0.1 kg.

### Knobs (tunable ⚠️)

- **Tip stagger per group** — take the real values from the draft mockups (primaries 10–20 cm);
  each ±1 cm of stagger ≈ ±1 LED per feather (±76 total).
- **Strip board** 4 cm/4 LEDs vs 3 cm/3 LEDs (~±0.1 kg of battery).
- **Row spans** — boards per row = span ÷ board length, once the layout is drawn.
- **Pitch** — 10 mm is affordable; 15 mm on the flight feathers cuts ~0.7 kg of battery.
- **Tip-dense 8 mm** option (+~10 %).
- **Runtime/brightness** (battery sizing).

## 7. Open decisions

- [ ] Confirm the per-group tip stagger from the draft mockups (primaries 10–20 cm; S/T/GC
      working 12/10/8 cm).
- [ ] Pitch + runtime: 10 mm @ 8 h 20 % → ~2.65 kg battery fits the 5 kg cap (slim margin);
      15 mm saves ~0.7 kg.
- [ ] Confirm alula sizes from the mockup (working ~11 cm total / ~8 cm vane).
- [ ] Back feathers: unlit structural covers (default) vs accent-lit boards.
- [ ] Strip boards: 4 cm/4-LED vs 3 cm/3-LED; entry in [boards/README.md](../../boards/README.md) (`covert-strip`).
- [ ] Chain segmentation (N) + power-hub placement (see [boards/README.md](../../boards/README.md)).

## References

- [Boards](../../boards/README.md) — core ideas + settled parts, incl. the individual feather board (10 mm ribbon).
- [Diffuser halo](../../investigations/diffuser-halo/) — light shaping/diffusion.
- [Connector pinout](../../docs/connector-pinout.md) — PWR / DATA-IN / DATA-OUT contract.
- [Feather outlines](outline-templates.md) — geometry + arrangement this file maps from.
