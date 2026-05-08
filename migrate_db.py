"""
migrate_db.py — One-time migration from old schema to new 4-table schema.
Drops the old attendance table and recreates it with session_id.
Old attendance data is preserved as a fallback session.
"""
import sqlite3
import os

DB = "database/attendance.db"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = OFF")

# Check if old schema (has 'name' column, no session_id)
cols = [c[1] for c in conn.execute("PRAGMA table_info(attendance)").fetchall()]
print("Current attendance columns:", cols)

if "session_id" not in cols:
    print("Migrating attendance table...")

    # Backup old data
    old_rows = conn.execute(
        "SELECT roll_no, name, date, time, confidence FROM attendance"
    ).fetchall()
    print(f"  Backed up {len(old_rows)} old attendance records")

    # Drop old table
    conn.execute("DROP TABLE attendance")

    # Create new table
    conn.execute("""
        CREATE TABLE attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no     TEXT NOT NULL,
            session_id  INTEGER NOT NULL,
            date        TEXT NOT NULL,
            time        TEXT NOT NULL,
            confidence  REAL,
            UNIQUE(roll_no, session_id),
            FOREIGN KEY (roll_no)    REFERENCES students(roll_no),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    print("  New attendance table created")

    # Migrate old data: create one legacy session per unique date
    if old_rows:
        # Ensure a legacy subject exists
        conn.execute("""
            INSERT OR IGNORE INTO subjects (id, code, name, department, credits)
            VALUES (1, 'LEGACY', 'Legacy Import', '', 3)
        """)
        # Create a session for each unique date in old data
        dates = list({r[2] for r in old_rows})
        date_session_map = {}
        for d in dates:
            cur = conn.execute(
                "INSERT INTO sessions (subject_id, date, start_time, faculty, notes) "
                "VALUES (1, ?, '00:00:00', 'Migrated', 'Auto-migrated from old schema')",
                (d,)
            )
            date_session_map[d] = cur.lastrowid

        # Insert old records into new table
        migrated = 0
        for roll_no, name, date_, time_, conf in old_rows:
            sid = date_session_map.get(date_)
            if sid:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO attendance "
                        "(roll_no, session_id, date, time, confidence) VALUES (?,?,?,?,?)",
                        (roll_no, sid, date_, time_, conf)
                    )
                    migrated += 1
                except Exception as e:
                    print(f"  Skipped {roll_no}/{date_}: {e}")
        print(f"  Migrated {migrated} records into new schema")

    conn.commit()
    print("Migration complete!")
else:
    print("Schema already up to date — no migration needed.")

conn.execute("PRAGMA foreign_keys = ON")
conn.close()

# Verify
conn2 = sqlite3.connect(DB)
cols2 = [c[1] for c in conn2.execute("PRAGMA table_info(attendance)").fetchall()]
print("Final attendance columns:", cols2)
conn2.close()
