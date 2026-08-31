#!/usr/bin/env python3
"""Generate KiCad schematics for the feather-strip boards (2020-LED path).

Design (from boards/feather-boards.md):
  - One 5 mm-wide strip cell: N x SK9822-EC20 (C2909059) daisy-chained.
  - Data in/out: ZH1.5-4P (C145992), pins 1-4 = +5V/GND/DI/CI (in) and +5V/GND/DO/CO (out)
    per docs/connector-pinout.md convention.
  - Power tap: PH2.0-2PWB (C47647), pins 1-2 = +5V/GND (pins 3-4 are mechanical anchors,
    left unconnected).
  - LED pins (C2909059): 1=SDO 2=GND 3=SDI 4=CKL 5=VDD 6=CKO.

Pipeline: kiutils (typed objects, no hand-written s-expressions) -> .kicad_sch
(v20211014, KiCad 6 format) -> `kicad-cli sch upgrade --force` -> KiCad 10 native
(v20260306) -> `kicad-cli sch erc` for validation.

Usage:
  python tools/gen_schematic.py --leds 6
  python tools/gen_schematic.py --all            # all SKUs from feather-boards.md
  python tools/gen_schematic.py --leds 4 --out /tmp/x.kicad_sch

The script is the source of truth; generated .kicad_sch files are build artifacts.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import uuid
from pathlib import Path

from kiutils.items.common import Effects, Font, Position as Pos
from kiutils.items.schitems import (
    Connection,
    Junction,
    LocalLabel,
    SchematicSymbol,
    Stroke,
)
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib

# ---------------------------------------------------------------- constants

ROOT = Path(__file__).resolve().parent.parent
LIBS = ROOT / "boards" / "2020-leds" / "libs"
OUT_DIR = ROOT / "boards" / "2020-leds" / "schematics"
KICAD_CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")

# SKU list = distinct LED counts per feather board (feather-boards.md §3)
SKUS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# part metadata: (lib entryName, lib file, pin -> signal map)
# ZH1.5-4P: pins 1-4 signals (+5V/GND/DI or DO, /CI or CO), 5-6 mechanical anchors
CONN_IN = ("ZH1.5-4PSMD", "C145992.kicad_sym", {"1": "+5V", "2": "GND", "3": "DI", "4": "CI"})
CONN_OUT = ("ZH1.5-4PSMD", "C145992.kicad_sym", {"1": "+5V", "2": "GND", "3": "DO", "4": "CO"})
# PH2.0-2PWB: pins 1-2 signals (+5V/GND), 3-4 anchors
CONN_PWR = ("PH2.0-2PWB", "C47647.kicad_sym", {"1": "+5V", "2": "GND"})
# SK9822-EC20: pin -> signal
LED = ("SK9822-EC20", "C2909059.kicad_sym", {
    "1": "SDO", "2": "GND", "3": "SDI", "4": "CKL", "5": "VDD", "6": "CKO",
})

# layout geometry (mm) — ALL on KiCad's 1.27mm schematic grid
GRID = 1.27
PITCH = 24 * GRID      # 30.48 symbol spacing along the strip
LED_Y = 40 * GRID      # 50.8 LED row y
CONN_Y = 40 * GRID     # connectors on the same row
PWR_Y = 80 * GRID      # 101.6 power-tap connector row (below)
RAIL_TOP = 20 * GRID   # 25.4 +5V rail y
RAIL_BOT = 60 * GRID   # 76.2 GND rail y
STUB = 2 * GRID        # 2.54 wire stub length
X_J1 = 10 * GRID       # 12.7 data-in connector x
X_LED0 = 10 * GRID     # 12.7 first LED x


def _sym(lib_id: str, x: float, y: float, ref: str, value: str,
         footprint: str, pins: dict[str, str], project: str, root_uuid: str) -> SchematicSymbol:
    """Build a SchematicSymbol instance referencing an embedded lib symbol."""
    from kiutils.items.schitems import Property, SymbolProjectInstance, SymbolProjectPath

    props = [
        Property(key="Reference", value=ref, id=None,
                 position=Pos(X=x, Y=y - 15, angle=0),
                 effects=Effects(font=Font(height=1.27, width=1.27))),
        Property(key="Value", value=value, id=None,
                 position=Pos(X=x, Y=y + 15, angle=0),
                 effects=Effects(font=Font(height=1.27, width=1.27))),
        Property(key="Footprint", value=footprint, id=None,
                 position=Pos(X=x, Y=y + 25, angle=0),
                 effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        Property(key="Datasheet", value=_datasheet_url(lib_id), id=None,
                 position=Pos(X=x, Y=y + 35, angle=0),
                 effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
    ]
    return SchematicSymbol(
        libraryNickname="wings",
        entryName=lib_id,
        position=Pos(X=x, Y=y, angle=0),
        unit=1,
        inBom=True,
        onBoard=True,
        dnp=False,
        fieldsAutoplaced=False,
        uuid=str(uuid.uuid4()),
        properties=props,
        pins={num: str(uuid.uuid4()) for num in pins},
        mirror=None,
        instances=[
            SymbolProjectInstance(
                name=project,
                paths=[SymbolProjectPath(
                    sheetInstancePath=f"/{root_uuid}",
                    reference=ref,
                    unit=1,
                )],
            )
        ],
    )


def _prop(name: str, value: str, x: float, y: float, hide: bool = False) -> "Property":
    from kiutils.items.common import Effects, Font
    from kiutils.items.schitems import Property
    return Property(
        key=name,
        value=value,
        id=None,
        position=Pos(X=x, Y=y, angle=0),
        effects=Effects(
            font=Font(height=1.27, width=1.27, thickness=None, bold=False, italic=False),
            hide=hide,
        ),
        showName=False,
    )


def _datasheet_url(entry: str) -> str:
    urls = {
        "SK9822-EC20": "http://www.normandled.com/upload/202003/SK9822-EC20%20LED%20Datasheet.pdf",
        "ZH1.5-4PSMD": "https://www.lcsc.com/product-detail/C145992.html",
        "PH2.0-2PWB": "https://www.lcsc.com/product-detail/C47647.html",
    }
    return urls.get(entry, "")


def _load_symbol(lib_file: str, entry: str):
    """Load one symbol definition from a .kicad_sym lib (utf-8)."""
    lib = SymbolLib.from_file(LIBS / lib_file, encoding="utf-8")
    for sym in lib.symbols:
        if sym.entryName == entry:
            return sym
    raise ValueError(f"symbol {entry} not found in {lib_file}")


def _label(text: str, x: float, y: float) -> LocalLabel:
    from kiutils.items.common import Effects, Font
    return LocalLabel(
        text=text,
        position=Pos(X=x, Y=y, angle=0),
        effects=Effects(font=Font(height=1.27, width=1.27, thickness=None, bold=False, italic=False)),
        uuid=str(uuid.uuid4()),
        fieldsAutoplaced=False,
    )


def _wire(x1: float, y1: float, x2: float, y2: float) -> Connection:
    return Connection(
        type="wire",
        points=[Pos(X=x1, Y=y1), Pos(X=x2, Y=y2)],
        stroke=Stroke(width=0, type="default"),
        uuid=str(uuid.uuid4()),
    )


def _junction(x: float, y: float) -> Junction:
    return Junction(position=Pos(X=x, Y=y), uuid=str(uuid.uuid4()))


def build_schematic(leds: int) -> Schematic:
    """Build the feather-strip schematic for `leds` LEDs."""
    project = "wings"
    root_uuid = str(uuid.uuid4())
    sch = Schematic.create_new()
    sch.generator = "gen_schematic.py"
    sch.uuid = root_uuid

    # --- embed lib symbols (self-contained schematic) ---
    # Inside lib_symbols, symbols are named "<nickname>:<entry>" to match lib_id.
    embed = {}
    for entry, lib_file, _ in (CONN_IN, CONN_PWR, LED):
        sym = _load_symbol(lib_file, entry)
        sym.entryName = f"wings:{entry}"
        embed[entry] = sym
    sch.libSymbols = list(embed.values())

    # --- symbol instances ---
    sch.schematicSymbols = []

    # data-in connector (left)
    sch.schematicSymbols.append(
        _sym(CONN_IN[0], X_J1, CONN_Y, "J1", "DATA-IN", "C145992:CONN-SMD_ZH1.5-4P_SMD", CONN_IN[2],
             project, root_uuid))
    # LEDs
    for i in range(leds):
        sch.schematicSymbols.append(
            _sym(LED[0], X_LED0 + i * PITCH, LED_Y, f"L{i+1}", "SK9822-EC20",
                 "C2909059:LED-SMD_6P-L2.0-W2.0-P0.80-TL", LED[2],
                 project, root_uuid))
    # data-out connector (right)
    x_out = X_LED0 + leds * PITCH
    sch.schematicSymbols.append(
        _sym(CONN_OUT[0], x_out, CONN_Y, "J2", "DATA-OUT", "C145992:CONN-SMD_ZH1.5-4P_SMD", CONN_OUT[2],
             project, root_uuid))
    # power tap (below)
    sch.schematicSymbols.append(
        _sym(CONN_PWR[0], X_LED0 + (leds - 1) * PITCH / 2, PWR_Y, "J3", "PWR-TAP",
             "C47647:CONN-SMD_2P-P2.00_PH2.0-SPWB", CONN_PWR[2],
             project, root_uuid))

    # --- wires: power rails + stubs, data chain ---
    wires: list[Connection] = []
    junctions: list[Junction] = []
    labels: list[LocalLabel] = []

    # power rails (horizontal) — terminate at the outermost LED junction points
    # so both wire ends land on junctions (no dangling endpoints).
    # LED VDD pins are at x = X_LED0 + i*PITCH + 8.89 ; GND at X_LED0 + i*PITCH - 8.89
    rail5_x0 = X_LED0 + 0 * PITCH + 8.89        # first LED's VDD x
    rail5_x1 = X_LED0 + (leds - 1) * PITCH + 8.89  # last LED's VDD x
    railg_x0 = X_LED0 + 0 * PITCH - 8.89        # first LED's GND x
    railg_x1 = X_LED0 + (leds - 1) * PITCH - 8.89  # last LED's GND x
    wires.append(_wire(rail5_x0, RAIL_TOP, rail5_x1, RAIL_TOP))   # +5V
    wires.append(_wire(railg_x0, RAIL_BOT, railg_x1, RAIL_BOT))   # GND
    # name the rails so connector labeled-stubs (+5V/GND) join them —
    # label EXACTLY at the rail end point
    labels.append(_label("+5V", rail5_x1, RAIL_TOP))
    labels.append(_label("GND", railg_x1, RAIL_BOT))

    def pin_xy(sym: SchematicSymbol, pin_num: str) -> tuple[float, float]:
        """Absolute pin position from the embedded symbol geometry (rotation 0).

        NOTE: `kicad-cli sch upgrade` (v20211014 -> v20260306) flips the Y of
        embedded lib-symbol pins, so the absolute Y is sym.Y - local.Y.
        """
        entry = sym.entryName
        lib_sym = embed[entry]
        # pin local position from first unit
        unit = lib_sym.units[0]
        for p in unit.pins:
            if str(p.number) == str(pin_num):
                return sym.position.X + p.position.X, sym.position.Y - p.position.Y
        raise ValueError(f"pin {pin_num} not found on {entry}")

    def route(sym: SchematicSymbol, pin_num: str, signal: str, rail_y: float | None):
        """Draw a stub from the pin to a rail (or a short stub + label at its end)."""
        px, py = pin_xy(sym, pin_num)
        if rail_y is not None:
            # vertical stub from pin up/down to the rail, plus a junction at the rail
            wires.append(_wire(px, py, px, rail_y))
            junctions.append(_junction(px, rail_y))
        else:
            # labeled stub: horizontal wire from pin, label EXACTLY at the wire end
            dx = STUB if px < sym.position.X else -STUB
            endx = px + dx
            wires.append(_wire(px, py, endx, py))
            labels.append(_label(signal, endx, py))

    # connectors -> rails: use SHORT labeled stubs (+5V/GND) instead of long
    # vertical wires through the board (avoids crossing-wire connections).
    for sym, pin_map in ((sch.schematicSymbols[0], CONN_IN[2]),
                         (sch.schematicSymbols[-2], CONN_OUT[2]),
                         (sch.schematicSymbols[-1], CONN_PWR[2])):
        for num, sig in pin_map.items():
            if sig in ("+5V", "GND"):
                route(sym, num, sig, None)   # labeled stub, connects to rail by name
            else:
                route(sym, num, sig, None)   # DI/CI/DO/CO also labeled stubs

    # LEDs: VDD/GND to rails, data chain via labeled stubs
    for i, sym in enumerate(sch.schematicSymbols[1:-2]):
        route(sym, "5", "+5V", RAIL_TOP)
        route(sym, "2", "GND", RAIL_BOT)
        if i == 0:
            route(sym, "3", "DI", None)   # SDI <- J1 DI
            route(sym, "4", "CI", None)   # CKL <- J1 CI
        else:
            prev = sch.schematicSymbols[1 + i - 1]
            route(sym, "3", f"D{i-1}", None)  # SDI <- prev SDO
            route(sym, "4", f"C{i-1}", None)  # CKL <- prev CKO
        if i == leds - 1:
            route(sym, "1", "DO", None)   # SDO -> J2 DO
            route(sym, "6", "CO", None)   # CKO -> J2 CO
        else:
            route(sym, "1", f"D{i}", None)  # SDO -> next SDI
            route(sym, "6", f"C{i}", None)  # CKO -> next CKL

    sch.graphicalItems = wires
    sch.junctions = junctions
    sch.labels = labels
    return sch


def run_kicad_cli(*args: str) -> None:
    r = subprocess.run([str(KICAD_CLI), *args], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"kicad-cli {' '.join(args)} failed ({r.returncode})")
    out = (r.stdout or "").strip()
    if out:
        print(out)


def generate(leds: int, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp.kicad_sch")
    sch = build_schematic(leds)
    # write utf-8 explicitly (kiutils to_file uses platform encoding)
    tmp.write_text(sch.to_sexpr(), encoding="utf-8")
    # upgrade to KiCad 10 native format
    run_kicad_cli("sch", "upgrade", "--force", str(tmp))
    # move to final name
    tmp.replace(out_path)
    # validate
    run_kicad_cli("sch", "erc", str(out_path))
    print(f"OK  {out_path.relative_to(ROOT)}  ({leds} LEDs)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--leds", type=int, help="LED count for one strip")
    g.add_argument("--all", action="store_true", help="generate all SKUs")
    ap.add_argument("--out", type=Path, help="output file (with --leds)")
    args = ap.parse_args()

    if args.all:
        for n in SKUS:
            generate(n, OUT_DIR / f"feather-strip-{n}led.kicad_sch")
    else:
        if args.out:
            generate(args.leds, args.out)
        else:
            generate(args.leds, OUT_DIR / f"feather-strip-{args.leds}led.kicad_sch")


if __name__ == "__main__":
    main()
