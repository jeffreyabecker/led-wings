# Featherbase Sourcing Sheet — regions the Atlas can't supply

This sheet tracks **only** the feather regions the USFWS Feather Atlas does
**not** provide (tertials, coverts, alula, scapulars, back/mantle coverts).
Primaries, secondaries, and tail come from the Atlas and are **not** tracked here.

Save each candidate image to `investigations/feather-outline/images/<region>/`
and record its **relative path** in the `Local image` column (e.g.
`images/tertial/tertial_01.jpg`). The per-region folders are
`tertial/`, `greater_covert/`, `median_covert/`, `lesser_covert/`,
`marginal_covert/`, `alula/`, `scapular/`, `back_mantle_covert/`. Keep the
specimen id + source URL for attribution.

> **License note (Featherbase):** non-commercial use, credit as
> *"Scientific Feather Collection www.featherbase.info"* + **specimen id**, and
> email the team before use. Record the specimen id in the table so attribution
> is captured at the source.

---

## How to use

1. Open a species page from the ranked target list
   ([`featherbase_targetlist.md`](featherbase_targetlist.md)).
2. Visually find a feather matching the region's **shape** below.
3. Save the image to `images/<region>/` and put its relative path in the region's
   table under `Local image`.
4. Record the specimen id + source URL for attribution.

Featherbase only groups scans as **primary vs secondary** publicly, so region
assignment is by eye. The `Featherbase code` column is the region abbreviation
from its own [glossary](https://www.featherbase.info/en/article/).

**Region → build group map** (the ones the USFWS Atlas lacks):

| Region | Build group | Featherbase code |
|---|---|---|
| Tertial | T | `SC` (scapular, "tertials") / `Hum` (humeral, "real tertials") |
| Greater covert | GC | `GPC` / `GSC` |
| Median covert | MD | `MSC` / `MPC` |
| Lesser covert | LS | `LSC` / `LPC` |
| Marginal covert | MG | `MaPC` / `MaSC` |
| Alula | A | `AL` |
| Scapular | SC | `SC` |
| Back / mantle covert | BC | `BA` (back) / `MA` (mantle) / `RU` (rump) |

---

## Scale — pixel → mm conversion

Featherbase specimen images are scans with an embedded **DPI**, and the
specimen page's `measure` tool uses it to convert pixels to physical units.

- **1 inch = DPI px = 25.4 mm**
- **`mm = px ÷ DPI × 25.4`** (or `px × (25.4 / DPI)`)
- Example at **150 DPI** (specimen 1698, Peregrine Falcon): `1 mm = 150/25.4
  = 5.906 px`, so **`mm = px × 0.16933`**.

> The DPI is read from the image's metadata (specimen 1698 = 150 DPI,
> 4133×2942 px). If a given image is missing/zero DPI, the image title
> (e.g. `Auflösung: 150.00 DPI`) or the page's measure tool is the fallback.

The specimen page also lists **per-feather lengths in mm** (`P1…P10`, `S1…S14`,
`R1…R6`). Use these to *verify* a measured feather's identity, not just guess by
look — see the [labelling guide](#labelling-guide--visual-distinguishing) below.

---

## Labelling guide — visual distinguishing

Region assignment is by shape **plus length**, because the per-feather mm table
is definitive for flight/tail feathers. Workflow:

1. **Measure** the feather (`px × 25.4 / DPI` = mm).
2. **Match to the mm table** — a match nails it as a primary/secondary/rectrix.
3. **The leftovers** (no mm-table entry) are your coverts / alula / scapulars —
   sort them by shape.

| Region | Shape to look for | Tip shape | Shaft / symmetry | Typical size |
|---|---|---|---|---|
| **Primary** | long, stiff, narrow | pointed; outer ones notched (emargination) | strongly asymmetric | longest on board (~13–24 cm) |
| **Secondary** | broad, softer | rounded | near-symmetric, centered | ~half primary length |
| **Tertial** | innermost wing feather, broad | very rounded, soft | near-symmetric | short (S13/S14 ≈ 6–9 cm) |
| **Greater covert** | small, rounded | rounded | symmetric | ~½–⅔ of covered feather |
| **Median covert** | smaller, rounder | rounded | symmetric | below greater covert |
| **Lesser covert** | small, round; graduated rows | rounded | symmetric | shrinking toward leading edge |
| **Marginal covert** | smallest, roundest | rounded | symmetric | leading-edge seal |
| **Alula** | tiny, stiff, slightly asymmetric | pointed | slightly asymmetric | thumb cluster |
| **Scapular** | elongated, rounded | rounded | near-symmetric | longer than coverts, not stiff |
| **Rectrix (tail)** | stiff, symmetric | pointed→rounded | centered | mid-length (~15–17 cm) |

**Key discriminator:** coverts/alula/scapulars have **no entry** in the mm
table. So a short, round feather that *does* match a listed length (e.g.
S13 = 87 mm, S14 = 64 mm) is an inner secondary/tertial, **not** a covert — the
short round inner secondaries are the easiest to mislabel.

Featherbase's own "tertial" nuance (from its glossary): it labels **scapulars**
as the "tertials" of common usage and **humerals** as the "real" tertials.

---

## Tertial (T)

**Featherbase codes:** `SC` (scapular, the "tertials" of common usage) · `Hum` (humeral, the "real" tertials)
**Shape to look for:** innermost wing feather — elongated, broad, very rounded, soft tip; sits closest to the body.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Greater covert (GC)

**Featherbase codes:** `GPC` (greater primary covert) · `GSC` (greater secondary covert)
**Shape to look for:** small, rounded, ~half the length of the flight feather it covers; sits directly over the base of a secondary/primary.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Median covert (MD)

**Featherbase codes:** `MSC` (median secondary covert) · `MPC` (median primary covert)
**Shape to look for:** smaller and rounder than the greater covert; one row above it.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Lesser covert (LS)

**Featherbase codes:** `LSC` (lesser secondary covert) · `LPC` (lesser primary covert)
**Shape to look for:** small, round; the graduated rows nearest the leading edge (in Featherbase's notes, median and lesser primary coverts are often hard to distinguish — record both if unsure).

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Marginal covert (MG)

**Featherbase codes:** `MaPC` (marginal primary covert) · `MaSC` (marginal secondary covert)
**Shape to look for:** smallest, roundest coverts; the leading-edge seal row.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Alula (A)

**Featherbase code:** `AL`
**Shape to look for:** tiny, stiff, slightly asymmetric; the thumb-feather cluster at the wrist. (Featherbase notes `ALC` = alula coverts in exceptional cases.)

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Scapular (SC)

**Featherbase code:** `SC` (scapularis / shoulder)
**Shape to look for:** elongated, rounded, near-symmetric; the shoulder rows bridging wing → body.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Back / mantle covert (BC)

**Featherbase codes:** `BA` (back) · `MA` (mantle) · `RU` (rump)
**Shape to look for:** broad, rounded shingles covering the upper back — the electronics-bay lid shape.

### Found images

| Candidate | Local image | Specimen id | Source URL | Notes |
|-----------|-------------|-------------|------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Progress log

| Date | Region | What changed |
|------|--------|--------------|
| | | |
