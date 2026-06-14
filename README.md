# 🎓 Facial Attendance System

A deep learning-powered facial attendance system using face recognition and liveness detection for automated, secure attendance marking.

## 📋 Overview

This project implements a comprehensive facial attendance system that uses advanced deep learning techniques including face detection (MTCNN), face recognition (ArcFace), and anti-spoofing liveness detection.

---

## ✨ Key Features

- ✅ **Face Detection**: MTCNN-based face detection from webcam feed
- ✅ **Face Recognition**: ArcFace embeddings for accurate identification (99.82% accuracy)
- ✅ **Liveness Detection**: Eye-blink based anti-spoofing using dlib EAR
- ✅ **Student Enrollment**: Automatic enrollment with 10 sample captures
- ✅ **Attendance Logging**: SQLite-based attendance tracking with timestamp
- ✅ **Dashboard**: Real-time Streamlit dashboard for visualization
- ✅ **Anti-Spoofing**: Prevents fake attendance using photos/videos

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Face Detection** | MTCNN |
| **Face Recognition** | ArcFace (DeepFace) |
| **Liveness Detection** | dlib EAR |
| **Database** | SQLite |
| **Dashboard** | Streamlit |
| **Language** | Python 3.10+ |
| **Vision** | OpenCV |

---

## 📁 Project Structure

```
facial_attendance/
├── main.py              # Main attendance system
├── enroll.py            # Student enrollment
├── detect.py            # Face detection (MTCNN)
├── recognize.py         # Face recognition (ArcFace)
├── liveness.py          # Liveness detection (dlib EAR)
├── attendance.py        # Attendance logging (SQLite)
├── dashboard.py         # Streamlit dashboard
├── requirements.txt     # Python dependencies
├── database/            # Auto-created (embeddings + SQLite)
└── faces/               # Auto-created (enrolled face images)
```

---

## ⚙️ Setup Instructions

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Download dlib landmark model
```bash
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
mv shape_predictor_68_face_landmarks.dat .
```

### Step 3: Enroll students
```bash
python enroll.py
```

### Step 4: Run attendance system
```bash
python main.py
```

### Step 5: View dashboard
```bash
streamlit run dashboard.py
```

---

## 📊 Model Performance

| Metric | Value |
|--------|-------|
| ArcFace accuracy (LFW) | 99.82% |
| Recognition threshold | 0.40 cosine |
| Processing speed | ~25 FPS (GPU) |
| Enrollment time | ~30 seconds |
| Liveness check | 1 blink |

---

## 🔑 Key Controls

| Key | Action |
|-----|--------|
| Q | Quit attendance system |
| R | Refresh student database |

---

## 💻 Example Usage

```python
from recognize import get_embeddings
from attendance import log_attendance

# Get face embedding
embedding = get_embeddings(face_image)

# Log attendance
log_attendance(student_id=1, name="John Doe")
```

---

## ⚠️ Notes

- First run downloads ArcFace model (~500MB) automatically
- Enrollment needs good lighting for best accuracy
- One attendance entry per student per day (auto-prevented)
- Confidence shown is cosine distance — lower = better match

---

## 👨‍💻 Author

**Pawan-142**  
- GitHub: [@Pawan-142](https://github.com/Pawan-142)

---

**Last Updated**: 2026-06-14
