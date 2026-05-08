"""
firebase_client.py - Firebase Admin SDK Initializer
Supports local JSON key and Streamlit Secrets for cloud hosting.
"""
import os
import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

_app = None
_db  = None

def _init():
    global _app, _db
    if _app is not None:
        return

    from config import FIREBASE_KEY_PATH

    # 1. Try Streamlit Secrets (for cloud hosting)
    # Use a try block because accessing st.secrets when empty can crash in some envs
    try:
        if hasattr(st, "secrets") and "firebase" in st.secrets:
            info = st.secrets["firebase"]["service_account"]
            if isinstance(info, str):
                info = json.loads(info)
            
            if not firebase_admin._apps:
                cred_obj = credentials.Certificate(info)
                _app = firebase_admin.initialize_app(cred_obj)
            else:
                _app = firebase_admin.get_app()
    except Exception:
        # Silently skip secrets if they don't exist or fail
        pass

    # 2. Fallback to Local JSON (for local dev)
    if _app is None:
        if os.path.exists(FIREBASE_KEY_PATH):
            if not firebase_admin._apps:
                cred = credentials.Certificate(FIREBASE_KEY_PATH)
                _app = firebase_admin.initialize_app(cred)
            else:
                _app = firebase_admin.get_app()
        else:
            raise FileNotFoundError(
                f"[Firebase] Key not found in Secrets and also missing at {FIREBASE_KEY_PATH}. "
                "Please ensure serviceAccountKey.json is in your project folder for local use."
            )

    if _db is None:
        _db  = firestore.client()
        print("[Firebase] Firestore connected OK")

def get_db():
    _init()
    return _db
