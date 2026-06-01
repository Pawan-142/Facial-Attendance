from deepface import DeepFace
import cv2
import numpy as np

img = np.ones((224, 224, 3), dtype=np.uint8) * 128
cv2.circle(img, (112, 112), 50, (200, 150, 150), -1)

try:
    results = DeepFace.represent(img, model_name="ArcFace", enforce_detection=False, anti_spoofing=True)
    print("Keys in result:", results[0].keys())
    print("is_real:", results[0].get("is_real"))
except Exception as e:
    print("Failed:", repr(e))
