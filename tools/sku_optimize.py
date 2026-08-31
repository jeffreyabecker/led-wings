"""Optimize the SKU board-length set for the 61-feather wing.

Constraint: board cap 233 mm = 7 LEDs (250x250 in-house reflow panel).
Proposed SKUs: B7=233(7), B6=200(6), B5=166(5), B4=133(4), B3=100(3) mm.
Minimize boards per feather (then dark excess). Verify coverage + totals.
"""
import csv
import math

PITCH = 33.3
SKUS = (7, 6, 5, 4, 3)  # LEDs per board (mm = LEDs*33.3)


def chain(n):
    best = None
    for b7 in range(n // 7 + 1):
        rem = n - b7 * 7
        for b6 in range(rem // 6 + 1):
            rem2 = rem - b6 * 6
            for b5 in range(rem2 // 5 + 1):
                rem3 = rem2 - b5 * 5
                for b4 in range(rem3 // 4 + 1):
                    rem4 = rem3 - b4 * 4
                    b3 = max(0, math.ceil(rem4 / 3))
                    cap = b7 * 7 + b6 * 6 + b5 * 5 + b4 * 4 + b3 * 3
                    if cap < n:
                        continue
                    key = (b7 + b6 + b5 + b4 + b3, cap - n)
                    if best is None or key < best[0]:
                        best = (key, (b7, b6, b5, b4, b3), cap)
    return best


rows = []
with open(r'mechanical\templates\feather-record.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cm = float(r['total_cm'])
        n = math.ceil(cm * 0.3)
        rows.append((r['feather'], cm, n))

by_len = {}
total_boards = total_dark = 0
counts = {7: 0, 6: 0, 5: 0, 4: 0, 3: 0}
print(f"{'feather':8} {'tot(cm)':8} {'LEDs':5} {'chain':18} {'brds':4} {'dark':4}")
for f, cm, n in sorted(rows, key=lambda x: -x[2]):
    (brds, dark), (b7, b6, b5, b4, b3), cap = chain(n)
    cs = '+'.join([f'B7'] * b7 + [f'B6'] * b6 + [f'B5'] * b5 + [f'B4'] * b4 + [f'B3'] * b3)
    total_boards += brds
    total_dark += dark
    for sku, c in ((7, b7), (6, b6), (5, b5), (4, b4), (3, b3)):
        counts[sku] += c
    print(f"{f:8} {cm:8.1f} {n:5d} {cs:18} {brds:4d} {dark:4d}")

print(f"\nPER WING : {len(rows)} feathers, {total_boards} boards, {total_dark} dark LEDs")
print(f"BOTH WINGS: {total_boards*2} boards")
print(f"SKU mix/wing: B7={counts[7]}  B6={counts[6]}  B5={counts[5]}  B4={counts[4]}  B3={counts[3]}")
print(f"SKU lengths: B7=233mm  B6=200mm  B5=166mm  B4=133mm  B3=100mm")
panels = math.ceil(total_boards * 2 / 50)
print(f"Panels (both wings + 24 structure = {total_boards*2+24} boards): "
      f"{math.ceil((total_boards*2+24)/50)} x 250x250 (cap {math.ceil((total_boards*2+24)/50)*50})")
print(f"Full white: {sum(r[2] for r in rows)*2*0.04:.1f} A both wings "
      f"= {sum(r[2] for r in rows)*2*0.2:.0f} W")
