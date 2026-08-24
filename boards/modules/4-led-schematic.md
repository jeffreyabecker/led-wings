# 4-LED Module — Schematic Definition

> Source of truth for the EasyEDA Pro schematic. Everything here maps 1:1 to the library
> symbols (LCSC codes) so it can be entered directly, no derivation needed.
> Pairs with [4-led-module.md](4-led-module.md) (board spec) and the
> [shared design core](README.md).

## Components

| Ref | Part | LCSC | Footprint |
|-----|------|------|-----------|
| J1 | JST-GH 4-pin SMD, top-entry (`SM04B-GHS-TB`) — **IN** | C189895 | 8.25 × 4.13 mm |
| J2 | JST-GH 4-pin SMD, top-entry (`SM04B-GHS-TB`) — **OUT** | C189895 | 8.25 × 4.13 mm |
| L1–L4 | SK9822-EC20 (2020, 2.0 × 2.0 mm) | C2909059 | LED-SMD_6P-… |
| C1–C4 | 100 nF 0603 X7R (decoupling, 1/LED) | C14663 | 0603 |

## Pin maps

**SK9822-EC20 symbol (EasyEDA pin order — verified from library data):**

| Pin | Name | Function |
|-----|------|----------|
| 1 | SDO | Data out |
| 2 | GND | Ground |
| 3 | SDI | Data in |
| 4 | CKI | Clock in |
| 5 | VDD | +5 V |
| 6 | CKO | Clock out |

> The EasyEDA symbol labels pin 4 **`CKL`**; the datasheet calls it **`CKI`**. Same pin.

**JST-GH connectors (canonical, see [connector-pinout](../../docs/connector-pinout.md)):**

| Pin | J1 (IN) | J2 (OUT) |
|-----|---------|----------|
| 1 | +5V | +5V |
| 2 | GND | GND |
| 3 | DI | DO |
| 4 | CI | CO |

## Nets

```
+5V   J1.1  J2.1  L1.5  L2.5  L3.5  L4.5  C1.1  C2.1  C3.1  C4.1
GND   J1.2  J2.2  L1.2  L2.2  L3.2  L4.2  C1.2  C2.2  C3.2  C4.2

DI    J1.3 ─ L1.3          (data in → LED1)
CI    J1.4 ─ L1.4          (clock in → LED1)

D1    L1.1 ─ L2.3          (SDO LED1 → SDI LED2)
D2    L2.1 ─ L3.3
D3    L3.1 ─ L4.3
DO    L4.1 ─ J2.3          (SDO LED4 → data out)

CLK1  L1.6 ─ L2.4          (CKO LED1 → CKI LED2)
CLK2  L2.6 ─ L3.4
CLK3  L3.6 ─ L4.4
CO    L4.6 ─ J2.4          (CKO LED4 → clock out)
```

## Connections to draw

| Net | From | To |
|-----|------|----|
| +5V | J1.1, J2.1, L1.5, L2.5, L3.5, L4.5, C1.1, C2.1, C3.1, C4.1 | (single rail) |
| GND | J1.2, J2.2, L1.2, L2.2, L3.2, L4.2, C1.2, C2.2, C3.2, C4.2 | (single rail) |
| DI | J1.3 | L1.3 |
| CI | J1.4 | L1.4 |
| D1 | L1.1 | L2.3 |
| D2 | L2.1 | L3.3 |
| D3 | L3.1 | L4.3 |
| DO | L4.1 | J2.3 |
| CLK1 | L1.6 | L2.4 |
| CLK2 | L2.6 | L3.4 |
| CLK3 | L3.6 | L4.4 |
| CO | L4.6 | J2.4 |

- **Decoupling:** C1 sits at L1, C2 at L2, C3 at L3, C4 at L4 — each cap's pin 1 on `+5V`,
  pin 2 on `GND`.
- **Signal flow:** DI/CI enter L1; each LED re-buffers and passes DO/CO to the next; L4 drives
  the OUT connector. Power and ground are shared rails across all four LEDs + both connectors.

## Design rules carried into layout

- LED pitch 10.4 mm, 4 LEDs centered on a 42 × 12 mm strip.
- Connectors at the ends: 8.25 mm axis across width, 4.13 mm axis into the 5.4 mm end margin.
- +5V / GND rails fill available width (1-layer flex, 1 oz / 4 mil).
