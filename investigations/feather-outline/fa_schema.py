import sqlite3

DB = r"data\featheratlas.sqlite"
c = sqlite3.connect(DB)

print("=== TABLES ===")
for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", name)

print("\n=== SCHEMA ===")
for (sql,) in c.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"):
    if sql:
        print(sql, "\n")
