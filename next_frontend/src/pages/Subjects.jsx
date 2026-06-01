import { useState } from 'react';
const API = 'http://localhost:8000';

export default function Subjects({ subjects, onRefresh, toast }) {
  const [form, setForm] = useState({ code: '', name: '', dept: '' });
  const [loading, setLoading] = useState(false);

  const handleAdd = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch(`${API}/api/subjects`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    setLoading(false);
    if (data.status === 'ok') { toast('Subject added!'); setForm({ code: '', name: '', dept: '' }); onRefresh(); }
    else toast('Subject code already exists', 'warn');
  };

  const handleDelete = async (code) => {
    if (!window.confirm(`Delete subject ${code}?`)) return;
    await fetch(`${API}/api/subjects/${code}`, { method: 'DELETE' });
    toast(`Deleted ${code}`); onRefresh();
  };

  const inp = { className: 'form-input' };

  return (
    <>
      <div className="metric-card">
        <div className="metric-title">Add New Subject</div>
        <form onSubmit={handleAdd} className="form-grid">
          <div className="form-group">
            <label>Code</label>
            <input required placeholder="e.g. CS301" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} pattern="[a-zA-Z0-9]+" title="Subject code must be alphanumeric without spaces" {...inp} />
          </div>
          <div className="form-group">
            <label>Subject Name</label>
            <input required placeholder="e.g. Data Structures" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} pattern="[A-Za-z0-9\s]+" title="Subject name must contain only letters, numbers, and spaces" {...inp} />
          </div>
          <div className="form-group">
            <label>Department</label>
            <select value={form.dept} onChange={e => setForm({ ...form, dept: e.target.value })} {...inp}>
              <option value="">All</option>
              {['CSE','IT','ECE','EEE','MECH','CIVIL'].map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <button disabled={loading} className="btn btn-primary">
            {loading ? 'Creating...' : '+ Create Subject'}
          </button>
        </form>
      </div>

      <div className="metric-card">
        <div className="metric-title">All Subjects ({subjects.length})</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Code</th><th>Name</th><th>Department</th><th>Year</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {subjects.map((s, i) => (
                <tr key={i}>
                  <td className="text-primary">{s.code}</td>
                  <td>{s.name}</td>
                  <td>{s.department || '—'}</td>
                  <td>{s.year || '—'}</td>
                  <td>
                    <button className="btn btn-danger" onClick={() => handleDelete(s.code)}>Delete</button>
                  </td>
                </tr>
              ))}
              {subjects.length === 0 && <tr><td colSpan="5" className="text-center">No subjects found</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
