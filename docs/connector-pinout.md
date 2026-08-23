# Connector Pinout — Logical Contract

> The shared signal/pin interface for all boards in this project (SK9822 addressable LED
> chain, JST-PH style). Physical parts — part numbers, header colors, orientation — live in
> each board's own docs.

## Signals

| Signal | Meaning |
|--------|---------|
| GND | Power ground + signal return |
| +5V (VCC) | LED power |
| DATA | Serial data, regenerated per LED |
| CLK | Serial clock, regenerated per LED |

## Wire colors

| Signal | Wire color |
|--------|------------|
| +5V (VCC) | Red |
| GND | Black |
| DATA | Yellow |
| CLK | Green |

## Pin maps (canonical)

**Data port — 4-pin**

| Pin | Signal |
|-----|--------|
| 1 | GND |
| 2 | DATA |
| 3 | CLK |
| 4 | +5V (VCC) |

**Power port — 2-pin**

| Pin | Signal |
|-----|--------|
| 1 | GND |
| 2 | +5V (VCC) |

## Port roles

| Role | Direction | Port | Notes |
|------|-----------|------|-------|
| IN | receives DATA+CLK (`DI`/`CI`) | 4-pin | controller or previous board's OUT |
| OUT | sends DATA+CLK (`DO`/`CO`) | 4-pin | to next board's IN |
| PWR | power injection | 2-pin | ≤2 A each; no data; reverse-polarity protection required |

Convention: an input-facing port is white, an output-facing port a distinct (non-white) color.

## Cabling rules

- **OUT → IN** is straight 1:1 (pin 1↔1 … pin 4↔4) — off-the-shelf JST-PH 4-pin female-to-female.
- **PWR** uses a 2-pin red/black pigtail (verify red = +5V).
- **Wire gauge:** JST-PH contacts accept 30–24 AWG; use 24 AWG near 2 A.
- **2 A limit** per JST-PH circuit — add more PWR points rather than bigger connectors.

## Rationale

- Power on the outer pins, signals inner — a reversed cable gives reverse polarity (caught by
  protection) and a harmless DATA↔CLK swap.
- Off-the-shelf cable compatibility is prioritized over keying; direction is marked by silkscreen.
- The 2-pin PWR port is physically incompatible with the 4-pin data ports.
