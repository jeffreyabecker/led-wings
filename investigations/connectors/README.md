# Board-to-Wire Connector Selection — Research

> **Status: proposal** — no connector family chosen yet. This supersedes the earlier
> JST-PNI wire-to-wire plan. Scope: **2-pin board-to-wire connectors for the strip ends**,
> **JLCPCB/LCSC-assembled** (part must be in the JLCPCB assembly library or available
> through LCSC for consigned/PCBA sourcing).

## Constraints (from project + user)

| # | Requirement | Source |
|---|---|---|
| 1 | **Small footprint / pitch** — strip is **10 mm wide**, chunk ends are tight | `boards/lighting-and-boards.md` |
| 2 | **Keyed vs unkeyed, or male/female split, so power ≠ data** | user requirement |
| 3 | **Board side must be JLCPCB-assembled** (SMT placement) | user requirement |
| 4 | Wire side is hand-crimped (or pre-made cable) | build reality |
| 5 | Current: power run ≤ ~1.4 A per chunk @100 %; data negligible | `boards/hub-board.md` §6 |
| 6 | Two separate 2-pin pairs per chunk end: **power** and **data** | `docs/connector-pinout.md` (legacy) |
| 7 | Wearable — must not back out under flex/vibration | `` |

## Key insight: how to stop mixing connectors

There are **three** independent mechanisms, and you want to use **two at once**:

1. **Pitch difference (best, mechanically enforced).** Power on one pitch, data on another.
   A data plug physically cannot enter a power receptacle. Zero label reading, zero mistakes.
2. **Keying / polarisation.** Same pitch, different key. Cheaper (one tool, one crimp die)
   but relies on the moulded key being distinct enough to feel.
3. **Gender / colour / position.** Weakest — colour is invisible in a wing at night; gender
   only stops the wrong *pairing* if the two families differ.

**Recommendation: use mechanism 1 (split by pitch) as the primary, and mechanism 3
(harness position discipline) as the secondary.** Details in the recommendation section.

## Candidate families

All parts below are standard, widely-stocked families that appear in the LCSC/JLCPCB
ecosystem (either directly as the JST original or as the ubiquitous pin-compatible clone).
Verify the exact LCSC C-number and JLCPCB library status before committing — see
§Verification.

### A. 1.0 mm pitch — JST SH class

| | |
|---|---|
| Board header (SMT, side entry) | `SM02B-SRSS-TB` |
| Board header (SMT, top entry) | `BM02B-SRSS-TB` |
| Wire housing | `SHR-02V-S-B` |
| Contact | `SSH-003T-P0.2-H` |
| **Pitch** | **1.0 mm** |
| **Current rating** | **1 A AC/DC (AWG #28)** |
| Voltage | 50 V |
| Wire | AWG #32–#28 (0.032–0.081 mm²) |
| Lock | Friction lock (no positive latch) |
| Mounting height | ~2.9 mm (side entry) |

**Verdict:** the smallest credible option. **1 A rating is marginal** — a power run at
1.2 A is already over the JST number. Fine for **data**, tight for power.

### B. 1.25 mm pitch — JST GH class

| | |
|---|---|
| Board header (SMT, side entry) | `SM02B-GHS-TB` |
| Wire housing | `GHR-02V-S` |
| Contact | `SSHL-002T-P0.2` |
| **Pitch** | **1.25 mm** |
| **Current rating** | **1 A AC/DC (AWG #28)** |
| Voltage | 50 V |
| Wire | AWG #30–#26 |
| Lock | **Friction lock + housing lock (positive latch)** |
| Mounting height | ~1.25 mm (very low) |

**Verdict:** as low-profile as SH but with a **proper latch** — a real win for a wearable.
Still 1 A, and the GH contact needs a **different crimp die** than SH (smaller).
GH is a strong "low-profile" pick but shares the 1 A ceiling.

### C. 1.5 mm pitch — JST ZH class

| | |
|---|---|
| Board header (SMT, side entry) | `SM02B-ZHS-TB` |
| Board header (SMT, top entry) | `BM02B-ZHS-TB` |
| Wire housing | `ZHR-2` |
| Contact | `SZH-002T-P0.5` |
| **Pitch** | **1.5 mm** |
| **Current rating** | **1 A AC/DC (AWG #26)** |
| Voltage | 50 V |
| Wire | AWG #32–#26 |
| Lock | Friction lock |
| Mounting height | ~3.5 mm |

**Verdict:** you already have `C145992` (ZH 4-pin) pulled into the library, so the
footprint and crimp tooling are known. Wider than SH/GH but the widest wire range.

### D. 2.0 mm pitch — JST PH class (already in use for hub taps)

| | |
|---|---|
| Board header (SMT, side entry) | `S2B-PH-SM4-TB` (aka `PH2.0-2PWB`, LCSC `C47647`) |
| Wire housing | `PHR-2` |
| Contact | `SPH-002T-P0.5S` |
| **Pitch** | **2.0 mm** |
| **Current rating** | **2 A AC/DC (AWG #24)** |
| Voltage | 100 V |
| Wire | AWG #32–#24 |
| Lock | Friction lock (with optional locking variant) |

**Verdict:** **the only family here rated for the power you actually need.** Already
specced for the hub taps, so the tooling, footprint and crimp die exist in the build.

### E. 2.0 mm pitch, keyed — JST PA class

| | |
|---|---|
| Board header (SMT, side entry) | `BM02B-PASS-TFT` |
| Wire housing | `PAR-02V` |
| Contact | `SPA-001T-P0.5` (or `-P0.5S`) |
| **Pitch** | **2.0 mm** |
| **Current rating** | **3 A AC/DC (AWG #22)** |
| Voltage | 250 V |
| Wire | AWG #28–#22 |
| Lock | **Positive lock (inner), panel lock** |
| Keying | **Yes — housing is polarised/keyed** |

**Verdict:** highest current in this survey (3 A), a real latch, and genuinely keyed.
Cost: 2.0 mm pitch is the largest footprint, and it needs its **own crimp die** — a third
die in the toolbox next to PH and the small-pitch family.
**Note:** the wire-to-wire sibling is the **PNI family** you originally picked — PA is its
wire-to-board partner, so this is the natural evolution of that plan.

### F. 2.0 mm, board-in (no header) — JST SJN class

| | |
|---|---|
| Board-in, side entry | `02P-SJN` |
| Contact | `SJN-001PT-0.9` |
| **Pitch** | **2.0 mm** |
| **Current rating** | **3 A AC/DC (AWG #22)** |
| Voltage | 250 V |
| Mounting | **Through-hole, side entry, 2.8 mm mounting height** |

**Verdict:** interesting because the housing **sits on the board** and you solder the
contacts straight through — no SMT header, no mating halves. But it is **through-hole**
(so *not* plain SMT assembly) and it is a board-in style, which means the wire exits the
board plane. Worth noting, probably not the pick here.

### G. 1.25 mm, unkeyed + latching alternatives (Molex PicoBlade / clones)

| | |
|---|---|
| Board header (SMT) | `53398-0271` (PicoBlade 1.25 mm, vertical) |
| Wire housing | `51021-0200` |
| **Pitch** | **1.25 mm** |
| **Current rating** | **1 A** |
| Lock | Friction lock |
| Note | PicoBlade clones (`MX1.25`) are **very** well stocked at LCSC, cheapest option |

**Verdict:** cheapest and best-stocked at LCSC, but **unkeyed** and 1 A — it fails the
"don't mix connectors" goal on its own. Use only if price dominates.

## Comparison

| Family | Pitch | Rating | Wire | Lock | Keyed | SMT | Die needed |
|---|---|---|---|---|---|---|---|
| **SH** | 1.0 mm | 1 A | #32–28 | friction | ✗ | ✓ | SH/1.0 |
| **GH** | 1.25 mm | 1 A | #30–26 | **latch** | ✗ | ✓ | GH/1.25 |
| **ZH** | 1.5 mm | 1 A | #32–26 | friction | ✗ | ✓ | ZH/1.5 |
| **PH** | 2.0 mm | **2 A** | #32–24 | friction | ✗ | ✓ | PH/2.0 *(have)* |
| **PA** | 2.0 mm | **3 A** | #28–22 | **latch** | **✓** | ✓ | PA/2.0 |
| **SJN** | 2.0 mm | 3 A | #28–22 | — | — | ✗ (THT) | — |
| **PicoBlade** | 1.25 mm | 1 A | #28–26 | friction | ✗ | ✓ | 1.25 |

## Recommendation

**Split by pitch — two families, two roles. This satisfies "small footprint" and
"can't mix them" simultaneously, with no reliance on colour or keys.**

| Role | Family | Board part | Rating | Why |
|---|---|---|---|---|
| **POWER** (hub tap ↔ chunk) | **PH, 2.0 mm** | `S2B-PH-SM4-TB` (`C47647`) | 2 A | Already in the BOM, tooling and footprint on hand; only family that clears the current; 2.0 mm is *wide on purpose* so it can never enter a data socket |
| **DATA** (chunk ↔ chunk) | **SH, 1.0 mm** *(or GH if you want the latch)* | `SM02B-SRSS-TB` | 1 A | Tiny, well-stocked, and 1.0 mm physically cannot mate with 2.0 mm PH |

Why this shape:

- **Physically enforced.** A 1.0 mm SH plug cannot enter a 2.0 mm PH receptacle and vice
  versa. Power/data mix-ups become impossible rather than merely unlikely.
- **Current-correct.** Data carries no current (regenerated SPI, negligible); 1 A is
  ample. Power gets the 2 A PH it already needs.
- **One new family only.** You already use PH. This adds exactly one small-pitch family
  (SH), not three.
- **Footprint budget.** 10 mm strip width fits a 2.0 mm power header plus a 1.0 mm data
  header side by side with room to spare.

**If you would rather have a positive latch on every connector** (strongly advised for a
wearable that flexes), swap the two rows:

| Role | Family | Board part | Note |
|---|---|---|---|
| POWER | **PA, 2.0 mm keyed** | `BM02B-PASS-TFT` | 3 A + latch + keyed — best electrical/safety pick |
| DATA | **GH, 1.25 mm latched** | `SM02B-GHS-TB` | latch in a tiny package |

This costs a third crimp die (PA) but gives a latch on both halves and 3 A on power.

**Fallback if price dominates:** PH (power) + PicoBlade/MX1.25 clone (data). Cheapest and
best-stocked, but the data side is unkeyed 1 A — acceptable *only* because the pitch
split already prevents mis-mating.

## Verification checklist (do before committing)

The LCSC/JLCPCB catalogue pages are JS-rendered and could not be scraped, so confirm each
of these in the JLCPCB parts library by hand:

1. **JLCPCB library status** — search the JST MPN *and* the generic name
   (e.g. `SM02B-SRSS-TB`, `SH 1.0 2P`, `S2B-PH-SM4-TB`, `PH2.0-2PWB`). JLCPCB stocks both
   JST originals and pin-compatible clones; confirm which, and whether it is
   **"Preferred"/"Standard"/"Extended"**.
2. **Record the LCSC C-number** for: board header, wire housing, and contact — all three,
   for each family. A missing housing/contact breaks the wire side.
3. **Assembled part vs basic part** — Extended parts may carry a per-order setup fee.
4. **Minimum order / reel** — SMT headers are tape-and-reel; confirm MOQ vs the ~300
   board-side connectors this build needs.
5. **Crimp die** — confirm a die exists for each contact series. The `SN-28B` style
   ratchet does **not** fit JST small-pitch contacts; budget one die per family.
6. **Current derating** — "1 A (AWG #28)" is at #28. If power runs at 1.2–1.4 A, stay on
   PH/PA (2–3 A), not SH/GH (1 A).
7. **Strip-side anchor** — confirm the SMT header + epoxy strain relief still fits the
   10 mm strip end (`boards/2020-leds/`).

## Open questions

- Does the strip end have room for a **2.0 mm header plus a 1.0 mm header**, or does the
  power tap stay on the hub side only?
- Is a **positive latch** a hard requirement, or is friction lock acceptable given the
  feathers will be potted/strain-relieved anyway?
- Do you want a **locking PH variant** (`S2B-PH-SM4-TB(LF)(SN)` has a friction lock; the
  `SM4` locking-latch variants exist) to get a latch without adding PA?
- Does JLCPCB assembly cover the **strip FPC** at all, or are the strip boards hand-built?
  This changes whether the board-side part must be in the JLC library.
