import sqlite3, re

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

# Broad body-part vocabulary to catch anything non-flight-feather
terms = re.compile(
    r'(terti|alula|covert|scapular|axillar|humeral|body|mantle|nape|crown|'
    r'breast|belly|flank|throat|neck|rump|down|contour|marginal|lesser|median|'
    r'greater|underwing|back|shoulder)',
    re.I,
)

print("=== Every row whose FileName OR Notes OR FeatherType mentions a body part (whole DB) ===")
rows = c.execute(
    "SELECT FileName, OrderName, Family, CommonName, LatinName, FeatherType, Sex, Age, Notes "
    "FROM Feathers"
).fetchall()
hits = []
for fn, order, fam, common, latin, ft, sex, age, notes in rows:
    hay = " ".join(str(x) for x in (fn, ft, notes) if x)
    if terms.search(hay):
        hits.append((fn, order, fam, common, latin, ft, sex, age, notes))

print(f"total hits: {len(hits)}")
for h in sorted(hits, key=lambda h: (h[2] or '', h[0])):
    print(f"  {h[0]:36} {h[1]:20} {h[2]:16} {h[3]:22} {h[5]:12} {h[6] or '':6} {h[7] or '':12} | {h[8] or ''}")

print("\n=== Notes that are non-empty (all rows) ===")
n = 0
for (fn, ft, notes) in c.execute("SELECT FileName, FeatherType, Notes FROM Feathers WHERE Notes IS NOT NULL AND TRIM(Notes) != ''"):
    print(f"  {fn:36} {ft:14} {notes}")
    n += 1
print(f"non-empty notes: {n}")
