"""
ui_helpers.py — Hyper-Premium Glassmorphic UI Design for VisionTrack
"""
import streamlit as st
import pandas as pd
from datetime import date

DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* KILL DEFAULT STREAMLIT ELEMENTS */
#MainMenu, footer, header, [data-testid="stHeader"], 
[data-testid="stToolbar"], [data-testid="stDecoration"],
.stApp > header {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* GLOBAL RESET */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 100%) !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
    width: 100vw !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #f8fafc !important;
}

[data-testid="stAppViewBlockContainer"] {
    max-width: 1400px !important;
    padding: 2rem 3rem !important;
    margin: 0 auto !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* NAVBAR / HEADER */
.vt-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 2rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.vt-logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
}

.vt-logo-glow {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 25px rgba(99, 102, 241, 0.5);
}

.vt-title-main {
    font-size: 24px; font-weight: 800; color: #fff;
    letter-spacing: -0.5px; line-height: 1;
}
.vt-title-sub {
    font-size: 11px; font-weight: 700; color: #6366f1;
    text-transform: uppercase; letter-spacing: 2px; margin-top: 4px;
}

.vt-status-pill {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    padding: 6px 16px; border-radius: 99px;
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 600; color: #10b981;
}

.vt-status-dot {
    width: 8px; height: 8px; background: #10b981; border-radius: 50%;
    animation: vt-pulse 2s infinite;
}
@keyframes vt-pulse { 0% {box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);} 70% {box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);} 100% {box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);} }

/* GLASS CARDS */
.vt-card {
    background: rgba(15, 23, 42, 0.4);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 24px;
    transition: transform 0.3s ease, border 0.3s ease;
}
.vt-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
}

/* METRICS */
div[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 24px !important;
    padding: 24px !important;
    text-align: center !important;
}
div[data-testid="stMetricValue"] { font-size: 42px !important; font-weight: 800 !important; color: #fff !important; }
div[data-testid="stMetricLabel"] p { font-size: 13px !important; color: #94a3b8 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }

/* TABS */
div[data-testid="stTabs"] [role="tablist"] {
    gap: 8px !important;
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    margin-bottom: 32px !important;
}
div[data-testid="stTabs"] [role="tab"] {
    border-radius: 12px 12px 0 0 !important;
    padding: 12px 24px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stTabs"] [role="tab"]:hover {
    color: #fff !important;
    background: rgba(255,255,255,0.02) !important;
}
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #6366f1 !important;
    background: rgba(99, 102, 241, 0.05) !important;
    border-bottom: 3px solid #6366f1 !important;
}

/* BUTTONS */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
    color: white !important;
    border: none !important;
    padding: 14px 28px !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 20px 30px -10px rgba(99, 102, 241, 0.5) !important;
    opacity: 0.9 !important;
}

/* INPUTS */
.stTextInput input, .stSelectbox [data-testid="stSelectbox"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    color: white !important;
    padding: 12px !important;
}

/* DATAFRAME STYLE */
[data-testid="stTable"], [data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.2) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    overflow: hidden !important;
}

/* SECTION TITLES */
.vt-section-title {
    font-size: 20px; font-weight: 700; color: #fff;
    margin: 40px 0 20px;
    display: flex; align-items: center; gap: 12px;
}
.vt-section-title::before {
    content: ''; width: 4px; height: 24px;
    background: linear-gradient(to bottom, #6366f1, #a855f7);
    border-radius: 4px;
}

/* BADGES */
.badge {
    padding: 6px 14px; border-radius: 10px; font-size: 12px; font-weight: 700;
    display: inline-flex; align-items: center; gap: 6px;
}
.badge-green { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
.badge-blue  { background: rgba(59, 130, 246, 0.1); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.2); }
.badge-red   { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }

/* FOOTER */
.vt-footer {
    text-align: center; padding: 4rem 0 2rem;
    color: #64748b; font-size: 13px; font-weight: 500;
}
.vt-footer span { color: #6366f1; font-weight: 700; }

</style>
"""

def inject_css():
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

def render_header():
    today_str = date.today().strftime("%A, %B %d, %Y")
    st.markdown(f\"\"\"
    <div class="vt-nav">
        <div class="vt-logo-container">
            <div class="vt-logo-glow">🎓</div>
            <div>
                <div class="vt-title-main">VisionTrack</div>
                <div class="vt-title-sub">Facial Attendance Intelligence</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 24px;">
            <div style="text-align: right">
                <div style="font-size: 13px; font-weight: 700; color: #fff">{today_str}</div>
                <div style="font-size: 11px; color: #94a3b8">Academic Session 2026</div>
            </div>
            <div class="vt-status-pill">
                <div class="vt-status-dot"></div>
                System Active
            </div>
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)

def render_footer():
    st.markdown(\"\"\"
    <div class="vt-footer">
        © 2026 <span>VisionTrack AI</span> • Optimized for Academic Integrity<br>
        <small style="color: #475569; margin-top: 8px; display: block;">Powered by DeepFace Engine • Cloud Synchronized via Firestore</small>
    </div>
    \"\"\", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="vt-section-title">{title}</div>', unsafe_allow_html=True)

def card(html, cls=""):
    st.markdown(f'<div class="vt-card {cls}">{html}</div>', unsafe_allow_html=True)

def confidence_badge(dist):
    if dist is None: return '<span class="badge badge-blue">Manual</span>'
    pct = max(0, int((1 - dist) * 100))
    if pct >= 80: return f'<span class="badge badge-green">✓ Confident {pct}%</span>'
    elif pct >= 65: return f'<span class="badge badge-blue">~ Neutral {pct}%</span>'
    else: return f'<span class="badge badge-red">! Low {pct}%</span>'

def build_attendance_df(records):
    if not records: return pd.DataFrame()
    df = pd.DataFrame(records)
    rename = {
        "roll_no": "Roll No", "name": "Name",
        "department": "Dept", "year": "Year",
        "subject_code": "Code", "subject_name": "Subject",
        "date": "Date", "time": "In Time", "confidence": "_conf",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "_conf" in df.columns:
        df["Verification"] = df["_conf"].apply(confidence_badge)
        df = df.drop(columns=["_conf"])
    return df
