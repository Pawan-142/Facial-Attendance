"""
dashboard.py — VisionTrack Attendance System
Run: streamlit run dashboard.py
"""
import queue
import threading
import time
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

from models import (
    init_db, get_all_students, get_all_subjects, get_all_sessions,
    add_student, update_student, delete_student_record,
    add_subject, delete_subject, get_subject,
    create_session, get_session_attendance, count_sessions,
    get_today_attendance, get_attendance_by_date,
    get_student_history, get_attendance_summary, get_daily_trend,
    mark_attendance, export_to_csv, export_to_excel,
)

# ── Auto-select Firebase or local SQLite ───────────────────────────────────────
from config import USE_FIREBASE
if USE_FIREBASE:
    try:
        from firebase_db import (
            init_db, get_all_students, get_all_subjects, get_all_sessions,
            add_student, update_student, delete_student_record,
            add_subject, delete_subject, get_subject,
            create_session, get_session_attendance, count_sessions,
            get_today_attendance, get_attendance_by_date,
            get_student_history, get_attendance_summary, get_daily_trend,
            mark_attendance, export_to_csv, export_to_excel,
        )
    except Exception as _fb_err:
        import streamlit as _st
        _st.warning(f"⚠️ Firebase unavailable ({_fb_err}) — using local SQLite.")

from face_db import load_face_db, delete_face_entry, list_enrolled
from enroll import enroll_student
from main import run_attendance_system
from config import (
    ATTENDANCE_THRESHOLD, DEPARTMENTS, YEARS,
    FACES_DIR, THRESHOLD, FRAME_SKIP,
)
from ui_helpers import (
    inject_css, render_header, render_footer,
    section, card, confidence_badge, build_attendance_df,
)

# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VisionTrack Attendance",
    page_icon="🎓", layout="wide",
    initial_sidebar_state="collapsed",
)
init_db()
inject_css()
render_header()
render_footer()

# ── Session state ──────────────────────────────────────────────────────────────
def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("cam_running",  False)
_ss("stop_event",   threading.Event())
_ss("cam_thread",   None)
_ss("frame_queue",  queue.Queue(maxsize=2))
_ss("active_session_id", None)
_ss("threshold",    THRESHOLD)
_ss("cam_started_at", 0.0)

# ── Helpers ────────────────────────────────────────────────────────────────────
def subject_options():
    subs = get_all_subjects()
    return {f"{s['code']} — {s['name']}": s["id"] for s in subs}

def _camera_worker(q: queue.Queue, stop_evt: threading.Event,
                   session_id: int, threshold: float):
    """Background thread: runs recognition, pushes RGB frames to queue."""
    from face_db import load_face_db
    from recognize import FrameSkipRecognizer, draw_recognition_results
    import cv2, time
    from config import COOLDOWN_SEC


    db         = load_face_db()
    recognizer = FrameSkipRecognizer(threshold=threshold)
    last_marked = {}
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return
    try:
        while not stop_evt.is_set():
            ret, frame = cam.read()
            if not ret:
                break
            results = recognizer.process(frame, db)
            
            for r in results:
                if not r.get("is_real") or r["roll_no"] is None:
                    continue
                rn = r["roll_no"]
                if time.time() - last_marked.get(rn, 0) < COOLDOWN_SEC:
                    r["status"] = "cooldown"
                    continue
                res = mark_attendance(rn, session_id, r["distance"])
                r["status"] = res  # 'marked' or 'duplicate'
                if res in ("marked", "duplicate"):
                    last_marked[rn] = time.time()

            frame = draw_recognition_results(frame, results)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                q.put_nowait(rgb)
            except queue.Full:
                pass
    except Exception as e:
        print(f"[FATAL ERROR IN CAMERA THREAD]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cam.release()


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🏠 Dashboard", "📷 Live Camera", "👥 Students", "📚 Subjects",
    "📋 Records", "📅 History", "📊 Analytics", "💾 Export",
])

# ─── TAB 0: Dashboard ─────────────────────────────────────────────────────────
with tabs[0]:
    section("📊 Today's Overview")
    students = get_all_students()
    today_rec = get_today_attendance()
    sessions_today = [s for s in get_all_sessions()
                      if s["date"] == date.today().isoformat()]
    n_enr   = len(students)
    n_pres  = len({r["roll_no"] for r in today_rec})
    n_abs   = max(0, n_enr - n_pres)
    pct     = round(n_pres / n_enr * 100, 1) if n_enr else 0
    total_s = count_sessions()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Enrolled Students", n_enr)
    c2.metric("Present Today",     n_pres, delta=f"+{n_pres}" if n_pres else None)
    c3.metric("Absent Today",      n_abs,  delta=f"-{n_abs}"  if n_abs  else None, delta_color="inverse")
    c4.metric("Attendance Rate",   f"{pct}%")
    c5.metric("Total Sessions",    total_s)

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        section("📋 Today's Attendance")
        if today_rec:
            df = build_attendance_df(today_rec)
            cols = [c for c in ["Roll No","Name","Dept","Verification","Time In"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No attendance recorded today. Start a Live Camera session.")

    with col_r:
        section("⚠️ Low Attendance Alerts")
        summary = get_attendance_summary()
        low = [s for s in summary if s["pct"] < ATTENDANCE_THRESHOLD and s["total_sessions"] > 0]
        if low:
            for s in low:
                card(
                    f"<div style='display:flex; justify-content:space-between; align-items:center'>"
                    f"<div><b>{s['name']}</b><br><small style='color:#94A3B8'>{s['roll_no']}</small></div>"
                    f"<div style='color:#F87171; font-size:18px; font-weight:800'>{s['pct']}%</div>"
                    f"</div>",
                    cls="vt-card-danger"
                )
        else:
            st.success("✅ All students above attendance threshold.")

        section("🏫 Today's Sessions")
        if sessions_today:
            for s in sessions_today:
                card(f"<b>{s['code']}</b> — {s['subject_name']}<br>"
                     f"Started: {s['start_time']}  |  Faculty: {s.get('faculty','—')}")
        else:
            st.info("No sessions started today.")

# ─── TAB 1: Live Camera ───────────────────────────────────────────────────────
with tabs[1]:
    section("📷 Live Attendance Camera")
    subs = subject_options()

    if not subs:
        st.warning("⚠️ No subjects found. Add subjects in the **Subjects** tab first.")
    else:
        col_cfg, col_btn = st.columns([3, 1])
        with col_cfg:
            selected_sub_label = st.selectbox("Select Subject", list(subs.keys()))
            subject_id = subs[selected_sub_label]
            faculty    = st.text_input("Faculty Name (optional)", placeholder="e.g. Dr. Ramesh Kumar")
            adv = st.expander("⚙️ Advanced Settings")
            with adv:
                thr = st.slider("Recognition Threshold", 0.25, 0.60,
                                st.session_state.threshold, 0.01,
                                help="Lower = stricter. Default 0.40")
                st.session_state.threshold = thr

        with col_btn:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if not st.session_state.cam_running:
                if st.button("▶  Start Session", type="primary", use_container_width=True):
                    db = load_face_db()
                    if not db:
                        st.error("No students enrolled. Go to Students tab.")
                    else:
                        sid = create_session(subject_id, faculty=faculty)
                        st.session_state.active_session_id = sid
                        st.session_state.stop_event.clear()
                        st.session_state.cam_running = True
                        q = queue.Queue(maxsize=2)
                        st.session_state.frame_queue = q
                        t = threading.Thread(
                            target=_camera_worker,
                            args=(q, st.session_state.stop_event,
                                  sid, st.session_state.threshold),
                            daemon=True,
                        )
                        t.start()
                        st.session_state.cam_thread = t
                        st.session_state.cam_started_at = time.time()
                        st.rerun()
            else:
                if st.button("⏹  Stop Session", type="primary", use_container_width=True):
                    st.session_state.stop_event.set()
                    st.session_state.cam_running = False
                    st.rerun()

        # ── Fragment: updates ONLY this component, no full-page flicker ──────
        @st.fragment(run_every=0.1)
        def _live_feed():
            if not st.session_state.cam_running:
                return  # fragment goes quiet once session ends

            sid = st.session_state.active_session_id
            st.caption(f"🎥 Session #{sid} live  •  Recognition running")

            # Non-blocking fetch — hold last frame when queue is momentarily empty
            try:
                frame = st.session_state.frame_queue.get_nowait()
                st.session_state["last_cam_frame"] = frame
            except queue.Empty:
                frame = st.session_state.get("last_cam_frame", None)

            if frame is not None:
                st.image(frame, channels="RGB", use_container_width=True)
            else:
                st.info("⏳ Starting camera — please wait…")

            # Detect if thread died naturally (after grace period)
            thread     = st.session_state.cam_thread
            started_at = st.session_state.get("cam_started_at", time.time())
            if thread and not thread.is_alive() and (time.time() - started_at > 6):
                st.session_state.cam_running = False
                st.session_state.pop("last_cam_frame", None)
                st.rerun()   # full rerun to show session summary

        if st.session_state.cam_running:
            _live_feed()
        elif st.session_state.active_session_id:
            sid  = st.session_state.active_session_id
            recs = get_session_attendance(sid)
            st.success(f"✅ Session ended — **{len(recs)} student(s)** marked present.")
            if recs:
                df = pd.DataFrame(recs)[["roll_no","name","time","confidence"]]
                df.columns = ["Roll No","Name","Time In","Distance"]
                df["Confidence"] = df["Distance"].apply(confidence_badge)
                st.write(df[["Roll No","Name","Time In","Confidence"]].to_html(
                    escape=False, index=False), unsafe_allow_html=True)

# ─── TAB 2: Students ──────────────────────────────────────────────────────────

with tabs[2]:
    section("👥 Enrolled Students")
    stud_list = get_all_students()
    enrolled_faces = {e["roll_no"] for e in list_enrolled()}

    # Enroll new student
    with st.expander("➕ Enroll New Student", expanded=not bool(stud_list)):
        with st.form("enroll_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            name    = c1.text_input("Full Name",    placeholder="e.g. Rahul Sharma")
            roll_no = c2.text_input("Roll No / ID", placeholder="e.g. 22CS101")
            c3, c4, c5 = st.columns(3)
            email   = c3.text_input("Email (opt.)", placeholder="student@college.edu")
            dept    = c4.selectbox("Department", [""] + DEPARTMENTS)
            year    = c5.selectbox("Year",       [""] + YEARS)
            force   = st.checkbox("Overwrite existing enrollment")
            submit  = st.form_submit_button("📸 Start Enrollment", type="primary")

        if submit:
            if not name or not roll_no:
                st.error("Name and Roll No are required.")
            else:
                add_student(roll_no, name, email, dept, year)
                stframe_e = st.empty()
                with st.spinner("Camera opening — follow pose guide…"):
                    res = enroll_student(name, roll_no, force=force, stframe=stframe_e)
                stframe_e.empty()
                if res == "exists":
                    st.warning(f"**{roll_no}** already enrolled. Enable 'Overwrite'.")
                elif res is True:
                    st.success(f"✅ **{name}** ({roll_no}) enrolled!")
                    st.rerun()
                else:
                    st.error("Enrollment incomplete. Try better lighting.")

    st.markdown("---")

    if not stud_list:
        st.info("No students enrolled yet.")
    else:
        search = st.text_input("", placeholder="🔍 Search by name, roll no or department…",
                               label_visibility="collapsed")
        for s in stud_list:
            if search and search.lower() not in (
                s["roll_no"] + s["name"] + s.get("department","")
            ).lower():
                continue

            face_badge = "🟢" if s["roll_no"] in enrolled_faces else "🔴"
            hist       = get_student_history(s["roll_no"])
            photo_path = os.path.join(FACES_DIR, s["roll_no"], "0.jpg")

            with st.expander(
                f"{face_badge} **{s['name']}** — {s['roll_no']}  "
                f"| {s.get('department','?')} {s.get('year','')}  "
                f"| {len(hist)} sessions attended"
            ):
                pc, dc = st.columns([1, 4])
                with pc:
                    if os.path.exists(photo_path):
                        st.image(photo_path, width=90, caption="Enrolled photo")
                    else:
                        st.markdown("📷 No photo")
                with dc:
                    st.markdown(
                        f"**Email:** {s.get('email','—')}  \n"
                        f"**Enrolled on:** {s.get('enrolled_at','—')[:10]}"
                    )
                    b1, b2 = st.columns(2)
                    if b1.button("🗑 Remove Student", key=f"del_{s['roll_no']}"):
                        delete_student_record(s["roll_no"])
                        delete_face_entry(s["roll_no"])
                        st.success(f"Removed {s['name']}")
                        st.rerun()
                    if b2.button("🔄 Re-enroll Face", key=f"reen_{s['roll_no']}"):
                        stfr = st.empty()
                        res  = enroll_student(s["name"], s["roll_no"],
                                              force=True, stframe=stfr)
                        stfr.empty()
                        st.success("Re-enrolled!") if res is True else st.error("Failed.")

                if hist:
                    df_h = pd.DataFrame(hist)[["date","time","subject_code","subject_name","confidence"]]
                    df_h.columns = ["Date","Time","Code","Subject","Distance"]
                    df_h["Confidence"] = df_h["Distance"].apply(confidence_badge)
                    st.write(df_h[["Date","Time","Code","Subject","Confidence"]].to_html(
                        escape=False, index=False), unsafe_allow_html=True)

# ─── TAB 3: Subjects ──────────────────────────────────────────────────────────
with tabs[3]:
    section("📚 Subject Management")
    with st.expander("➕ Add New Subject", expanded=True):
        with st.form("subj_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            code    = c1.text_input("Code",   placeholder="e.g. CS401")
            sname   = c2.text_input("Name",   placeholder="Machine Learning")
            sdept   = c3.selectbox("Dept",    [""] + DEPARTMENTS)
            credits = c4.number_input("Credits", 1, 6, 3)
            if st.form_submit_button("Add Subject", type="primary"):
                if not code or not sname:
                    st.error("Code and Name are required.")
                elif add_subject(code, sname, sdept, credits):
                    st.success(f"✅ Subject **{code}** added!")
                    st.rerun()
                else:
                    st.warning(f"Subject code **{code}** already exists.")

    st.markdown("---")
    section("📋 All Subjects")
    all_subs = get_all_subjects()
    if not all_subs:
        st.info("No subjects added yet.")
    else:
        for sub in all_subs:
            nsess = count_sessions(sub["id"])
            c1, c2 = st.columns([6, 1])
            with c1:
                card(
                    f"<b>{sub['code']}</b> — {sub['name']}"
                    f"&nbsp;&nbsp;<span class='badge badge-blue'>{sub.get('department','')}</span>"
                    f"&nbsp;<span class='badge badge-green'>{sub.get('credits',3)} credits</span>"
                    f"&nbsp;<span class='badge badge-yellow'>{nsess} sessions</span>"
                )
            with c2:
                if st.button("🗑", key=f"delsub_{sub['id']}",
                             help=f"Delete {sub['code']}"):
                    delete_subject(sub["id"])
                    st.rerun()

# ─── TAB 4: Records ───────────────────────────────────────────────────────────
with tabs[4]:
    section("📋 Today's Attendance Log")
    subs_map = subject_options()
    sub_filter_opts = {"All Subjects": None, **subs_map}

    col_s, col_f, col_exp = st.columns([3, 2, 1])
    with col_s:
        search4 = st.text_input("", placeholder="🔍 Search name or roll no…",
                                label_visibility="collapsed", key="rec_search")
    with col_f:
        sub_sel4 = st.selectbox("Filter by Subject", list(sub_filter_opts.keys()),
                                label_visibility="collapsed", key="rec_sub")
    with col_exp:
        exp_csv = st.button("⬇ CSV", use_container_width=True)

    if exp_csv:
        path = export_to_csv()
        with open(path, "rb") as f:
            st.download_button("Download CSV", f, "attendance_today.csv", "text/csv")

    sid4 = sub_filter_opts[sub_sel4]
    records4 = get_today_attendance(sid4)

    if search4:
        records4 = [r for r in records4 if
                    search4.lower() in r.get("name","").lower() or
                    search4.lower() in r.get("roll_no","").lower()]

    if records4:
        df4 = build_attendance_df(records4)
        cols4 = [c for c in ["Roll No","Name","Dept","Subject","Time In","Confidence"]
                 if c in df4.columns]
        st.write(df4[cols4].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No attendance records match your filters today.")

    # Manual attendance override
    st.markdown("---")
    section("✏️ Manual Attendance Entry")
    with st.expander("Mark or Override Attendance Manually"):
        all_sessions = get_all_sessions()
        if not all_sessions:
            st.info("No sessions exist yet.")
        else:
            sess_opts = {f"#{s['id']} — {s['code']} {s['date']} {s['start_time']}": s["id"]
                         for s in all_sessions}
            man_sess = st.selectbox("Session", list(sess_opts.keys()), key="man_sess")
            man_roll = st.text_input("Roll No", key="man_roll",
                                     placeholder="e.g. 22CS101")
            if st.button("Mark Present", type="primary", key="man_mark"):
                sid_m = sess_opts[man_sess]
                res   = mark_attendance(man_roll.strip(), sid_m, confidence=None)
                if res == "marked":
                    st.success(f"✅ {man_roll} marked present for session #{sid_m}")
                elif res == "duplicate":
                    st.info("Already marked for this session.")
                else:
                    st.error("Roll No not found or DB error.")

# ─── TAB 5: History ───────────────────────────────────────────────────────────
with tabs[5]:
    section("📅 Browse Attendance by Date")
    col_d, col_sub5 = st.columns([2, 3])
    with col_d:
        sel_date = st.date_input("Date", value=date.today(),
                                 max_value=date.today(), key="hist_date")
    with col_sub5:
        sub_sel5 = st.selectbox("Subject", list(sub_filter_opts.keys()),
                                key="hist_sub")
    sid5    = sub_filter_opts[sub_sel5]
    recs5   = get_attendance_by_date(sel_date.isoformat(), sid5)
    all_stu = get_all_students()

    if recs5:
        st.success(f"✅ {len(recs5)} student(s) present on {sel_date.strftime('%d %B %Y')}")
        df5 = build_attendance_df(recs5)
        cols5 = [c for c in ["Roll No","Name","Dept","Subject","Time In","Confidence"]
                 if c in df5.columns]
        st.write(df5[cols5].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning(f"No records for {sel_date.strftime('%d %B %Y')}.")

    # Absentee list
    st.markdown("---")
    section("🚫 Absentee List")
    present_rolls = {r["roll_no"] for r in recs5}
    absentees     = [s for s in all_stu if s["roll_no"] not in present_rolls]
    if absentees:
        df_abs = pd.DataFrame(absentees)[["roll_no","name","department","year"]]
        df_abs.columns = ["Roll No","Name","Department","Year"]
        st.dataframe(df_abs, use_container_width=True, hide_index=True)
        csv_abs = df_abs.to_csv(index=False).encode()
        st.download_button("⬇ Download Absentee List",
                           csv_abs, f"absent_{sel_date.isoformat()}.csv", "text/csv")
    else:
        st.success("All enrolled students were present.")

# ─── TAB 6: Analytics ─────────────────────────────────────────────────────────
with tabs[6]:
    section("📊 Attendance Analytics")
    PALETTE = ["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6",
               "#EC4899","#06B6D4","#84CC16","#F97316","#6366F1"]

    col_f6a, col_f6b = st.columns([2, 2])
    with col_f6a:
        sub_sel6 = st.selectbox("Subject", list(sub_filter_opts.keys()), key="ana_sub")
    with col_f6b:
        dept_filter = st.selectbox("Department", ["All"] + DEPARTMENTS, key="ana_dept")

    sid6    = sub_filter_opts[sub_sel6]
    summary = get_attendance_summary(sid6)

    if dept_filter != "All":
        summary = [s for s in summary if s.get("department") == dept_filter]

    if not summary:
        st.info("No data yet. Run camera sessions to see analytics.")
    else:
        df_sum = pd.DataFrame(summary)
        df_sum["Status"] = df_sum["pct"].apply(
            lambda p: "✅ OK" if p >= ATTENDANCE_THRESHOLD else "⚠️ Low"
        )
        threshold_line = ATTENDANCE_THRESHOLD

        # Row 1: bar chart + pie
        r1c1, r1c2 = st.columns([3, 2])
        with r1c1:
            st.markdown("**Attendance % per Student**")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_sum["name"], y=df_sum["pct"],
                marker_color=[PALETTE[i % len(PALETTE)] for i in range(len(df_sum))],
                marker_line_width=0,
                text=df_sum["pct"].apply(lambda x: f"{x}%"),
                textposition="outside",
                textfont=dict(color='#F8FAFC')
            ))
            fig_bar.add_hline(y=threshold_line, line_dash="dash",
                              line_color="#F87171",
                              annotation_text=f"{threshold_line}% Threshold",
                              annotation_position="right",
                              annotation_font=dict(color="#F87171"))
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", 
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                yaxis=dict(range=[0, 110], gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                xaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False),
                xaxis_tickangle=-30,
                margin=dict(t=40, b=10, l=0, r=0),
                showlegend=False, height=350,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        with r1c2:
            st.markdown("**Attendance Share**")
            fig_pie = px.pie(
                df_sum, values="days_present", names="name",
                color_discrete_sequence=PALETTE,
                hole=0.6,
            )
            fig_pie.update_traces(textinfo="label+percent", textfont_color="#F8FAFC", marker=dict(line=dict(color='#020617', width=2)))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                margin=dict(t=10, b=10, l=0, r=0),
                showlegend=False, height=350,
                font=dict(color="#94A3B8"),
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

        # Row 2: table + low-attendance alerts
        st.markdown("---")
        r2c1, r2c2 = st.columns([3, 2])
        with r2c1:
            st.markdown("**Student Breakdown**")
            disp = df_sum[["roll_no","name","department","days_present",
                           "total_sessions","pct","Status"]].copy()
            disp.columns = ["Roll No","Name","Dept","Present","Total","Pct %","Status"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

        with r2c2:
            st.markdown("**⚠️ Students Below Threshold**")
            low6 = df_sum[df_sum["pct"] < threshold_line]
            if low6.empty:
                st.success("All students above threshold 🎉")
            else:
                for _, row in low6.iterrows():
                    card(
                        f"<div style='display:flex; justify-content:space-between; align-items:center'>"
                        f"<div><b>{row['name']}</b><br><small style='color:#94A3B8'>{row['roll_no']}</small></div>"
                        f"<div style='color:#F87171; font-size:24px; font-weight:800'>{row['pct']}%</div>"
                        f"</div>",
                        cls="vt-card-danger"
                    )

        # Row 3: trend line (attendance per day)
        st.markdown("---")
        st.markdown("**Attendance Trend (Total Present per Day)**")
        trend = get_daily_trend(sid6)
        if trend:
            df_trend = pd.DataFrame(trend)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_trend["date"], y=df_trend["count"],
                mode='lines+markers',
                line=dict(color='#06B6D4', width=3),
                marker=dict(size=8, color='#06B6D4', symbol='circle'),
                fill='tozeroy',
                fillcolor='rgba(6, 182, 212, 0.1)',
            ))
            fig_trend.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", 
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                margin=dict(t=10, b=10, l=0, r=0),
                height=300,
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Not enough data to show a trend yet.")

# ─── TAB 7: Export ────────────────────────────────────────────────────────────
with tabs[7]:
    section("💾 Export Attendance Data")
    card("""
        Download the full attendance log as <b>CSV</b> or <b>Excel (.xlsx)</b>.<br>
        Filter by date range and subject before exporting.
    """)
    c1e, c2e, c3e = st.columns([2, 2, 2])
    with c1e:
        from_d = st.date_input("From Date",
                               value=date.today() - timedelta(days=30), key="exp_from")
    with c2e:
        to_d   = st.date_input("To Date", value=date.today(), key="exp_to")
    with c3e:
        sub_sel7 = st.selectbox("Subject", list(sub_filter_opts.keys()), key="exp_sub")
    sid7 = sub_filter_opts[sub_sel7]

    col_csv, col_xl = st.columns(2)
    with col_csv:
        if st.button("📄 Generate CSV", type="primary", use_container_width=True):
            path = export_to_csv(from_date=from_d.isoformat(),
                                 to_date=to_d.isoformat(), subject_id=sid7)
            with open(path, "rb") as f:
                st.download_button("⬇ Download CSV", f,
                                   os.path.basename(path), "text/csv",
                                   use_container_width=True)
    with col_xl:
        if st.button("📊 Generate Excel", type="primary", use_container_width=True):
            try:
                path = export_to_excel(from_date=from_d.isoformat(),
                                       to_date=to_d.isoformat(), subject_id=sid7)
                with open(path, "rb") as f:
                    st.download_button(
                        "⬇ Download Excel", f,
                        os.path.basename(path),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
            except ImportError:
                st.error("Install openpyxl: `pip install openpyxl`")

    # Preview
    st.markdown("---")
    section("👁 Preview Export")
    preview = get_attendance_by_date(date.today().isoformat(), sid7)
    if preview:
        df_prev = build_attendance_df(preview)
        cols_p  = [c for c in ["Roll No","Name","Dept","Subject","Date","Time In","Confidence"]
                   if c in df_prev.columns]
        st.dataframe(df_prev[cols_p], use_container_width=True, hide_index=True)
    else:
        st.info("No records match the selected filters.")
