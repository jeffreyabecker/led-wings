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

`boards/led-segment/design-readiness.md` carried a **~70 unique LED board shapes** placeholder
for ~1400 LEDs. Lighting all 12 greater coverts shifts it to **~76 individual board shapes**:

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

## 6. LED budget

- Round budget stays **~1400 LEDs** (≈ 20-LED average over the individual feathers) — but the
  6 added inner-greater-covert boards are small (≈ half a secondary each), so re-check the total
  before locking.
- Per-feather LED counts (and any primary-vs-covert redistribution) are still open.

## 7. Open decisions

- [ ] LED budget per feather → confirms the 20-LED average, or redistributes primaries vs coverts.
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
