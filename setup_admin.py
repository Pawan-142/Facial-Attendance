from firebase_client import get_db
from auth import get_password_hash

def setup_default_users():
    db = get_db()
    users_ref = db.collection('users')
    
    # Check if admin already exists
    admin = users_ref.document('admin').get()
    if not admin.exists:
        print("Creating default Admin account...")
        users_ref.document('admin').set({
            "username": "admin",
            "password_hash": get_password_hash("admin123"),
            "role": "admin",
            "name": "System Administrator"
        })
        print("Admin created (admin / admin123)")
    else:
        print("Admin account already exists.")

    # Create a demo teacher account
    teacher = users_ref.document('teacher1').get()
    if not teacher.exists:
        print("Creating default Teacher account...")
        users_ref.document('teacher1').set({
            "username": "faculty1",
            "password_hash": get_password_hash("faculty123"),
            "role": "teacher",
            "name": "Dr. Smith"
        })
        print("Teacher created (faculty1 / faculty123)")

    # Create a demo student account
    student = users_ref.document('student1').get()
    if not student.exists:
        print("Creating default Student account...")
        users_ref.document('student1').set({
            "username": "2024CS01",
            "password_hash": get_password_hash("student123"),
            "role": "student",
            "name": "Alex Student",
            "reference_id": "2024CS01"
        })
        print("Student created (2024CS01 / student123)")

if __name__ == "__main__":
    setup_default_users()
