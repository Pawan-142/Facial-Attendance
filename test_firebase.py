"""Test Firebase Firestore connection."""
import sys
sys.path.insert(0, ".")

try:
    from firebase_client import get_db
    db = get_db()

    # Write a test document
    db.collection("_test").document("ping").set({"status": "ok", "project": "visiontrack04"})
    print("✅ Firestore WRITE  — success")

    # Read it back
    doc = db.collection("_test").document("ping").get()
    print(f"✅ Firestore READ   — {doc.to_dict()}")

    # Clean up
    db.collection("_test").document("ping").delete()
    print("✅ Firestore DELETE — success")
    print("\n🎉 Firebase connected! Ready to use.")

except Exception as e:
    print(f"❌ Firebase connection failed: {e}")
    raise
