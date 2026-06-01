import { useState } from 'react';
import { Modal } from '../components/Modal';

const API = 'http://localhost:8000';
const DEPTS = ['CSE', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL'];
const YEARS = ['1st Year', '2nd Year', '3rd Year', '4th Year'];

export default function Students({ students, onRefresh, toast }) {
  const [search, setSearch] = useState('');
  const [enrollForm, setEnrollForm] = useState({ name: '', roll_no: '', email: '', dept: '', year: '', force: false });
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [editStudent, setEditStudent] = useState(null);
  const [historyStudent, setHistoryStudent] = useState(null);
  const [history, setHistory] = useState([]);

  const filtered = students.filter(s =>
    !search || `${s.name} ${s.roll_no} ${s.department}`.toLowerCase().includes(search.toLowerCase())
  );

  const handleEnroll = async (e) => {
    e.preventDefault();
    setIsEnrolling(true);
    toast('Camera starting — follow the pose guide below!', 'warn');
    try {
      // POST returns immediately — enrollment runs in background thread
      await fetch(`${API}/api/enroll`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...enrollForm, dept: enrollForm.dept }),
      });

      // Poll /api/enroll/status every second until done
      let done = false;
      while (!done) {
        await new Promise(r => setTimeout(r, 1000));
        const s = await fetch(`${API}/api/enroll/status`).then(r => r.json());
        if (s.status === 'success') {
          toast('Enrolled successfully!');
          onRefresh();
          setEnrollForm({ name: '', roll_no: '', email: '', dept: '', year: '', force: false });
          done = true;
        } else if (s.status === 'exists') {
          toast(s.message || 'Already enrolled. Enable Overwrite.', 'warn');
          done = true;
        } else if (s.status === 'failed') {
          const msg = (s.message || 'Enrollment failed.').replace(/\*\*/g, '');
          toast(msg, 'error');
          done = true;
        }
        // status === 'running' → keep polling
      }
    } catch { toast('Server error', 'error'); }
    setIsEnrolling(false);
  };

  const handleDelete = async (roll_no, name) => {
    if (!window.confirm(`Remove ${name} (${roll_no})?`)) return;
    await fetch(`${API}/api/students/${roll_no}`, { method: 'DELETE' });
    toast(`Removed ${name}`); onRefresh();
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    await fetch(`${API}/api/students/${editStudent.roll_no}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: editStudent.name, email: editStudent.email, dept: editStudent.department, year: editStudent.year }),
    });
    toast('Student updated!'); setEditStudent(null); onRefresh();
  };

  const handleViewHistory = async (s) => {
    const res = await fetch(`${API}/api/students/${s.roll_no}/history`);
    setHistory(await res.json());
    setHistoryStudent(s);
  };

  const inp = { className: 'form-input', style: { marginBottom: 12 } };

  return (
    <>
      <div className="metric-card" style={{ marginBottom: 20 }}>
        <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Enroll New Student</div>
        <form onSubmit={handleEnroll} style={{ padding: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <input required placeholder="Full Name" value={enrollForm.name} onChange={e => setEnrollForm({ ...enrollForm, name: e.target.value })} pattern="[A-Za-z\s]+" title="Name must contain only letters and spaces" {...inp} />
            <input required placeholder="Roll No / ID" value={enrollForm.roll_no} onChange={e => setEnrollForm({ ...enrollForm, roll_no: e.target.value })} pattern="[a-zA-Z0-9]+" title="Roll No must be alphanumeric without spaces" {...inp} />
            <input type="email" placeholder="Email (optional)" value={enrollForm.email} onChange={e => setEnrollForm({ ...enrollForm, email: e.target.value })} {...inp} />
            <select value={enrollForm.dept} onChange={e => setEnrollForm({ ...enrollForm, dept: e.target.value })} {...inp}>
              <option value="">Department</option>
              {DEPTS.map(d => <option key={d}>{d}</option>)}
            </select>
            <select value={enrollForm.year} onChange={e => setEnrollForm({ ...enrollForm, year: e.target.value })} {...inp}>
              <option value="">Year</option>
              {YEARS.map(y => <option key={y}>{y}</option>)}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 14 }}>
              <input type="checkbox" checked={enrollForm.force} onChange={e => setEnrollForm({ ...enrollForm, force: e.target.checked })} />
              Overwrite existing
            </label>
          </div>
          <button disabled={isEnrolling} className="btn btn-primary" style={{ marginTop: 4 }}>
            {isEnrolling ? '📸 Look at Camera...' : '+ Capture & Enroll'}
          </button>
        </form>

        {/* Live enrollment camera feed with pose guide */}
        {isEnrolling && (
          <div style={{ marginTop: 20 }}>
            <div style={{ background: '#f0f4ff', border: '2px solid var(--primary)', borderRadius: 10, padding: '10px 16px', marginBottom: 12, color: 'var(--primary)', fontWeight: 600, fontSize: 14 }}>
              📷 Follow the pose instructions shown on the camera feed below. Hold each pose until captured.
            </div>
            <div style={{ borderRadius: 12, overflow: 'hidden', background: '#000', lineHeight: 0, boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
              <img
                src={`${API}/enrollment_feed`}
                alt="Enrollment Camera"
                style={{ width: '100%', maxHeight: 420, objectFit: 'contain', display: 'block' }}
              />
            </div>
            <p style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
              The oval guide turns green when your face is correctly aligned — hold still to capture.
            </p>
          </div>
        )}
      </div>

      <div className="metric-card">
        <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)", display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>All Students ({filtered.length})</span>
          <input placeholder="Search name / roll no..." value={search} onChange={e => setSearch(e.target.value)}
            className="form-input" style={{ width: 260, padding: '8px 12px', fontSize: 13, marginBottom: 0 }} />
        </div>
        <div style={{ padding: 24 }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Roll No</th><th>Name</th><th>Dept</th><th>Year</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 700, color: 'var(--primary)' }}>{s.roll_no}</td>
                  <td>{s.name}</td>
                  <td>{s.department || '—'}</td>
                  <td>{s.year || '—'}</td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => handleViewHistory(s)}>History</button>
                    <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => setEditStudent({ ...s, department: s.department || '' })}>Edit</button>
                    <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: 12 }} onClick={() => handleDelete(s.roll_no, s.name)}>Delete</button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan="5" style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>No students found</td></tr>}
            </tbody>
          </table>
        </div>
        </div>
      </div>

      {/* Edit Modal */}
      {editStudent && (
        <Modal title="Edit Student" onClose={() => setEditStudent(null)}>
          <form onSubmit={handleEdit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input required placeholder="Name" value={editStudent.name} onChange={e => setEditStudent({ ...editStudent, name: e.target.value })} pattern="[A-Za-z\s]+" title="Name must contain only letters and spaces" {...inp} />
            <input type="email" placeholder="Email" value={editStudent.email || ''} onChange={e => setEditStudent({ ...editStudent, email: e.target.value })} {...inp} />
            <select value={editStudent.department} onChange={e => setEditStudent({ ...editStudent, department: e.target.value })} {...inp}>
              <option value="">Department</option>
              {DEPTS.map(d => <option key={d}>{d}</option>)}
            </select>
            <select value={editStudent.year || ''} onChange={e => setEditStudent({ ...editStudent, year: e.target.value })} {...inp}>
              <option value="">Year</option>
              {YEARS.map(y => <option key={y}>{y}</option>)}
            </select>
            <button className="btn btn-primary">Save Changes</button>
          </form>
        </Modal>
      )}

      {/* History Modal */}
      {historyStudent && (
        <Modal title={`${historyStudent.name} — Attendance History`} onClose={() => setHistoryStudent(null)}>
          <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>{history.length} sessions attended</p>
          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead><tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '8px 0' }}>Date</th><th>Time</th><th>Subject</th>
              </tr></thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 0' }}>{h.date}</td>
                    <td>{h.time}</td>
                    <td>{h.subject_name || h.subject_code || '—'}</td>
                  </tr>
                ))}
                {history.length === 0 && <tr><td colSpan="3" style={{ padding: 24, textAlign: 'center' }}>No records</td></tr>}
              </tbody>
            </table>
          </div>
        </Modal>
      )}
    </>
  );
}
