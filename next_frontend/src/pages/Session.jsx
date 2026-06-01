import { useState } from 'react';
import { Camera } from 'lucide-react';
const API = 'http://localhost:8000';

export default function Session({ subjects, toast }) {
  const [form, setForm] = useState({ subject_id: '', faculty: '' });
  const [isActive, setIsActive] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const handleStart = async (e) => {
    e.preventDefault();
    if (!form.subject_id) { toast('Select a subject first', 'warn'); return; }
    const res = await fetch(`${API}/api/session/start`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (data.status === 'ok') { setIsActive(true); setSessionId(data.session_id); toast('Session started!'); }
  };

  const handleStop = async () => {
    await fetch(`${API}/api/session/stop`, { method: 'POST' });
    setIsActive(false); setSessionId(null);
    toast('Session ended. Attendance saved.');
  };

  return (
    <div className="metric-card">
      <div className="metric-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Live Attendance Session</span>
        {isActive && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#ef4444', fontSize: 13, fontWeight: 700 }}>
            <span style={{ width: 8, height: 8, background: '#ef4444', borderRadius: '50%', animation: 'pulse 1.5s infinite' }}></span>
            RECORDING
          </span>
        )}
      </div>
      <div>
        {!isActive ? (
          <form onSubmit={handleStart} className="form-grid" style={{ marginBottom: 24 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Select Subject</label>
              <select required value={form.subject_id} onChange={e => setForm({ ...form, subject_id: e.target.value })} className="form-input">
                <option value="">Select Subject...</option>
                {subjects.map(s => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Faculty Name (optional)</label>
              <input placeholder="Faculty Name" value={form.faculty} onChange={e => setForm({ ...form, faculty: e.target.value })} className="form-input" />
            </div>
            <button className="btn btn-primary" style={{ height: '42px' }}>
              ▶ Start Attendance Session
            </button>
          </form>
        ) : (
          <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 10, padding: '10px 20px', color: '#166534', fontWeight: 600 }}>
              Session Active — Recognizing faces...
            </div>
            <button onClick={handleStop} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 24px', borderRadius: 8, cursor: 'pointer', fontWeight: 700 }}>
              ⏹ Stop Session
            </button>
          </div>
        )}

        {/* Camera Feed — only mounts when session is active to avoid holding camera */}
        <div style={{ borderRadius: 12, overflow: 'hidden', background: '#111', lineHeight: 0, boxShadow: '0 4px 20px rgba(0,0,0,0.15)', minHeight: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {isActive ? (
            <img
              src={`${API}/video_feed`}
              alt="Camera Feed"
              style={{ width: '100%', maxHeight: 480, objectFit: 'contain', display: 'block' }}
            />
          ) : (
            <div style={{ color: '#666', textAlign: 'center', padding: 48 }}>
              <Camera size={48} style={{ marginBottom: 12, opacity: 0.3 }} />
              <p style={{ fontSize: 14 }}>Start a session to activate the camera</p>
            </div>
          )}
        </div>
        {isActive && (
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 10 }}>
            Session ID: <code>{sessionId}</code> — Attendance is being recorded automatically when a face is recognised.
          </p>
        )}
      </div>
    </div>
  );
}
