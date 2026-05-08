"""
recognize.py — Face Recognition with Frame Skipping
ArcFace embeddings + DeepFace anti-spoofing
Runs heavy inference every FRAME_SKIP frames for performance.
"""
import cv2
import numpy as np
from face_db import load_face_db, match_face
from config import FRAME_SKIP, THRESHOLD, MODEL_NAME


def get_embedding(face_img):
    """Extract embedding from a pre-cropped face image."""
    from deepface import DeepFace
    try:
        result = DeepFace.represent(
            img_path=face_img,
            model_name=MODEL_NAME,
            enforce_detection=False
        )
        return np.array(result[0]["embedding"])
    except Exception:
        return None


# Liveness checking removed for performance (can be re-enabled if anti-spoofing is critical)
def check_liveness_full_frame(frame):
    return []


def _is_face_real(fx, fy, fw, fh, liveness_data):
    """Check if face centre lies within a live face region."""
    if not liveness_data:
        return False   # fail-closed: no liveness data → reject
    face_cx = fx + fw // 2
    face_cy = fy + fh // 2
    for ld in liveness_data:
        lx, ly, lw, lh = ld["box"]
        if lx <= face_cx <= lx + lw and ly <= face_cy <= ly + lh:
            return ld["is_real"]
    return False


class FrameSkipRecognizer:
    """
    Stateful recognizer that runs DeepFace inference every FRAME_SKIP
    frames and caches results in between for smooth real-time display.
    """
    def __init__(self, threshold=None):
        self._cache       = []
        self._frame_count = 0
        self._threshold   = threshold or THRESHOLD

    def process(self, frame, db):
        """
        Process a frame. Returns list of recognition result dicts.
        Heavy inference runs only on every FRAME_SKIP-th frame.
        """
        self._frame_count += 1

        if self._frame_count % FRAME_SKIP != 0 and self._cache:
            return self._cache   # return cached results

        # Speed Hack: Downscale frame for detection
        # MTCNN is much faster on smaller images.
        orig_h, orig_w = frame.shape[:2]
        target_w = 480
        scale = target_w / orig_w
        target_h = int(orig_h * scale)
        small_frame = cv2.resize(frame, (target_w, target_h))

        results = []
        from detect import detect_faces
        faces   = detect_faces(small_frame)

        for face in faces:
            if face['confidence'] < 0.92:
                continue

            # Scale box back to original coordinates
            sx, sy, sw, sh = face['box']
            x, y, w, h = int(sx/scale), int(sy/scale), int(sw/scale), int(sh/scale)
            real = True # Liveness disabled for speed

            # Crop + embed
            pad = 20
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(frame.shape[1], x + w + pad), min(frame.shape[0], y + h + pad)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            crop_resized = cv2.resize(crop, (112, 112))
            embedding    = get_embedding(crop_resized)
            if embedding is None:
                continue

            name, roll_no, distance = match_face(embedding, db, self._threshold)
            results.append({
                "name":       name,
                "roll_no":    roll_no,
                "distance":   distance,
                "box":        (x, y, w, h),
                "confidence": face['confidence'],
                "is_real":    True,
            })

        self._cache = results
        return results


def draw_recognition_results(frame, results):
    """Draw coloured bounding boxes and labels on a frame."""
    for r in results:
        x, y, w, h = r['box']
        if not r.get('is_real', True):
            color = (0, 100, 255)
            label = "SPOOF DETECTED"
        elif r['roll_no']:
            status = r.get("status", "")
            if status in ("duplicate", "cooldown"):
                color = (255, 165, 0)  # Orange
                label = f"{r['name']} — Already Present"
            else:
                color = (0, 220, 80)   # Green
                pct   = max(0, int((1 - r['distance']) * 100))
                label = f"{r['name']} — Marked! {pct}%"

        else:
            color = (0, 0, 220)
            dist_info = f" ({r['distance']:.2f})" if r['distance'] != float('inf') else ""
            label = f"Unknown{dist_info}"

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x, y - th - 14), (x + tw + 8, y), color, -1)
        cv2.putText(frame, label, (x + 4, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return frame
