"""
attendance.py
─────────────────────────────────────
Attendance Logging using SQLite
Prevents duplicate entries within the same session
"""

import sqlite3
import os
from datetime import datetime, date

DB_FILE = "database/attendance.db"


def init_db():
    """Create attendance table if it doesn't exist."""
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no     TEXT    NOT NULL,
            name        TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            time        TEXT    NOT NULL,
            confidence  REAL,
            UNIQUE(roll_no, date)   -- one entry per student per day
        )
    """)
    conn.commit()
    conn.close()


def mark_attendance(name, roll_no, confidence=None):
    """
    Mark attendance for a student.

    Prevents duplicate entries for the same day.

    Args:
        name       : student display name
        roll_no    : student roll number
        confidence : recognition distance (optional)

    Returns:
        'marked'     if successfully marked
        'duplicate'  if already marked today
        'error'      on failure
    """
    init_db()

    today     = date.today().isoformat()             # e.g. 2024-03-15
    now       = datetime.now().strftime("%H:%M:%S")  # e.g. 14:32:01

    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("""
            INSERT INTO attendance (roll_no, name, date, time, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (roll_no, name, today, now, confidence))
        conn.commit()
        print(f"  [SUCCESS] Attendance marked — {name} ({roll_no}) at {now}")
        return "marked"

    except sqlite3.IntegrityError:
        # Duplicate — already marked today
        return "duplicate"

    except Exception as e:
        print("  [ERROR] DB error occurred.")
        return "error"

    finally:
        conn.close()


def get_today_attendance():
    """
    Fetch all attendance records for today.

    Returns:
        list of dicts: roll_no, name, date, time, confidence
    """
    init_db()
    today = date.today().isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("""
        SELECT roll_no, name, date, time, confidence
        FROM attendance
        WHERE date = ?
        ORDER BY time ASC
    """, (today,))

    rows = [
        {"roll_no": r[0], "name": r[1], "date": r[2],
         "time": r[3], "confidence": r[4]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return rows


def get_attendance_by_date(query_date):
    """Fetch attendance for a specific date (YYYY-MM-DD)."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("""
        SELECT roll_no, name, date, time, confidence
        FROM attendance
        WHERE date = ?
        ORDER BY time ASC
    """, (query_date,))

    rows = [
        {"roll_no": r[0], "name": r[1], "date": r[2],
         "time": r[3], "confidence": r[4]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return rows


def get_student_attendance(roll_no):
    """Fetch complete attendance history for one student."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("""
        SELECT roll_no, name, date, time, confidence
        FROM attendance
        WHERE roll_no = ?
        ORDER BY date DESC
    """, (roll_no,))

    rows = [
        {"roll_no": r[0], "name": r[1], "date": r[2],
         "time": r[3], "confidence": r[4]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return rows


def get_attendance_summary():
    """
    Summary: total days present per student across all records.

    Returns:
        list of dicts: roll_no, name, days_present
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("""
        SELECT roll_no, name, COUNT(*) as days_present
        FROM attendance
        GROUP BY roll_no
        ORDER BY days_present DESC
    """)
    rows = [
        {"roll_no": r[0], "name": r[1], "days_present": r[2]}
        for r in cursor.fetchall()
    ]
    conn.close()
    return rows


def export_to_csv(output_path="attendance_export.csv"):
    """Export all attendance records to CSV."""
    import csv
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute("""
        SELECT roll_no, name, date, time, confidence
        FROM attendance
        ORDER BY date DESC, time ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Roll No", "Name", "Date", "Time", "Confidence"])
        writer.writerows(rows)

    print(f"[SUCCESS] Exported {len(rows)} records to {output_path}")
    return output_path


if __name__ == "__main__":
    # Quick test
    init_db()
    print("Today's attendance:")
    for r in get_today_attendance():
        print(f"  {r['roll_no']} | {r['name']} | {r['time']}")
