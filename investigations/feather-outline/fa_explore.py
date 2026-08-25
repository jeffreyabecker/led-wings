import sqlite3

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

print("=== Distinct FeatherType ===")
for (t, n) in c.execute("SELECT FeatherType, COUNT(*) FROM Feathers GROUP BY FeatherType ORDER BY COUNT(*) DESC"):
    print(f"  {t!r:30} {n}")

print("\n=== Distinct OrderName ===")
for (o, n) in c.execute("SELECT OrderName, COUNT(*) FROM Feathers GROUP BY OrderName ORDER BY OrderName"):
    print(f"  {o!r:30} {n}")

print("\n=== Distinct Family in Accipitriformes ===")
for (f, n) in c.execute("SELECT Family, COUNT(*) FROM Feathers WHERE OrderName='Accipitriformes' GROUP BY Family ORDER BY Family"):
    print(f"  {f!r:30} {n}")

print("\n=== Distinct FeatherType in Accipitriformes ===")
for (t, n) in c.execute("SELECT FeatherType, COUNT(*) FROM Feathers WHERE OrderName='Accipitriformes' GROUP BY FeatherType ORDER BY COUNT(*) DESC"):
    print(f"  {t!r:30} {n}")

print("\n=== Sample rows (Accipitriformes) ===")
for r in c.execute("SELECT FileName, Family, CommonName, LatinName, FeatherType, Sex, Age, NbrMarkedFeathers FROM Feathers WHERE OrderName='Accipitriformes' LIMIT 20"):
    print("  ", r)
