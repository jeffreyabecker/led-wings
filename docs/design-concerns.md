# LED Lighting PCB — Design Concerns

> Project: Addressable LED lighting PCBs
> LED part: [SK9822-EC20](https://www.lcsc.com/product-detail/C2909059.html) (LCSC `C2909059`)
> Connectors: JST-PH style (input / output / power injection)

## Part summary

- **SK9822-EC20** — 5V addressable RGB LED with built-in driver IC.
- **Package:** 2020 SMD (2.0 × 2.0 mm), ~0.2 W per device.
- **Protocol:** 4-wire — `VCC`, `GND`, `DATA`, `CLK` (APA102-compatible). Separate clock and
  data lines, each regenerated on the device's `DO`/`CO` outputs.
- **Current draw:** ~40 mA per LED at full-brightness white (R+G+B all on).

References:
- [LCSC product page](https://www.lcsc.com/product-detail/C2909059.html)
- [SK9822-EC20 datasheet (Normand LED)](http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf)
- [SK9822-EC20 overview](https://www.normandled.com/Product/view/id/840.html)

---

## 1. Power delivery — the #1 problem (5V is unforgiving)

- Each LED draws ~0.2 W at 5V → **~40 mA at full-brightness white**. A 100-LED string is
  **4 A** — cannot be pushed through one thin trace or one connector pin.
- **Voltage drop:** at 5 V there is almost no headroom. Even 0.5 V drop = 10%, which shows up
  as pink/wrong colors (blue channel dies first) and flicker at the far end of the string.
  This is why power injection is planned — but the injection interval must be **calculated**,
  not guessed.
- **Copper weight / trace width:** a 1 oz, 10 mm-wide trace drops ~60 mV per meter per amp.
  At 4 A over a strip this adds up fast. Use 2 oz copper or wide pours; treat the power path
  as a bus, not a signal trace.
- **Ground is a bus too.** Return current is the same 4 A. Starving ground shifts the
  clock/data reference.

## 2. JST-PH connector limits (the critical constraint)

- **JST-PH is rated ~2 A per circuit** (typically mated with 24–28 AWG wire). One VCC pin +
  one GND pin = **2 A max through the connector** — roughly 50 SK9822 LEDs at full white, less
  with margin.
- For larger strings: **add more 2-pin injection points** (each ≤2 A) rather than a bigger
  connector.
- **Pinout discipline:** pick one canonical pinout and use it everywhere. A mismatched
  daisy-chain connector is the classic way to blow a whole string.
- **Polarity/reversal protection:** JST-PH is not keyed against swapping power polarity. Add
  series Schottky or P-MOSFET reverse-polarity protection and/or a fuse, plus unambiguous
  silkscreen marking.

## 3. Signal integrity (data + clock)

- Separate `CLK` + `DATA`, regenerated on each device's `DO`/`CO` outputs → far more robust
  than 1-wire WS2812. Still:
  - **Series resistor (33–100 Ω)** on DATA and CLK — lives on the controller board (external),
    damping the controller→first-board cable.
  - Keep clock and data paired and reasonably matched; avoid large loop areas.
  - Expect **5 V logic** on data/clock. Level shifting from the controller is handled
    **externally** — not a board-level concern.
- Long runs: `CLK` is the double-clock risk. A pull-down/termination on the last board's `CO`
  can help on very long daisy chains.

## 4. Decoupling / bypass caps

- **Bulk cap (100–470 µF)** at each power-injection point to absorb inrush/transients.
- **100 nF ceramic near each LED or every few LEDs** (0.1 µF per device ideal; one per 1–4
  LEDs in practice).
- Caps also suppress constant-current driver switching noise that couples back onto data lines.

## 5. Thermal

- 0.2 W/device is small, but a dense board at full white is a real heat load; the 2020 package
  has little thermal mass.
- Use **copper pours** on VCC/GND as heat spreaders; avoid tiny thermal reliefs that choke heat.
- For sustained full-white, derate current or add spacing/airflow — lifetime and color stability
  drop fast with junction temperature.

## 6. Layout & manufacturability

- The 2020 package has **fine pads and a specific center/thermal pad** — follow the datasheet
  footprint exactly. Pick-and-place + reflow, not hand-solder friendly at density.
- **Mark data direction on silkscreen** (`DI` vs `DO`) — SK9822 is directional; every board in
  the chain must be oriented consistently.
- Keep high-current power path separate from signal path; return `DO`/`CO` cleanly to the next
  connector without crossing the power bus.

## 7. Protections & robustness

- **Fuse** (or polyfuse) — on the controller/distribution board (one per strand).
- **ESD/TVS** — on the controller board; segments rely on the SK9822's internal ESD protection.
- Reverse-polarity protection as noted in §2 (stays per board).

---

## TL;DR

The two things most likely to kill the project:

1. **Current capacity vs. the 2 A JST-PH limit.**
2. **5 V voltage drop over the string.**

Followed by signal integrity on `CLK`/`DATA` and bypassing. Everything else is refinement.

## Open items / next steps

- [ ] Calculate LEDs per injection point and per PH connector at target brightness (trace width,
      copper weight).
- [x] Define canonical connector pinout — see [connector-pinout.md](connector-pinout.md).
- [x] Input/output both 4-pin for off-the-shelf cables; direction marked by silkscreen — see [connector-pinout.md](connector-pinout.md).
- [x] Source connector part numbers (Boomele/JST-PH on LCSC) — see [selected-parts.md](selected-parts.md).
- [ ] Schematic symbol/footprint spec (connectors + SK9822-EC20).
