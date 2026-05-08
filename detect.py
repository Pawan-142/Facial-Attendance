"""
detect.py
─────────────────────────────────────
Face Detection using MTCNN
Detects faces in real-time from webcam
and returns bounding boxes + landmarks
"""

import cv2
from mtcnn import MTCNN

# Initialize MTCNN detector (loads once)
detector = MTCNN()


def detect_faces(frame):
    """
    Detect all faces in a given BGR frame.

    Args:
        frame: BGR image from OpenCV

    Returns:
        list of dicts with keys:
            - box: [x, y, w, h]
            - confidence: float (0 to 1)
            - keypoints: dict of facial landmarks
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb_frame)
    return faces


def crop_face(frame, padding=20):
    """
    Detect and crop the largest/most confident face in a frame.

    Args:
        frame   : BGR image from OpenCV
        padding : pixels to add around face box

    Returns:
        cropped face resized to 112x112 (ArcFace input size)
        or None if no face detected
    """
    faces = detect_faces(frame)

    if not faces:
        return None

    # Pick the most confident face
    face = max(faces, key=lambda f: f['confidence'])

    if face['confidence'] < 0.95:
        return None

    x, y, w, h = face['box']

    # Add padding (clamped to frame borders)
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(frame.shape[1], x + w + padding)
    y2 = min(frame.shape[0], y + h + padding)

    cropped = frame[y1:y2, x1:x2]

    if cropped.size == 0:
        return None

    # Resize to standard ArcFace input
    return cv2.resize(cropped, (112, 112))


def draw_detections(frame, faces, label=None):
    """
    Draw bounding boxes and landmarks on frame.

    Args:
        frame  : BGR image
        faces  : output from detect_faces()
        label  : optional text label override

    Returns:
        annotated frame
    """
    for face in faces:
        if face['confidence'] < 0.95:
            continue

        x, y, w, h = face['box']
        conf = face['confidence']

        # Bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Label
        text = label if label else f"Face {conf:.2f}"
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Facial landmarks (eyes, nose, mouth corners)
        for point in face['keypoints'].values():
            cv2.circle(frame, point, 4, (0, 0, 255), -1)

    # Face count
    cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    return frame


def run_live_detection():
    """
    Run real-time face detection from webcam.
    Press Q to quit.
    """
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("[ERROR] Cannot open camera")
        return

    print("[*] Live detection running... Press Q to quit")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        faces = detect_faces(frame)
        frame = draw_detections(frame, faces)

        cv2.imshow("MTCNN Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_live_detection()
