"""Recompute the custom LED board inventory from feather-record.csv.

Model (per the custom-electronics proposal, Option B):
- SK9822-EC20 at 30/m pitch (33.3 mm) on 5 mm-wide boards
- Board length = LED count * 33.3 mm (per-LED pitch)
- Assembly panel cap 250x250 mm -> max board 233 mm = 7 LEDs (B7)
- SKUs B7 (7 LEDs), B4 (4), B3 (3); per-feather boards chained to reach LED count
- Feather length basis: measured TOTAL from feather-record.csv (authoritative)

Chaining: for each feather's LED count n, choose the combination of B7/B4/B3
that minimizes (number of boards, then dark-LED excess) and covers >= n.
"""
import csv
import math
from collections import OrderedDict

PITCH_MM = 33.3
SKUS = (7, 4, 3)  # LEDs per board, descending


def leds_for_cm(cm):
    """LEDs at 30/m (33.3 mm pitch), ceiling so the strip covers the feather."""
    return math.ceil(cm * 30.0 / 100.0)


def chain(n):
    """Minimize (boards, dark excess) covering n LEDs with SKUs {7,4,3}."""
    best = None
    for b7 in range(n // 7 + 1):
        rem = n - b7 * 7
        for b4 in range(rem // 4 + 1):
            rem2 = rem - b4 * 4
            b3 = max(0, math.ceil(rem2 / 3))
            cap = b7 * 7 + b4 * 4 + b3 * 3
            if cap < n:
                continue
            key = (b7 + b4 + b3, cap - n)
            if best is None or key < best[0]:
                best = (key, (b7, b4, b3), cap)
    return best


def main():
    rows = []
    with open(r'mechanical\templates\feather-record.csv', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)

    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r['group'], []).append(r)

    print(f"{'feather':8} {'tot(cm)':8} {'LEDs':5} {'chain':14} {'brds':5} {'len(mm)':8}")
    total_leds = total_boards = total_len = 0
    total_by_sku = {7: 0, 4: 0, 3: 0}
    total_dark = 0
    for g, feats in groups.items():
        print(f"-- {g} ({len(feats)} feathers) --")
        for r in feats:
            cm = float(r['total_cm'])
            n = leds_for_cm(cm)
            (brds, dark), (b7, b4, b3), cap = chain(n)
            chain_s = '+'.join(
                [f'B7' * 0] + [f'B7'] * b7 + [f'B4'] * b4 + [f'B3'] * b3) or 'B3'
            chain_s = '+'.join([f'B7'] * b7 + [f'B4'] * b4 + [f'B3'] * b3)
            ln = n * PITCH_MM
            total_leds += n
            total_boards += brds
            total_len += ln
            total_dark += dark
            total_by_sku[7] += b7
            total_by_sku[4] += b4
            total_by_sku[3] += b3
            print(f"{r['feather']:8} {cm:8.1f} {n:5d} {chain_s:14} {brds:5d} {ln:8.0f}")
        print()

    print(f"PER WING : feathers={len(rows):3d}  LEDs={total_leds:4d}  "
          f"boards={total_boards:4d}  strip_len={total_len/1000:.3f} m  "
          f"dark_LEDs={total_dark}")
    print(f"BOTH WINGS: LEDs={total_leds*2:4d}  boards={total_boards*2:4d}  "
          f"strip_len={total_len*2/1000:.3f} m")
    print(f"SKU mix/wing: B7={total_by_sku[7]}  B4={total_by_sku[4]}  B3={total_by_sku[3]}")

    # Panel math: 50 strips of 5 mm across a 250 mm panel
    per_panel = 50
    for wing, boards in (('per wing', total_boards), ('both wings', total_boards * 2)):
        panels = math.ceil(boards / per_panel)
        print(f"Panels ({wing}, {boards} boards): {panels} x 250x250  "
              f"(capacity {panels * per_panel}, spare {panels * per_panel - boards})")

    # Full-white power at 40 mA/LED
    for label, n in (('per wing', total_leds), ('both wings', total_leds * 2)):
        print(f"Full white {label}: {n*0.04:.1f} A @ 5V = {n*0.2:.0f} W")


if __name__ == '__main__':
    main()
