#!/usr/bin/env python3
"""Validate mechanical/feather/generator/feathers.json against the backlog schema invariants."""
import collections
import json
import math
import sys

PATH = "mechanical/feather/generator/feathers.json"


def round_half_up(value: float, ndigits: int = 1) -> float:
    """Round to ndigits using half-up (files use half-up, not banker's rounding)."""
    factor = 10 ** ndigits
    return math.floor(value * factor + 0.5) / factor


def main() -> int:
    with open(PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    fs = data["feathers"]

    print("feathers:", len(fs))
    ids = [f["id"] for f in fs]
    if len(ids) != len(set(ids)):
        dupes = [i for i, c in collections.Counter(ids).items() if c > 1]
        print("ERROR duplicate ids:", dupes)
        return 1
    print("groups:", dict(collections.Counter(f["group"] for f in fs)))

    errors = []
    for f in fs:
        rid = f["id"]
        if f["rachis_split"]["outer"] + f["rachis_split"]["inner"] != 100:
            errors.append(f"{rid}: rachis split != 100")
        if f["vane_cm"] > f["total_cm"]:
            errors.append(f"{rid}: vane_cm > total_cm")
        if f["total_cm"] - f["vane_cm"] < 0:
            errors.append(f"{rid}: quill < 0")
        expected = round_half_up(f["chord_ratio_pct"] / 100.0 * f["total_cm"], 1)
        if abs(expected - f["max_width_cm"]) > 0.06:
            errors.append(f"{rid}: max_width_cm {f['max_width_cm']} != chord_ratio*total {expected}")
        if f["lit"] and f["max_width_cm"] < 1.4:
            errors.append(f"{rid}: lit feather below 1.4 cm vane floor")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(" -", e)
        return 1

    lit = [f for f in fs if f["lit"]]
    print("all invariants OK")
    print("lit count:", len(lit))
    print("min lit max_width_cm:", min(f["max_width_cm"] for f in lit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
