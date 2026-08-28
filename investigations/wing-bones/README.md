# Wing Bones — Bone Structure Investigation

> Scope: the **"bone" structure** of the folded wing — the member layout (no humerus —
> radius/ulna + fused carpal), the backplate that carries the harness + electronics, and the
> body-anatomy constraints that bound it all. This feeds the frame design in
> [`mechanical/structural/`](../../mechanical/structural/README.md); locking decisions happens
> in [design-readiness.md](../../mechanical/structural/design-readiness.md).
>
> Legend: ✅ = decided/confirmed · ⚠️ = estimate to confirm · 🧍 = needs wearer measurement.

## Status

`investigation` — structure decisions locked (Option C, no humerus, envelope 55 cm); wearer
measurements filled from size-L standards (⚠️); remaining research tracks (angles refinement,
Q4/Q5, pipe-foam, bay/straps) pending.

## Questions & initial positions

| # | Question | Initial position | Confidence | Source / basis |
|---|----------|------------------|-----------|----------------|
| 1 | Allowable total width of the wing structure | **50 cm** (hard limit) | ✅ | Tailor's-tape shoulder-to-shoulder, locked in design-readiness |
| 2 | Backplate shape (where harness straps attach) | **angular-shield** — straight-edged taper 44 → ~37 cm, height ~30–32 cm (working dims) | ⚠️ | Initial guess, now dimensioned — see Backplate geometry |
| 3 | Overall backplate height | bounded **21–42 cm** (B1–B3); final TBD | 🧍 | Wearer back length + bay footprint |
| 4 | Wing-fold rise above the shoulders | **0 cm** — fold at the acromion line (decided) | ✅ | User decision; clean front view |
| 5 | Backplate top offset below trapezius top | **≈ 3–4 cm below C7** (2–5 cm guidance) → plate top ≈ shoulder line | ⚠️ | Neck clearance at C7 — see Q4/Q5 findings below |
| 6 | Humerus: build it, or blend into the backplate? | **Skip the humerus — wing root blends into the backplate** (Option C) | ✅ | User decision |
| 7 | Radius/ulna angle vs the spine | **≈ 0–5° splay** (Option C straight members) | ⚠️ | Working value — refine via anatomy research |
| 8 | Fused carpal angle vs the radius member | **≈ 20–25° fan** (Option C fanned carpal) | ⚠️ | Working value — refine via anatomy research |
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
  - **Primaries P1–P10 → carpal (hand) member** — longest = P4 @ **55 cm** (D1 decision) →
    sets the carpal member's position/run so the primaries reach the 55 cm hem (mid-butt).
  - **Secondaries S1–S11 → ulna / forearm member** — the row above the primaries.
  - **Coverts (GPC/GSC/MD/LC/MG) + alula → upper-arm/backplate shoulder zone**, stacking
    shingle-style over the remex bases toward the shoulders.
- Implication: the members' geometry **is** the feather-layout geometry — the "bones" must land
  where each feather row attaches, and the 4 cm tails dictate minimum member thickness/layup.

## Geometry — Option C (decided ✅, angles ⚠️)

Coordinate system: origin = spine centerline at backplate top; **X** lateral (left/right),
**Y** down the back toward the waist, **Z** out of the back. Viewing from behind the wearer,
per wing (mirrored left/right):

```
      spine │   C7 / trapezius top  ▲ neck — nothing may cross above ~C7
            │
  ┌─────────┼─────────┐   ← backplate top edge at the shoulder line (Q5: ≈3–4 cm below C7)
  │         │         │
  │  bay:   │         │   (electronics only — battery is off-back in a side pack)
  │ hubs+   │         │
  │ ctrl    │         │
  └────┬────┴────┬────┘
       │         │        ← wing roots ON the backplate (no humerus — Q6 ✅:
  radius/ulna  radius/ulna    the root blends into the plate at the acromion line)
       │         │
       │   ╲   ╱  │        ← Q7: radius/ulna ≈ straight, θ1 ≈ 0–5° splay vs spine
      wrist    wrist
       │   ╲   ╱  │        ← Q8: carpal fans outward, θ2 ≈ 20–25° vs radius
      carpal  carpal
      (primaries P1–P10 attach along here, longest = P4 @ 55 cm)
       ▼         ▼
     tips @ y=55 (mid-butt), inside the ±25 cm envelope
```

Member lengths (⚠️ to refine once feather attachment rows are fixed): **no humerus** — the
radius/ulna member starts at the backplate wing root; radius/ulna + carpal partition the 55 cm
folded height with the primaries, whose roots sit along the carpal (near the top of its run)
and hang to the mid-butt hem.

## Q4/Q5 findings — shoulder-line clearance (⚠️ research-derived)

**Q4 — wing-fold rise above the shoulders: 0 cm ✅ (decided)** — the fold sits at the acromion
line; nothing rises above the shoulders. Front view = clean (wings are a back piece); a hint of
front visibility is available later via covert overhang over the shoulder cap (styling, not
structure), never by raising the fold.

- The acromion line sits **~4 cm below C7** (B4, measured) — the C7 plane is the highest
  structure may go; the neck (base circumference ~40 cm → ~6 cm from the spine at C7) occupies
  the zone above it near the spine.
- Backpack/cosplay-harness practice: the frame/strap top sits **at or just below the top of the
  shoulders** — never riding above ([The North Face fit guide](https://www.thenorthface.com/en-se/exploration/our-journal/how-to-fit-and-wear-a-backpack),
  [OutDoz fit guide](https://outdoz.com/how-is-a-hiking-backpack-supposed-to-fit/),
  [cosplay wing harness tutorials](https://www.cestlasara.com/2019/04/26/cosplay-wing-harness-tutorial/),
  [laureltreeworkshop](http://laureltreeworkshop.com/cosplay-wing-harness/)).
- **Hard ceiling:** nothing crosses the C7 plane (~4 cm above the acromion). (A rise of ≤ +2 cm
  at the roots would be collision-safe, but Q4 is decided at 0 cm.)

**Q5 — backplate top offset below the trapezius top: ≈ 3–4 cm below C7** → the plate top lands
**at the shoulder line** (given B4 = 4 cm).

- The trapezius "top" at the midline ≈ the C7/neck-base line; the plate must clear it so it
  doesn't dig on neck extension (looking up) or shoulder shrug, and stays under the collar line.
- Common rigid-frame/backplate guidance: top edge **2–5 cm below C7**.
- **Wearer feel-test (confirm):** plate top at the shoulder line — look up, turn the head,
  shrug — no contact, no pressure.

→ Together: plate top ≈ acromion line; wing roots (±20 cm, C1) mount at the plate's top
corners; the fold does not rise above the shoulders.

## Backplate geometry (working ⚠️)

```
Backplate — angular shield (back view, spine centerline)
              ←———— 44 cm ————→   E1 @ shoulder line (y = 0)
        ┌─────────────────────┐   ← top edge at the acromion line
        │  ( ∨ small neck-    │     · over-shoulder strap anchors + wing
        │    relief scoop )   │       roots co-located at the corners (±20)
        │   ┌───────────┐     │
        │   │ bay 15×12 │     │   ← electronics only (hubs + controller)
        │   │  y≈14–26  │     │     centered on the spine
        │   └───────────┘     │
        │                     │   ← straight-edged taper:
        │                     │     44 @ y=0 → 42 @ y≈17 → ~37 @ y≈30
        └─────────────────────┘
              ←—— ~37 cm ——→     ← bottom edge y≈30–32 (≈6–8 cm above the waist)
```

- **Shape:** angular-shield — straight edges, angular corners (cuts cleanly from
  cross-laminated cardboard); tapers linearly between the measured widths E1 (44 @ shoulder
  line) → E2 (42 @ mid-scapula, y≈17) → ~37 @ bottom.
- **Top edge:** at the acromion line (Q5); **small center neck-relief scoop** (~2–3 cm deep at
  the spine) — the plate's upper-middle edge arches downward, a standard ergonomics pattern to
  clear the C7/neck region ([e.g., backplate harness patents](http://data.epo.org/publication-server/rest/v1.2/patents/EP2243347NWA1/document.html)).
- **Wing roots + straps:** co-located at the top corners (±20 cm, C1) — the shoulder strap
  pulls up at the same reinforced corner the wing loads down on.
- **Height:** ~30–32 cm (bottom ~6–8 cm above the natural waist y=38) — clears the waist bend;
  inside the 21–42 cm bounds (B1–B3).
- **Bay:** ~15 × 12 cm ⚠️ (6–8 MP1584EN + Pixelblaze + shifter + wiring + airflow), centered on
  the spine at y≈14–26 — clear of the members at ±20.
- **Material + thickness:** TBD (open decision); needs enough layup for the +4 cm quill-embed
  tails and stiffness for the wing-root load.
- **Feel-test:** top edge at the shoulder line — look up, turn, shrug, bend — no contact at the
  neck, no digging at the bottom when bending.

## Wearer measurement checklist 🧍

> Fit is to a **specific person** — values below are filled from **standard men's size-L
> measurements** (the wearer wears a large t-shirt) + standard adult-male anthropometry.
> ⚠️ = size-L-derived estimate, not tape-measured (re-measure if precision matters) ·
> ✅ = measured. Landmarks: C7 = most prominent bump at the neck base (flex head forward);
> acromion = bony shoulder tip; scapula angle = bottom tip of the shoulder blade.

### A — Width envelope (Q1)

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| A1 | Shoulder-to-shoulder, over the back | hard width limit | tailor's tape across the upper back at its widest, arms down | **50** ✅ |
| A2 | Biacromial breadth | sanity-check 50 cm vs straight bone width | straight distance between the two acromion points (palpate the bony shoulder tips) | **40** ⚠️ |

### B — Vertical placement / backplate height (Q3, Q5)

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| B1 | C7 → inferior angle of scapula | the backplate must span this for wing-root mounting | tape down the spine to the bottom tip of the shoulder blade | **21** ⚠️ |
| B2 | C7 → natural waist | backplate lower bound | tape down the spine to the narrowest waist point (bend sideways to find the crease) | **42** ⚠️ |
| B3 | C7 → iliac crest | absolute lower bound — don't go past this | tape down the spine to the top of the hip bone | **45** ⚠️ |
| B4 | C7 (neck base) → acromion line, vertical drop | the shoulder-rise region (top of trapezius); sets the Q5 offset and plate-top line | from the neck-base mark straight down to the shoulder-top (acromion) plane | **4** ⚠️ |

### C — Shoulder / wing-root (Q4, Q6)

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| C1 | Acromion → spine centerline (left + right) | wing-root X-offset from the spine | horizontal tape from each acromion point to the spine at the same height | **20** each ⚠️ |
| C2 | Acromion height above floor | shoulder-line reference for "fold rise" (Q4) | stand against a wall; mark + measure | **137** ⚠️ |
| C3 | Neck-base circumference | clearance for anything rising above the shoulders (Q4) | tape around the neck base, just below C7 | **40** ⚠️ |

### D — Wing-tip target (envelope height)

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| D1 | Shoulder line → desired wing-tip line, down the back | sets the folded-wing envelope height (was ~75 cm) | tape from the acromion line straight down the back to where the wing tips should end | **55** ✅ (decision: mid-butt) |

### E — Backplate width profile (Q2 shape, Q3)

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| E1 | Back width at the shoulder line | plate top edge width (angular-shield top) | across the back at the acromion line | **44** ⚠️ |
| E2 | Back width at mid-scapula | bay-level plate width (widest point) | across the back at the widest scapula point | **42** ⚠️ |
| E3 | Back width at the natural waist | plate bottom edge width | across the back at the waist line | **35** ⚠️ |

### F — Harness anchors

> **Configuration (decided ✅): over-the-shoulder straps with a strap across the chest**
> (cross-chest / sternum strap). With the battery off-back, the backplate needs no
> load-bearing waist belt — F2/F3 are optional (only if a waist belt or side-pack belt is
> used later).

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| F1 | Chest circumference | sizing the cross-chest strap | around the chest at its widest, under the arms | **104** ⚠️ |
| F2 | Waist circumference | optional — waist belt / side-pack belt later | around the natural waist | **89** ⚠️ |
| F3 | Hip circumference (iliac crest) | optional — same | around the hips at the iliac crest | **109** ⚠️ |

### G — Context

| # | Measurement | Why | How | Recorded (cm) |
|---|-------------|-----|-----|---------------|
| G1 | Standing height | overall scaling context | barefoot against a wall | **167** ✅ |

### Basis — size-L derived values

- Men's size-L body ranges: chest 40–42" (102–107 cm) → 104 · waist 34–36" (86–91 cm) → 89 ·
  neck 15.5–16" (39–41 cm) → 40. Sources: [Trespass men's size guide](https://trespass.ie/pages/mens-sizes-guide),
  [New Look men's trousers/jeans guide](https://www.newlook.com/uk/framework/size-guide-mens-trousersjeans),
  [Regatta regular-fit t-shirt](https://www.regattalifestyle.com/products/regular-fit-basic-t-shirt-987030-black).
- Adult-male anthropometry anchors: biacromial breadth ~38–42 cm
  ([CityU anthropometry — shoulder breadth](http://personal.cityu.edu.hk/meachan/online%20anthropometry/Chapter2/Ch2-18.htm),
  [average shoulder width](https://www.healthline.com/health/average-shoulder-width)); acromion
  height ≈ 0.80–0.84 × stature → 167 × 0.82 ≈ 137; C7 ≈ 3–5 cm above the acromion plane;
  nape-to-waist ~42–46 cm (→ 42 at this stature); scapula angle ~T7, ~21–24 cm below C7.
- ⚠️ These are working values for the initial design — the wearer can re-measure the ones that
  end up load-bearing (A1, B2, C1, F1).

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

- **Center of mass**: battery is **off-back** (external side pack) → the back carries wings +
  light electronics only; the wing mass still sits behind the spine → backward torque.
- **Electronics bay footprint**: hubs + controller + wiring only (~15 × 12 cm ⚠️) — no battery
  in the bay (battery is external; pack dims in [`../battery/options.md`](../battery/options.md)
  matter only for the side pack).
- **Door clearance**: ✅ no passage narrower than 50 cm exists — the 50 cm envelope is the hard limit (locked in design-readiness).
- **Wing root stress**: the shoulder fold point carries the whole wing's weight.
- **Feathers over bones**: bones must sit under the feather layer (no poking through).
- **Sitting / bending**: backrest and wing-tip ground clearance.
- **Getting it on/off** solo; strap load path (over-shoulder straps + cross-chest strap).
- **Ventilation** for the bucks (battery is external); sweat/moisture.

## Sources

- Men's size-L body ranges: [Trespass men's size guide](https://trespass.ie/pages/mens-sizes-guide),
  [New Look men's trousers/jeans guide](https://www.newlook.com/uk/framework/size-guide-mens-trousersjeans),
  [Regatta regular-fit t-shirt](https://www.regattalifestyle.com/products/regular-fit-basic-t-shirt-987030-black).
- Adult-male anthropometry: [CityU anthropometry — shoulder breadth](http://personal.cityu.edu.hk/meachan/online%20anthropometry/Chapter2/Ch2-18.htm),
  [average shoulder width](https://www.healthline.com/health/average-shoulder-width).
- Local sizing authority: [golden-eagle feather data](../../mechanical/templates/golden-eagle-feather-data.md),
  [templates README](../../mechanical/templates/README.md).

## Inputs to structural design

Decisions feed [design-readiness.md](../../mechanical/structural/design-readiness.md) (locking
happens there): envelope 50 × 55 cm · Option C members, no humerus · battery external ·
over-shoulder + cross-chest harness · wearer measurements above.
