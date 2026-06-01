import os
import random
from datetime import datetime
from firebase_db import (
    add_subject, add_student, create_session, mark_attendance, init_db
)
from firebase_client import get_db

print("Connecting to Firebase...")
init_db()

print("Creating fake subjects...")
cs101 = add_subject("CS101", "Introduction to Programming", "Computer Science", 3)
ee205 = add_subject("EE205", "Digital Logic Design", "Electrical Engineering", 4)
ma301 = add_subject("MA301", "Linear Algebra", "Mathematics", 3)

print("Creating fake students...")
add_student("2024CS01", "Alex Student", "alex@college.edu", "Computer Science", "2024")
add_student("2024CS02", "Sarah Jenkins", "sarah@college.edu", "Computer Science", "2024")
add_student("2024EE01", "Michael Scott", "michael@college.edu", "Electrical Engineering", "2024")
add_student("2024MA01", "Jim Halpert", "jim@college.edu", "Mathematics", "2024")
add_student("2024EE02", "Pam Beesly", "pam@college.edu", "Electrical Engineering", "2024")

print("Creating live sessions and marking attendance...")
session_cs = create_session("CS101", "Dr. Smith", "Lecture on Python Basics")
session_ee = create_session("EE205", "Dr. Brown", "Lecture on Boolean Algebra")

# Mark attendance
mark_attendance("2024CS01", session_cs, confidence=0.98)
mark_attendance("2024CS02", session_cs, confidence=0.95)
mark_attendance("2024MA01", session_cs, confidence=0.88)
mark_attendance("2024EE01", session_ee, confidence=0.99)
mark_attendance("2024EE02", session_ee, confidence=0.97)

print("Database successfully seeded with test data!")
