"""
liveness.py
─────────────────────────────────────
Liveness Detection using Eye Cascades
Detects real blinks to prevent photo/video spoofing
"""

import cv2
import numpy as np

# ── OpenCV Setup ──────────────────────────────────
# Load the pre-trained Haar cascades for eyes
EYE_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)

# Consecutive frames eyes must be missing to count as blink
CONSEC_FRAMES = 2

def are_eyes_open(frame, face_box=None):
    """
    Detect if eyes are open using OpenCV Haar Cascade.
    If face_box is provided, we only search the upper half of the face for eyes.
    
    Returns:
        True if at least one eye is detected, False otherwise
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    if face_box is not None:
        x, y, w, h = face_box
        # Search only the upper half of the face bounding box
        roi_gray = gray[y:y + int(h/1.8), x:x + w]
        if roi_gray.size == 0:
            return True # fallback
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(10, 10))
    else:
        eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
    return len(eyes) > 0


class LivenessChecker:
    """
    Tracks blinks across frames and flags liveness.

    Usage:
        checker = LivenessChecker()
        while capturing:
            is_live, eyes_open = checker.update(frame)
            if is_live:
                proceed with recognition
    """

    def __init__(self, blinks_required=1):
        self.blinks_required  = blinks_required
        self.blink_count      = 0
        self.consec_below     = 0   # frames with eyes closed

    def reset(self):
        self.blink_count  = 0
        self.consec_below = 0

    def update(self, frame, face_box=None):
        """
        Process the next frame and check for blink.

        Args:
            frame (ndarray): Current BGR frame
            face_box (tuple): Optional (x,y,w,h) of detected face to restrict eye search

        Returns:
            (is_live: bool, eyes_open: bool)
        """
        eyes_open = are_eyes_open(frame, face_box)

        if not eyes_open:
            self.consec_below += 1
        else:
            if self.consec_below >= CONSEC_FRAMES:
                self.blink_count += 1
            self.consec_below = 0

        is_live = self.blink_count >= self.blinks_required
        return is_live, eyes_open


def draw_liveness_info(frame, eyes_open, blink_count, is_live):
    """Overlay blink status on the frame."""
    color = (0, 255, 0) if is_live else (0, 165, 255)
    
    status_text = "LIVE" if is_live else "WAITING"
    eye_status  = "OPEN" if eyes_open else "CLOSED"

    cv2.putText(frame, f"Blinks: {blink_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Eyes: {eye_status}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Liveness: {status_text}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame

