# Wing Bones — Bone Structure Investigation

> Scope: the **"bone" structure** of the folded wing — the member layout (humerus?,
> radius/ulna, fused carpal), the backplate that carries the harness + electronics, and the
> body-anatomy constraints that bound it all. This feeds the frame design in
> [`mechanical/structural/`](../../mechanical/structural/README.md); locking decisions happens
> in [design-readiness.md](../../mechanical/structural/design-readiness.md).
>
> Legend: ✅ = sourced/confirmed · ⚠️ = estimate to confirm · 🧍 = needs wearer measurement.

## Status

`investigation` — research in progress; initial values below are **recommendations pending
wearer measurements** (body-specific dimensions).

## Questions & initial positions

| # | Question | Initial position | Confidence | Source / basis |
|---|----------|------------------|-----------|----------------|
| 1 | Allowable total width of the wing structure | **50 cm** (hard limit) | ✅ | Tailor's-tape shoulder-to-shoulder, locked in design-readiness |
| 2 | Backplate shape (where harness straps attach) | angular-shield | ⚠️ | Initial guess — to validate |
| 3 | Overall backplate height | TBD | 🧍 | Depends on wearer back length (C7 → waist) + bay footprint |
| 4 | Wing-fold rise above the shoulders | TBD | 🧍 | Neck/head clearance |
| 5 | Backplate top offset below trapezius top | TBD | 🧍 | Neck clearance at C7 |
| 6 | Humerus: build it, or blend into the backplate? | TBD | ⚠️ | Bird anatomy + cosplay convention |
| 7 | Radius/ulna angle vs the spine | TBD | ⚠️ | Folded-wing anatomy |
| 8 | Fused carpal angle vs the radius member | TBD | ⚠️ | Folded-wing anatomy |
| 9 | **Pipe-foam alternatives** — other anchoring/padding strategies available in **multiple colors** | TBD | ⚠️ | New track — see below |

## Design inputs from the build plan (local, ✅)

### Electronics bay contents (settled parts, [`boards/README.md`](../../boards/README.md))

> **Battery (deferred ✅ user decision):** the backplate does **not** carry the battery — if a
> mobility battery is needed it lives in a **side pack**. The bay is electronics only, so its
> footprint no longer depends on pack size; the 2000 px vs 1400 px power decision stays open
> (see [design-readiness](../../mechanical/structural/design-readiness.md)).

| Item | Qty | Approx. footprint | Source |
|------|-----|-------------------|--------|
| MP1584EN buck module | ~6–8 | ~22 × 17 mm each | boards/README.md |
| Pixelblaze V3 controller | 1 | ~42 × 24 mm | boards/README.md |
| 74AHCT125 level shifter | 1 | ~17.5 × 16 mm | boards/README.md |
| Wago 221 lever nuts, fuse holders, wiring | — | small; routed along the wing top edges | boards/README.md |

→ Bay footprint is small (⚠️ ~15 × 12 cm incl. airflow); the backplate's size is set by **body
geometry + wing-root mounting**, not the battery.

### Feathers mount INTO the bones (quill embed)

- Quill wire cut = costume total **+ 4 cm mount tail**, "embed below the skin line into the
  frame" ([templates README](../../mechanical/templates/README.md)) → **the bone members are the
  mounting substrate the feather quills embed into**, not just decoration.
- Attachment mapping (bird anatomy, [golden-eagle data](../../mechanical/templates/golden-eagle-feather-data.md)):
  - **Primaries P1–P10 → carpal (hand) member** — longest = P4 @ 75 cm → sets the carpal member's
    position/run so the primaries reach the ~75 cm hem.
  - **Secondaries S1–S11 → ulna / forearm member** — the row above the primaries.
  - **Coverts (GPC/GSC/MD/LC/MG) + alula → upper-arm/backplate shoulder zone**, stacking
    shingle-style over the remex bases toward the shoulders.
- Implication: the members' geometry **is** the feather-layout geometry — the "bones" must land
  where each feather row attaches, and the 4 cm tails dictate minimum member thickness/layup.

## Geometry draft ⚠️ pending research

Coordinate system (draft): origin = spine centerline at backplate top; **X** lateral
(left/right), **Y** down the back toward the waist, **Z** out of the back. Viewing from behind
the wearer, per wing (mirrored left/right):

```
      spine │   C7 / trapezius top  ▲ neck — nothing may cross above ~C7
            │
  ┌─────────┼─────────┐   ← backplate top edge (offset below trapezius top, Q5)
  │         │         │
  │  bay:   │         │
  │ battery │         │
  │ + hubs  │         │
  └────┬────┴────┬────┘
       │         │        ← wing roots at the shoulder joints (acromion line)
      humerus   humerus   (Q6: included or blended into plate?)
       │         │
      elbow     elbow
       │         │
    radius/ulna  radius/ulna   ← Q7: angle vs spine (splay θ1)
       │         │
      wrist     wrist
       │         │
      carpal    carpal        ← Q8: angle vs radius member (fold θ2)
      (primaries P1–P10 attach along here, longest = P4 @ 75 cm)
```

Draft member lengths (⚠️ to refine once feather attachment rows are fixed): humerus
~15–20 cm if included; radius/ulna + carpal together span the folded-wing height below the
elbow such that the primaries reach the ~75 cm hem.

## Wearer measurement checklist (draft protocol 🧍)

Body-specific dimensions — the wearer measures these with a tailor's tape; research below
gives typical defaults to sanity-check against.

| Measurement | Why | How |
|-------------|-----|-----|
| Shoulder-to-shoulder (over back) | hard width limit (Q1) | tailor's tape across the upper back, arms down |
| Biacromial breadth | sanity-check the 50 cm | straight distance between the acromion points (palpate the bony shoulder tips) |
| C7 → inferior scapula angle | backplate min/max height (Q3) | find C7 (most prominent bump at neck base when head is flexed forward); tape to the bottom point of the shoulder blade |
| C7 → natural waist | backplate lower bound (Q3) | tape down the spine to the narrowest waist point |
| C7 → iliac crest | absolute lower bound (Q3) | tape down the spine to the top of the hip bone |
| Neck base → top of trapezius | Q5 offset | vertical drop from the neck base line to where the back "starts" |
| Wing rise above shoulder (visual) | Q4 | stand against a wall, mark acromion height; decide max visible rise above it |
| Acromion → spine centerline (X-offset) | wing-root position | tape horizontally from each acromion to the spine at shoulder level |

## Pipe-foam alternatives — anchoring + color (new track)

**What the pipe foam currently does** ([design-readiness](../../mechanical/structural/design-readiness.md)):

1. **Pads + rounds** the cardboard bone profile (feathers sit on it; foam faces the wearer).
2. **Anchor substrate** — the feather quill wires (+4 cm mount tails) embed into the frame;
   the foam receives/seats them.
3. **Visible underlayer** — where feathers overlap thinly, the covering shows → **color matters**.

**Investigate:** alternatives that keep the padding + anchoring function and are available in
**multiple colors**. Candidates to compare (✅ availability, ⚠️ to verify):

- EVA foam sheets/rolls (many colors, several thicknesses) — likely primary alternative
- Craft foam (thin EVA, wide color range)
- Closed-cell foam sheet (camping-mat grade; colors limited)
- Neoprene sheet (colors; stretch)
- Self-adhesive foam strips (colors; quick)
- Felt (colors; softer anchor, less padding)
- Non-foam anchoring strategies: velcro (hook/loop) feather mounts, zip-tie / wire-wrap
  through the cardboard layup, channel/spline slots, direct adhesive to cardboard

**Criteria:** color range · thickness/stiffness options · quill-embed hold · weight · cost ·
flammability near LEDs · moisture/sweat · workability · availability. → Deliver a comparison
table + a recommendation (keep pipe foam / switch / hybrid).

## Other considerations (draft list)

- **Center of mass**: battery is **off-back** (side pack, deferred) → the back carries wings +
  light electronics only; the wing mass still sits behind the spine → backward torque.
- **Electronics bay footprint**: battery + 2 buck hubs + controller + airflow — battery pack
  dims from [`../battery/options.md`](../battery/options.md) (3S Li-ion ~500–710 Wh).
- **Door clearance**: envelope 50 cm wide × 75 cm tall fits a standard ~0.8–0.9 m door.
- **Wing root stress**: the shoulder fold point carries the whole wing's weight.
- **Feathers over bones**: bones must sit under the feather layer (no poking through).
- **Sitting / bending**: backrest and wing-tip ground clearance.
- **Getting it on/off** solo; strap load path (shoulders vs waist belt).
- **Ventilation** for battery + bucks; sweat/moisture.

## Wearer measurement checklist (TBD — to fill)

| Measurement | Why | How |
|-------------|-----|-----|
| … | … | … |

## Sources

(to fill as research lands)

## Inputs to structural design

(to fill — recommended initial values + links to updated `mechanical/structural/` docs)
