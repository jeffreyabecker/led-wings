# Hub Modules — Logical Hub List & Module Spec

> **Status: draft ⚠️** — the hub list below derives from the **templates feather
> inventory** (`mechanical/templates/README.md`, authoritative ✅) + the lighting model
> (exposed-tip stagger + bleed @ 96 LED/m). LED counts per feather are from
> [`lighting-and-boards.md`](lighting-and-boards.md); re-derive if the lighting model
> changes. The module spec (§3) is a starting point for "do we DIY the buck" — see §4.

## 1. System context (locked)

- **12 V bus** runs along the wing's top edge (feather bases); hubs hang off it and feed
  short **5 V runs** into their cluster. Data is separate (one daisy-chain per wing).
- **Feather inventory (authoritative — templates README):** P1–P10, S1–S11, A-B/A-T,
  GPC1–GPC6, GSC1–GSC10, MD1–MD4, LC1–LC8, MG1–MG12, U1–U10 — **73 feathers/wing**.
  (The lighting map's "S1–S12 / GC1–GC12 / T1–T4" are superseded by the templates.
  T (tertials) are **not in the templates inventory** — ⚠️ see §4.5.)
- **Full-white per feather** (40 mA/LED @ 96 LED/m, lighting map counts): P **0.68 A**
  (17 LEDs) · S **0.56 A** (14) · A **0.40 A** (10) · GSC **0.40 A** (10) · GPC **0.40 A**
  (10, if lit) · rows **1.08 A** (27 LED) · MD/LC/MG ⚠️ (see §4.6).
- **Cluster rule (being revisited ⚠️):** original ≤ **~2 A** per hub (MP1584EN no-heatsink
  envelope). The region grouping below lands at **2.8–3.4 A/hub** — see §4.1.

## 2. Logical hub list (per wing — mirror for the second wing)

Hubs grouped by **physical region** (user's grouping), so each hub sits near its feathers:

| Hub | Feeds | Full-white ⚠️ | Region |
|-----|-------|--------------:|--------|
| H1 | P1–P5 | **3.40 A** | carpal spar, outer (wing tip) |
| H2 | P6–P10 | **3.40 A** | carpal spar, inner |
| H3 | S1–S5 | **2.80 A** | forearm spar, outer |
| H4 | S6–S11 | **3.36 A** | forearm spar, inner |
| H5 | A-B, A-T + GPC1–GPC6 | **3.20 A** | carpal root / wrist (near P10) |
| H6 | GSC1–GSC10 + MD1–MD4 + LC1–LC8 | **7.52 A** ⚠️ | shoulder / covert zone |

**Per wing: 6 hubs · both wings: 12 hubs.** Each hub = one or more bucks + fuse +
terminals (see §3/§4.1).

> ⚠️ **H6's 7.5 A is dominated by the covert groups** — see §4.6: if MD/LC (and possibly
> GSC) stay **shared strips** rather than individual chunks, H6's real draw is much lower
> (~2–3 A). H6 may also need **two buck channels** regardless.

## 3. Hub module spec (draft)

| Item | Value | Status |
|------|-------|--------|
| Input | 12 V bus (12–16.8 V, 4S Li-ion) | ✅ |
| Reverse polarity | MDD `SS34` (C8678) on 12 V in | ✅ |
| Buck | 12→5 V, **~3.5 A practical** ⚠️ (2.8–3.4 A hubs; single MP1584EN no longer covers all) | ⚠️ module vs DIY (§4.2) |
| Protection | Fuse per 5 V feed (ATO inline holder or polyfuse) | ✅ |
| Terminals | Push-in (spring-clamp), Wago 2060-class — no screws | ✅ |
| Bus splice | Wago 221 lever nuts hub-to-hub (12 V daisy-chain) | ✅ |
| Outputs | 1 fused 5 V feed per feather in the hub (or per cluster + branches — ⚠️) | open |

## 4. Open decisions

### 4.1 Hub count / current rule (affects §2 + §3)
- **Updated (100 % safe design):** with no brightness cap, the region hubs are sized by
  **full-white current** (see `feather-boards.md` §4): **9 × 2.5 A bucks/wing**
  (P 5.24 A → 3 · S 4.00 A → 2 · rest 7.76 A → 4). 18 total both wings.
- **17 injection taps/wing** (34 total) — every tap ≤ 1.36 A on a 2 A `PH2.0-2PWB`.
- The earlier ≤2 A micro-cluster list (18/wing) and the 6-region-hub list are
  superseded by the group-buck + injection-tap design in `feather-boards.md`.
- The custom 2020-LED path (0.2 W/LED) halves currents only if the medium changes —
  current design uses the off-the-shelf 40 mA/LED model.

### 4.2 DIY buck or module?
Schematic trivial, **layout is the real work** (critical loop, ground pour, inductor
choice), savings ~$1/hub — worth it if the hub becomes a custom PCB (the 2020-leds libs
pull suggests that direction). One prototype hub + bench test before committing.

### 4.3 Placement
`boards/README.md` says hubs along the wing's **top edge**; `mechanical/structural/` says
the **backplate bay** (~15 × 12 cm, electronics only). 12 region hubs on a backplate bay
fits the bay footprint; resolve before finalizing feed lengths.

### 4.4 Feather inventory — resolved ✅
**Templates README is authoritative**: S1–S11, GPC1–GPC6. Supersedes the lighting map
where they disagree (S1–S12, GPC1–GPC10).

### 4.5 Tertials ⚠️
T1–T4 appear in the lighting map but **not in the templates inventory**. Where do they
go — merged into H4 (inner forearm / elbow side), or dropped?

### 4.6 Covert rows — shared strip vs individual chunks ⚠️
H6's current depends on the lighting form:
- **Individual chunks** (like GSC1–10 at 0.40 A each): H6 ≈ **7.5 A** — needs 2× channels.
- **Shared strips** (lighting map's current form: median 27 + lesser 54 + marginal 27
  LED/wing): H6 = GSC chunks + ~2.2 A rows ≈ **~4.5–6.2 A** — still 2× channels.
- Decide the covert lighting form before locking H6's buck spec.

### 4.7 GPC lighting
GPC1–GPC6 are "optional cover layer" in the lighting map. H5 assumes them lit
(0.40 A each → +2.4 A). If unlit, H5 = **0.80 A** (alula only) and can share with H2.

## 5. References

- [Templates (feather inventory, authoritative)](../mechanical/templates/README.md) — P/S/A/GPC/GSC/MD/LC/MG/U sizes
- [Feather lighting & boards](lighting-and-boards.md) — LED map, chunk counts, rows
- [Boards](README.md) — build plan, settled COTS parts, cluster rule
- [Connector pinout](../docs/connector-pinout.md) — PWR / DATA wire legend
- [Parts list](parts-list.md) — buck, fuses, terminals, SS34
- [Wing structure plan](../mechanical/structural/wing-structure-plan.md) — spar layout, mount positions
