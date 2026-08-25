# Pigtail Crimping — JST-PH Build Guide

> Every wire termination in this build is a **2-pin JST-PH** (2.0 mm pitch, 2 A/circuit)
> crimped by hand. Chunks unplug for service; dead chunks swap in seconds. The signal/color
> legend is [connector-pinout.md](connector-pinout.md); this file is the *how to crimp* guide.

## Why JST-PH

- **2 A/circuit rating** matches the plan's 2 A power-pigtail budget exactly; real max is
  ~0.68 A full-white per 17-LED chunk (~0.15 A @ 20 % brightness) — comfortable margin.
- **Small + light** (2.0 mm pitch) — 88 terminations × 3 connectors on a wearable.
- **Contact range 24–28 AWG** covers power (24 AWG) and data (26–28 AWG) with **one contact
  part** for the whole build.
- Cheap and ubiquitous; crimped by the common **SN-28B** tool.
- Alternatives: JST-XH (2.54 mm, 3 A — bulkier), JST-GH (1.25 mm, 1 A — undersized for power).

## The scheme (why headers aren't on the strip)

PH is a **wire-to-board** system: the male side is always a header, and the 2.0 mm pitch does
**not** match SK9822 strip pads (~2.54 mm). So the strip end keeps **soldered stub leads**
(6 wires per chunk, strain-relieved — unchanged from the plan), and every *connector* is a
crimped PH. The single male plug lives on each chunk's **data-out**, which makes every jumper
a pure female–female crimp.

| Connector | Pairs | Chunk end | Matches |
|---|---|---|---|
| Power-in | +5V (red) / GND (black) | **female** `PHR-2` | hub power feed (female + bare) |
| Data-in | DI (yellow) / CI (green) | **female** `PHR-2` | previous chunk's data-out plug, or controller feed |
| Data-out | DO (orange) / CO (blue) | **male plug** (PH header soldered to lead) | female–female jumper → next chunk's data-in |

- **Data jumpers** chunk→chunk: 2-pin **female–female**, crimped both ends.
- **Hub power feeds:** female `PHR-2` at the chunk end; bare/tinned wire into the perfboard
  screw terminal.
- **Controller chain-head feeds** (2 chains): male plug at the chunk end (PH header soldered
  to the lead), bare/tinned at the level-shifter/controller.

## Parts

| Part | JST number | Notes |
|---|---|---|
| Socket contact (crimp) | `SPH-002T-P0.5` | **24–28 AWG** — one part for power + data |
| Housing, 2-pin female | `PHR-2` | the crimped side of every link |
| Header, 2-pin | `B2B-PH-K-S` (top entry) · `S2B-PH-K-S` (right angle) | soldered to the data-out lead to make the male plug |
| Crimp tool | IWISS/iCrimp **SN-28B** | also does XH/VH/Dupont; upgrade: ratcheting crimper (HT-225D class) for consistency |

## Crimp procedure (SN-28B)

1. Strip ~2 mm of insulation; slide the wire into the contact — strands fully inside the wire
   barrel, insulation inside the insulation barrel.
2. Seat the contact in the SN-28B **PH** die position (the notch sized for the contact's wire
   barrel — not the pin barrel).
3. Squeeze firmly — the wire barrel closes in a "B" over the strands.
4. **Pull test:** the wire must not pull out; the insulation must not be trapped by the wire
   barrel.
5. Insert into the `PHR-2` housing until the latch clicks; tug to confirm.
6. Heat-shrink each finished connector joint (2:1, ~3 mm).

## Wire gauge vs contact

- **Power pigtails: 24 AWG** silicone (top of the `SPH-002T-P0.5` range; 24 AWG carries the
  2 A budget with margin at these short runs).
- **Data: 26–28 AWG** silicone.
- **12 V hub bus** (perfboard screw terminals — no connector): 14–16 AWG.

## Counts + shopping list (88 terminations: 80 individual feathers + 8 covert rows)

Per termination: power-in + data-in (2 female) + data-out (1 male plug) → ~220 female
connectors / ~90 male plugs, ~440 crimped contacts, ~90 data jumpers + ~90 hub feeds.
Buy with ~25 % margin.

| Item | Part | Qty (w/ margin) | Typical source |
|---|---|---|---|
| Contacts | `SPH-002T-P0.5` | ~550 | DigiKey / Mouser / AliExpress bulk |
| Housings | `PHR-2` | ~280 | same |
| Headers | `B2B-PH-K-S` (2-pin) | ~120 | same |
| Kit option | PH2.0 connector kit (housings + contacts) | 1–2 | Amazon/eBay (~$15–25) |
| Crimp tool | SN-28B | 1 | Amazon (~$20–30) |
| Wire | 24 AWG silicone red + black (power); 26–28 AWG yellow/green/orange/blue (data) | ~15 m each color | Amazon spool kits |
| Heat shrink | 2:1, ~3 mm | 1 pack | any |
| Strain relief | epoxy/glue over the soldered pad sets | — | any |

## Bench test

Crimp quality only shows up downstream: a bad joint darkens everything after it. Bench-test
each chunk at full brightness before mounting (per [boards/README.md](../boards/README.md)).
