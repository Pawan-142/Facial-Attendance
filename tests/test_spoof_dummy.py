from deepface import DeepFace
import cv2
import numpy as np

# create a dummy image that looks like a face so enforce_detection doesn't fail
img = np.ones((224, 224, 3), dtype=np.uint8) * 128
cv2.circle(img, (112, 112), 50, (200, 150, 150), -1)

try:
    results = DeepFace.extract_faces(img, anti_spoofing=True, enforce_detection=False)
    for res in results:
        print("is_real:", res.get("is_real", "Not found"))
except Exception as e:
    print("Failed:", repr(e))
