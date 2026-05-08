from deepface import DeepFace
import cv2
import sys

print("Loading camera...")
cam = cv2.VideoCapture(0)
ret, frame = cam.read()
if not ret:
    print("Camera failed")
    sys.exit(1)

print("Running DeepFace.extract_faces with anti_spoofing=True...")
try:
    results = DeepFace.extract_faces(frame, anti_spoofing=True, enforce_detection=False)
    for res in results:
        print("is_real:", res.get("is_real", "Not found"))
except Exception as e:
    print("Failed:", repr(e))
cam.release()
