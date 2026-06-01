import { useState } from 'react';
import { Download } from 'lucide-react';
const API = 'http://localhost:8000';

export default function Export() {
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const csvUrl = () => {
    const p = new URLSearchParams();
    if (fromDate) p.set('from_date', fromDate);
    if (toDate) p.set('to_date', toDate);
    return `${API}/api/export/csv?${p}`;
  };

  const excelUrl = () => {
    const p = new URLSearchParams();
    if (fromDate) p.set('from_date', fromDate);
    if (toDate) p.set('to_date', toDate);
    return `${API}/api/export/excel?${p}`;
  };

  const inp = { className: 'form-input' };

  return (
    <div className="metric-card">
      <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Export Attendance Reports</div>
      <div style={{ padding: 32 }}>
        <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>
          Download attendance records as CSV or Excel. Filter by date range or leave blank to export all records.
        </p>

        <div style={{ display: 'flex', gap: 16, marginBottom: 32, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>From Date</label>
            <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} {...inp} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>To Date</label>
            <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} {...inp} />
          </div>
          <button onClick={() => { setFromDate(''); setToDate(''); }} className="btn btn-outline" style={{ height: 42 }}>
            Clear Dates
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <a href={csvUrl()} download>
            <button style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '14px 28px', borderRadius: 10, cursor: 'pointer', fontWeight: 700, fontSize: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
              <Download size={18} /> Download CSV
            </button>
          </a>
          <a href={excelUrl()} download>
            <button style={{ background: '#10b981', color: '#fff', border: 'none', padding: '14px 28px', borderRadius: 10, cursor: 'pointer', fontWeight: 700, fontSize: 15, display: 'flex', alignItems: 'center', gap: 10 }}>
              <Download size={18} /> Download Excel (.xlsx)
            </button>
          </a>
        </div>

        <div style={{ marginTop: 32, background: 'var(--bg-card-hover)', borderRadius: 12, padding: 20, fontSize: 14, color: 'var(--text-muted)' }}>
          <b>Exported fields:</b> Roll No, Name, Department, Year, Subject Code, Subject Name, Date, Time, Confidence Score
        </div>
      </div>
    </div>
  );
}
