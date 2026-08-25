import sqlite3, re

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

# Any FileName or Notes mentioning tertial/alula/median/lesser/marginal/back/mantle/contour/down
pat = re.compile(r'(terti|alula|median|lesser|marginal|mantle|contour|down|back.?covert|neck|rump|crown)', re.I)
print("=== FileName/Notes with body/covert/tertial/alula hints (whole DB) ===")
rows = c.execute("SELECT DISTINCT FileName, FeatherType, Notes FROM Feathers").fetchall()
for fn, ft, notes in rows:
    if pat.search(fn or '') or pat.search(notes or ''):
        print(f"  {fn:40} type={ft:15} notes={notes}")

print("\n=== ALL 'Other' + 'Coverts' rows with feather counts ===")
for r in c.execute("SELECT FileName, OrderName, CommonName, LatinName, FeatherType, NbrMarkedFeathers, Notes FROM Feathers WHERE FeatherType IN ('Other','Coverts') ORDER BY OrderName, FileName"):
    print("  ", r)

# Count how many DISTINCT species have each type
print("\n=== species count per FeatherType (whole DB) ===")
for r in c.execute("SELECT FeatherType, COUNT(DISTINCT LatinName) FROM Feathers GROUP BY FeatherType ORDER BY 2 DESC"):
    print("  ", r)
