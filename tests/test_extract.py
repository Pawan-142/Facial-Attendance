from deepface import DeepFace
import cv2

cam = cv2.VideoCapture(0)
ret, frame = cam.read()
if ret:
    try:
        results = DeepFace.extract_faces(frame, anti_spoofing=True, enforce_detection=False)
        print("Faces found:", len(results))
        for res in results:
            print("is_real:", res.get("is_real"))
            print("box:", res["facial_area"])
    except Exception as e:
        print("Error:", repr(e))
cam.release()
