# Feather Outline Templates

> Status: **ideation** · derived from first principles (bird-wing anatomy) · nothing locked.
> Legend: ✅ = anatomy fact (sourced) · ⚠️ = design estimate (to be locked later).

This lists every individual feather outline template the piece needs — the wing surface plus
the back/shoulder cover over the electronics — grounded in how a real bird wing is built. It is
the *mechanical* envelope only: **outlines (geometry) and how the feathers arrange/layer**.
Lighting (which feathers are lit, individual boards vs shared strips) and board mapping live
separately in [lighting-and-boards.md](lighting-and-boards.md).

## 1. Grounding — what a wing actually has

A bird wing is a stack of feather **groups**, each with its own job and silhouette:

| Group | Position | Job | Typical count |
|-------|----------|-----|---------------|
| **Primaries** | hand (outermost) | thrust — long, stiff, asymmetric | 9–11 |
| **Secondaries** | forearm (ulna) | lift — broad, rounded | 10–25 (species-dependent) |
| **Tertials** | innermost ulna/humerus | cover the folded wing — elongated | 3–4 |
| **Greater coverts** | over secondary/primary bases | smooth airflow; ~1 per flight feather | ≈ secondaries |
| **Median coverts** | one row above the greater coverts | surface smoothing | 1 row |
| **Lesser coverts** | 2–4 rows to the leading edge | leading-edge surface | 2–4 rows |
| **Marginal coverts** | leading edge | leading-edge seal | 1 row |
| **Alula** | thumb (digit I) | leading-edge slot / slow-flight control | 3–5 |
| **Scapulars** | shoulder | join wing to body | few |
| **Back (mantle) coverts** | upper back / between wings | cover the body + electronics bay | several rows |

Sources: [Wing coverts — Wikipedia](https://en.wikipedia.org/wiki/Wing-Coverts) ·
[FWS Feather Atlas — Identifying feather position](https://www.fws.gov/lab/featheratlas/id-position.html) ·
[Bird Study merit badge — Wing feathers](https://merit-badge.university/merit-badges/bird-study/guide/req2b/).

### Shape signatures (the geometry each template must encode)

- **Primary** — asymmetric: rachis offset toward the leading edge (outer vane ≈ ⅓ width,
  inner vane ≈ ⅔); narrow; pointed tip; shaft bows forward; the outer 3–5 have an
  **emargination** (a notch cut into the outer vane near the tip). ✅
- **Secondary** — near-symmetric (rachis ≈ centered); broad; blunt/rounded tip; gentle curve. ✅
- **Tertial** — elongated, broad, very rounded, near-symmetric; soft tip. ✅
- **Greater covert** — small, rounded, symmetric, slightly curved; mirrors the flight feather
  it covers at roughly half its length. ✅
- **Median covert** — smaller and rounder than the greater covert. ✅
- **Lesser covert** — small and round; several graduated rows shrinking toward the leading edge. ✅
- **Marginal covert** — smallest, round; hugs the leading edge. ✅
- **Alula** — tiny, stiff, slightly asymmetric; mounted at the wrist. ✅
- **Scapular** — elongated, rounded, near-symmetric; layered rows over the shoulder; bridges
  wing → body. ✅
- **Back (mantle) covert** — broad, rounded, near-symmetric; overlaps like shingles (top
  feathers over bottom), covering the upper back. ✅

## 2. Outline model decisions

- **Two wings, mirrored.** A right-wing template is a left-wing template flipped about the
  body axis. The lists below are **per wing**; multiply by 2 for the pair. The back coverts
  (§3.7) are a single center-back set.
- **Reference scale.** Lengths are relative to the longest primary (P4 = 100). Now locked to
  **P4 = 100 cm** (1 unit = 1 cm) from the physical envelope — see §6.
- **Chord ratios.** "Vane width" is a % of feather length (chord ratio) and sets each
  template's silhouette. The absolute mm floor a *lit* feather must meet is a board constraint
  — see [lighting-and-boards.md](lighting-and-boards.md).
- **Back & shoulder cover layer.** The scapulars + back coverts are a *cover* over the harness
  and electronics bay (battery, power-hubs, controller), not a flight surface. They mount to the
  harness/backplate, not the wing frame.

## 3. Individual feather outlines — enumerated

> Per wing unless noted; the back coverts (§3.7) are a single shared center-back set.

### 3.1 Primaries — P1…P10 (10)

Ordered outermost → innermost. The outer feathers are longer-stiffer, narrower, more curved
and notched; the inner ones relax toward the secondary shape.

| ID | Length | Vane width* | Rachis (outer:inner) | Tip | Curvature | Emargination |
|----|-------:|------------:|----------------------|-----|-----------|--------------|
| P1 | 74 | 13 % | 30:70 | pointed, hooked | high | yes |
| P2 | 86 | 14 % | 31:69 | pointed | high | yes |
| P3 | 94 | 15 % | 33:67 | pointed | high | yes |
| P4 | 100 | 16 % | 34:66 | pointed | med-high | yes |
| P5 | 98 | 17 % | 35:65 | pointed | med | yes |
| P6 | 93 | 18 % | 37:63 | pointed | med | no |
| P7 | 88 | 19 % | 40:60 | pointed | med-low | no |
| P8 | 82 | 20 % | 43:57 | rounded-point | low | no |
| P9 | 77 | 21 % | 46:54 | rounded | low | no |
| P10 | 72 | 22 % | 48:52 | rounded | low | no |

\* vane width as % of feather length (chord ratio).

### 3.2 Secondaries — S1…S12 (12)

Ordered outermost → innermost. Broad, rounded, near-symmetric; length tapers gently toward
the body.

| ID | Length | Vane width* | Rachis (outer:inner) | Tip | Curvature |
|----|-------:|------------:|----------------------|-----|-----------|
| S1 | 78 | 24 % | 46:54 | rounded | low |
| S2 | 79 | 24 % | 47:53 | rounded | low |
| S3 | 79 | 25 % | 48:52 | rounded | low |
| S4 | 78 | 25 % | 49:51 | rounded | low |
| S5 | 77 | 25 % | 49:51 | rounded | low |
| S6 | 76 | 25 % | 50:50 | rounded | low |
| S7 | 74 | 24 % | 50:50 | rounded | low |
| S8 | 72 | 24 % | 50:50 | rounded | low |
| S9 | 70 | 23 % | 50:50 | rounded | low |
| S10 | 67 | 22 % | 50:50 | rounded | low |
| S11 | 64 | 21 % | 50:50 | rounded | low |
| S12 | 60 | 20 % | 50:50 | rounded | low |

### 3.3 Tertials — T1…T4 (4)

Innermost, elongated and very rounded; these cover the wing when it folds.

| ID | Length | Vane width* | Tip |
|----|-------:|------------:|-----|
| T1 | 74 | 26 % | very rounded |
| T2 | 78 | 27 % | very rounded |
| T3 | 80 | 28 % | very rounded |
| T4 | 82 | 29 % | very rounded |

### 3.4 Greater coverts — GC1…GC12 (12)

One per secondary; each `GCn` mirrors `Sn` at ≈ 50 % length, ≈ 24 % vane width, rounded,
slightly curved. Enumerate as GC1–GC12 (outer → inner).

### 3.5 Alula — A-B (bottom) + A-T (top) (2, per side)

Two tiny, stiff, slightly asymmetric thumb feathers at the wrist: the **bottom alula** and the
**top alula**. Both are lit individually. Length ≈ 14–16 % of P4 (≈ 11 cm total, ~8 cm vane),
vane width ≈ 22 % (≈ 2.5 cm).

### 3.6 Scapulars — SC1…SC6 (6, per side)

Shoulder feathers that bridge the wing to the body and cover the wing base + shoulder straps.
Elongated, rounded, near-symmetric; layered so each overlaps the one below it.

| ID | Length | Vane width* | Tip |
|----|-------:|------------:|-----|
| SC1 | 55 | 28 % | rounded |
| SC2 | 58 | 29 % | rounded |
| SC3 | 61 | 30 % | rounded |
| SC4 | 63 | 30 % | rounded |
| SC5 | 62 | 29 % | rounded |
| SC6 | 58 | 28 % | rounded |

### 3.7 Back coverts — BC1…BC8 (8, center back)

Broad, rounded shingles covering the **electronics bay** (battery, power-hubs, controller) on
the upper back. BC1 sits highest (below the neck), BC8 lowest (lumbar); each overlaps the one
below. Together they form a removable lid for service access.

| ID | Length | Vane width* | Tip |
|----|-------:|------------:|-----|
| BC1 | 42 | 30 % | rounded |
| BC2 | 45 | 31 % | rounded |
| BC3 | 48 | 32 % | rounded |
| BC4 | 52 | 33 % | rounded |
| BC5 | 53 | 33 % | rounded |
| BC6 | 51 | 32 % | rounded |
| BC7 | 48 | 31 % | rounded |
| BC8 | 44 | 30 % | rounded |

## 4. Arrangement & layering

The wing is a shingled stack: each feather overlaps the one behind/inside it — bases covered,
tips free — so the surface reads as one continuous silhouette. Order below is **topmost →
bottommost** (as viewed from above).

| Layer | Templates | Position / overlap |
|-------|-----------|--------------------|
| Back coverts | BC1–BC8 | center-back shingles over the electronics bay; BC1 highest (near neck) → BC8 lowest (lumbar); each overlaps the one below |
| Scapulars | SC1–SC6 (per side) | shoulder rows bridging wing → body; layered, each over the one below |
| Flight feathers | P1–P10, S1–S12, T1–T4 | the wing surface; primaries outermost → tertials innermost; each outer feather overlaps the inner one's base |
| Greater coverts | GC1–GC12 | one over each secondary's base at ≈ 50 % of its length; cover the flight-feather bases |
| Median coverts | (1 row) | one row above the greater coverts |
| Lesser coverts | (2–4 rows) | graduate toward the leading edge |
| Marginal coverts | (1 row) | leading-edge row; wraps the leading edge |
| Alula | A-B (bottom) + A-T (top) | at the wrist (thumb / digit I), leading-edge slot |

- **Flight-feather order (outer → inner):** P1…P10 → S1…S12 → T1…T4. P1 is the outermost
  primary; S1 sits adjacent to P10; T1…T4 are innermost, over the folded-wing area.
- **Covert stacking:** the covert rows sit *over* the flight-feather bases and shorten row by
  row as they approach the leading edge (greater → median → lesser → marginal).
- **Greater-covert pairing:** `GCn` mirrors `Sn` at ≈ 50 % length — one greater covert per
  secondary.
- **Shingle direction:** every feather points toward the wing tip and overlaps the feather
  behind it (the more-distal feather lies on top).
- **Mirroring:** the right wing is the left wing flipped about the body axis. Back coverts are
  a single center-back set (not mirrored); scapulars are per-side.
- **Cover layer:** scapulars + back coverts sit over the harness/electronics bay and mount to
  the harness/backplate, not the wing frame.

## 5. Open decisions

- [ ] Feather width: slender streamers (~6–8 cm) vs broad plumes (~10–16 cm) at ~75 cm length.
- [ ] Confirm hem clearance + panel height (working: field ≈ longest primary P4 = 75 cm).
- [ ] Layout: left/right wing columns + center back covers, vs one continuous feather field.
- [ ] Diffuser geometry per template family (primary notch vs secondary round vs covert).
- [ ] Left/right: confirm a single mirrored master is sufficient (vs hand-tuned pairs).
- [ ] Shingle overlap: exact % each feather's base is covered by the feather over it.
- [ ] Electronics-bay access: removable/hinged lid layout over battery + hubs + controller.

## 6. Physical size & scaling

Envelope from the P4 mockup + shoulder measurement: **50 cm wide × ~75 cm tall**, folded flat on
the back.

- **Width:** 50 cm (shoulder-to-shoulder, measured) — the hard limit for the whole assembly.
- **Height:** set by the longest feather. The P4 mockup is **75 cm quill-to-tip** with a **56 cm
  vane** — that's the longest primary, so the folded wing field is ~75 cm tall, hanging from the
  shoulders down the back (past the butt, clear of the floor).
- **Form:** a **folded** wing laid flat on the back — feathers point down/back and overlap
  shingle-style, **not** an extended, outspread wing. Longest feathers (primaries) reach the hem;
  coverts stack up toward the shoulders. This is what §4's layering model fills.

### Scale factor (from the P4 mockup)

| Reference | Value |
|-----------|-------|
| Longest primary (P4) | 100 relative units |
| Mockup | **75 cm** quill-to-tip, **56 cm** vane |
| Scale | **1 unit = 0.75 cm** (P4 = 75 cm) |

### Re-scaled flight-feather lengths (cm, quill-to-tip) — × 0.75

| Primary | cm | Secondary | cm | Tertial | cm |
|---------|---:|-----------|---:|---------|---:|
| P1 | 56 | S1 | 59 | T1 | 56 |
| P2 | 65 | S2 | 59 | T2 | 59 |
| P3 | 71 | S3 | 59 | T3 | 60 |
| P4 | 75 | S4 | 59 | T4 | 62 |
| P5 | 74 | S5 | 58 | | |
| P6 | 70 | S6 | 57 | | |
| P7 | 66 | S7 | 56 | | |
| P8 | 62 | S8 | 54 | | |
| P9 | 58 | S9 | 53 | | |
| P10 | 54 | S10 | 50 | | |
| | | S11 | 48 | | |
| | | S12 | 45 | | |

Vane length ≈ **0.75 × total** (from P4: 56/75). Coverts & back (cm, total): greater coverts
GC1–GC12 ≈ **22–29** (half their secondary); scapulars SC1–SC6 ≈ **41–47**; back coverts BC1–BC8
≈ **32–40**.

### Width (⚠️ design decision)

Feather widths must be chosen, not taken from real-bird vane ratios (13–22 % of length → 10–16 cm
at this scale — too fat for ~76 in a 50 cm panel). Recommended: **long-narrow feathers**, ~6–8 cm
wide for the flight feathers (still ≥ ~14 mm to carry the 10 mm LED ribbon). Choose slender
streamers vs broad plumes.

> Width vs lighting is resolved: a single 10 mm ribbon lights a ~2–3 cm band, so vane edges glow
> dimmer than the rachis — the **bright-rachis gradient is accepted** (no dual boards). See
> [lighting-and-boards.md](lighting-and-boards.md).

### Layout (folded wing, flat on back)

- One 50 cm panel centered on the spine, mounted at the shoulders.
- Left/right wings occupy the outer ~20–22 cm; back coverts sit in the center over the
  electronics bay.
- Feathers hang downward, overlapping top-over-bottom; longest (primaries) at the hem.

## 7. Drafting dimensions (cm)

> Working absolute dims to draw each outline as a vector. Scale from §6: **1 unit = 0.75 cm**,
> **vane ≈ 0.75 × total** (P4: 75 total / 56 vane). Widths below are the **working "slender"
> values** (⚠️ — confirm the §6 Width decision before locking).

### Flight feathers

| ID | Total | Vane | Max width | Tip | Rachis (out:in) | Curve |
|----|------:|-----:|----------:|-----|-----------------|-------|
| P1 | 56 | 42 | 4.5 | pointed, hooked | 30:70 | high |
| P2 | 65 | 48 | 5 | pointed | 31:69 | high |
| P3 | 71 | 53 | 5 | pointed | 33:67 | high |
| P4 | 75 | 56 | 5.5 | pointed | 34:66 | med-high |
| P5 | 74 | 55 | 5.5 | pointed | 35:65 | med |
| P6 | 70 | 52 | 5.5 | pointed | 37:63 | med |
| P7 | 66 | 50 | 6 | pointed | 40:60 | med-low |
| P8 | 62 | 46 | 6 | rounded-point | 43:57 | low |
| P9 | 58 | 43 | 6 | rounded | 46:54 | low |
| P10 | 54 | 41 | 6.5 | rounded | 48:52 | low |
| S1 | 59 | 44 | 7 | rounded | 46:54 | low |
| S2 | 59 | 44 | 7 | rounded | 47:53 | low |
| S3 | 59 | 44 | 7 | rounded | 48:52 | low |
| S4 | 59 | 44 | 7 | rounded | 49:51 | low |
| S5 | 58 | 43 | 7 | rounded | 49:51 | low |
| S6 | 57 | 43 | 7 | rounded | 50:50 | low |
| S7 | 56 | 42 | 7 | rounded | 50:50 | low |
| S8 | 54 | 41 | 7 | rounded | 50:50 | low |
| S9 | 53 | 39 | 7 | rounded | 50:50 | low |
| S10 | 50 | 38 | 6.5 | rounded | 50:50 | low |
| S11 | 48 | 36 | 6.5 | rounded | 50:50 | low |
| S12 | 45 | 34 | 6.5 | rounded | 50:50 | low |
| T1 | 56 | 42 | 8 | very rounded | ≈50:50 | low |
| T2 | 59 | 44 | 8 | very rounded | ≈50:50 | low |
| T3 | 60 | 45 | 8 | very rounded | ≈50:50 | low |
| T4 | 62 | 46 | 8 | very rounded | ≈50:50 | low |

All cm. **Total** = quill-to-tip · **Vane** = barbed outline (quill ≈ total − vane) · **Max
width** = vane width at the widest point (≥ ~1.4 cm to carry the 10 mm LED ribbon).

### Coverts & back (cm)

| Group | Total | Vane | Max width | Tip |
|-------|------:|-----:|----------:|-----|
| Greater coverts GC1–GC12 | 23–30 (half its secondary) | 17–23 | 6 | rounded |
| Alula A-B + A-T | 11 | 8 | 2.5 | rounded, slightly asymmetric |
| Scapulars SC1–SC6 | 41–47 | 31–35 | 7 | rounded |
| Back coverts BC1–BC8 | 32–40 | 24–30 | 8 | rounded |

### How to draw one feather (vector recipe)

1. Draw the **rachis** as a straight line of length **Total**.
2. Mark the **vane** over the top **Vane** length (the bare quill is the lower `Total − Vane`).
3. Sweep the outline to **Max width** at ~40–50 % of vane length from the base, tapering to the tip.
4. Offset the shaft by the **rachis** split (outer:inner) across that width — asymmetric for
   primaries (shaft near the leading edge), ≈ centered (50:50) for the rounded feathers.
5. Finish the tip per the **Tip** column; add the **emargination** notch to the outer vane near
   the tip of the outer primaries (P1–P5).
6. Apply **Curve** by bowing the rachis (high for outer primaries, ~straight for coverts).

## References

- [Wing coverts — Wikipedia](https://en.wikipedia.org/wiki/Wing-Coverts)
- [FWS Feather Atlas — Identifying feather position](https://www.fws.gov/lab/featheratlas/id-position.html)
- [Bird Study merit badge — Wing feathers](https://merit-badge.university/merit-badges/bird-study/guide/req2b/)
- [Covert feather — ScienceDirect](https://www.sciencedirect.com/topics/veterinary-science-and-veterinary-medicine/covert-feather)
