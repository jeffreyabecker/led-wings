# 6-LED Strip Module — High-Level Design (62 × 12 mm)

> Variant of the [shared design core](README.md). This file adds the 6-LED-specific numbers;
> everything common (block diagram, routing topology, signal contract, fab) lives in the core.
> Status legend: ✅ settled · ⚠️ to confirm at layout · ⬜ TBD.

## 1. Purpose

The chain-head/long-run module. Used **92×** per build — the leading module of every individual
feather chain (head + the long mid section):

| Chain | Modules | 6-LED count |
|-------|---------|------------:|
| P1–P10 (6+6+4) | 2× 6-LED | 2 |
| S1–S12 (6+4+4) | 1× 6-LED | 1 |
| T1–T4 (4+4+4) | — | 0 |
| GC1–GC12 (6+4) | 1× 6-LED | 1 |
| Alula A-B/A-T (6+4) | 1× 6-LED | 1 |

It maximizes the lit run per connector pair on the long flight feathers (10.4 mm pitch over a
52 mm span).

## 2. Mechanical envelope

- **Board:** 62.0 × 12.0 mm, **1-layer flex PCB**, 1 oz copper, LEDs + connectors on one side.
- **LED row:** 6× SK9822-EC20 (2020 pkg, 2.0 × 2.0 mm), **10.4 mm pitch**, centered on the strip.
- **End margins:** 5.0 mm each end — fits the JST-GH footprint short axis (4.13 mm) with
  0.87 mm clearance ✅ (long axis 8.25 mm across the width).
- **Connectors:** JST-GH 4-pin SMD (top-entry) at each end — `IN` at one end, `OUT` at the other.
- **Mounting:** **adhesive-only** (VHB/tape) to the feather substrate; no holes.

### Placement sketch (top view, not to scale)

```
<── 62.0 mm ─────────────────────────────────────────────>
┌──────┐   ●────●────●────●────●────●   ┌──────┐
│  IN  │   │    │    │    │    │    │   │ OUT  │
│ GH4  │   L1   L2   L3   L4   L5   L6  │ GH4  │
└──────┘                                └──────┘
 5.0 mm  10.4 10.4 10.4 10.4 10.4        5.0 mm
 (IN)    ◄────── 52.0 mm span ──────►    (OUT)
```

- LED centers: x = 5.0 / 15.4 / 25.8 / 36.2 / 46.6 / 57.0 mm from the IN end.
- Connectors sit at the ends; their pads point inward toward the LED row.
- `IN` on the chain-head side, `OUT` on the tail side — never reversed (silk `IN`/`OUT` marks).

## 3. Electrical design

- **Signal contract:** IN = `GND`/`SDI`/`CLK`/`+5V`, OUT = `+5V`/`CKO`/`SDO`/`GND`
  ([canonical pinout](../../docs/connector-pinout.md)).
- **Power:** +5V and GND rails run full-length, through both connectors with **crossed pin
  order** (IN pin 4 `+5V` ↔ OUT pin 1; IN pin 1 `GND` ↔ OUT pin 4). Sized for the
  inter-injection budget ≤ ~0.8 A.
- **Data:** `SDI`/`CLK` → LED1 → … → LED6 → `SDO`/`CKO`. Each SK9822 re-buffers its outputs;
  5 short hops (10.4 mm each) — no termination, no series R on the module.
- **Decoupling:** 1× 100 nF 0603 **per LED** (settled) — C1–C6, one beside each pixel.

### Netlist (per module)

| Ref | Part | Qty | Designators |
|-----|------|----:|-------------|
| LED | SK9822-EC20 (C2909059) | 6 | L1–L6 |
| Decoupling | 100 nF 0603 (C14663) | 6 | C1–C6 |
| Connector | JST-GH 4-pin SMD (C189895) | 2 | J1 (IN), J2 (OUT) |

## 4. Electrical behavior in the system

| Parameter | Value |
|-----------|-------|
| LEDs | 6 |
| Full-white draw | 0.24 A @ 5 V (6 × 40 mA) |
| @ 20 % brightness | ~0.05 A |
| Segment impact | 3× 6-LED between injections = 18 LEDs ≈ 0.72 A full white — inside the 0.8 A budget ✓ (4× 6-LED = 0.96 A ✗ — keep ≤ 3× 6-LED or ≤ 4× 4-LED per injection span) |
| Data throughput | 1 frame hop per LED, trivial at 8 MHz SPI |

> ⚠️ **Injection cadence note:** the 6-LED module is the current-heavy unit. At full white the
> inter-injection budget (≤ 0.8 A) allows **at most 3× 6-LED modules** (or 4× 4-LED) between
> injection pigtails — the plan's "4–6 modules" cadence only holds at the ≤ 20–25 % brightness
> cap. Flagged for the injection-pacing open decision in [boards/README](../README.md).

## 5. Fab & panel notes

- EasyEDA Pro → JLCPCB flex + PCBA; **1-layer flex, 1 oz / 4 mil, default coverlay**, stiffener
  under the two connectors only.
- **Schematic first**, then layout; panelized file (tab-routed) supplied by us (panel layout ⬜).
- Silk: `6LED`, `IN`/`OUT`, pin numbers, L1–L6 indices.

## 6. Open items (this variant)

- Final panel placement — 20 per mixed panel (see [core panel plan](README.md#panel-plan-mixed-%C3%975-minimum-order)).
