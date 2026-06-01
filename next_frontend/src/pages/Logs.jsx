import { useState, useEffect } from 'react';
const API = 'http://localhost:8000';

export default function Logs({ subjects }) {
  const [logs, setLogs] = useState([]);
  const [logDate, setLogDate] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (logDate) params.set('log_date', logDate);
    if (subjectId) params.set('subject_id', subjectId);
    const res = await fetch(`${API}/api/logs?${params}`);
    setLogs(await res.json());
    setLoading(false);
  };

  useEffect(() => { fetchLogs(); }, [logDate, subjectId]);

  const selStyle = { className: 'form-input' };

  return (
    <div className="metric-card">
      <div className="metric-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <span>Attendance Logs ({logs.length} records)</span>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input type="date" value={logDate} onChange={e => setLogDate(e.target.value)} className="form-input" title="Filter by date" style={{ padding: '8px 12px', minHeight: '38px' }} />
          <select value={subjectId} onChange={e => setSubjectId(e.target.value)} className="form-input" style={{ padding: '8px 12px', minHeight: '38px' }}>
            <option value="">All Subjects</option>
            {subjects.map(s => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
          </select>
          <button onClick={() => { setLogDate(''); setSubjectId(''); }} className="btn btn-outline" style={{ padding: '8px 14px', height: '38px' }}>
            Clear
          </button>
        </div>
      </div>
      <div style={{ padding: 24 }}>
        {loading ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</div>
        ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Subject</th><th>Roll No</th><th>Name</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l, i) => (
                <tr key={i}>
                  <td style={{ color: 'var(--text-muted)' }}>{l.time}</td>
                  <td style={{ fontWeight: 600 }}>{l.subject_name || l.subject_code || '—'}</td>
                  <td className="text-primary">{l.roll_no}</td>
                  <td>{l.name}</td>
                </tr>
              ))}
              {logs.length === 0 && <tr><td colSpan="4" className="text-center" style={{ padding: 32 }}>No logs found</td></tr>}
            </tbody>
          </table>
        </div>
        )}
      </div>
    </div>
  );
}
