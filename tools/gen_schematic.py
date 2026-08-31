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

# SKU list = distinct segment LED counts from the group-board design
# (feather-boards.md §3 — 6 segment lengths, 7–12 LEDs)
SKUS = [7, 8, 9, 10, 11, 12]

# part metadata: (lib entryName, lib file, pin -> signal map)
# ZH1.5-4P: 6 pins — 1-4 signals, 5-6 mechanical anchors (NC).
# Connector pinout per the flip-corrected convention (user-verified):
#   DATA-IN : 1=GND 2=CI 3=DI 4=+5V
#   DATA-OUT: 1=+5V 2=DO 3=CO 4=GND
CONN_IN = ("ZH1.5-4PSMD", "C145992.kicad_sym", {"1": "GND", "2": "CI", "3": "DI", "4": "+5V"})
CONN_OUT = ("ZH1.5-4PSMD", "C145992.kicad_sym", {"1": "+5V", "2": "DO", "3": "CO", "4": "GND"})
# PH2.0-2PWB: pins 1-2 signals (+5V/GND), 3-4 anchors
CONN_PWR = ("PH2.0-2PWB", "C47647.kicad_sym", {"1": "+5V", "2": "GND"})
# Bulk decoupling cap per segment board — 22uF 25V X5R 1206 (JLCPCB BASIC), C12891.
# The SK9822-EC20 has NO internal decoupling cap; one bulk cap per board spans the
# rails at the power-tap end (data lines route under it on the back copper).
CAP = ("CL31A226KAHNNNE", "C12891.kicad_sym", {"1": "+5V", "2": "GND"})
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
RAIL_GND = 20 * GRID   # 25.4 GND rail y (ABOVE the LED row)
RAIL_5V = 60 * GRID    # 76.2 +5V rail y (BELOW the LED row)
STUB = 2 * GRID        # 2.54 wire stub length
X_J1 = -10 * GRID      # -12.7 data-in connector x (left of L1, no overlap)
X_LED0 = 10 * GRID     # 12.7 first LED x
ROT_J1 = 180           # data-in connector rotated 180 (clockwise)
ROT_LED = 270          # LEDs rotated 270 (counter-clockwise): SDI/GND/SDO top row,
                       #   CKL/VDD/CKO bottom row — straight chain + rail drops.


def _sym(lib_id: str, x: float, y: float, ref: str, value: str,
         footprint: str, pins: dict[str, str], project: str, root_uuid: str,
         angle: int = 0) -> SchematicSymbol:
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
        position=Pos(X=x, Y=y, angle=angle),
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
        "CL31A226KAHNNNE": "https://www.lcsc.com/product-detail/C12891.html",
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


# Empirically-verified pin offsets (mm from symbol center) as KiCad 10 actually
# places them after `sch upgrade` (which flips embedded-symbol pin Y, and
# rotation is applied in KiCad's y-down convention). Verified by fine netlist
# probing at 1.27mm resolution:
#   LED rot=270 : SDI(3)=(-2.54,-8.89) GND(2)=(0,-8.89) SDO(1)=(+2.54,-8.89)   [top row]
#                 CKL(4)=(-2.54,+8.89) VDD(5)=(0,+8.89) CKO(6)=(+2.54,+8.89)   [bottom row]
#   ZH1.5 rot=180: 1=(+6.35,+3.81) 2=(+6.35,+1.27) 3=(+6.35,-1.27) 4=(+6.35,-3.81)
#                  5=(-6.35,-3.81) 6=(-6.35,+3.81)
#   rot=0 (unrotated): LED pins are the raw local coords with Y flipped.
PIN_OFFSETS = {
    # (entry, angle) -> {pin: (x, y)}
    ("SK9822-EC20", 270): {
        "1": (2.54, -8.89), "2": (0, -8.89), "3": (-2.54, -8.89),
        "4": (-2.54, 8.89), "5": (0, 8.89), "6": (2.54, 8.89),
    },
    ("ZH1.5-4PSMD", 180): {
        "1": (6.35, 3.81), "2": (6.35, 1.27), "3": (6.35, -1.27), "4": (6.35, -3.81),
        "5": (-6.35, -3.81), "6": (-6.35, 3.81),
    },
}


def pin_xy(sym: SchematicSymbol, pin_num: str, embed: dict) -> tuple[float, float]:
    """Absolute pin position, using empirically-verified rotated offsets.

    These account for both the symbol rotation AND the `kicad-cli sch upgrade`
    Y-flip quirk, so wires land exactly on the pins KiCad will see.
    """
    entry = sym.entryName
    angle = sym.position.angle or 0
    key = (entry, angle)
    if key in PIN_OFFSETS and pin_num in PIN_OFFSETS[key]:
        ox, oy = PIN_OFFSETS[key][pin_num]
        return sym.position.X + ox, sym.position.Y + oy
    # fallback: unrotated — raw local with the upgrade Y-flip
    lib_sym = embed[entry]
    unit = lib_sym.units[0]
    for p in unit.pins:
        if str(p.number) == str(pin_num):
            return sym.position.X + p.position.X, sym.position.Y - p.position.Y
    raise ValueError(f"pin {pin_num} not found on {entry}")


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
    for entry, lib_file, _ in (CONN_IN, CONN_PWR, LED, CAP):
        sym = _load_symbol(lib_file, entry)
        sym.entryName = f"wings:{entry}"
        embed[entry] = sym
    sch.libSymbols = list(embed.values())

    # --- symbol instances ---
    sch.schematicSymbols = []

    # data-in connector (left), rotated 180 so its pin row faces the strip
    sch.schematicSymbols.append(
        _sym(CONN_IN[0], X_J1, CONN_Y, "J1", "DATA-IN", "C145992:CONN-SMD_ZH1.5-4P_SMD", CONN_IN[2],
             project, root_uuid, angle=ROT_J1))
    # LEDs, rotated 90 CCW
    for i in range(leds):
        sch.schematicSymbols.append(
            _sym(LED[0], X_LED0 + i * PITCH, LED_Y, f"L{i+1}", "SK9822-EC20",
                 "C2909059:LED-SMD_6P-L2.0-W2.0-P0.80-TL", LED[2],
                 project, root_uuid, angle=ROT_LED))
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
    # bulk decoupling cap (below the power tap; joins the rails by net name)
    sch.schematicSymbols.append(
        _sym(CAP[0], X_LED0 + (leds - 1) * PITCH / 2, PWR_Y + 40 * GRID, "C1", "22uF",
             "C12891:C1206", CAP[2], project, root_uuid))

    # --- wires: power rails + drops, data chain ---
    wires: list[Connection] = []
    junctions: list[Junction] = []
    labels: list[LocalLabel] = []

    # rot=270 LED pin offsets (mm from symbol center), verified by probe:
    #   SDO(1)=(+2.54,-8.89) GND(2)=(0,-8.89) SDI(3)=(-2.54,-8.89)   top row
    #   CKL(4)=(-2.54,+8.89) VDD(5)=(0,+8.89) CKO(6)=(+2.54,+8.89)   bottom row
    TOP_Y = LED_Y - 8.89    # data-in row: SDI/GND/SDO
    BOT_Y = LED_Y + 8.89    # clock-in row: CKL/VDD/CKO
    x_leds = [X_LED0 + i * PITCH for i in range(leds)]

    # power rails (horizontal), spanning the first..last LED x
    rail_x0 = x_leds[0]
    rail_x1 = x_leds[-1]
    wires.append(_wire(rail_x0, RAIL_GND, rail_x1, RAIL_GND))   # GND bus (top)
    wires.append(_wire(rail_x0, RAIL_5V, rail_x1, RAIL_5V))     # +5V bus (bottom)
    # name the rails at their right ends so connector labeled-stubs join them
    labels.append(_label("GND", rail_x1, RAIL_GND))
    labels.append(_label("+5V", rail_x1, RAIL_5V))

    # LEDs: GND straight UP to GND bus, VDD straight DOWN to +5V bus
    for x in x_leds:
        # GND pin (top row) -> straight up to GND rail
        wires.append(_wire(x, TOP_Y, x, RAIL_GND))
        junctions.append(_junction(x, RAIL_GND))
        # VDD pin (bottom row) -> straight down to +5V rail
        wires.append(_wire(x, BOT_Y, x, RAIL_5V))
        junctions.append(_junction(x, RAIL_5V))

    # data chain: straight HORIZONTAL wires between adjacent LEDs, each with a
    # net label so KiCad registers the connection (a bare wire between pins is
    # drawn but NOT netlisted in KiCad 10 — verified by test).
    #   SDO_i -> SDI_{i+1} on the top row; CKO_i -> CKL_{i+1} on the bottom row
    for i in range(leds - 1):
        xm = (x_leds[i] + 2.54 + x_leds[i + 1] - 2.54) / 2  # wire midpoint
        wires.append(_wire(x_leds[i] + 2.54, TOP_Y, x_leds[i + 1] - 2.54, TOP_Y))  # SDO->SDI
        wires.append(_wire(x_leds[i] + 2.54, BOT_Y, x_leds[i + 1] - 2.54, BOT_Y))  # CKO->CKL
        labels.append(_label(f"D{i}", xm, TOP_Y))
        labels.append(_label(f"C{i}", xm, BOT_Y))

    # first LED's SDI/CKL: labeled stubs to J1 (DI/CI by name)
    wires.append(_wire(x_leds[0] - 2.54, TOP_Y, x_leds[0] - 2.54 - STUB, TOP_Y))
    labels.append(_label("DI", x_leds[0] - 2.54 - STUB, TOP_Y))
    wires.append(_wire(x_leds[0] - 2.54, BOT_Y, x_leds[0] - 2.54 - STUB, BOT_Y))
    labels.append(_label("CI", x_leds[0] - 2.54 - STUB, BOT_Y))

    # last LED's SDO/CKO: labeled stubs to J2 (DO/CO by name)
    wires.append(_wire(x_leds[-1] + 2.54, TOP_Y, x_leds[-1] + 2.54 + STUB, TOP_Y))
    labels.append(_label("DO", x_leds[-1] + 2.54 + STUB, TOP_Y))
    wires.append(_wire(x_leds[-1] + 2.54, BOT_Y, x_leds[-1] + 2.54 + STUB, BOT_Y))
    labels.append(_label("CO", x_leds[-1] + 2.54 + STUB, BOT_Y))

    # connectors -> rails: SHORT labeled stubs (+5V/GND/DI/CI/DO/CO)
    def conn_stub(sym: SchematicSymbol, pin_num: str, signal: str):
        """Short horizontal labeled stub from a connector pin."""
        px, py = pin_xy(sym, pin_num, embed)
        dx = STUB if px < sym.position.X else -STUB
        endx = px + dx
        wires.append(_wire(px, py, endx, py))
        labels.append(_label(signal, endx, py))

    for sym, pin_map in ((sch.schematicSymbols[0], CONN_IN[2]),
                         (sch.schematicSymbols[leds + 1], CONN_OUT[2]),
                         (sch.schematicSymbols[leds + 2], CONN_PWR[2]),
                         (sch.schematicSymbols[leds + 3], CAP[2])):
        for num, sig in pin_map.items():
            conn_stub(sym, num, sig)

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
