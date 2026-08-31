"""Board lengths per feather from feather-record.csv + the user's grouping.

Model: 30/m pitch (33.3 mm/LED), LEDs = ceil(total_cm * 0.3),
board length = LEDs * 33.3 mm. Panel cap (Option B, 250x250 in-house) = 233 mm = 7 LEDs,
so longer feathers chain from SKU boards.
"""
import csv
import re
from collections import OrderedDict

PITCH = 33.3

manual_raw = [
    "pc4-6",
    "PC1,A4,MC1-5,U2-7,SC9",
    "U1,U8, L1-6",
    "P1-5,P8-10",
    "P7,S1-9",
    "A1-3,PC2-3,SC2-8,Sc10, S10",
]

def expand(item):
    m = re.match(r"^([A-Za-z]+)(\d+)-(\d+)$", item.strip())
    if not m:
        return [item.strip().upper()]
    prefix, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
    return [f"{prefix}{i}".upper() for i in range(lo, hi + 1)]

group_of = {}
for i, line in enumerate(manual_raw, 1):
    for item in line.split(","):
        if item.strip():
            for f in expand(item):
                group_of.setdefault(f, i)

rows = {}
with open(r'mechanical\templates\feather-record.csv', newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cm = float(r['total_cm'])
        leds = -(-int(cm * 30) // 100)  # ceil(cm*0.3)
        rows[r['feather']] = dict(cm=cm, leds=leds, mm=round(leds * PITCH),
                                  group=group_of.get(r['feather'].upper(), 0))

# Distinct length histogram
hist = OrderedDict()
for f, d in sorted(rows.items(), key=lambda kv: kv[1]['mm']):
    hist.setdefault(d['mm'], []).append(f)

print("== DISTINCT BOARD LENGTHS (per wing) ==")
print(f"{'len(mm)':8} {'LEDs':5} {'count':6}  feathers (G#)")
for ln, feats in hist.items():
    leds = round(ln / PITCH)
    names = ", ".join(f"{f}(G{rows[f]['group']})" for f in feats)
    print(f"{ln:8d} {leds:5d} {len(feats):6d}  {names}")

total_leds = sum(d['leds'] for d in rows.values())
print(f"\n61 feathers -> {len(hist)} distinct lengths, {total_leds} LEDs/wing, "
      f"strip {total_leds*PITCH/1000:.2f} m/wing")
over = [f for f, d in rows.items() if d['mm'] > 233]
print(f"Feathers > 233 mm cap ({len(over)}): need chains or bigger panels: "
      + ", ".join(over))

# Per user group
print("\n== PER USER GROUP ==")
for i, line in enumerate(manual_raw, 1):
    feats = [f for f, d in rows.items() if d['group'] == i]
    feats.sort(key=lambda f: rows[f]['mm'])
    detail = ", ".join(f"{f}:{rows[f]['mm']}mm/{rows[f]['leds']}L" for f in feats)
    print(f"G{i} ({len(feats)} feathers): {detail}")
