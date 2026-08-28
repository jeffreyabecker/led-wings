# Golden Eagle — Feather Measurements

Measured feather data for the golden eagle (*Aquila chrysaetos*, North American form
*A. c. canadensis* — the same species as the "California golden eagle") pulled from published /
institutional sources to anchor template sizing.

> **Status:** ✅ flight feathers (primaries, secondaries, rectrices) **measured** from multiple
> sources · ⚠️ alula + all covert groups (greater primary, greater secondary, median, lesser,
> underwing) **no published numeric data found** — working estimates below are flagged and must
> be validated before templates are locked.
>
> **Units:** cm throughout (sources below gave cm; featherbase mm, converted).
>
> **Caveat — dimorphism:** females run ~7 % larger in wing chord than males (631 vs 593 mm mean,
> [Birds of the World appendix](https://birdsoftheworld.org/bow/appendix/ACT1053401/APP1005437)).
> Feathers scale with the bird: adult-male feather lengths below × **1.07** ≈ female. All flight
> feather data is from **males**; the immature male specimen is from **California**.

## Sources

| Source | What it gives | Access |
|--------|---------------|--------|
| USFWS **Feather Atlas** (`featheratlas.sqlite` — `Feathers` table, `TF1–12`/`VF1–12` cols) | Total + vane length per feather for golden eagle wing scans (GOEA_wing_ad_Pri/Sec — adult ♂ BRD 901, Nevada; GOEA_wing_imm_Pri/Sec — first-year ♂ BRD 876, **California**; tail scans) | [fws.gov/lab/featheratlas](https://www.fws.gov/lab/featheratlas/) (DB: `/lab/featheratlas/data/featheratlas.sqlite`) |
| **Jenni, Ganz, Milanesi & Winkler 2020** (PLoS ONE 15(4):e0231925, data DOI 10.5281/zenodo.3724459) | 45 plucked remiges (14 primaries, 31 secondaries) from **6 dead golden eagles**; length **including the embedded calamus**, growth rate, mass, calamus width/height | [Zenodo record](https://zenodo.org/records/3724459) (CSV also archived in `data/` here) |
| **featherbase.info** specimen 3996 + species page | Partial primary lengths (mm) + species-level stats (longest primary, secondary span, wing length) | [blue.featherbase.info/en/specimen/3996](https://blue.featherbase.info/en/specimen/3996) |
| **Birds of the World — Morphological measurements of North American Golden Eagles** (Liguori et al. 2020; Bortolotti 1984; Friedmann 1950) | Body-level: wing chord, tail length by age/sex (context / scaling anchors) | [BOW appendix](https://birdsoftheworld.org/bow/appendix/ACT1053401/APP1005437) |
| **Plumarium** (Spanish feather collection) | Feather **counts** per wing: 10 primaries, 17 secondaries, 12 rectrices | [plumarium.es — Águila real](https://plumarium.es/aguila-real-%c2%b7-plumarium/) |
| The Raptor Center (UMN) — "Fabulous Feathers: Alulas" | Alula: 3–5 feathers per wing, digit-1 origin, young birds longer | [raptorcenter blog](http://theraptorcenternews.blogspot.com/2017/12/fabulous-feathers-part-2-alulas.html) |

## Feather counts (real wing)

| Group | Real count | Costume plan (templates README) |
|-------|-----------:|----------------------------------|
| Primaries | 10 / wing | P1–P10 ✅ |
| Secondaries | **17** / wing (S1 = outermost) | S1–S11 (atlas scanned only the outer 8) |
| Rectrices (tail) | 12 | — (not in plan) |
| Alula | 3–5 / wing (digit-1) | A-B, A-T |
| Greater primary coverts | ~10 (one per primary; outer ones tiny) | GPC1–GPC6 |
| Greater secondary coverts | ~17 | GSC1–GSC10 |
| Median secondary coverts | ~17 (a row) | MD1–MD4 |
| Lesser secondary coverts | variable (several rows) | LC1–LC8 |
| Underwing coverts | mirror of upperwing | U1–U10 |

## Measured — Primaries (total / vane, cm)

| P# | Adult ♂ (Nevada, BRD 901) | First-year ♂ (California, BRD 876) | Jenni et al. 2020 (n≥1, incl. calamus) | ♀ est. (adult ♂ × 1.07) |
|----|---------------------------|------------------------------------|----------------------------------------|--------------------------|
| | TF / VF | TF / VF | TF | TF |
| P1 | 39.0 / 31.1 | 35.7 / 28.2 | 33.3–36.1 | 41.7 |
| P2 | 40.4 / 32.1 | 37.4 / 29.2 | 42.1–46.2 | 43.2 |
| P3 | 43.3 / 33.9 | 39.7 / 31.1 | 48.8–54.0 | 46.3 |
| P4 | 47.4 / 37.4 | 44.1 / 34.3 | 49.6 | 50.7 |
| P5 | 53.3 / 42.6 | 49.3 / 38.7 | 53.4–57.1 | 57.0 |
| P6 | 54.0 / 43.0 | 49.6 / 39.4 | 51.5–54.5 | 57.8 |
| P7 | **53.7 / 43.9** | 48.5 / 39.5 | — | **57.5** |
| P8 | 51.4 / 42.6 | 47.3 / 38.8 | 44.9 | 55.0 |
| P9 | 46.3 / 38.6 | 42.6 / 35.3 | — | 49.5 |
| P10 | 33.4 / 29.0 | 31.8 / 27.6 | 40.6 | 35.7 |

- **Numbering (2026-08):** primaries follow the **USFWS Feather Atlas convention — numbered
  from the outside (wing tip) working in**: **P1 = the outermost (wing-tip) primary**, P10 =
  the innermost (adjacent to the secondaries).
- Longest primary: **P5 or P6** (P5 = 75 %, P6 = 25 % of birds, featherbase n=4; atlas adult ♂:
  P6 54.0 > P7 53.7 > P5 53.3). Longest-primary span **51.8–53.9 cm** (featherbase).
- Cross-check: Zenodo individual BERN/GR36 (likely ♀, 53.4–57.1 cm) brackets the female estimate.
- Vane fraction (atlas adult ♂): **0.78–0.87** — inner primaries P7–P10 0.82–0.87, outer P1–P6 ≈ 0.78–0.80. *(Costume mockup used 0.75 for P4 — real is ~0.82.)*
- Bare shaft (TF − VF, adult ♂): P10 4.4 → P6 11.0 → P1 7.9 cm. **This is the covered base the strip must hide** (plus wiring margin).

## Measured — Secondaries (total / vane, cm; S1 = outermost/longest)

| S# | Adult ♂ (BRD 901) | First-year ♂ (CA, BRD 876) | Jenni et al. 2020 | ♀ est. (× 1.07) |
|----|--------------------|----------------------------|-------------------|------------------|
| | TF / VF | TF / VF | TF | TF |
| S1 | 37.0 / 30.6 | 34.3 / 28.3 | 38.7 | 39.6 |
| S2 | 36.9 / 30.4 | 34.2 / 28.0 | 38.1 | 39.5 |
| S3 | 35.3 / 28.9 | 33.6 / 27.5 | 38.7 | 37.8 |
| S4 | 32.5 / 27.0 | 31.5 / 25.8 | 36.9 | 34.8 |
| S5 | 31.6 / 26.1 | 31.1 / 25.6 | 35.2 | 33.8 |
| S6 | 30.6 / 25.0 | 29.9 / 24.4 | 34.5 | 32.7 |
| S7 | 28.3 / 23.0 | 28.5 / 23.7 | 28.1–33.0 | 30.3 |
| S8 | 27.6 / 23.0 | 26.5 / 22.0 | 28.0–29.7 | 29.5 |
| S9 | — | — | 29.2–31.6 | — |
| S10 | — | — | 29.0–30.0 | — |
| S11 | — | — | 28.4 | — |
| S12 | — | — | 27.1–29.2 | — |
| S13 | — | — | 26.7–27.7 | — |
| S14 | — | — | 28.2 | — |

- Secondary span (species, featherbase n=4): **36.0–40.0 cm** (S1). Atlas adult ♂ S1–S8 27.6–37.0 cm.
- Vane fraction (adult ♂): **0.81–0.83**. Bare shaft: **4.6–6.5 cm**.
- Real wings carry **17 secondaries**; the atlas scanned only the outer 8. Jenni et al. covers S1–S14.

## Measured — Tail rectrices (context; not in costume plan)

Atlas adult ♂ (BRD 901): R1–R6 TF 34.6 / 35.8 / 36.4 / 35.8 / 35.3 / 35.5, VF 30.0 / 31.1 / 31.0 / 30.5 / 30.0 / 29.7 cm.
Body tail length: ♂ 326 (289–371, n=183), ♀ 346 (298–375, n=108) mm (BOW appendix).

## Body context (scaling anchors)

| Measure | ♂ mean (range) | ♀ mean (range) | Source |
|---------|----------------|----------------|--------|
| Wing chord | 593 (545–636) mm, n=190 | 631 (586–666) mm, n=107 | Liguori et al. 2020 via BOW |
| Wing chord (museum skins) | 580.5 (555–610) | 633.2 (620–666) | Friedmann 1950 via BOW |
| Tail length | 326 (289–371) mm, n=183 | 346 (298–375) mm, n=108 | Liguori et al. 2020 via BOW |

**Calamus ("quill") dimensions** (Jenni et al. 2020 — the part embedded under the skin):
primaries width 5.9–7.3 mm × height 6.1–9.3 mm; secondaries 4.5–6.9 × 4.6–7.8 mm.

## ⚠️ Not published — alula + coverts (working estimates only)

**No published numeric data was found for golden eagle alula, greater/median/lesser coverts, or
underwing coverts.** (The Feather Atlas scans remiges + rectrices only; featherbase/plumarium give
counts and photos, not lengths; veterinary gross-anatomy studies of raptor wings give counts, not
covert lengths.) Known facts: alula 3–5 feathers on digit-1, young birds longer; coverts sit in
overlapping rows over the remex bases.

Working estimates below use standard avian wing-anatomy ratios (covert ≈ ½ of the remex it covers,
median ≈ 0.6 × GSC, lesser ≈ 0.5–0.65 × median, alula ≈ 0.25–0.35 × P1) applied to the measured
adult-♂ primaries/secondaries. **These are estimates, not data — validate before locking
templates** (see Open tasks).

| Group | Basis | Working est. (adult ♂, total cm) |
|-------|-------|----------------------------------|
| Greater primary coverts GPC1–GPC6 | ≈ 0.45–0.55 × covered primary, inner set (P5–P10; e.g., P10 33.4 → 15–18) | 15–18 |
| Greater secondary coverts GSC1–GSC10 | ≈ 0.45–0.55 × secondary | 17–20 outer → 14–16 inner |
| Median secondary coverts MD1–MD4 | ≈ 0.55–0.65 × GSC | 9–13 |
| Lesser secondary coverts LC1–LC8 | ≈ 0.5–0.65 × median | 5–9 |
| Marginal coverts MG1–MG12 | smallest upperwing row | 3–6 |
| Alula A-B / A-T | ≈ 0.25–0.35 × P1 (33.4) | 8–12 (longest) |
| Underwing coverts U1–U10 | ≈ 0.8–0.95 × upperwing equivalent | 14–19 |

## Build implications

1. **Design scale:** costume **× 0.9085** — the folded wing fits the 55 cm envelope with the
   primaries in Atlas order (P1 = wing tip; longest ≈ P5/P6 ≈ 49/48 cm, tips peak at 55; was × 1.024 →
   × 1.40). Apply one global scale factor
   (generator `--vane-ratio-adjustment` + uniform scale), don't hand-tune per feather.
2. **Vane fraction:** real flight feathers are 0.78–0.87 vane/total; the mockup's 0.75 runs
   low — shift vane ratio up (toward 0.80–0.82) to keep the lit-vane silhouette eagle-proportioned.
3. **Covered base:** bare shaft (TF − VF) is 4.4–11.0 cm on primaries, 4.6–6.5 cm on secondaries —
   the LED strip's covered base + wiring exit should fit inside that, hidden at the skin line.
4. **Quill embed:** the calamus is fully below the skin in life (5.9–7.3 × 6.1–9.3 mm primaries) —
   feathers mount through the "skin" into the frame (see constructability note).

## Open tasks

- [ ] Validate covert/alula/underwing estimates — photograph a real golden eagle wing (museum
      specimen or molted set) with a **ruler**, or measure from a scale-calibrated image.
- [ ] Decide male vs female sizing for the costume (female ≈ ×1.07) and lock the global scale.
- [ ] Re-confirm the secondaries count the costume needs (real = 17; plan = 11).
- [ ] Re-cut LED chunk counts in `boards/` once template sizing is locked from this file.

## Archived data

- `data/jenni_etal_2020_golden_eagle_final.csv` — raw flight-feather measurements (6 birds;
  Jenni et al. 2020, Zenodo DOI 10.5281/zenodo.3724459, open data).
- Feather Atlas numbers were queried from `https://www.fws.gov/lab/featheratlas/data/featheratlas.sqlite`
  (`Feathers` table: `TF1–12` total length, `VF1–12` vane length, cm; rows `GOEA_wing_*`).
