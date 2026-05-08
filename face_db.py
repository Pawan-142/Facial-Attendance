"""
face_db.py — Unified Face Embedding Database
Supports both local pickle (offline) and Firebase Firestore (cloud).
Controlled by config.USE_FIREBASE.
"""
import os
import pickle
import numpy as np
from config import FACE_DB_PATH, DATABASE_DIR, THRESHOLD, USE_FIREBASE

# In-memory cache to avoid re-fetching from Firestore on every frame
_cache = None
_cache_ts = 0
_CACHE_TTL = 30   # seconds


def _firestore_load():
    """Load embeddings from Firestore `embeddings` collection."""
    from firebase_client import get_db
    db = get_db()
    result = {}
    for doc in db.collection("embeddings").stream():
        data = doc.to_dict()
        # Convert lists/dicts → numpy arrays
        raw_embs = data.get("embeddings", [])
        data["embeddings"] = [
            np.array(e["data"] if isinstance(e, dict) else e)
            for e in raw_embs if e
        ]
        if "embedding" in data and data["embedding"]:
            data["embedding"] = np.array(data["embedding"])
        result[doc.id] = data
    return result


def _firestore_save(db_local):
    """Write all embeddings to Firestore."""
    from firebase_client import get_db
    db = get_db()
    for roll_no, data in db_local.items():
        serialized = dict(data)
        # Firestore doesn't allow nested arrays, wrap in dict
        if "embeddings" in serialized:
            serialized["embeddings"] = [
                {"data": e.tolist() if hasattr(e, "tolist") else e}
                for e in serialized["embeddings"]
            ]
        if "embedding" in serialized and serialized["embedding"] is not None:
            emb = serialized["embedding"]
            serialized["embedding"] = emb.tolist() if hasattr(emb, "tolist") else emb
        db.collection("embeddings").document(roll_no).set(serialized)


def load_face_db(force_refresh=False):
    global _cache, _cache_ts
    import time

    if USE_FIREBASE:
        if not force_refresh and _cache is not None and (time.time() - _cache_ts < _CACHE_TTL):
            return _cache
        try:
            _cache    = _firestore_load()
            _cache_ts = time.time()
            return _cache
        except Exception as e:
            print(f"[face_db] Firestore load failed: {e}. Falling back to local.")
            # Fall through to local

    # Local pickle fallback
    if os.path.exists(FACE_DB_PATH):
        with open(FACE_DB_PATH, "rb") as f:
            return pickle.load(f)
    return {}


def save_face_db(db_local):
    global _cache, _cache_ts
    _cache    = db_local
    _cache_ts = __import__("time").time()

    if USE_FIREBASE:
        try:
            _firestore_save(db_local)
            return
        except Exception as e:
            print(f"[face_db] Firestore save failed: {e}. Saving locally.")

    # Local pickle fallback
    os.makedirs(DATABASE_DIR, exist_ok=True)
    with open(FACE_DB_PATH, "wb") as f:
        pickle.dump(db_local, f)


def delete_face_entry(roll_no):
    global _cache
    db = load_face_db()
    if roll_no in db:
        del db[roll_no]
        save_face_db(db)
        if _cache and roll_no in _cache:
            del _cache[roll_no]
        if USE_FIREBASE:
            try:
                from firebase_client import get_db
                get_db().collection("embeddings").document(roll_no).delete()
            except Exception as e:
                print(f"[face_db] Firestore delete failed: {e}")
        return True
    return False


def match_face(query_embedding, db, threshold=None):
    """
    Match against all stored embeddings.
    Compares every individual capture for best accuracy.
    """
    if threshold is None:
        threshold = THRESHOLD

    best_match    = None
    best_distance = float("inf")

    from scipy.spatial.distance import cosine
    for roll_no, data in db.items():
        embeddings = data.get("embeddings", None)
        if embeddings is None:
            emb = data.get("embedding")
            embeddings = [emb] if emb is not None else []

        for emb in embeddings:
            if emb is None:
                continue
            try:
                dist = cosine(query_embedding, np.array(emb))
            except Exception:
                continue
            if dist < best_distance:
                best_distance = dist
                best_match    = data

    if best_distance < threshold and best_match:
        return best_match["display_name"], best_match["roll_no"], best_distance
    return "Unknown", None, best_distance


def list_enrolled():
    db = load_face_db()
    result = []
    for roll_no, data in db.items():
        embs = data.get("embeddings", [data.get("embedding")])
        result.append({
            "roll_no":      roll_no,
            "display_name": data.get("display_name", roll_no),
            "num_samples":  len([e for e in embs if e is not None]),
        })
    return result
