"""
config.py — VisionTrack Central Configuration
All paths, thresholds, and constants live here.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR  = os.path.join(BASE_DIR, "database")
FACES_DIR     = os.path.join(BASE_DIR, "faces")
DB_FILE       = os.path.join(DATABASE_DIR, "attendance.db")   # local fallback
FACE_DB_PATH  = os.path.join(DATABASE_DIR, "embeddings.pkl")  # local fallback
EXPORT_DIR    = os.path.join(BASE_DIR, "exports")

# ── Firebase ────────────────────────────────────────────────────────────────────
# 1. Go to console.firebase.google.com → your project (VisionTrack)
# 2. Gear icon → Project Settings → Service Accounts tab
# 3. Click "Generate new private key" → save as serviceAccountKey.json here
# NOTE: Firebase Storage NOT required — Firestore free tier is enough.
FIREBASE_KEY_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")
USE_FIREBASE      = True   # Set False to use local SQLite instead

# ── Face Recognition ───────────────────────────────────────────────────────────
MODEL_NAME    = "ArcFace"
THRESHOLD     = 0.40          # cosine distance — lower = stricter
FRAME_SKIP    = 5             # run DeepFace every Nth frame
COOLDOWN_SEC  = 10            # seconds before re-trying same face
NUM_CAPTURES  = 10            # photos captured during enrollment
ANTI_SPOOFING = False         # Set to True for liveness checks (can cause false positives)

# ── Attendance Policy ──────────────────────────────────────────────────────────
ATTENDANCE_THRESHOLD = 75     # % below which student is flagged

# ── College Metadata ───────────────────────────────────────────────────────────
COLLEGE_NAME  = "VisionTrack University"
DEPARTMENTS   = ["CSE", "ECE", "ME", "CE", "IT", "MBA", "EEE", "CIVIL"]
YEARS         = ["1st Year", "2nd Year", "3rd Year", "4th Year",
                 "PG 1st Year", "PG 2nd Year"]
