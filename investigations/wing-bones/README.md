# Wing Bones — Bone Structure Investigation

> Scope: the **"bone" structure** of the folded wing — the member layout (no humerus —
> radius/ulna + fused carpal), the backplate that carries the harness + electronics, and the
> body-anatomy constraints that bound it all. This feeds the frame design in
> [`mechanical/structural/`](../../mechanical/structural/README.md); locking decisions happens
> in [design-readiness.md](../../mechanical/structural/design-readiness.md).
>
> **→ Matured:** the concrete build plan lives in
> [`mechanical/structural/wing-structure-plan.md`](../../mechanical/structural/wing-structure-plan.md).
> This investigation keeps the reasoning, measurements, and sources.
>
> Legend: ✅ = decided/confirmed · ⚠️ = estimate to confirm · 🧍 = needs wearer measurement.

## Status

`investigation → plan delivered` — structure decisions locked (Option C, no humerus, envelope
55 cm, θ1 = 0° / θ2 = 20°, feather-root layout computed); wearer measurements filled from
size-L standards (⚠️). Remaining: pipe-foam alternatives + frame/build details (see the plan
§8).

## Questions & initial positions

| # | Question | Initial position | Confidence | Source / basis |
|---|----------|------------------|-----------|----------------|
| 1 | Allowable total width of the wing structure | **50 cm** (hard limit) | ✅ | Tailor's-tape shoulder-to-shoulder, locked in design-readiness |
| 2 | Backplate shape (where harness straps attach) | **angular-shield** — straight-edged taper 44 → ~37 cm, height ~30–32 cm (working dims) | ⚠️ | Initial guess, now dimensioned — see Backplate geometry |
| 3 | Overall backplate height | bounded **21–42 cm** (B1–B3); final TBD | 🧍 | Wearer back length + bay footprint |
| 4 | Wing-fold rise above the shoulders | **0 cm** — fold at the acromion line (decided) | ✅ | User decision; clean front view |
| 5 | Backplate top offset below trapezius top | **≈ 3–4 cm below C7** (2–5 cm guidance) → plate top ≈ shoulder line | ⚠️ | Neck clearance at C7 — see Q4/Q5 findings below |
| 6 | Humerus: build it, or blend into the backplate? | **Skip the humerus — wing root blends into the backplate** (Option C) | ✅ | User decision |
| 7 | Radius/ulna angle vs the spine | **0°** — parallel to the spine (Option C straight member) | ⚠️ | Working value — anatomy-supported |
| 8 | Fused carpal angle vs the radius member | **20°** fan (range 15–25°) — short upper spar | ⚠️ | Working value — anatomy-supported |
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
  - **Primaries P1–P10 → carpal (hand) member** — longest ≈ P5/P6 ≈ 49/48 cm (scale ×0.9085) →
    sets the carpal member's run so the primaries' tips reach the 55 cm hem (mid-butt).
  - **Secondaries S1–S11 → ulna / forearm member** — the row above the primaries.
  - **Coverts (GPC/GSC/MD/LC/MG) + alula → upper-arm/backplate shoulder zone**, stacking
    shingle-style over the remex bases toward the shoulders.
- Implication: the members' geometry **is** the feather-layout geometry — the "bones" must land
  where each feather row attaches, and the 4 cm tails dictate minimum member thickness/layup.

## Geometry — Option C (decided ✅, layout ⚠️ working)

Coordinate system: origin = spine centerline at the shoulder line; **X** lateral (left/right),
**Y** down the back toward the waist, **Z** out of the back. Viewing from behind the wearer,
per wing (mirrored left/right):

```
      spine │   C7 / trapezius top  ▲ nothing crosses above ~C7
            │
  ┌─────────┼─────────┐   ← backplate top edge at the shoulder line (Q5)
  │         │         │
  │  bay:   │         │   (electronics only — battery is off-back)
  │ hubs+   │         │
  │ ctrl    │         │
  └────┬────┴────┬────┘
       │         │        ← wing root ON the plate corner (±20, y=0) — no humerus (Q6 ✅).
    radius/ulna  ╲         two spars spring from the root:
       │         ╲ carpal   · radius/ulna straight down (θ1 = 0°), ~13 cm
       │          ╲         · carpal fans outward (θ2 = 20°), ~14 cm
       │           ╲
    (S1–S11 on    (P1–P10 on the carpal, Atlas order P1 = wing tip)
     the forearm)
       │            ╲
       ▼             ▼
   tips y≈33–38    tips y≈30–55 (mid-butt)
   (secondaries)   (primaries)
```

**Key finding — bones are short upper spars; the scale is set by Atlas order:** the
55 cm envelope with the primaries mounted **P1→P10** (P1 = wing tip at the carpal's distal
end, P10 = innermost at the root "wrist") forces the **scale down to × 0.9085** — the longest
primaries (P5/P6, mid-series) can't exceed 55 − root_y, so P5 ≈ 48.4 cm with its tip exactly
at 55. The members are ~13–14 cm spars near the fold, hidden under the coverts; the feathers
dominate the lower ~40 cm. (The earlier ×1.024 scale forced the longest primaries to share the
top mount and scrambled the order — superseded.)

### Members (per wing)

| Member | From | To | Angle | Carries |
|--------|------|----|-------|---------|
| Radius/ulna (forearm) | (±20, 0) root | (±20, 13) | θ1 = **0°** (parallel to spine) | S1–S11 |
| Carpal (hand) | (±20, 0) root | (±24.8, 13.2) | θ2 = **20°** fan (15–25° range) | P1–P10, alula |

### Feather roots + tips (working ⚠️ — right wing; y from the shoulder line)

**Primaries** along the carpal (s = arc length from the root; y ≈ 0.94·s, x ≈ 20 + 0.34·s;
Atlas order — P1 = wing tip at the carpal's distal end, P10 = innermost at the root "wrist"):

| Feather | s (cm) | Root y | Root x | L (cm) | Tip y |
|---------|-------:|-------:|-------:|-------:|------:|
| P1 | 12.6 | 11.8 | 24.3 | 35.4 | 47.2 |
| P2 | 11.2 | 10.5 | 23.8 | 36.7 | 47.2 |
| P3 | 9.8 | 9.2 | 23.4 | 39.3 | 48.5 |
| P4 | 8.4 | 7.9 | 22.9 | 43.1 | 51.0 |
| P5 | 7.0 | 6.6 | 22.4 | 48.4 | **55.0** |
| P6 | 5.6 | 5.3 | 21.9 | 49.1 | 54.4 |
| P7 | 4.2 | 3.9 | 21.4 | 48.8 | 52.7 |
| P8 | 2.8 | 2.6 | 21.0 | 46.7 | 49.3 |
| P9 | 1.4 | 1.3 | 20.5 | 42.1 | 43.4 |
| P10 | 0 | 0.0 | 20.0 | 30.3 | 30.3 |

**Secondaries** on the forearm spar (x = ±20):

| Feather | Root y | L (cm) | Tip y |
|---------|-------:|-------:|------:|
| S1 | 4.0 | 33.6 | 37.6 |
| S2 | 4.5 | 33.5 | 38.0 |
| S3 | 5.0 | 32.1 | 37.1 |
| S4 | 6.0 | 29.5 | 35.5 |
| S5 | 6.5 | 28.7 | 35.2 |
| S6 | 7.0 | 27.8 | 34.8 |
| S7 | 7.5 | 25.7 | 33.2 |
| S8 | 8.0 | 25.1 | 33.1 |
| S9 | 8.5 | 24.5 | 33.0 |
| S10 | 9.0 | 24.0 | 33.0 |
| S11 | 9.5 | 23.6 | 33.1 |

**Coverts (deep coverage — bones hidden to y ≈ 15–18):** GPC1–6 roots y≈2–8 (tips ≈ 17–32) ·
GSC1–10 roots y≈1–8 (tips ≈ 18–20) · MD1–4 y≈0–4 (tips ≈ 10–13) · LC1–8 y≈0–3 (tips ≈ 6–8) ·
MG1–12 y≈0–2 (tips ≈ 3–5) · alula A-B/A-T at the carpal root end (near P10, pos ≈ 12–13) ·
underwing U1–10 mirrored on the spar undersides.

**Width check:** carpal end x ≈ 24.8, P10 root x ≈ 24.3 — inside the ±25 cm envelope; tips hang
vertical (same x as their roots). Any extra tip splay beyond the 20° fan comes from **bending
the quill wires** at build (build detail, not spar angle).

**θ refinement (anatomy-supported):** folded-wing kinematics show the hand folding back against
the forearm, with the forearm near-parallel to the body axis when at rest
([pigeon elbow/wrist kinematics](https://pmc.ncbi.nlm.nih.gov/articles/PMC5582118/),
[How pigeons couple elbow and wrist motion](https://royalsocietypublishing.org/rsif/article/14/133/20170224/64818),
[Proctor & Lynch, Manual of Ornithology](https://catalogue.librariesni.org.uk/)). Working values:
**θ1 = 0°, θ2 = 20°** (θ2 range 15–25°).

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
