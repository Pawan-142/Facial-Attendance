import sqlite3, os

db = "database/attendance.db"
print("DB exists:", os.path.exists(db))

if os.path.exists(db):
    conn = sqlite3.connect(db)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Tables:", [t[0] for t in tables])
    for t in tables:
        cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
        print(f"  {t[0]}:", [c[1] for c in cols])
    conn.close()
else:
    print("No DB found - init_db will create fresh one")
    from models import init_db
    init_db()
    conn = sqlite3.connect(db)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("Created tables:", [t[0] for t in tables])
    for t in tables:
        cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
        print(f"  {t[0]}:", [c[1] for c in cols])
    conn.close()
