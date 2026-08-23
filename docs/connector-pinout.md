# Connector Pinout — SK9822 LED Boards

> Scope: JST-PH style connectors for **input**, **output**, and **power injection** on
> addressable LED PCBs (SK9822-EC20, LCSC `C2909059`).

## Design principles

1. **One canonical pinout, used everywhere.** Input and output share the same pin numbering on
   pins 1–4. A straight 1:1 cable daisy-chains OUT → IN correctly.
2. **Off-the-shelf cable compatibility first.** Input and output are both **4-pin** so they use
   ubiquitous ready-made JST-PH 4-pin cables. Direction is marked by silkscreen (`IN` / `OUT`),
   not by connector keying — a deliberate tradeoff in favor of buying cables off the shelf.
3. **Power on the outer pins, signals on the inner pins.** This is defensive: if a cable is
   wired reversed, the result is reverse polarity on power (caught by the reverse-polarity
   protection) and a harmless DATA↔CLK swap — not a blown part.
4. **JST-PH = 2 A per circuit.** Power is a 2-pin connector (≤2 A per injection point); add more injection points rather than bigger connectors.
5. **Unambiguous silkscreen.** Pin 1 marker, signal names, and `IN` / `OUT` data direction on
   every board.
6. **SMD, side-entry (parallel to board).** All headers are surface-mount with the cable
   entering parallel to the board — required for flex PCB (no through-hole parts).

## Wire color standard

| Signal | Wire color |
|--------|------------|
| +5V (VCC) | Red |
| GND | Black |
| DATA | Yellow |
| CLK | Green |

## Header color coding (board side)

| Port | Header color |
|------|--------------|
| `J_IN` (input) | White / natural |
| `J_OUT` (output) | Distinct (≠ white) |
| `J_PWR` (power injection) | 2-pin, white/natural — distinct by pin count |

## Input connector — `J_IN` (4-pin JST-PH, white)

Carries power + data + clock **into** the board. On the first board this is the controller feed;
on downstream boards it is the previous board's output.

| Pin | Signal | Wire | Notes |
|-----|--------|------|-------|
| 1 | GND | Black | Power ground + signal return |
| 2 | DATA (`DI`) | Yellow | Data in from controller / previous board |
| 3 | CLK (`CI`) | Green | Clock in |
| 4 | +5V (VCC) | Red | Power in |

## Output connector — `J_OUT` (4-pin JST-PH, distinct color)

Carries power pass-through + regenerated data/clock **out** of the board, to the next board's
input. Identical pin order to `J_IN`, so a straight 1:1 off-the-shelf cable chains them.

| Pin | Signal | Wire | Notes |
|-----|--------|------|-------|
| 1 | GND | Black | Power ground + signal return |
| 2 | DATA (`DO`) | Yellow | Data out to next board |
| 3 | CLK (`CO`) | Green | Clock out to next board |
| 4 | +5V (VCC) | Red | Power pass-through |

## Power injection connector — `J_PWR` (2-pin JST-PH)

Power only — **no data**, always 2-pin. Being 2-pin makes it physically incompatible with the
4-pin data connectors, and the JST-PH key means the cable fits only one way.

| Pin | Signal | Wire |
|-----|--------|------|
| 1 | GND | Black |
| 2 | +5V (VCC) | Red |

**Foolproofing (non-negotiable):**
- Keyed 2-pin vs 4-pin — a data cable cannot reach power, and vice versa.
- Reverse-polarity protection (Schottky or P-MOSFET) is **required** on board.
- Silkscreen: pin-1 marker plus `GND` / `+5V`.

> Each injection point is ≤2 A. Need more? Add more injection points — don't grow the connector.

## Summary table

| Connector | Pins | Pin 1 | Pin 2 | Pin 3 | Pin 4 | Max current |
|-----------|------|-------|-------|-------|-------|-------------|
| `J_IN` (input, white) | 4 | GND | DATA (DI) | CLK (CI) | +5V | 2 A |
| `J_OUT` (output, distinct) | 4 | GND | DATA (DO) | CLK (CO) | +5V | 2 A |
| `J_PWR` (injection, 2-pin white) | 2 | GND | +5V | — | — | 2 A |

## Cabling rules

- **OUT → IN** daisy-chain cables are **straight 1:1** (pin 1↔1 … pin 4↔4) — a standard
  off-the-shelf JST-PH 4-pin female-to-female cable. No crossover.
- **Direction is marked on the silkscreen** (`IN` / `OUT`). Input and output share the same
  pinout by design, so a cable physically fits either port — be careful to feed data into `IN`
  and take the next segment from `OUT`.
- **Wire gauge:** JST-PH contacts accept **30–24 AWG**. Use **24 AWG** for any pin expected to
  carry near its 2 A rating; keep power runs as short as practical.
- **Power injection (`J_PWR`, 2-pin):** use a 2-pin red/black pigtail (verify red = +5V).
  Never feed power backward through `J_OUT` beyond the 2 A input rating.
