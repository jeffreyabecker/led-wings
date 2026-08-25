# Pigtail Crimping — JST-PNI Build Guide

> Every wire termination in this build is a **2-pin JST-PNI** (2.0 mm pitch, wire-to-wire)
> crimped by hand — **both plug and receptacle crimp, so there are no soldered headers
> anywhere**. Chunks unplug for service; dead chunks swap in seconds. The signal/color legend
> is [connector-pinout.md](connector-pinout.md); this file is the *how to crimp* guide.

## Why JST-PNI

- **Wire-to-wire** — both genders take crimp terminals (unlike PH/XH where the male side is a
  solder header). Every chunk end is a receptacle; every jumper/feed is a plug.
- **Compact (2.0 mm)** vs Molex Micro-Fit 3.0's 3.0 mm bulk — better for a wearable.
- **~2–3 A class** (confirm exact rating in the
  [ePNI-WW datasheet](http://www.jst-india.com/downloads/series/ePNI-WW_(21-08-25).pdf)) —
  the wiring is organized so no single run exceeds that.
- **All pigtails are hand-made** — no pre-made cables; every link is crimped in the build.

## The scheme

Each chunk gets **three 2-pin receptacles** (soldered stub wires to the strip pads, then
crimped):

| Connector | Pairs | Chunk end | Matches |
|---|---|---|---|
| Power-in | +5V (red) / GND (black) | **receptacle** `PNIRR-02VF` | hub power feed (plug + bare) |
| Data-in | DI (yellow) / CI (green) | **receptacle** `PNIRR-02VF` | previous chunk's data-out, or controller feed |
| Data-out | DO (yellow) / CO (green) | **receptacle** `PNIRR-02VF` | data jumper (plug–plug) → next chunk |

- **Data jumpers** chunk→chunk: 2-pin **plug–plug** (`PNIRP-02V-S` both ends), crimped.
- **Hub power feeds:** plug at the chunk end; bare/tinned wire into the perfboard screw
  terminal.
- **Controller chain-head feeds** (2 chains): plug into the first chunk's data-in; bare at the
  level-shifter/controller.

## Parts

| Part | JST number | Notes |
|---|---|---|
| Receptacle housing, 2-pin | `PNIRR-02VF` | every chunk end (power-in / data-in / data-out) |
| Plug housing, 2-pin | `PNIRP-02V-S` | every jumper / feed end |
| Socket contact | `SPNI-001T-P0.5` | crimp into receptacles |
| Pin contact | `BPNI-001T-P0.5` | crimp into plugs |
| Crimp tool | JST PN-family tool, or ratchet + PN dies | **SN-28B does NOT fit PNI contacts** |

## Crimp procedure

1. Strip ~2 mm; slide the wire into the contact — strands fully inside the wire barrel,
   insulation in the insulation barrel.
2. Seat the contact in the PN-family die position (the notch sized for the contact's wire
   barrel — not the pin barrel).
3. Squeeze firmly — the wire barrel closes in a "B" over the strands.
4. **Pull test:** the wire must not pull out; insulation must not be trapped by the wire
   barrel.
5. Insert into the housing until the latch clicks; tug to confirm.
6. Heat-shrink each finished joint (2:1, ~3 mm).

## Wire gauge vs rating

- **Power: 20–22 AWG** silicone (within the PNI contact range, which covers 22 AWG).
- **Data: 24 AWG** silicone.
- **Current:** plan the wiring so no single run exceeds **~2–3 A** (PNI class rating).
- **12 V hub bus** (perfboard screw terminals — no connector): 14–16 AWG.

## Counts + shopping list (88 terminations: 80 individual feathers + 8 covert rows)

Per termination: 3 receptacles (chunk) + jumpers/feeds as plugs → ~264 receptacles,
~260 plugs, ~1050 contacts total. Buy with ~20 % margin.

| Item | Part | Qty (w/ margin) | Typical source |
|---|---|---|---|
| Receptacles | `PNIRR-02VF` | ~320 | DigiKey / Mouser / AliExpress |
| Plugs | `PNIRP-02V-S` | ~320 | same |
| Contacts | socket `SPNI-001T-P0.5` + pin `BPNI-001T-P0.5` | ~650 + ~650 | same |
| Crimp tool | JST PN tool / ratchet + PN dies | 1 | TBD |
| Wire | 20–22 AWG red/black + 24 AWG yellow/green | ~15 m each | spool kits |
| Heat shrink | 2:1, ~3 mm | 1 pack | any |
| Strain relief | epoxy/glue over the soldered pad sets | — | any |

## Bench test

Crimp quality only shows up downstream: a bad joint darkens everything after it. Bench-test
each chunk at full brightness before mounting (per [boards/README.md](../boards/README.md)).
