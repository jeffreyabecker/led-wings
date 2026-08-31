"""Diff a manually-grouped feather list (with ranges like P1-5, MC1-5) against feather-record.csv."""
import csv
import re
from collections import Counter

manual_raw = [
    "pc4-6",
    "PC1,A4,MC1-5,U2-7,SC9",
    "U1,U8, L1-6",
    "P1-5,P8-10",
    "P7,S1-9",
    "A1-3,PC2-3,SC2-8,Sc10, S10",
]


def expand(item):
    """Expand 'PC1-5' -> [PC1..PC5]; pass through plain 'PC1'."""
    m = re.match(r"^([A-Za-z]+)(\d+)-(\d+)$", item.strip())
    if not m:
        return [item.strip()]
    prefix, lo, hi = m.group(1), int(m.group(2)), int(m.group(3))
    return [f"{prefix}{i}" for i in range(lo, hi + 1)]


groups = []
for line in manual_raw:
    feats = []
    for item in line.split(","):
        if item.strip():
            feats.extend(expand(item))
    groups.append(feats)

listed = [f for g in groups for f in g]
listed = [f.upper() for f in listed]

with open(r'mechanical\templates\feather-record.csv', newline='', encoding='utf-8') as f:
    csv_feathers = [r['feather'] for r in csv.DictReader(f)]

listed_counter = Counter(listed)
csv_counter = Counter(csv_feathers)

print("== Duplicates in manual list ==")
for f, n in listed_counter.items():
    if n > 1:
        print(f"  {f}: listed {n}x")

print("\n== Feathers in CSV but MISSING from manual list ==")
missing = [f for f in csv_feathers if listed_counter[f] == 0]
for f in missing:
    print(f"  {f}")

print("\n== Listed but NOT in CSV (typos?) ==")
unknown = [f for f in listed_counter if f not in csv_counter]
for f in unknown:
    print(f"  {f}")

print(f"\n== Totals ==")
print(f"  CSV feathers:   {len(csv_feathers)}")
print(f"  Listed unique:  {len(listed_counter)}")
print(f"  Missing:        {len(missing)}")

print("\n== Manual groups (normalized) ==")
for i, g in enumerate(groups, 1):
    print(f"  G{i}: {', '.join(sorted(set(f.upper() for f in g)))}  ({len(set(g))} unique)")
