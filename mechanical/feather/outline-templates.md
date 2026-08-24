# Feather Outline Templates

> Status: **ideation** · derived from first principles (bird-wing anatomy) · nothing locked.
> Legend: ✅ = anatomy fact (sourced) · ⚠️ = design estimate (to be locked later).

This lists every individual feather outline template the piece needs — the wing surface plus
the back/shoulder cover over the electronics — grounded in how a real bird wing is built. It
is the *mechanical* envelope list; each lit feather maps 1:1 to a `boards/led-segment/` board
(the 10 mm LED ribbon) that runs along its rachis.

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

## 2. Model decisions (first principles)

- **Two wings, mirrored.** A right-wing template is a left-wing template flipped about the
  body axis. The list below is **per wing**; multiply by 2 for the pair.
- **Individual vs shared.** Flight feathers + alula get one board each (individual templates).
  The dense, small coverts (median/lesser/marginal, and optionally the inner greater coverts)
  are better served by **shared under-lit strips**, not one board each — this matches the
  "shared under-lit strip (lesser coverts / leading edge)" board already noted in
  [`boards/README.md`](../../boards/README.md).
- **The 10 mm ribbon.** Each individual feather carries one `led-segment` board (fixed 10 mm
  wide) along its rachis. So every template needs a **vane ≥ ~14 mm wide** at the ribbon's
  widest point (10 mm board + diffuser margin). Feather widths below are chord ratios that
  respect this floor.
- **Reference scale.** Lengths are relative to the longest primary (P4 = 100). Absolute size
  is one parameter (wing-span decision) and scales the whole list uniformly.
- **Back & shoulder cover layer.** The scapulars + back coverts are a *cover* over the harness
  and electronics bay (battery, power-hubs, controller), not a flight surface. They default to
  unlit structural covers and mount to the harness/backplate, not the wing frame.

## 3. Individual feather templates — enumerated

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

> ⚠️ See §5: only the outer 9 (GC1–GC9) are recommended as **individual** boards; GC10–GC12
> fold into the shared covert strip.

### 3.5 Alula — A1…A4 (4)

Tiny, stiff, slightly asymmetric, mounted at the wrist. Length ≈ 14–16 % of P4, vane width
≈ 22 %. Enumerate as A1–A4.

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

> ⚠️ Back feathers default to **unlit structural covers** (they hide the electronics, not light
> them). If lit, they become additional `led-segment` boards and add to the §5 totals.

## 4. Shared strip templates (not individual feathers)

These cover the dense covert rows. They are under-lit ribbons with a repeating feather-scallop
edge, not discrete board-per-feather outlines.

| Template | Covers | Notes |
|----------|--------|-------|
| `median-covert-strip` | 1 row above the greater coverts | scalloped edge, graduated toward leading edge |
| `lesser-covert-strip` | 2–3 rows toward the leading edge | shorter scallops each row |
| `marginal-covert-strip` | leading edge | smallest scallops; wraps the leading edge |
| `inner-greater-covert-strip` | GC10–GC12 | optional; carries the innermost covert scallops |

## 5. Count reconciliation vs the ~70 board shapes

`boards/led-segment/design-readiness.md` carries a **~70 unique LED board shapes** placeholder
for ~1400 LEDs. This anatomy-derived list reconciles cleanly:

| Group | Per wing | Both wings |
|-------|---------:|-----------:|
| Primaries (P1–P10) | 10 | 20 |
| Secondaries (S1–S12) | 12 | 24 |
| Tertials (T1–T4) | 4 | 8 |
| Greater coverts as boards (GC1–GC9) | 9 | 18 |
| **Individual board total** | **35** | **70** |

- **70 individual feathers = 52 flight feathers (P+S+T) + 18 individual greater coverts** ✅
- Alula (A1–A4, 8 both wings) is **optional** as individual boards — small enough (1–2 LEDs)
  to fold into the marginal/leading-edge strip instead. ⚠️
- Everything else (median/lesser/marginal coverts, GC10–GC12) is served by the shared strips
  in §4.
- **Back & shoulder feathers (§3.6–§3.7) are additional mechanical templates, not part of the
  70.** They cover the electronics and default to unlit covers; if lit they add boards on top
  of the 70. ⚠️

## 6. Open decisions

- [ ] Absolute scale: wing span → sets the mm behind every relative length above.
- [ ] LED budget per feather → confirms 20-LED average, or redistributes primaries vs coverts.
- [ ] Alula as individual boards vs part of the leading-edge strip.
- [ ] Back feathers: unlit structural covers (default) vs accent-lit boards.
- [ ] Electronics-bay access: removable/hinged lid layout over battery + hubs + controller.
- [ ] Diffuser geometry per template family (primary notch vs secondary round vs covert).
- [ ] Left/right: confirm a single mirrored master is sufficient (vs hand-tuned pairs).

## References

- [Wing coverts — Wikipedia](https://en.wikipedia.org/wiki/Wing-Coverts)
- [FWS Feather Atlas — Identifying feather position](https://www.fws.gov/lab/featheratlas/id-position.html)
- [Bird Study merit badge — Wing feathers](https://merit-badge.university/merit-badges/bird-study/guide/req2b/)
- [Covert feather — ScienceDirect](https://www.sciencedirect.com/topics/veterinary-science-and-veterinary-medicine/covert-feather)
