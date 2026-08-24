"""G9 tests — markdown sync / lint."""

import json
import os
import shutil
from pathlib import Path

import pytest

from feathergen.markdown_sync import (
    lint_flight_rows,
    lint_markdown,
    main,
    parse_flight_rows,
)

REPO = Path(__file__).resolve().parents[4]  # repo root
MD = REPO / "mechanical" / "feather" / "outline-templates.md"
FEATHERS = REPO / "mechanical" / "feather" / "generator" / "feathers.json"

SCRATCH = Path(__file__).resolve().parents[1] / ".test-out"


@pytest.fixture(autouse=True)
def scratch():
    shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(SCRATCH, exist_ok=True)
    yield SCRATCH
    shutil.rmtree(SCRATCH, ignore_errors=True)


def drifted_md(replacements):
    """Copy the real markdown with ``(old, new)`` substitutions applied."""
    text = MD.read_text(encoding="utf-8")
    for old, new in replacements:
        assert old in text, f"pattern not found: {old!r}"
        text = text.replace(old, new, 1)
    p = SCRATCH / "drifted.md"
    p.write_text(text, encoding="utf-8")
    return p


# --- parsing ----------------------------------------------------------------


def test_parser_finds_all_flight_rows():
    text = MD.read_text(encoding="utf-8")
    rows = parse_flight_rows(text)
    ids = [r["id"] for r in rows]
    assert len(ids) == 26  # P10 + S12 + T4
    assert ids[:3] == ["P1", "P2", "P3"]
    assert ids[-1] == "T4"
    # spot-check a few rows
    p4 = next(r for r in rows if r["id"] == "P4")
    assert p4["total"] == 75.0
    assert p4["vane"] == 56.0
    assert p4["rachis_outer"] == 34
    assert p4["rachis_inner"] == 66
    assert p4["curve"] == "med-high"


def test_parser_handles_approx_rachis():
    text = MD.read_text(encoding="utf-8")
    rows = parse_flight_rows(text)
    t4 = next(r for r in rows if r["id"] == "T4")
    assert t4["rachis_outer"] == 50
    assert t4["rachis_inner"] == 50


# --- lint passes on the real file -------------------------------------------


def test_lint_passes_on_current_file():
    assert lint_markdown(MD, FEATHERS) == []


def test_lint_flight_rows_clean():
    data = json.loads(FEATHERS.read_text(encoding="utf-8"))
    rows = parse_flight_rows(MD.read_text(encoding="utf-8"))
    assert lint_flight_rows(rows, data) == []


# --- drifted rows are flagged ------------------------------------------------


def test_lint_flags_drifted_total():
    p = drifted_md([("| P4 | 75 | 56 |", "| P4 | 74 | 56 |")])
    ms = lint_markdown(p, FEATHERS)
    assert any("P4" in m and "total" in m for m in ms)


def test_lint_flags_drifted_vane():
    p = drifted_md([("| S6 | 57 | 43 |", "| S6 | 57 | 42 |")])
    ms = lint_markdown(p, FEATHERS)
    assert any("S6" in m and "vane" in m for m in ms)


def test_lint_flags_drifted_rachis():
    p = drifted_md([("| P1 | 56 | 42 | 4.5 | pointed, hooked | 30:70 |", "| P1 | 56 | 42 | 4.5 | pointed, hooked | 31:69 |")])
    ms = lint_markdown(p, FEATHERS)
    assert any("P1" in m and "rachis" in m for m in ms)


def test_lint_flags_drifted_curve():
    p = drifted_md([("| P4 | 75 | 56 | 5.5 | pointed | 34:66 | med-high |", "| P4 | 75 | 56 | 5.5 | pointed | 34:66 | low |")])
    ms = lint_markdown(p, FEATHERS)
    assert any("P4" in m and "curve" in m for m in ms)


def test_lint_ignores_max_width_drift():
    # max width is superseded by the data file — a drift there is NOT a mismatch
    p = drifted_md([("| P4 | 75 | 56 | 5.5 | pointed | 34:66 | med-high |", "| P4 | 75 | 56 | 9.9 | pointed | 34:66 | med-high |")])
    assert lint_markdown(p, FEATHERS) == []


def test_lint_ignores_tip_wording_drift():
    # tip is free-form in the doc ("very rounded" vs "very-rounded") — not linted
    p = drifted_md([("| T1 | 56 | 42 | 8 | very rounded | ≈50:50 | low |", "| T1 | 56 | 42 | 8 | rounded | ≈50:50 | low |")])
    assert lint_markdown(p, FEATHERS) == []


# --- errors -----------------------------------------------------------------


def test_lint_missing_table():
    p = SCRATCH / "no-table.md"
    p.write_text("# nothing here", encoding="utf-8")
    ms = lint_markdown(p, FEATHERS)
    assert ms and "no §7 flight-feather rows" in ms[0]


def test_lint_missing_feather():
    p = drifted_md([("| S12 | 45 | 34 | 6.5 | rounded | 50:50 | low |", "| S12 | 45 | 34 | 6.5 | rounded | 50:50 | low |\n| S13 | 44 | 33 | 6.5 | rounded | 50:50 | low |")])
    ms = lint_markdown(p, FEATHERS)
    assert any("S13" in m and "missing" in m for m in ms)


# --- CLI --------------------------------------------------------------------


def test_main_ok(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["markdown_sync", str(MD), str(FEATHERS)])
    rc = main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK" in out


def test_main_drifted(monkeypatch, capsys):
    p = drifted_md([("| P4 | 75 | 56 |", "| P4 | 74 | 56 |")])
    monkeypatch.setattr("sys.argv", ["markdown_sync", str(p), str(FEATHERS)])
    rc = main()
    assert rc == 1
    assert "MISMATCHES" in capsys.readouterr().out


def test_main_bad_args(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["markdown_sync", "only-one-arg"])
    assert main() == 2
