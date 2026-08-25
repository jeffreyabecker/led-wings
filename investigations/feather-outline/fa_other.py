import sqlite3

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

print("=== 'Other' rows (all orders) ===")
for r in c.execute("SELECT FileName, OrderName, Family, CommonName, LatinName, Sex, Age, Notes FROM Feathers WHERE FeatherType='Other'"):
    print("  ", r)

print("\n=== 'Coverts' / 'Remiges' / 'Remiges ' rows (all orders) ===")
for r in c.execute("SELECT FileName, OrderName, Family, CommonName, LatinName, FeatherType FROM Feathers WHERE FeatherType IN ('Coverts','Remiges','Remiges ') ORDER BY OrderName"):
    print("  ", r)

print("\n=== FileName patterns hinting body/covert/alula/scapular (all orders) ===")
import re
rows = c.execute("SELECT DISTINCT FileName FROM Feathers").fetchall()
pat = re.compile(r'(cover|covert|alula|scapular|body|breast|belly|flank|throat|nape|crown|mantle|down|contour)', re.I)
for (fn,) in rows:
    if pat.search(fn):
        print("  ", fn)
