from deepface import DeepFace
import cv2
import numpy as np

img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    res = DeepFace.extract_faces(img, anti_spoofing=True)
    print("Anti-spoofing is supported!")
except TypeError:
    print("Anti-spoofing NOT supported (wrong arguments)")
except Exception as e:
    print("Error:", repr(e))
