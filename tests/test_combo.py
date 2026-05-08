import cv2
import numpy as np
from deepface import DeepFace

# create a dummy image
img = np.ones((500, 500, 3), dtype=np.uint8) * 128
cv2.circle(img, (250, 250), 100, (200, 150, 150), -1)

try:
    faces = DeepFace.extract_faces(img, detector_backend="mtcnn", enforce_detection=False, anti_spoofing=True)
    for face in faces:
        print("is_real:", face.get("is_real"))
        print("box:", face["facial_area"])
        
        # Now try to represent using face["face"]
        face_img = face["face"]
        # face_img is float32 [0, 1]. Represent usually expects uint8 [0, 255] if it's going to re-preprocess, but enforce_detection=False means it skips extraction.
        # Actually, let's just pass the original cropped image from the frame instead of face["face"] to be safe!
        box = face["facial_area"]
        x, y, w, h = box["x"], box["y"], box["w"], box["h"]
        crop = img[max(0, y):y+h, max(0, x):x+w]
        
        emb = DeepFace.represent(crop, model_name="ArcFace", enforce_detection=False)
        print("Embedding length:", len(emb[0]["embedding"]))
except Exception as e:
    print("Error:", repr(e))
