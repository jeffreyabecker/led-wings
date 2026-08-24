# Boards — Core Ideas & Settled Parts

> The consolidated electrical-board document: what each board role is **for** (core idea),
> what is **locked**, and which **part numbers are settled**. The canonical split power/data
> pinout lives in [../docs/connector-pinout.md](../docs/connector-pinout.md).
>
> Status: ✅ selected · ⚠️ to confirm · ⬜ TBD. All boards are `ideation` — nothing is `design`
> or `ready` yet.

| Board | Status | Core idea |
|-------|--------|-----------|
| LED segment (feather) | ideation | SK9822 flex ribbon, one per lit feather — data daisy-chain + power in |
| Shared strip (covert strip) | ideation | Chains of short 4-LED boards under the dense covert rows |
| Controller | ideation | Single central unit for both wings — COTS Pixelblaze V3 + level shifters, N `DATA`+`CLK` chain outputs |
| Power-hub | ideation | 12 V→5 V buck + fused 5 V fan-out to a feather cluster |

## System (locked)

- **Split power/data.** Data daisy-chains feather→feather from a **single central controller
  driving both wings**; power fans out from local power-hubs on a 12 V bus. 5 V exists only on
  the short hub→feather tails; the 12 V bus is drop-tolerant (see power-hub "why 12 V" below).
- **Routing:** data chains run along the wing's **top edge** (the feather bases — the only
  cable entrance); power-hubs sit along the same edge feeding short 5 V runs into clusters.
- **Controller (settled ✅):** Pixelblaze V3 Standard (ElectroMage) — ESP32, 8 data
  channels, 3.3 V logic → one level shifter per channel, N ≤ 8 chains.
- **Pixel:** SK9822-EC20, 5 V, ~40 mA/LED full white. Working budget ~1270 LEDs / ~136 boards
  both wings (see [feather lighting](../mechanical/feather/lighting-and-boards.md)).
- **Toolchain:** KiCad 10 + `pcbnew` Python scripting; feather geometry is parameterized.
- ~1270 LEDs of cumulative data-regen delay → several chains with a conservative SPI clock.

## LED segment (feather) — one per lit feather

- **Core idea:** a passive 10 mm flex ribbon of SK9822-EC20 LEDs. Each LED regenerates
  DATA+CLK, so data daisy-chains: `DI`/`CI` in → first LED … last LED's `DO`/`CO` →
  `DATA OUT` → next feather. Power comes in on its own connector from a nearby power-hub.
  **No buck, no fuse — LEDs + caps + reverse-polarity only.**
- **Geometry (parameterized):** fixed 10 mm width; "top" = 0 mm (start of length, the only
  cable entrance); per board: overall length (mm) + bend points `(offset, deg)`; bends
  realized as arcs (not sharp corners); LEDs at offsets from top to chip center.
- **Connectors (SMD side-entry, flex-compatible):**
  - `J_PWR` — 2-pin power in, JST-PH 2.0 mm — `GND` / `+5V` (fed from a power-hub)
  - `J_IN` — 2-pin data in, JST-GH 1.25 mm — `DI` / `CI`
  - `J_OUT` — 2-pin data out, JST-GH 1.25 mm — `DO` / `CO`
  - Pin maps: [connector pinout](../docs/connector-pinout.md). Last feather's `J_OUT` is unused.
- **Limits:** 2 A per JST-PH circuit · 1 A per JST-GH circuit. One power feed per feather; the
  run carries only its own board's current.
- **Deferred to other boards:** series R + ESD/TVS + level shifter → controller; fuse + buck →
  power-hub.

## Shared strip (covert strip)

- **Core idea:** dense covert rows (median / lesser / marginal) are **not** one long ribbon —
  each row is a **chain of short boards**, so the row keeps one common LED orientation for
  animations.
- Working: 40 × 10 mm, 4 × SK9822-EC20 at 10 mm pitch (30 × 10 mm / 3-LED variant for tighter
  rows).
- **Connectors: 4-pin, power + data combined** — `+5V`/`GND`/`DI`/`CI` in,
  `+5V`/`GND`/`DO`/`CO` out (unlike the feather's separate `J_PWR` + `J_IN`/`J_OUT`). Chained
  tip-to-tail: `DI` in one end → LEDs in order → `DO` out the far end — the chain behaves as
  one logical strip, and power rides the chain (fed at the chain head from a power-hub).
- ~56 strip boards / ~224 LEDs both wings; 4 LEDs ≈ 0.16 A full-white per board.

## Controller — one central unit, drives both wings

- **Core idea:** the wing's brain — drives the data chains only. It does **not** distribute
  power (power-hub's job). Form: a carrier board hosting a COTS Pixelblaze V3 Standard plus
  the per-channel conditioning below.
- **Controller (settled ✅):** **Pixelblaze V3 Standard** (ElectroMage) — ESP32, 8 data
  channels, 3.3 V logic, so each channel needs its own level shifter; N ≤ 8 chains.
- **Holds:** level shifter (3.3 V → 5 V) per output; series R (33–100 Ω) per output; ESD/TVS
  per output; N × 2-pin JST-GH data outputs (`DATA`+`CLK`), each into the first feather of a
  chain.
- **Open:** N (chain count); chain timing / clock budget.

## Power-hub — 12 V in → 5 V out

- **Core idea:** local power-distribution node. One buck per hub sized for its cluster; fans
  out `+5V`/`GND` to N feathers over short 2-pin runs (matching the feather `J_PWR`); 12 V bus
  in from the battery/wall source. **No data.**
- **Holds:** 12 V→5 V buck + inductor; fuse per 5 V output; reverse-polarity + ESD/TVS on the
  12 V input; bulk + decoupling caps.
- **Load model:** ~0.4 A/feather full white, ~0.08 A @ 20 %.
- **Why 12 V (settled):** a 5 V bus can't scale — on a 2 m / 12 AWG reference bus, full-white
  drops ~33 % (color shift; blue dies first) vs ~6 % on 12 V (~1 % @ 20 % brightness). One
  MP1584-class 3 A buck covers a hub's cluster (~2–4 A full white).
- **Open:** buck part (MP2315 / MP1584-class vs larger); feathers per hub; fuse ratings; 12 V
  input connector; 12 V bus topology (daisy-chain hub-to-hub vs star); placement along the
  wing's top edge.

## Settled part numbers

| Ref | Role | Part | Mfr | MPN | Source | Qty | Status |
|-----|------|------|-----|-----|--------|-----|--------|
| `U1` | Controller (COTS) — drives both wings | Pixelblaze V3 Standard — ESP32, 8 data channels, 3.3 V logic | ElectroMage | Pixelblaze V3 Standard | [Tindie](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) | 1 | ✅ |
| `LED*` | Pixel — SK9822 RGB, 5 V, 2020 | — | OPSCO | `SK9822-EC20` | [C2909059](https://www.lcsc.com/product-detail/C2909059.html) | per LED map | ✅ |
| `C*` | Bulk — 47 µF, 1206 X5R 10V | — | Samsung | `CL31A476MPHNNNE` | [C96123](https://www.lcsc.com/product-detail/C96123.html) | 1 / board | ✅ |
| `C*` | Decoupling — 100 nF, 0603 X7R 50V | — | Yageo | `CC0603KRX7R9BB104` | [C14663](https://www.lcsc.com/product-detail/C14663.html) | 1 per LED (or 1–4) | ✅ |
| `D*` | Reverse-polarity — 3A, 40V, SMA | — | MDD | `SS34` | [C8678](https://www.lcsc.com/product-detail/C8678.html) | 1 / board | ✅ |
| `J_PWR` | Power in (GND/+5V), 2-pin JST-PH 2.0 mm | SMD side-entry | JST | `S2B-PH-SM4-TB` | [C295747](https://www.lcsc.com/product-detail/C295747.html) | 1 / board | ⚠️ |
| `J_IN`/`J_OUT` | Data in/out (DI/CI · DO/CO), 2-pin JST-GH 1.25 mm | SMD side-entry | JST | `SM02B-GHS-TB(LF)(SN)` | [C189893](https://www.lcsc.com/product-detail/C189893.html) | 2 / board | ⚠️ |
| `J*` | Power-hub 5 V output — matches feather `J_PWR` | — | JST | `S2B-PH-SM4-TB` | [C295747](https://www.lcsc.com/product-detail/C295747.html) | N / hub | ⚠️ |

- ✅ = part number settled · ⚠️ = candidate, confirm before freezing the connector contract.
- **Not settled (no part number yet):** controller level shifter + series R + ESD/TVS;
  strip-board 4-pin power+data connectors; power-hub buck (MP2315/MP1584-class candidate) +
  inductor + fuse + TVS + 12 V input connector; all cables (off-the-shelf, source TBD).
- **Footprints:** SK9822-EC20 — [JLCPCB EasyEDA part (OPSCO / C2909059)](https://jlcpcb.com/partdetail/OPSCOOptoelectronics-SK9822EC20/C2909059);
  JST connectors — confirm in the `Connector_JST` lib or create.

## Open decisions (compact)

- **Feather scripting/geometry:** bend sign convention + radius (flex min bend); LED lateral
  position; connector + DI orientation; schematic approach (one parameterized schematic vs
  PCB-only generation); decoupling density; 5 V trace width; max LEDs per board.
- **Feather mfg/test:** stiffener under SMD connectors; coverlay vs soldermask; panelization +
  fiducials; test points; silkscreen set; SK9822 `.kicad_sym`/`.kicad_mod` + JST footprints.
- **Controller:** N chains (≤ 8 channels); level-shifter part; series-R value; ESD/TVS part.
- **Power-hub:** buck part + rating; feathers per hub; fuse rating; 12 V input connector +
  protection; bus topology (hub-to-hub vs star); bus conductor gauge; placement.
- **System:** chain segmentation (≤ 8 chains on one Pixelblaze); SPI clock budget; failure
  handling (per-feather `DI`→`DO` bypass vs a segment going dark on one dead feather);
  full-white policy (brief ceiling vs sustained); strip-board size (40 mm/4-LED vs
  30 mm/3-LED); strip 4-pin connector part + pin map.

## References

- [Connector pinout](../docs/connector-pinout.md) — canonical PWR / DATA-IN / DATA-OUT contract
- [Battery](../investigations/battery/) — 12 V source sizing
- [Feather lighting](../mechanical/feather/lighting-and-boards.md) — LED map + board counts
- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [Pixelblaze V3 Standard (ElectroMage / Tindie)](https://www.tindie.com/products/electromage/pixelblaze-v3-standard-wifi-led-controller/) — settled controller (✅)
