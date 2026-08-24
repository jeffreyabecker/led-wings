# 4-LED Strip Module — High-Level Design (42 × 12 mm)

> Variant of the [shared design core](README.md). This file adds the 4-LED-specific numbers;
> everything common (block diagram, routing topology, signal contract, fab) lives in the core.
> Status legend: ✅ settled · ⚠️ to confirm at layout · ⬜ TBD.

## 1. Purpose

The workhorse module. Used **176×** per build and appears in *every* chain type — mid/tail
sections of feather chains and all covert rows:

| Chain | Modules | 4-LED count |
|-------|---------|------------:|
| P1–P10 (6+6+4) | 1× 4-LED | 1 |
| S1–S12 (6+4+4) | 2× 4-LED | 2 |
| T1–T4 (4+4+4) | 3× 4-LED | 3 |
| GC1–GC12 (6+4) | 1× 4-LED | 1 |
| Alula A-B/A-T (6+4) | 1× 4-LED | 1 |
| Covert rows | 7 × 4-LED | 7 |

It is also the module that forms a whole short chain by itself (e.g., a single 4-module covert
row segment).

## 2. Mechanical envelope

- **Board:** 42.0 × 12.0 mm, **1-layer flex PCB**, 1 oz copper, LEDs + connectors on one side.
- **LED row:** 4× SK9822-EC20 (2020 pkg, 2.0 × 2.0 mm), **10.4 mm pitch**, centered on the strip.
- **End margins:** 5.4 mm each end — fits the JST-GH footprint short axis (4.13 mm) with
  1.27 mm clearance ✅ (long axis 8.25 mm across the width).
- **Connectors:** JST-GH 4-pin SMD (top-entry) at each end — `IN` at one end, `OUT` at the other.
- **Mounting:** **adhesive-only** (VHB/tape) to the feather substrate; no holes.

### Placement sketch (top view, not to scale)

```
<── 42.0 mm ────────────────────────────────>
┌──────┐   ●────●────●────●   ┌──────┐
│  IN  │   │    │    │    │   │ OUT  │
│ GH4  │   L1   L2   L3   L4  │ GH4  │
└──────┘                       └──────┘
 5.4 mm  10.4 10.4 10.4        5.4 mm
 (IN)    ◄── 31.2 mm span ──►  (OUT)
```

- LED centers: x = 5.4 / 15.8 / 26.2 / 36.6 mm from the IN end.
- Connectors sit at the ends; their pads point inward toward the LED row.
- `IN` on the chain-head side, `OUT` on the tail side — never reversed (silk `IN`/`OUT` marks).

## 3. Electrical design

- **Signal contract:** IN = `+5V`/`GND`/`DI`/`CI`, OUT = `+5V`/`GND`/`DO`/`CO`
  ([canonical pinout](../../docs/connector-pinout.md)).
- **Power:** +5V and GND rails run full-length, pass straight through both connectors (1:1).
  Sized for the inter-injection budget ≤ ~0.8 A.
- **Data:** `DI`/`CI` → LED1 → LED2 → LED3 → LED4 → `DO`/`CO`. Each SK9822 re-buffers its
  outputs; 3 short hops (10.4 mm each) — no termination, no series R on the module.
- **Decoupling:** 1× 100 nF 0603 **per LED** (settled) — C1–C4, one beside each pixel.

### Netlist (per module)

| Ref | Part | Qty | Designators |
|-----|------|----:|-------------|
| LED | SK9822-EC20 (C2909059) | 4 | L1–L4 |
| Decoupling | 100 nF 0603 (C14663) | 4 | C1–C4 |
| Connector | JST-GH 4-pin SMD (C189895) | 2 | J1 (IN), J2 (OUT) |

## 4. Electrical behavior in the system

| Parameter | Value |
|-----------|-------|
| LEDs | 4 |
| Full-white draw | 0.16 A @ 5 V (4 × 40 mA) |
| @ 20 % brightness | ~0.03 A |
| Segment impact | 4× 4-LED between injections = 16 LEDs ≈ 0.64 A full white — inside the 0.8 A budget ✓ |
| Data throughput | 1 frame hop per LED, trivial at 8 MHz SPI |

## 5. Fab & panel notes

- EasyEDA Pro → JLCPCB flex + PCBA; **1-layer flex, 1 oz / 4 mil, default coverlay**, stiffener
  under the two connectors only.
- **Schematic first**, then layout; panelized file (tab-routed) supplied by us (panel layout ⬜).
- Silk: `4LED`, `IN`/`OUT`, pin numbers, L1–L4 indices.

## 6. Open items (this variant)

- Panel placement/quantity math once the full module count (~176) is frozen.
