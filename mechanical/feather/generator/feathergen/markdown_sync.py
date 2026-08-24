"""G9 — markdown sync / lint.

Checks that the §7 "Flight feathers" table in outline-templates.md matches
feathers.json (per §8's "markdown tables are never hand-maintained" rule).

Compared fields (identical semantics in both sources): **Total** (cm),
**Vane** (cm), **Rachis (out:in)**, **Curve**. Skipped:

- **Max width** — explicitly superseded by the chord-ratio-derived
  ``max_width_cm`` in feathers.json (§7 note; §6 width decision).
- **Tip** — free-form in the doc ("pointed, hooked" for P1, "very rounded"
  with a space) vs the canonical enum in feathers.json.

Usage: ``lint_markdown(path_to_md, path_to_feathers)`` returns a list of
mismatch strings (empty = clean). Also exposes a CLI:

    python -m feathergen.markdown_sync outline-templates.md feathers.json

See backlog-geometry-engine.md task G9.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Sequence

# row id in the §7 flight table matches one of these groups
_FLIGHT_ID = re.compile(r"^(P|S|T)\d+$")
_HEADER_FLIGHT = "### Flight feathers"
_HEADER_COVERTS = "### Coverts & back"

# allowed curvature values (from CURVATURE_BOW_FRACTION in rachis.py)
_CURVATURES = {"high", "med-high", "med", "med-low", "low", "straight"}


def parse_flight_rows(markdown: str) -> list[dict[str, object]]:
    """Parse the §7 flight-feathers table into rows:
    ``{"id", "total", "vane", "rachis_outer", "rachis_inner", "curve"}``.
    """
    lines = markdown.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == _HEADER_FLIGHT)
        end = next(
            i
            for i in range(start + 1, len(lines))
            if ln_startswith(lines[i], _HEADER_COVERTS)
        )
    except StopIteration:
        return []

    rows: list[dict[str, object]] = []
    for ln in lines[start:end]:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 7 or not _FLIGHT_ID.match(cells[0]):
            continue
        rachis = re.fullmatch(r"(?:≈)?(\d+):(\d+)", cells[5])
        if not rachis:
            continue
        rows.append(
            {
                "id": cells[0],
                "total": float(cells[1]),
                "vane": float(cells[2]),
                "rachis_outer": int(rachis.group(1)),
                "rachis_inner": int(rachis.group(2)),
                "curve": cells[6],
            }
        )
    return rows


def ln_startswith(line: str, prefix: str) -> bool:
    return line.strip().startswith(prefix)


def lint_flight_rows(rows: Sequence[dict[str, object]], data) -> list[str]:
    """Compare parsed §7 rows against a feathers.json ``data`` dict."""
    by_id = {f["id"]: f for f in data["feathers"]}
    mismatches: list[str] = []
    for row in rows:
        fid = row["id"]
        feather = by_id.get(fid)
        if feather is None:
            mismatches.append(f"{fid}: missing from feathers.json")
            continue
        if row["total"] != feather["total_cm"]:
            mismatches.append(
                f"{fid}: total {row['total']} != {feather['total_cm']}"
            )
        if row["vane"] != feather["vane_cm"]:
            mismatches.append(
                f"{fid}: vane {row['vane']} != {feather['vane_cm']}"
            )
        split = feather["rachis_split"]
        if row["rachis_outer"] != split["outer"] or row["rachis_inner"] != split["inner"]:
            mismatches.append(
                f"{fid}: rachis {row['rachis_outer']}:{row['rachis_inner']} "
                f"!= {split['outer']}:{split['inner']}"
            )
        if row["curve"] not in _CURVATURES or row["curve"] != feather["curvature"]:
            mismatches.append(
                f"{fid}: curve {row['curve']} != {feather['curvature']}"
            )
    return mismatches


def lint_markdown(markdown_path: str | Path, feathers_path: str | Path) -> list[str]:
    """Lint the §7 flight table of a markdown file against feathers.json."""
    markdown = Path(markdown_path).read_text(encoding="utf-8")
    data = json.loads(Path(feathers_path).read_text(encoding="utf-8"))
    rows = parse_flight_rows(markdown)
    if not rows:
        return ["no §7 flight-feather rows found (parser didn't match the table)"]
    return lint_flight_rows(rows, data)


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python -m feathergen.markdown_sync OUTLINE_MD FEATHERS_JSON")
        return 2
    mismatches = lint_markdown(argv[0], argv[1])
    if mismatches:
        print("MISMATCHES:")
        for m in mismatches:
            print(f" - {m}")
        return 1
    print("OK: §7 flight table matches feathers.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
