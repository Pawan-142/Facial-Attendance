"""
fastapi_app.py — VisionTrack FastAPI Backend (Full Featured)
"""
import cv2
import time
import threading
import io
import queue
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Response, Query, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from auth import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from firebase_client import get_db
import pandas as pd

# Adapter so enroll.py can stream frames to the React browser
class FrameQueue:
    """Acts like a Streamlit stframe but puts JPEG bytes into a queue."""
    def __init__(self):
        self.q = queue.Queue(maxsize=4)
        self.done = False
        self._last_error = None

    def image(self, frame_rgb):
        try:
            import numpy as np
            frame_bgr = cv2.cvtColor(np.array(frame_rgb), cv2.COLOR_RGB2BGR)
            ret, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                try:
                    self.q.put_nowait(buf.tobytes())
                except queue.Full:
                    try: self.q.get_nowait()   # drop oldest, add newest
                    except: pass
                    try: self.q.put_nowait(buf.tobytes())
                    except: pass
        except Exception as ex:
            print(f"[FrameQueue] {ex}")

    def error(self, msg):
        self._last_error = msg

    def empty(self):
        pass

    def close(self):
        self.done = True

from recognize import FrameSkipRecognizer, draw_recognition_results
from face_db import load_face_db, delete_face_entry
from firebase_db import (
    get_all_students, get_today_attendance, get_attendance_by_date,
    add_subject, get_all_subjects, delete_subject,
    create_session, get_all_sessions,
    add_student, update_student, delete_student_record,
    mark_attendance, get_student_history, get_attendance_summary,
    get_daily_trend, export_to_excel,
)
from enroll import enroll_student
from config import COOLDOWN_SEC, ATTENDANCE_THRESHOLD

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic Models ────────────────────────────────────────────
class SubjectModel(BaseModel):
    code: str
    name: str
    dept: str

class EnrollModel(BaseModel):
    roll_no: str
    name: str
    email: str = ""
    dept: str = ""
    year: str = ""
    force: bool = False

class UpdateStudentModel(BaseModel):
    name: str
    email: str = ""
    dept: str = ""
    year: str = ""

class SessionModel(BaseModel):
    subject_id: str
    faculty: str = ""

class LoginRequest(BaseModel):
    username: str
    password: str

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ── Thread-safe State ──────────────────────────────────────────
_lock = threading.Lock()
_state = {
    "cam": None,
    "db": load_face_db(),
    "recognizer": FrameSkipRecognizer(),
    "last_marked": {},
    "active_session_id": None,
    "enrollment_fq": None,   # active FrameQueue during enrollment
}

def _get(key):
    with _lock:
        return _state[key]

def _set(key, val):
    with _lock:
        _state[key] = val

# ── Camera Stream ──────────────────────────────────────────────
def generate_frames():
    with _lock:
        if _state["cam"] is None or not _state["cam"].isOpened():
            _state["cam"] = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    try:
        while True:
            with _lock:
                cam = _state["cam"]
                success, frame = cam.read() if cam else (False, None)
                session_id = _state["active_session_id"]
                db = _state["db"]
                recognizer = _state["recognizer"]
                last_marked = _state["last_marked"]

            if not success or frame is None:
                time.sleep(0.05)
                continue

            if session_id is not None:
                results = recognizer.process(frame, db)
                now = time.time()
                for r in results:
                    roll_no = r.get("roll_no")
                    if roll_no and r.get("is_real", True):
                        in_cooldown = now - last_marked.get(roll_no, 0) < COOLDOWN_SEC
                        if in_cooldown:
                            r["status"] = "cooldown"
                        else:
                            result = mark_attendance(
                                roll_no=roll_no,
                                session_id=session_id,
                                confidence=r.get("distance"),
                            )
                            print(f"[ATTENDANCE] {roll_no} -> {result}")
                            r["status"] = result  # 'marked' or 'duplicate'
                            with _lock:
                                _state["last_marked"][roll_no] = now
                frame = draw_recognition_results(frame, results)
            else:
                cv2.putText(frame, "Standby - Start a Session to begin",
                            (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 120, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buffer.tobytes() + b'\r\n')
    finally:
        with _lock:
            cam = _state["cam"]
            if cam is not None and cam.isOpened():
                cam.release()
                print("[Camera] Hardware released via stream disconnect.")
            _state["cam"] = None

# ── Endpoints ──────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "status": "online",
        "name": "VisionTrack Attendance System API",
        "documentation": "http://localhost:8000/docs",
        "frontend": "http://localhost:5173"
    }

@app.post("/api/auth/login")
def login(req: LoginRequest):
    db = get_db()
    users_ref = db.collection('users')
    docs = users_ref.where('username', '==', req.username).limit(1).stream()
    user_doc = None
    for doc in docs:
        user_doc = doc.to_dict()
        break
    
    if not user_doc or not verify_password(req.password, user_doc.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token_data = {
        "sub": user_doc["username"],
        "role": user_doc["role"],
        "name": user_doc.get("name", ""),
        "reference_id": user_doc.get("reference_id", "")
    }
    access_token = create_access_token(data=token_data)
    return {"status": "ok", "access_token": access_token, "user": token_data}

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/enrollment_feed")
def enrollment_feed():
    """Streams enrollment frames; waits up to 8s for enrollment to begin."""
    def gen():
        # Wait for the enrollment thread to open the camera and set fq
        fq = None
        for _ in range(80):   # 80 x 0.1s = 8 seconds max wait
            fq = _get("enrollment_fq")
            if fq is not None:
                break
            time.sleep(0.1)

        if fq is None:
            return  # enrollment never started

        while True:
            try:
                jpg = fq.q.get(timeout=0.5)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                       + jpg + b'\r\n')
            except queue.Empty:
                if fq.done:
                    break
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/stats")
def get_stats(user: dict = Depends(get_current_user)):
    from collections import defaultdict
    from datetime import datetime

    students      = get_all_students()
    today_records = get_today_attendance()
    
    student_analytics = None

    # Filter for student role
    if user.get("role") == "student":
        roll_no = user.get("reference_id")
        today_records = [r for r in today_records if r.get("roll_no") == roll_no]
        students = [s for s in students if s.get("roll_no") == roll_no]
        
        # Calculate deep analytics for the student
        all_sessions = get_all_sessions()
        attended_logs = get_student_history(roll_no)
        attended_session_ids = {log.get("session_id") for log in attended_logs}
        
        missed_sessions_raw = [s for s in all_sessions if s.get("id") not in attended_session_ids]
        
        # Deduplicate by (date, subject_id) and count sessions
        unique_missed = {}
        for s in missed_sessions_raw:
            key = (s.get("date"), s.get("subject_id"))
            if key not in unique_missed:
                s_copy = dict(s)
                s_copy["count"] = 1
                unique_missed[key] = s_copy
            else:
                unique_missed[key]["count"] += 1
        missed_sessions = list(unique_missed.values())
        
        months = defaultdict(lambda: {"attended": 0, "missed": 0})
        
        for log in attended_logs:
            date_str = log.get("date", "")
            if date_str:
                try:
                    month_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %Y")
                    months[month_name]["attended"] += 1
                except ValueError:
                    pass
                    
        for s in missed_sessions:
            date_str = s.get("date", "")
            if date_str:
                try:
                    month_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %Y")
                    months[month_name]["missed"] += 1
                except ValueError:
                    pass
                    
        def sort_key(m_str):
            try:
                return datetime.strptime(m_str, "%b %Y")
            except:
                return datetime.min
                
        monthly_trend = [{"month": k, "attended": v["attended"], "missed": v["missed"]} 
                         for k, v in sorted(months.items(), key=lambda x: sort_key(x[0]))]
        
        student_analytics = {
            "total_sessions": len(all_sessions),
            "total_attended": len(attended_logs),
            "missed_sessions": missed_sessions,
            "monthly_trend": monthly_trend[-6:]
        }

    total   = len(students)
    present = len({r.get("roll_no") for r in today_records if r.get("roll_no")})
    absent  = max(0, total - present)
    sorted_records = sorted(today_records, key=lambda x: x.get("time", ""), reverse=True)
    feed = [{"name": r.get("name", r.get("roll_no", "Unknown")),
             "time": r.get("time", ""),
             "status": "Present"}
            for r in sorted_records[:5]]
    return {
        "total": total, "present": present, "absent": absent,
        "feed": feed, "students": students, "logs": sorted_records,
        "student_analytics": student_analytics
    }

# Students
@app.put("/api/students/{roll_no}")
def edit_student(roll_no: str, data: UpdateStudentModel):
    update_student(roll_no, data.name, data.email, data.dept, data.year)
    return {"status": "ok"}

@app.delete("/api/students/{roll_no}")
def delete_student_endpoint(roll_no: str):
    delete_student_record(roll_no)
    delete_face_entry(roll_no)
    with _lock:
        _state["db"] = load_face_db()
    return {"status": "ok"}

@app.get("/api/students/{roll_no}/history")
def student_history(roll_no: str):
    return get_student_history(roll_no)

# Subjects
@app.get("/api/subjects")
def list_subjects():
    return get_all_subjects()

@app.post("/api/subjects")
def add_new_subject(sub: SubjectModel):
    ok = add_subject(sub.code, sub.name, sub.dept)
    return {"status": "ok" if ok else "duplicate"}

@app.delete("/api/subjects/{subject_id}")
def delete_subject_endpoint(subject_id: str):
    delete_subject(subject_id)
    return {"status": "ok"}

# Sessions
@app.get("/api/sessions")
def list_sessions():
    return get_all_sessions()

@app.post("/api/session/start")
def start_session(sess: SessionModel, user: dict = Depends(get_current_user)):
    if user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    with _lock:
        _state["db"] = load_face_db()
        _state["last_marked"] = {}
    sid = create_session(sess.subject_id, sess.faculty)
    _set("active_session_id", sid)
    print(f"[SESSION] Started: {sid}")
    return {"status": "ok", "session_id": sid}

@app.post("/api/session/stop")
def stop_session():
    _set("active_session_id", None)
    # Release the camera hardware so it stops
    with _lock:
        cam = _state["cam"]
        if cam is not None and cam.isOpened():
            cam.release()
        _state["cam"] = None
    return {"status": "ok"}

@app.get("/api/session/status")
def session_status():
    sid = _get("active_session_id")
    return {"active": sid is not None, "session_id": sid}

# Logs (with date + subject filter)
@app.get("/api/logs")
def get_logs(
    log_date: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    if log_date:
        records = get_attendance_by_date(log_date, subject_id)
    else:
        records = get_today_attendance(subject_id)
        
    if user.get("role") == "student":
        roll_no = user.get("reference_id")
        records = [r for r in records if r.get("roll_no") == roll_no]
        
    return sorted(records, key=lambda x: x.get("time", ""), reverse=True)

# Analytics
@app.get("/api/analytics")
def get_analytics():
    summary = get_attendance_summary()
    alerts  = [s for s in summary if s["pct"] < ATTENDANCE_THRESHOLD and s["total_sessions"] > 0]
    subjects = get_all_subjects()
    
    # Build daily trend for last 14 days using all attendance
    today = date.today()
    trend = []
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        recs = get_attendance_by_date(d)
        trend.append({"date": d[-5:], "count": len(recs)})  # MM-DD format

    return {
        "summary": summary,
        "alerts": alerts,
        "trend": trend,
        "subject_count": len(subjects),
    }

# Enrollment — runs in background so /enrollment_feed streams in parallel
_enroll_result = {"status": "idle", "message": ""}

@app.post("/api/enroll")
def enroll_student_api(data: EnrollModel, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can enroll students")
    global _enroll_result
    # Release live-session camera first
    with _lock:
        cam = _state["cam"]
        if cam is not None and cam.isOpened():
            cam.release()
            time.sleep(1.0)  # Give Windows hardware a second to fully release
        _state["cam"] = None

    fq = FrameQueue()
    _set("enrollment_fq", fq)
    _enroll_result = {"status": "running", "message": ""}

    add_student(data.roll_no, data.name, data.email, data.dept, data.year)

    def _run():
        global _enroll_result
        res = enroll_student(data.name, data.roll_no, force=data.force, stframe=fq)
        fq.close()
        _set("enrollment_fq", None)
        with _lock:
            _state["db"] = load_face_db()
        if res is True:
            _enroll_result = {"status": "success", "message": ""}
        elif res == "exists":
            _enroll_result = {"status": "exists", "message": "Student already enrolled. Enable Overwrite."}
        else:
            msg = getattr(fq, '_last_error', None) or "Enrollment incomplete. Check lighting and face position."
            msg = (msg or "").replace("**", "")
            _enroll_result = {"status": "failed", "message": msg}

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}

@app.get("/api/enroll/status")
def enroll_status():
    return _enroll_result

# Export
@app.get("/api/export/csv")
def export_csv(from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None)):
    records = get_attendance_by_date(from_date) if from_date else get_today_attendance()
    df  = pd.DataFrame(records) if records else pd.DataFrame()
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"},
    )

@app.get("/api/export/excel")
def export_excel_endpoint(from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None)):
    path = export_to_excel(from_date=from_date, to_date=to_date)
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename="attendance.xlsx")


if __name__ == "__main__":
    import uvicorn
    print("[VisionTrack] Starting FastAPI backend on http://localhost:8000")
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=False)
