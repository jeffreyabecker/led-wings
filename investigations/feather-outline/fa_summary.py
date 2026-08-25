import sqlite3

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

# Clean feather-type distribution (trim whitespace, fold typos)
print("=== FeatherType (normalized) distribution ===")
d = {}
for (t,) in c.execute("SELECT FeatherType FROM Feathers"):
    k = (t or '').strip()
    if k in ('Rectrices', 'Rectirces'): k = 'Tail (Rectrices)'
    elif k in ('Remiges',): k = 'Wing (Remiges)'
    elif k in ('Secondaries', 'Secondary'): k = 'Secondaries'
    elif k in ('Primaries',): k = 'Primaries'
    d[k] = d.get(k, 0) + 1
for k in sorted(d, key=lambda x: -d[x]):
    print(f"  {k:22} {d[k]}")

print("\n=== The ONLY non-flight/tail feathers in the ENTIRE database ===")
for r in c.execute("SELECT FileName, OrderName, CommonName, LatinName, FeatherType, Notes FROM Feathers WHERE TRIM(FeatherType) IN ('Other','Coverts') ORDER BY OrderName"):
    print("  ", r)

print("\n=== Accipitriformes: distinct species per type ===")
for r in c.execute("SELECT TRIM(FeatherType), COUNT(DISTINCT LatinName) FROM Feathers WHERE OrderName='Accipitriformes' GROUP BY TRIM(FeatherType) ORDER BY 2 DESC"):
    print("  ", r)
