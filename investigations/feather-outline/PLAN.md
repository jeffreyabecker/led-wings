# Feather Outline Sourcing — Plan (one-off, raster-based)

> Status: **ideation/planning** · one-off output, not a reusable pipeline.
> Shift: instead of a parametric generator, **source real feather images and trace their
> outlines**. One good set of outputs, not a system.
> Evidence + working extraction: [`feather-outline/`](./) (`contour.py`, `extract.py`,
> `out/overlay_scaled.png`, `out/outlines.json`).

---

## 1. Approach

For each feather type below, **find a clean photo of that feather**, then run it through the
existing extraction (background-subtract → marching-squares trace → Douglas-Peucker
simplify → smooth), scale to the 54 cm reference, and write SVG/DXF. Repeat per feather until
the build's set is covered.

This is deliberately **not** a reusable process: no generalized calibration, no parameter
fitting, no interpolation engine. Just "good source image → good outline," repeated as many
times as needed.

## 2. What we already have (the reference chart)

The current eagle identification chart (`reference_feathers.png`) provides, cleanly labeled:

- **Tail feathers** (R1–R6)
- **Primaries** + **secondaries** (flight feathers)
- **Scapulars**, **greater primary/secondary coverts**, **median + lesser secondary coverts**
- **Alula**
- **Body feathers** (crown, forehead, throat, breast, flank, belly, thigh, back/mantle,
  underwing coverts, tail coverts)

Good news: it traces the **dark, well-separated** ones cleanly (flight + tail feathers). Pale
downy feathers and overlapping rows need assistance.

## 3. What the build actually needs (the hangup)

The build (`feathers.json`) has **10 groups / 114 feathers**. The chart's labeled set does
**not** line up with these. The groups and what the chart gives:

| Group | Feathers | What the chart gives (usable?) |
|-------|---------|-------------------------------|
| **P** (primaries) | P1–P10 (10) | ✅ flight feathers — usable as *shape* source |
| **S** (secondaries) | S1–S12 (12) | ✅ flight feathers — usable |
| **T** (tertials) | T1–T4 (4) | ⚠️ not separately shown; innermost rounded flight feather needed |
| **GC** (greater coverts) | GC1–GC12 (12) | ✅ one covert row shown |
| **MD** (median coverts) | MD1–MD12 (12) | ✅ shown |
| **LS** (lesser coverts) | LS1-1…LS3-12 (36) | ✅ shown (3 graduated rows implied) |
| **MG** (marginal coverts) | MG1–MG12 (12) | ⚠️ smallest coverts; may need the leading-edge row |
| **A** (alula) | A-B, A-T (2) | ✅ shown |
| **SC** (scapulars) | SC1–SC6 (6) | ✅ shown |
| **BC** (back coverts) | BC1–BC8 (8) | ⚠️ back/mantle body feathers shown, but not the 8 shingle set |

**Key implication:** you don't need to source 114 individual feathers. Within a group the
feathers are **graduations** of one shape (varying length/width/roundness). So you need one
**good shape archetype per group** — then the remaining feathers in that group are produced by
scaling/graduating that one outline, not by sourcing each one.

## 4. The sourcing list (one image per archetype)

This is the actionable list. Find *one clean, isolated, well-lit* feather per archetype. Aim
for a **flat, uniform background** (the current chart's neutral gray is ideal) and the feather
fully in frame, no overlap from neighbors.

| # | Feather (archetype) | Provides build group(s) | Source note |
|---|--------------------|------------------------|-------------|
| 1 | **Primary** (outer, hooked + emargination notch) | P1–P5 | narrow, pointed, shaft bows, notched outer vane |
| 2 | **Primary** (inner, rounded, no notch) | P6–P10 | relaxes toward secondary shape |
| 3 | **Secondary** (broad, rounded, ~symmetric) | S1–S12 | the main wing surface shape |
| 4 | **Tertial** (innermost, very rounded, elongated) | T1–T4 | unlike a normal secondary; softer, broader |
| 5 | **Greater covert** (small, rounded, ~half a secondary) | GC1–GC12 | the base-covering row |
| 6 | **Median covert** (smaller, rounder) | MD1–MD12 | one row up |
| 7 | **Lesser covert** (small, round) | LS1-1…LS3-12 | 3 graduated rows — 1 archetype + gradation |
| 8 | **Marginal covert** (smallest, round) | MG1–MG12 | leading-edge seal |
| 9 | **Alula** | A-B, A-T | tiny, stiff, slightly asymmetric — 1 archetype covers both |
| 10 | **Scapular** (elongated, rounded, ~symmetric) | SC1–SC6 | shoulder bridge |
| 11 | **Back/mantle covert** (broad, rounded shingle) | BC1–BC8 | the electronics-bay lid shape |

**11 archetype images** cover all 114 build feathers, assuming within-group graduation is
acceptable. If you want *precise* per-feather silhouettes (e.g. every primary distinct), you'd
source more — but that contradicts "one good set of outputs."

> **Settled:** we do **not** need distinct per-feather silhouettes. One archetype per group,
> graduated/scaled across the group's feathers. If a distinct silhouette happens to turn up
> while sourcing (e.g. a second primary already isolated in the image), we can fold it in —
> but it is not a requirement.

## 5. Sources to look for

The current chart is a great template for what a source looks like (flat gray plate, feathers
laid flat, north-facing light). Good places to find clean, per-feather isolated shots:

- **Federal / state feather-ID plates** (e.g. USFWS Feather Atlas) — flat, labeled, dark
  feather on light background, ideal for tracing.
- **University/ornithology collection scans** (digitized specimens, usually flat + uniform
  mount).
- **High-quality feather stock/photo references** with isolated feathers on white/gray.

Avoid: feathers photographed at an angle, overlapping each other, with strong shadows, or
with any scale/annotation overlapping the silhouette (all of those break the background
subtraction).

## 6. What we need to confirm vs the build

- **Species and scale mismatch.** The chart is one eagle's plate; its proportions are the
  eagle's, not the design matrix (which anchors P4 = 75 cm). We borrow *shape*, then
  **normalize each traced outline to the build's `total_cm`** and re-derive `vane` / width as
  ratios — matching what `feathers.json` already specifies.
- **Within-group graduation.** Confirmed acceptable? (We think yes for a one-off.) If the
  gradual shrink/round across P1→P10 or the covert rows must be *exact*, that's more source
  images and more work.
- **Tertials + marginal + back coverts** are the groups the reference can't cleanly supply —
  plan to source these specifically (rows 4, 8, 11).

## 7. Output form (one good set)

For each of the 11 archetypes → one **scale-normalized closed outline** (SVG + DXF + a JSON
record `{group, total_cm, vane_cm, max_width_cm, peak_s, outline_cm}`), then graduate to the
full 114 as needed. Store as `outline_library.json` + `out/{svg,dxf}/`. This is the deliverable
that replaces `feather_outline`'s output for the build.

## 8. Out of scope (deliberately)

- The arrangement engine (A1–A8) — it transforms these outlines, doesn't generate them.
- A reusable calibration/interpolation engine — one-off, not a system.
- `--vane-ratio-adjustment` — dropped; widths come from the normized trace.
- `feather_outline`'s parametric geometry — superseded once the traced outlines are in hand.

## 9. Next action

Source the **11 archetype images** (shortlist: USFWS Feather Atlas + collection scans). Then
run each through the existing `extract.py`, normalize to `total_cm`, and build
`outline_library.json`. Validate: the generated outline must be simple, closed, positive-bbox,
and (for lit feathers) meet the ~1.4 cm vane floor.
