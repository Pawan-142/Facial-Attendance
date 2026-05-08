"""
main.py — Attendance System Pipeline
Runs: Detection → Liveness → Recognition → DB Logging
Accepts threading.Event for clean stop from Streamlit UI.
"""
import cv2
import time
import threading
from recognize import FrameSkipRecognizer, draw_recognition_results
from face_db import load_face_db
from models import mark_attendance, get_session_attendance
from config import COOLDOWN_SEC


def run_attendance_system(stframe=None, stop_event: threading.Event = None,
                          session_id: int = None, threshold: float = None):
    """
    Full attendance marking pipeline.

    Args:
        stframe    : Streamlit st.empty() placeholder — if None, uses cv2.imshow
        stop_event : threading.Event; set it to stop the loop
        session_id : active session ID to log attendance against
        threshold  : cosine distance override (None = use config default)
    """
    db = load_face_db()
    if not db:
        print("[ERROR] No students enrolled.")
        return

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("[ERROR] Cannot open camera")
        return

    recognizer   = FrameSkipRecognizer(threshold=threshold)
    last_marked  = {}         # roll_no → epoch of last attempt
    today_count  = 0
    count_frames = 0
    status_text  = "Waiting for student…"
    status_color = (180, 180, 180)

    print(f"[*] Session {session_id} — Attendance System Running")

    try:
        while True:
            # Check stop signal
            if stop_event and stop_event.is_set():
                break

            ret, frame = cam.read()
            if not ret:
                break

            results = recognizer.process(frame, db)
            frame   = draw_recognition_results(frame, results)

            for r in results:
                if not r.get("is_real", True):
                    status_text  = "SPOOF DETECTED — show your real face"
                    status_color = (0, 80, 255)
                    continue

                if r["roll_no"] is None:
                    status_text  = "Unknown person — not enrolled"
                    status_color = (0, 0, 200)
                    continue

                roll_no = r["roll_no"]
                now     = time.time()

                # In-memory cooldown (DB UNIQUE constraint is the real guard)
                if now - last_marked.get(roll_no, 0) < COOLDOWN_SEC:
                    status_text  = f"{r['name']} — already recorded"
                    status_color = (0, 180, 180)
                    continue

                res = mark_attendance(
                    roll_no=roll_no,
                    session_id=session_id,
                    confidence=r["distance"],
                )
                last_marked[roll_no] = now

                if res == "marked":
                    today_count += 1
                    status_text  = f"✓  {r['name']} marked present!"
                    status_color = (0, 220, 80)
                    print(f"  [OK] {r['name']} ({roll_no})  dist={r['distance']:.3f}")
                elif res == "duplicate":
                    status_text  = f"{r['name']} already marked"
                    status_color = (0, 180, 180)

            # Overlay: bottom status bar
            count_frames += 1
            if count_frames % 30 == 0:
                today_count = len(get_session_attendance(session_id)) if session_id else today_count

            fh, fw = frame.shape[:2]
            cv2.rectangle(frame, (0, fh - 50), (fw, fh), (25, 25, 25), -1)
            cv2.putText(frame, status_text, (10, fh - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
            cv2.putText(frame, f"Present: {today_count}", (fw - 180, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 220, 0), 2)

            if stframe is not None:
                stframe.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                cv2.imshow("VisionTrack — Attendance", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    db = load_face_db()
                    print("[INFO] Database refreshed")

    finally:
        cam.release()
        if stframe is None:
            cv2.destroyAllWindows()

    # Final summary
    if session_id:
        records = get_session_attendance(session_id)
        print(f"\n[*] Session ended — {len(records)} present")
        for r in records:
            print(f"  {r['roll_no']:<12} {r['name']:<22} {r['time']}")


if __name__ == "__main__":
    run_attendance_system()
