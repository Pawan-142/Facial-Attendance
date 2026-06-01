"""
seed_multiple_subjects.py — Multi-Subject & Historical Attendance Database Seeder
Supports both Firebase Firestore and Local SQLite.
"""
import os
import random
from datetime import datetime, date, timedelta
import config

# Force initialization of DB layers
if config.USE_FIREBASE:
    from firebase_client import get_db
    db = get_db()
    print("[Seeder] Connected to Firebase Firestore.")
else:
    import sqlite3
    print(f"[Seeder] Using local SQLite database at {config.DB_FILE}")

# ── Mock Data Definitions ──────────────────────────────────────────────────────
DEPARTMENTS = ["CSE", "ECE", "ME", "CIVIL", "MBA"]
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

SUBJECTS_DATA = [
    {"code": "CS101", "name": "Introduction to Programming", "dept": "CSE", "credits": 3},
    {"code": "EE205", "name": "Digital Logic Design", "dept": "ECE", "credits": 4},
    {"code": "MA301", "name": "Linear Algebra", "dept": "CSE", "credits": 3},
    {"code": "CS202", "name": "Data Structures & Algorithms", "dept": "CSE", "credits": 4},
    {"code": "EC102", "name": "Electronic Devices & Circuits", "dept": "ECE", "credits": 3},
    {"code": "MBA101", "name": "Principles of Management", "dept": "MBA", "credits": 3},
]

STUDENTS_DATA = [
    {"roll_no": "2024CS01", "name": "Alex Student", "email": "alex@college.edu", "dept": "CSE", "year": "1st Year"},
    {"roll_no": "2024CS02", "name": "Sarah Jenkins", "email": "sarah@college.edu", "dept": "CSE", "year": "1st Year"},
    {"roll_no": "2024CS03", "name": "Dwight Schrute", "email": "dwight@college.edu", "dept": "CSE", "year": "2nd Year"},
    {"roll_no": "2024EE01", "name": "Michael Scott", "email": "michael@college.edu", "dept": "ECE", "year": "2nd Year"},
    {"roll_no": "2024MA01", "name": "Jim Halpert", "email": "jim@college.edu", "dept": "ME", "year": "3rd Year"},
    {"roll_no": "2024EE02", "name": "Pam Beesly", "email": "pam@college.edu", "dept": "ECE", "year": "2nd Year"},
    {"roll_no": "123", "name": "ABC", "email": "abc@college.edu", "dept": "CSE", "year": "4th Year"},
]

FACULTY_MEMBERS = ["Dr. Smith", "Dr. Ramesh Kumar", "Prof. Angela Martin", "Dr. Brown", "Prof. Jim Halpert"]

# Generate dates for the last 7 days
today = date.today()
DATES_LIST = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

# ── Clean & Seed ────────────────────────────────────────────────────────────────
def seed_firebase():
    print("[Firebase] Cleaning existing records...")
    # Clean collections
    for collection in ["subjects", "sessions", "attendance", "students"]:
        docs = db.collection(collection).stream()
        for d in docs:
            d.reference.delete()
    print("[Firebase] Clean completed.")

    # 1. Seed Students
    print("[Firebase] Seeding students...")
    for s in STUDENTS_DATA:
        db.collection("students").document(s["roll_no"]).set({
            "roll_no": s["roll_no"],
            "name": s["name"],
            "email": s["email"],
            "department": s["dept"],
            "year": s["year"],
            "enrolled_at": datetime.now().isoformat()
        })

    # 2. Seed Subjects
    print("[Firebase] Seeding subjects...")
    subject_ids = {}
    for sub in SUBJECTS_DATA:
        doc_ref = db.collection("subjects").document()
        doc_ref.set({
            "code": sub["code"],
            "name": sub["name"],
            "department": sub["dept"],
            "credits": sub["credits"]
        })
        subject_ids[sub["code"]] = doc_ref.id

    # 3. Seed Sessions and Attendance
    print("[Firebase] Seeding historical sessions and attendance...")
    for code, sub_id in subject_ids.items():
        # For each subject, create 3-5 sessions on different dates
        num_sessions = random.randint(3, 5)
        chosen_dates = random.sample(DATES_LIST, num_sessions)
        
        for d in chosen_dates:
            start_time = f"{random.randint(9, 15):02d}:{random.choice([0, 30]):02d}:00"
            faculty = random.choice(FACULTY_MEMBERS)
            
            # Create session
            session_ref = db.collection("sessions").document()
            session_ref.set({
                "subject_id": sub_id,
                "date": d,
                "start_time": start_time,
                "faculty": faculty,
                "notes": f"Lecture on {code} topics"
            })
            session_id = session_ref.id
            
            # Mark attendance for a random subset of students
            for student in STUDENTS_DATA:
                # Every student has an 80% chance of being present to make analytics look natural
                if random.random() < 0.80:
                    time_in = f"{start_time[:2]}:{random.randint(0, 10):02d}:{random.randint(0, 59):02d}"
                    confidence = round(random.uniform(0.12, 0.39), 4) # Cosine distance (lower = better)
                    
                    doc_id = f"{student['roll_no']}__{sub_id}__{d}"
                    db.collection("attendance").document(doc_id).set({
                        "roll_no": student["roll_no"],
                        "session_id": session_id,
                        "date": d,
                        "time": time_in,
                        "confidence": confidence
                    })

    print("[Firebase] Database successfully seeded with comprehensive multi-subject data!")

def seed_sqlite():
    os.makedirs(config.DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.cursor()

    print("[SQLite] Cleaning and recreating tables...")
    cursor.executescript("""
        DROP TABLE IF EXISTS attendance;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS students;

        CREATE TABLE students (
            roll_no     TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT DEFAULT '',
            department  TEXT DEFAULT '',
            year        TEXT DEFAULT '',
            enrolled_at TEXT NOT NULL
        );

        CREATE TABLE subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            department  TEXT DEFAULT '',
            credits     INTEGER DEFAULT 3
        );

        CREATE TABLE sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id  INTEGER NOT NULL,
            date        TEXT NOT NULL,
            start_time  TEXT NOT NULL,
            faculty     TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        );

        CREATE TABLE attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no     TEXT NOT NULL,
            session_id  INTEGER NOT NULL,
            date        TEXT NOT NULL,
            time        TEXT NOT NULL,
            confidence  REAL,
            UNIQUE(roll_no, session_id),
            FOREIGN KEY (roll_no)     REFERENCES students(roll_no),
            FOREIGN KEY (session_id)  REFERENCES sessions(id)
        );
    """)
    conn.commit()

    # 1. Seed Students
    print("[SQLite] Seeding students...")
    for s in STUDENTS_DATA:
        cursor.execute(
            "INSERT INTO students (roll_no, name, email, department, year, enrolled_at) VALUES (?, ?, ?, ?, ?, ?)",
            (s["roll_no"], s["name"], s["email"], s["dept"], s["year"], datetime.now().isoformat())
        )
    
    # 2. Seed Subjects
    print("[SQLite] Seeding subjects...")
    subject_ids = {}
    for sub in SUBJECTS_DATA:
        cursor.execute(
            "INSERT INTO subjects (code, name, department, credits) VALUES (?, ?, ?, ?)",
            (sub["code"], sub["name"], sub["dept"], sub["credits"])
        )
        subject_ids[sub["code"]] = cursor.lastrowid
    conn.commit()

    # 3. Seed Sessions and Attendance
    print("[SQLite] Seeding historical sessions and attendance...")
    for code, sub_id in subject_ids.items():
        num_sessions = random.randint(3, 5)
        chosen_dates = random.sample(DATES_LIST, num_sessions)
        
        for d in chosen_dates:
            start_time = f"{random.randint(9, 15):02d}:{random.choice([0, 30]):02d}:00"
            faculty = random.choice(FACULTY_MEMBERS)
            
            cursor.execute(
                "INSERT INTO sessions (subject_id, date, start_time, faculty, notes) VALUES (?, ?, ?, ?, ?)",
                (sub_id, d, start_time, faculty, f"Lecture on {code} topics")
            )
            session_id = cursor.lastrowid
            
            for student in STUDENTS_DATA:
                if random.random() < 0.80:
                    time_in = f"{start_time[:2]}:{random.randint(0, 10):02d}:{random.randint(0, 59):02d}"
                    confidence = round(random.uniform(0.12, 0.39), 4)
                    
                    try:
                        cursor.execute(
                            "INSERT INTO attendance (roll_no, session_id, date, time, confidence) VALUES (?, ?, ?, ?, ?)",
                            (student["roll_no"], session_id, d, time_in, confidence)
                        )
                    except sqlite3.IntegrityError:
                        pass # Unique constraint safety
    
    conn.commit()
    conn.close()
    print("[SQLite] Database successfully seeded with comprehensive multi-subject data!")

# ── Main Entry ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if config.USE_FIREBASE:
        seed_firebase()
    else:
        seed_sqlite()
