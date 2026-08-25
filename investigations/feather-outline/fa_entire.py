import sqlite3

DB = r"C:\ode\wings-pcbs\investigations\feather-outline\data\featheratlas.sqlite"
c = sqlite3.connect(DB)

# 1) Confirm the Feathers table columns (any hidden region field?)
cols = [r[1] for r in c.execute("PRAGMA table_info(Feathers)")]
print("Feathers columns:", cols)

# 2) Distinct FeatherType across the ENTIRE database (no WHERE clause)
print("\nDistinct FeatherType (entire DB, raw + trimmed):")
for (t, n) in c.execute("SELECT FeatherType, COUNT(*) FROM Feathers GROUP BY FeatherType ORDER BY 2 DESC"):
    print(f"  raw={t!r:24} n={n}")

# 3) Everything that is NOT a flight/tail feather, across ENTIRE DB
print("\nRows whose FeatherType is not Primaries/Secondaries/Rectrices/Remiges (entire DB):")
q = """
SELECT FileName, OrderName, Family, CommonName, TRIM(FeatherType) AS ft, Notes
FROM Feathers
WHERE TRIM(FeatherType) NOT IN ('Primaries','Secondaries','Rectrices','Remiges')
ORDER BY OrderName, FileName
"""
rows = c.execute(q).fetchall()
print(f"  total: {len(rows)}")
for r in rows:
    print("  ", r)

# 4) Filename-level hunt for the 5 missing categories, EXACT word boundaries
import re
print("\nFilename contains alula/tertial/covert/scapular/axillar/humeral/body (entire DB):")
pat = re.compile(r'(alula|terti|covert|scapular|axillar|humeral|\bbody\b)', re.I)
n = 0
for (fn,) in c.execute("SELECT DISTINCT FileName FROM Feathers"):
    if pat.search(fn or ''):
        print("  ", fn)
        n += 1
print(f"  total filename hits: {n}")

# 5) Total feather count
print("\nTotal rows in Feathers:", c.execute("SELECT COUNT(*) FROM Feathers").fetchone()[0])
print("Total distinct species:", c.execute("SELECT COUNT(DISTINCT LatinName) FROM Feathers").fetchone()[0])
print("Total orders:", c.execute("SELECT COUNT(DISTINCT OrderName) FROM Feathers").fetchone()[0])
