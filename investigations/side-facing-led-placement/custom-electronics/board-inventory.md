# Board inventory — panelized FPC subset

Assembly panels are capped at **250 × 250 mm** (stencil/reflow guideline), so the max
board length is **233 mm = 7 LEDs** @ 33.3 mm pitch. **Material: FR-4 thin core
(0.6–0.8 mm) baseline; FPC fallback.**

## SKU subset (all with per-LED score lines)

| SKU | Length | LEDs | Role |
|---|---|---|---|
| B7 | 233 mm | 7 | workhorse: primaries, secondaries, coverts, structure |
| B4 | 133 mm | 4 | exact fits (8, 12-LED feathers), cleaner chains |
| B3 | 100 mm | 3 | alula, tail ends, trim |

{7,4,3} resolves most feather counts exactly (18 = 7+7+4, 15 = 7+4+4, 24 = 7+7+7+3);
addressable "dark LED" rounding covers the rest. Drop B4 for minimalism if desired.

## Counts (both wings, ~780 LEDs) ⚠️ — feather lengths assumed

- **~108 × B7 + ~28 × B4/B3**
- Panels (50 strips each, 5 mm wide): **3 × B7 + 1 × B4/B3 = 4 panels**, all ≤ 250×250
- Material margin ~35 % for rounding-up + cutting waste

## Chain links ⚠️

~55 board-to-board links across both wings, each a **JST-PH 4-pin cable**
(VDD/VSS/DI/CI) — structure strips (0.8 m) are 4-board chains, longest primaries
3-board. Recheck against measured feather lengths before locking the SKU mix.
