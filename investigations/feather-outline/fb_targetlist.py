"""Build a ranked Featherbase target list for the feather regions the USFWS
Atlas cannot supply (coverts, alula, scapulars, tertials, body/mantle/back).

Featherbase only exposes primary-vs-secondary grouping publicly, so this list
ranks species by specimen count -- more specimens = more individual feathers to
visually sort for the missing regions. Reads already-fetched order/family HTML.
"""
import re, html, os, json

TMP = r"C:\Users\jeffr\AppData\Local\Temp"
PAGES = [
    ("Accipitriformes",            os.path.join(TMP, "fb_accip.html"), "order"),
    ("Falconiformes",              os.path.join(TMP, "fb_falc.html"),  "order"),
    ("Corvidae (Passeriformes)",   os.path.join(TMP, "fb_corvidae.html"), "family"),
]

def parse(path):
    with open(path, encoding="utf-8") as fh:
        h = fh.read()
    # Each species row: <tr> ... <a href="/en/species/genus/species"> ... <td data-sort-value="N">
    rows = []
    # split by <tr> blocks
    for tr in re.split(r'<tr\b', h, flags=re.I):
        m_link = re.search(r'href="(/en/species/([a-z]+)/([a-z]+))"', tr, re.I)
        if not m_link:
            continue
        url = m_link.group(1)
        latin = m_link.group(2).capitalize() + " " + m_link.group(3)
        m_count = re.search(r'data-sort-value="(\d+)"', tr, re.I)
        n = int(m_count.group(1)) if m_count else 0
        rows.append({"url": url, "latin": latin, "n": n})
    return rows

out = []
seen = set()
for group, path, kind in PAGES:
    if not os.path.exists(path):
        print(f"MISSING {path}")
        continue
    for r in parse(path):
        if r["latin"] in seen:
            continue
        seen.add(r["latin"])
        out.append({"group": group, "latin": r["latin"], "n": r["n"], "url": r["url"]})

out.sort(key=lambda r: -r["n"])

print(f"total species: {len(out)}")
for r in out:
    print(f"{r['n']:3d}  {r['latin']:32} {r['group']:24} https://www.featherbase.info{r['url']}")

# write to repo
dst = r"C:\ode\wings-pcbs\investigations\feather-outline\featherbase_targetlist.md"
lines = [
    "# Featherbase target list — regions the USFWS Atlas can't supply",
    "",
    "Ranked by specimen count (more specimens = more individual feather scans to",
    "visually sort). Featherbase only exposes primary/secondary grouping publicly,",
    "so coverts / alula / scapulars / tertials / body-mantle-back must be picked by",
    "eye from each species' image grid. URLs are the species scan pages.",
    "",
    "| Specimens | Species | Group | Page |",
    "|-----------|---------|-------|------|",
]
for r in out:
    lines.append(f"| {r['n']} | {r['latin']} | {r['group']} | https://www.featherbase.info{r['url']} |")
open(dst, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"\nwrote {dst}")
