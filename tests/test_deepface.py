import cv2
import numpy as np
from deepface import DeepFace
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("Creating dummy face...")
dummy_face = np.zeros((112, 112, 3), dtype=np.uint8)

print("Running DeepFace.represent...")
try:
    result = DeepFace.represent(
        img_path=dummy_face,
        model_name="ArcFace",
        enforce_detection=False
    )
    print("Success! Embedding shape:", np.array(result[0]["embedding"]).shape)
except Exception as e:
    print("Failed with exception:", repr(e))
