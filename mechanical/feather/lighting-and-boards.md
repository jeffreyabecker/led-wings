# Feather Lighting & Boards

> Status: **ideation** · nothing locked · pairs with [outline-templates.md](outline-templates.md).
> Legend: ✅ = anatomy/selected fact · ⚠️ = design estimate (to be locked later).

How the mechanical feather outlines map to LED boards. [outline-templates.md](outline-templates.md)
carries the geometry + arrangement; this file carries **which feathers are lit, how** (individual
board vs shared strip vs unlit structural), and the board count / LED budget.

## 1. Board model

- **One lit feather = one `boards/led-segment/` board.** A fixed 10 mm flexible ribbon that runs
  along the feather's rachis; its geometry comes from the outline template (length + bend points).
- **Vane floor.** Every *lit individual* feather needs a **vane ≥ ~14 mm wide** at the ribbon's
  widest point (10 mm board + diffuser margin). The chord ratios in the outline tables already
  respect this floor.
- **Connectors enter at the feather base (top)** — the only cable entrance. Data daisy-chains
  feather→feather; power fans out from local power-hubs. See
  [`boards/led-segment/`](../../boards/led-segment/) and
  [topology](../../investigations/topology/).
- **Shared strips are a different board type** — continuous under-lit ribbons with a scalloped
  feather edge, not one board per feather.

## 2. Lighting map

| Group | Lighting | Form |
|-------|----------|------|
| Primaries P1–P10 | lit | individual `led-segment` board each |
| Secondaries S1–S12 | lit | individual board each |
| Tertials T1–T4 | lit | individual board each |
| Greater coverts GC1–GC12 | **lit** | individual board each — incl. inner GC10–GC12 |
| Alula A1–A4 | optional ⚠️ | individual boards, or folded into the leading-edge strip |
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

## 4. Shared strip templates (not individual feathers)

| Template | Covers | Notes |
|----------|--------|-------|
| `median-covert-strip` | 1 row above the greater coverts | scalloped edge, graduated toward leading edge |
| `lesser-covert-strip` | 2–3 rows toward the leading edge | shorter scallops each row |
| `marginal-covert-strip` | leading edge | smallest scallops; wraps the leading edge |

## 5. Count reconciliation

`boards/led-segment/design-readiness.md` carried a **~70 unique LED board shapes** placeholder.
Lighting all 12 greater coverts shifts it to **~76 individual board shapes** (per-feather LED
counts are derived in §6):

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries (P1–P10) | 10 | 20 |
| Secondaries (S1–S12) | 12 | 24 |
| Tertials (T1–T4) | 4 | 8 |
| Greater coverts (GC1–GC12) | 12 | 24 |
| **Individual lit boards** | **38** | **76** |

- **76 individual lit feathers = 52 flight feathers (P+S+T) + 24 greater coverts** ✅
- **Alula (A1–A4)** is optional — 8 more boards if individual, else folded into the
  leading-edge strip. ⚠️
- **Shared strips (median/lesser/marginal)** are separate boards, not part of the 76.
- **Scapulars + back coverts** default to unlit structural covers; if lit they add boards on
  top of the 76. ⚠️

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

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries | 170 | 340 |
| Secondaries | 168 | 336 |
| Tertials | 48 | 96 |
| Greater coverts | 120 | 240 |
| **Individual boards total** | **506** | **~1010** |

- Optional alula: ~2–3 LEDs × 4 per wing ≈ **20** if lit individually.
- Shared strips (median/lesser/marginal): TBD, ≈ **100–200** total once strip geometry is set —
  not part of the 1010.

### What this costs (power → battery → weight)

- Full white: 1010 × 40 mA ≈ **40 A @ 5 V** — never run full white.
- 20 % brightness: ≈ 8.1 A @ 5 V = 40 W → ÷ 90 % buck ≈ **45 W** from the battery.
- 8 h @ 20 %: ≈ **360 Wh** → ≈ **2.1 kg** LiPo (~170 Wh/kg).
- Total: frame ~0.9 + feathers ~0.6 + electronics ~0.6 + battery ~2.1 ≈ **~4.2 kg** — fits the
  5 kg cap with ~0.8 kg margin for strips + alula.

### Knobs (tunable ⚠️)

- **Tip stagger per group** — take the real values from the draft mockups (primaries 10–20 cm);
  each ±1 cm of stagger ≈ ±1 LED per feather (±76 total).
- **Pitch** — 10 mm is now affordable; 15 mm cuts to ~700 LEDs and saves ~0.7 kg of battery.
- **Tip-dense 8 mm** option (+~10 %).
- **Runtime/brightness** (battery sizing).

## 7. Open decisions

- [ ] Confirm the per-group tip stagger from the draft mockups (primaries 10–20 cm; S/T/GC
      working 12/10/8 cm).
- [ ] Pitch + runtime: 10 mm @ 8 h 20 % → ~2.1 kg battery fits the 5 kg cap; 15 mm saves ~0.7 kg.
- [ ] Alula as individual boards vs part of the leading-edge strip.
- [ ] Back feathers: unlit structural covers (default) vs accent-lit boards.
- [ ] Shared-strip board type: its own `boards/` entry + how it joins the data chain.
- [ ] Chain segmentation (N) + power-hub placement (see [topology](../../investigations/topology/)).

## References

- [LED segment board](../../boards/led-segment/) — the individual feather board (10 mm ribbon).
- [Topology](../../investigations/topology/) — split power/data, chain segmentation.
- [Diffuser halo](../../investigations/diffuser-halo/) — light shaping/diffusion.
- [Connector pinout](../../docs/connector-pinout.md) — PWR / DATA-IN / DATA-OUT contract.
- [Feather outlines](outline-templates.md) — geometry + arrangement this file maps from.
