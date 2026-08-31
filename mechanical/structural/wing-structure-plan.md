# Wing Structure — Build Plan (locked ✅)

> Concrete, buildable plan for the wing structure — bones, backplate, feather mounting.
> Distilled from the [wing-bones investigation](../../investigations/wing-bones/README.md)
> (reasoning, measurements, and sources live there). **Locked decisions live in
> [design-readiness.md](design-readiness.md)** — this is the *how-we-build-it* doc.
>
> **Status: geometry + feather sizes are LOCKED** (measured templates, feather-record.csv).
> The only open items are fabrication decisions — see §8 (working defaults noted).

## 1. Summary

- ✅ **Folded wing laid flat on the back** — envelope **50 cm wide × ~55 cm tall**; feather
  tips at **mid-butt**; feather sizes **measured from the physical templates**
  ([feather-record.csv](../../mechanical/templates/feather-record.csv), longest ≈ P5/P4 ≈
  43.5/43.0 cm); primaries mount in Atlas order P1→P10 (P1 = wing tip); tips peak at **~51 cm**
  — ~4 cm short of the 55 cm target (accepted — still mid-butt).
- ✅ **Bones are short upper spars** (~13–14 cm) hidden under the coverts; the feathers
  dominate the lower ~40 cm. **No humerus** — the wing root blends into the backplate.
- ✅ **Backplate**: angular shield carrying the electronics bay, wing roots, and strap anchors.

## 2. Coordinate system

Origin = spine centerline at the **shoulder line** (y = 0). **X** lateral (left/right,
± toward the arms), **Y** down the back (waist = positive), **Z** out of the back.
Tips at y = 55 (mid-butt). Nothing crosses above ~C7 (≈ −4 cm).

## 3. Backplate — angular shield ✅ (geometry locked; material TBD)

| Feature | Value | Basis |
|---------|-------|-------|
| Top edge | 44 cm wide @ shoulder line (±22) | E1 |
| Taper | 44 @ y=0 → 42 @ y≈17 → **~37 @ bottom** (straight edges, angular corners) | E2, E3 |
| Height | **~30–32 cm** (bottom ~6–8 cm above the natural waist) | B1–B3 + bend clearance |
| Neck relief | small center scoop (~2–3 cm deep at the spine) | C7 clearance |
| Wing roots + straps | **co-located at the top corners (±20, y=0)** — the strap pulls up where the wing loads down | C1 |
| Electronics bay | **deferred to the electronics phase** — backplate stays sized for the future ~15 × 12 cm cutout ⚠️ @ y≈14–26 (hubs + controller only) | user decision |
| Material | TBD ⚠️ — **working default: cross-laminated cardboard, ~10 mm layup** (seats the +4 cm quill-embed tails + carries wing-root load) | open decision |

## 4. Wing members (per wing, mirrored left/right) ✅

| Member | From | To | Angle | Length | Carries |
|--------|------|----|-------|--------|---------|
| Forearm spar (radius/ulna) | (±20, 0) root | (±20, 13) | θ1 = **0°** (parallel to spine) | ~13 cm | S1–S10 |
| Carpal spar (hand) | (±20, 0) root | (±24.8, 13.2) | θ2 = **20°** fan (15–25° range) | ~14 cm | P1–P10, alula |

- Both spars spring from the **reinforced root corner** (a Y-bracket on the plate corner).
- Spars: cross-laminated cardboard (**working default ~10 mm layup** — seats the +4 cm quill
  tails), foam-padded, covered (covering TBD — pipe-foam alternatives investigation).

## 5. Feather mounting — roots & tips ✅ (measured templates)

> **Position convention:** every mount point is its **position along the spar**, measured from
> the spar's **outside (distal) edge — 0 = the spar's outer end**, increasing toward the
> backplate/root. Spar lengths: forearm **13 cm**, carpal **14 cm**. **Feather numbering follows
> the USFWS Feather Atlas: numbers start at the outside of the wing and work in** — P1 = the
> wing-tip primary (carpal's distal tip), S1 = the outermost secondary (wrist side, adjacent to
> the primaries). The x/y back-plane derivation lives in the
> [wing-bones investigation](../../investigations/wing-bones/README.md).

**Primaries on the carpal spar** (14 cm long; pos 0 = the carpal's distal tip at (±24.8, 13.2);
Atlas order — P1 = wing tip at the outside, P10 = innermost at the root "wrist". L = measured
from [feather-record.csv](../../mechanical/templates/feather-record.csv)):

| Feather | Mount pos (cm from outside edge) | L (cm) | Tip y |
|---------|---------------------------------:|-------:|------:|
| P1 | 1.4 | 30.7 | 42.5 |
| P2 | 2.8 | 39.5 | 50.0 |
| P3 | 4.2 | 41.5 | 50.7 |
| P4 | 5.6 | 43.0 | **50.9** |
| P5 | 7.0 | 43.5 | 50.1 |
| P6 | 8.4 | 42.5 | 47.8 |
| P7 | 9.8 | 37.0 | 41.0 |
| P8 | 11.2 | 33.0 | 35.6 |
| P9 | 12.6 | 31.1 | 32.4 |
| P10 | 14 | 29.0 | 29.0 |

**Secondaries on the forearm spar** (13 cm long; pos 0 = the spar's lower end at (±20, 13);
Atlas order — S1 = outermost at the wrist side (pos 9), numbering works in toward the elbow;
L = measured):

| Feather | Mount pos (cm from outside edge) | L (cm) | Tip y |
|---------|---------------------------------:|-------:|------:|
| S1 | 9 | 24.8 | 28.8 |
| S2 | 8.5 | 29.3 | 33.8 |
| S3 | 8 | 27.8 | 32.8 |
| S4 | 7 | 27.0 | 33.0 |
| S5 | 6.5 | 26.2 | 32.7 |
| S6 | 6 | 25.0 | 32.0 |
| S7 | 5.5 | 23.2 | 30.7 |
| S8 | 5 | 22.0 | 30.0 |
| S9 | 4.5 | 18.6 | 27.1 |
| S10 | 4 | 15.0 | 24.0 |

**Tip lines (design check):** primaries — **50.9 (P4)** → 29.0 (P10), deepest at the longest
feathers mid-series; secondaries — 33.8 (S2) → 24.0 (S10), sitting over the primaries' root
zone. Tips hang vertical. ⚠️ **The measured templates put the tips at ~51 cm — ~4 cm short of
the 55 cm mid-butt envelope** (the physical feathers are smaller than the projection; the
envelope would need longer feathers or lower mounts to reach 55).

**Coverts (deep coverage — bones hidden to y ≈ 15–18), mount zones:**
- PC1–6 (over primaries P5–P10): carpal, pos ≈ 5.5 → 14 (tips ≈ 17–32)
- SC1–10 (over S1–S10): forearm, pos ≈ 12 → 5 (tips ≈ 18–20)
- MC1–5: forearm, pos ≈ 13 → 9 (tips ≈ 10–13)
- L1–6: forearm, pos ≈ 13 → 10 (tips ≈ 6–8)
- Alula A1–A4: carpal root end, pos ≈ 12–13 (near P10)
- Underwing U1–10: mirrored on the spar undersides (same positions as their upperwing equivalents)

**Mounting:** quill wires embed **+4 cm** into the spars (below the "skin line"); extra tip
splay comes from **bending the quill wires** (not the spar angle). **No coincident mounts** —
primaries are spaced ~1.4 cm along the carpal in P1→P10 order.

**Width check:** carpal end x ≈ 24.8, P1 root x ≈ 24.6 — inside the ±25 cm envelope.

## 6. Harness

- **Over-the-shoulder straps + cross-chest (sternum) strap**; anchors at the plate's top
  corners (shared with the wing roots). No load-bearing waist belt.

## 7. Fabrication steps (build order)

1. Cut the **backplate** from cross-laminated cardboard (angular shield + neck scoop, §3 dims).
2. Cut the **spars** (2 per wing), assemble the **root Y-brackets**, mount to the plate corners.
3. **Laminate + seal** the cardboard (⚠️ layup + seal TBD — open decision).
4. *(Bay deferred to the electronics phase — the LED-free build carries no electronics.)*
5. **Dry-fit feather rows**: secondaries → primaries → coverts; adjust the stagger on the
   mockup before committing (especially the estimated groups).
6. Mount the **quills** (+4 cm embed), bend wires for tip splay.
7. **Back-coverts panel** over the (future) bay — a removable feathered cover for the LED-free
   build (bay hardware deferred with the electronics phase).
8. Fit the **harness straps** (over-shoulder + cross-chest).

## 8. Open items — fabrication decisions only (with working defaults)

- **Feather substrate** — **deferred to Phase 2** (foam trials finalize it); this phase builds
  the feathers from **various packing foams** (user decision).
- **Covering/anchor material** (pipe-foam vs alternatives) — working default: **foam pipe
  wrap**; the alternatives investigation (colors) may change it (Q9 track).
- **Cardboard layup + seal** — working default: **~10 mm cross-laminated** layup, sealed for
  moisture/flame.
- **Backplate material + thickness** — working default: **cross-laminated cardboard, ~10 mm**.
- **Electronics bay — deferred to the electronics phase** — the LED-free build has no bay; the
  backplate stays sized for the future ~15 × 12 cm cutout. The back-coverts panel is a pure
  feathered cover for now.
- **Mockup validation** — dry-fit the feather-root layout (measured sizes) before committing
  the covert rows.
- **Vane ratio** for the generator (target ~0.80–0.82) — affects diffuser shapes, not the
  bone structure.

## 9. Weight

Worn structure ≈ **~2.0 kg** ⚠️ (frame 0.9 + feathers 0.2 + LEDs 0.3 + electronics 0.6);
battery external (side pack). See [design-readiness.md](design-readiness.md).
