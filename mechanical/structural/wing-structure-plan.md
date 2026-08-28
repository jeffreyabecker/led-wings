# Wing Structure — Build Plan (working ⚠️)

> Concrete, buildable plan for the wing structure — bones, backplate, feather mounting.
> Distilled from the [wing-bones investigation](../../investigations/wing-bones/README.md)
> (reasoning, measurements, and sources live there). **Locked decisions live in
> [design-readiness.md](design-readiness.md)** — this is the *how-we-build-it* doc.
> ⚠️ Working — validate the feather-root layout and estimates on the mockup before committing.

## 1. Summary

- **Folded wing laid flat on the back** — envelope **50 cm wide × 55 cm tall**; feather tips at
  **mid-butt** (55 cm below the shoulder line); feather scale **× 0.9085** — the primaries mount
  in anatomical order P1→P10, longest ≈ P5/P6 (49/48 cm), tips peaking at 55.
- **Bones are short upper spars** (~13–14 cm) hidden under the coverts; the feathers dominate
  the lower ~40 cm. **No humerus** — the wing root blends into the backplate.
- **Backplate**: angular shield carrying the electronics bay, wing roots, and strap anchors.

## 2. Coordinate system

Origin = spine centerline at the **shoulder line** (y = 0). **X** lateral (left/right,
± toward the arms), **Y** down the back (waist = positive), **Z** out of the back.
Tips at y = 55 (mid-butt). Nothing crosses above ~C7 (≈ −4 cm).

## 3. Backplate — angular shield

| Feature | Value | Basis |
|---------|-------|-------|
| Top edge | 44 cm wide @ shoulder line (±22) | E1 |
| Taper | 44 @ y=0 → 42 @ y≈17 → **~37 @ bottom** (straight edges, angular corners) | E2, E3 |
| Height | **~30–32 cm** (bottom ~6–8 cm above the natural waist) | B1–B3 + bend clearance |
| Neck relief | small center scoop (~2–3 cm deep at the spine) | C7 clearance |
| Wing roots + straps | **co-located at the top corners (±20, y=0)** — the strap pulls up where the wing loads down | C1 |
| Electronics bay | ~15 × 12 cm ⚠️ centered on the spine, y≈14–26 (hubs + controller only) | settled parts |
| Material | TBD ⚠️ (cross-laminated cardboard candidate; layup/thickness for the +4 cm quill-embed tails + stiffness) | open decision |

## 4. Wing members (per wing, mirrored left/right)

| Member | From | To | Angle | Length | Carries |
|--------|------|----|-------|--------|---------|
| Forearm spar (radius/ulna) | (±20, 0) root | (±20, 13) | θ1 = **0°** (parallel to spine) | ~13 cm | S1–S11 |
| Carpal spar (hand) | (±20, 0) root | (±24.8, 13.2) | θ2 = **20°** fan (15–25° range) | ~14 cm | P1–P10, alula |

- Both spars spring from the **reinforced root corner** (a Y-bracket on the plate corner).
- Spars: cross-laminated cardboard (~10 mm layup ⚠️ — needs to seat the +4 cm quill tails),
  foam-padded, covered (covering TBD — pipe-foam alternatives investigation).

## 5. Feather mounting — roots & tips (working ⚠️)

> **Position convention:** every mount point is its **position along the spar**, measured from
> the spar's **outside (distal) edge — 0 = the spar's outer end**, increasing toward the
> backplate/root. Spar lengths: forearm **13 cm**, carpal **14 cm**. The x/y back-plane
> derivation lives in the [wing-bones investigation](../../investigations/wing-bones/README.md).

**Primaries on the carpal spar** (14 cm long; pos 0 = the carpal's distal tip at (±24.8, 13.2);
anatomical order — P1 at the root end "wrist", P10 at the outside tip):

| Feather | Mount pos (cm from outside edge) | L (cm) | Tip y |
|---------|---------------------------------:|-------:|------:|
| P10 | 1.4 | 35.4 | 47.3 |
| P9 | 2.8 | 36.7 | 47.2 |
| P8 | 4.2 | 39.3 | 48.5 |
| P7 | 5.6 | 43.1 | 51.0 |
| P6 | 7.0 | 48.4 | **55.0** |
| P5 | 8.4 | 49.1 | 54.4 |
| P4 | 9.8 | 48.8 | 52.7 |
| P3 | 11.2 | 46.7 | 49.3 |
| P2 | 12.6 | 42.1 | 43.4 |
| P1 | 14 | 30.3 | 30.3 |

**Secondaries on the forearm spar** (13 cm long; pos 0 = the spar's lower end at (±20, 13)):

| Feather | Mount pos (cm from outside edge) | L (cm) | Tip y |
|---------|---------------------------------:|-------:|------:|
| S11 | 3.5 | 23.6 | 33.1 |
| S10 | 4 | 24.0 | 33.0 |
| S9 | 4.5 | 24.5 | 33.0 |
| S8 | 5 | 25.1 | 33.1 |
| S7 | 5.5 | 25.7 | 33.2 |
| S6 | 6 | 27.8 | 34.8 |
| S5 | 6.5 | 28.7 | 35.2 |
| S4 | 7 | 29.5 | 35.5 |
| S3 | 8 | 32.1 | 37.1 |
| S2 | 8.5 | 33.5 | 38.0 |
| S1 | 9 | 33.6 | 37.6 |

**Tip lines (design check):** primaries — 55.0 (P6) graduating down to 30.3 (P1), deepest at
the longest feathers mid-carpal; secondaries — 38.0 (S2) → 33.0 (S9/S10), sitting over the
primaries' root zone. Tips hang vertical.

**Coverts (deep coverage — bones hidden to y ≈ 15–18), mount zones:**
- GPC1–6: carpal, pos ≈ 12 → 5.5 (tips ≈ 17–32)
- GSC1–10: forearm, pos ≈ 12 → 5 (tips ≈ 18–20)
- MD1–4: forearm, pos ≈ 13 → 9 (tips ≈ 10–13)
- LC1–8: forearm, pos ≈ 13 → 10 (tips ≈ 6–8)
- MG1–12: forearm, pos ≈ 13 → 11 (tips ≈ 3–5)
- Alula A-B/A-T: carpal root end, pos ≈ 12–13 (near P1)
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
4. Mount the **electronics bay** (hubs + controller), route wiring egress + strain relief.
5. **Dry-fit feather rows**: secondaries → primaries → coverts; adjust the stagger on the
   mockup before committing (especially the estimated groups).
6. Mount the **quills** (+4 cm embed), bend wires for tip splay.
7. **Back-coverts lid** over the bay (hinged/removable — open decision).
8. Fit the **harness straps** (over-shoulder + cross-chest).

## 8. Open items feeding this plan

- **Pipe-foam alternative** — covering/anchor material + color (investigation track D).
- **Cardboard layup + seal** — moisture/flame barrier.
- **Backplate material + thickness** — integration with spars and straps.
- **Bay lid** sealing/access; **back-coverts lid** carries electronics or not.
- **Mockup validation** of the feather-root layout (roots/tips tables above).
- Vane-ratio shift to **~0.80–0.82** (generator `--vane-ratio-adjustment`).

## 9. Weight

Worn structure ≈ **~2.1 kg** ⚠️ (frame 0.9 + feathers 0.3 + LEDs 0.3 + electronics 0.6);
battery external (side pack). See [design-readiness.md](design-readiness.md).
