"""
enroll.py — Student Enrollment
Captures NUM_CAPTURES face photos → stores ALL embeddings individually
Uses face_db.py as single source of truth
"""
import cv2
import os
import time
import numpy as np
from deepface import DeepFace
from detect import detect_faces, crop_face
from face_db import load_face_db, save_face_db
from config import FACES_DIR, NUM_CAPTURES, MODEL_NAME


def get_embedding(face_img):
    """Extract ArcFace embedding from a cropped 112×112 face image."""
    try:
        result = DeepFace.represent(
            img_path=face_img,
            model_name=MODEL_NAME,
            enforce_detection=False
        )
        return np.array(result[0]["embedding"])
    except Exception as e:
        print(f"  [WARN] Embedding failed: {e}")
        return None


def enroll_student(name, roll_no, force=False, stframe=None):
    """
    Enroll a student by capturing NUM_CAPTURES face images.

    Stores EACH embedding individually (not just mean) for better
    match accuracy across poses and lighting conditions.

    Returns:
        True       — success
        False      — incomplete capture / camera error
        "exists"   — already enrolled (and force=False)
    """
    db = load_face_db()
    if roll_no in db and not force:
        return "exists"

    student_dir = os.path.join(FACES_DIR, roll_no)
    os.makedirs(student_dir, exist_ok=True)

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("[ERROR] Cannot open camera")
        return False

    POSE_INSTRUCTIONS = [
        "Look STRAIGHT at the camera",
        "Turn face SLIGHTLY LEFT",
        "Turn face SLIGHTLY RIGHT",
        "Tilt head SLIGHTLY LEFT",
        "Tilt head SLIGHTLY RIGHT",
        "Look SLIGHTLY UP",
        "Look SLIGHTLY DOWN",
        "SMILE naturally",
        "NEUTRAL expression",
        "Look STRAIGHT again (final)",
    ]

    def draw_guide(frame, face_in_position):
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        axes = (int(w * 0.18), int(h * 0.32))
        color = (0, 255, 80) if face_in_position else (0, 165, 255)
        overlay = frame.copy()
        cv2.ellipse(overlay, (cx, cy), (axes[0]+6, axes[1]+6), 0, 0, 360,
                    (0, 180, 60) if face_in_position else (0, 100, 180), 8)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        cv2.ellipse(frame, (cx, cy), axes, 0, 0, 360, color, 3)
        for off in [(0, -axes[1]), (0, axes[1]), (axes[0], 0), (-axes[0], 0)]:
            cv2.circle(frame, (cx + off[0], cy + off[1]), 6, color, -1)
        return frame, cx, cy, axes

    def face_in_oval(box, cx, cy, axes):
        if not box:
            return False
        x, y, w, h = box
        dx = ((x + w // 2) - cx) / axes[0]
        dy = ((y + h // 2) - cy) / axes[1]
        return (dx * dx + dy * dy) <= 1.1

    embeddings = []
    count = 0

    try:
        while count < NUM_CAPTURES:
            ret, frame = cam.read()
            if not ret:
                break

            faces = detect_faces(frame)
            box   = faces[0]['box'] if faces else None
            fh, fw = frame.shape[:2]
            cx, cy = fw // 2, fh // 2
            axes   = (int(fw * 0.18), int(fh * 0.32))
            in_pos = face_in_oval(box, cx, cy, axes)

            frame, cx, cy, axes = draw_guide(frame, in_pos)

            # Top banner
            cv2.rectangle(frame, (0, 0), (fw, 52), (20, 20, 20), -1)
            cv2.putText(frame,
                        f"Step {count+1}/{NUM_CAPTURES}:  {POSE_INSTRUCTIONS[count]}",
                        (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 255, 80) if in_pos else (0, 200, 255), 2)

            # Bottom bar + progress
            cv2.rectangle(frame, (0, fh - 50), (fw, fh), (20, 20, 20), -1)
            cv2.rectangle(frame, (0, fh - 6),
                          (int(fw * count / NUM_CAPTURES), fh), (0, 200, 80), -1)
            msg = "Face aligned! Hold still…" if in_pos else "Align your face inside the oval"
            cv2.putText(frame, f"{msg}   [{count}/{NUM_CAPTURES} captured]",
                        (10, fh - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 80) if in_pos else (80, 80, 80), 2)

            # Capture when face is aligned
            if in_pos:
                face_crop = crop_face(frame)
                if face_crop is not None:
                    img_path = os.path.join(student_dir, f"{count}.jpg")
                    cv2.imwrite(img_path, face_crop)
                    emb = get_embedding(face_crop)
                    if emb is not None:
                        embeddings.append(emb)
                        count += 1
                        flash = frame.copy()
                        cv2.rectangle(flash, (0, 0), (fw, fh), (0, 255, 80), 8)
                        if stframe is not None:
                            stframe.image(cv2.cvtColor(flash, cv2.COLOR_BGR2RGB))
                        time.sleep(0.5)

            if stframe is not None:
                stframe.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                time.sleep(0.04)
            else:
                cv2.imshow("Enrollment — VisionTrack", frame)
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
    finally:
        cam.release()
        if stframe is None:
            cv2.destroyAllWindows()

    if count < NUM_CAPTURES:
        print(f"[ERROR] Incomplete enrollment: {count}/{NUM_CAPTURES}")
        return False

    # Save ALL embeddings (not just mean) for better accuracy
    db = load_face_db()
    db[roll_no] = {
        "roll_no":      roll_no,
        "display_name": name,
        "embeddings":   embeddings,          # full list
        "embedding":    np.mean(embeddings, axis=0),  # kept for legacy compat
        "num_samples":  count,
    }
    save_face_db(db)
    print(f"[SUCCESS] Enrolled {name} ({roll_no}) — {count} embeddings saved")
    return True
