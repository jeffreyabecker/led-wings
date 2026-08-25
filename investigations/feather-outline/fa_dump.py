import sqlite3

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

def dump(order, label):
    print(f"\n===== {label} ({order}) =====")
    rows = c.execute(
        "SELECT FileName, CommonName, LatinName, FeatherType, Sex, Age, NbrMarkedFeathers "
        "FROM Feathers WHERE OrderName=? ORDER BY Family, LatinName, FeatherType, FileName",
        (order,),
    ).fetchall()
    print(f"total rows: {len(rows)}")
    for r in rows:
        print("  ", r)

dump('Accipitriformes', 'ACCIPITRIFORMES')
dump('Falconiformes', 'FALCONIFORMES')

# Passeriformes Corvidae family
print("\n===== PASSERIFORMES / Corvidae =====")
for r in c.execute("SELECT FileName, CommonName, LatinName, FeatherType, Sex, Age, NbrMarkedFeathers FROM Feathers WHERE OrderName='Passeriformes' AND Family='Corvidae' ORDER BY LatinName, FeatherType"):
    print("  ", r)

# all families in Passeriformes
print("\n===== Passeriformes families =====")
for r in c.execute("SELECT Family, COUNT(*) FROM Feathers WHERE OrderName='Passeriformes' GROUP BY Family ORDER BY Family"):
    print("  ", r)
