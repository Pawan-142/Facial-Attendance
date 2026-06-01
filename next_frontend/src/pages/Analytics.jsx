import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
const API = 'http://localhost:8000';
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Analytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/analytics`).then(r => r.json()).then(setData).catch(() => {});
  }, []);

  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading analytics...</div>;

  const pieData = [
    { name: 'Above 75%', value: data.summary.filter(s => s.pct >= 75).length },
    { name: 'Below 75%', value: data.summary.filter(s => s.pct < 75).length },
  ];

  return (
    <>
      {/* Daily Trend Chart */}
      <div className="metric-card" style={{ marginBottom: 20 }}>
        <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Daily Attendance (Last 14 Days)</div>
        <div style={{ padding: 24 }}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.trend} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} name="Students Present" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Pie Chart */}
        <div className="metric-card">
          <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Attendance Status</div>
          <div style={{ padding: 24 }}>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map((_, i) => <Cell key={i} fill={i === 0 ? '#10b981' : '#ef4444'} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Low Attendance Alerts */}
        <div className="metric-card">
          <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }} style={{ color: '#ef4444' }}>Low Attendance Alerts</div>
          <div style={{ padding: 16, maxHeight: 260, overflowY: 'auto' }}>
            {data.alerts.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>All students above threshold</div>
            ) : data.alerts.map((s, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{s.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.roll_no} • {s.department}</div>
                </div>
                <div style={{ fontWeight: 800, fontSize: 18, color: '#ef4444' }}>{s.pct}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full Student Summary Table */}
      <div className="metric-card">
        <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Student Attendance Summary</div>
        <div style={{ padding: 24 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--text-muted)', fontSize: 13 }}>
                <th style={{ padding: '10px 0' }}>Student</th><th>Sessions Attended</th><th>Total</th><th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {data.summary.map((s, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 0' }}>
                    <div style={{ fontWeight: 600 }}>{s.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.roll_no}</div>
                  </td>
                  <td>{s.days_present}</td>
                  <td>{s.total_sessions}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ flex: 1, height: 6, background: 'var(--bg-hover)', borderRadius: 3 }}>
                        <div style={{ height: '100%', width: `${s.pct}%`, background: s.pct >= 75 ? '#10b981' : '#ef4444', borderRadius: 3 }} />
                      </div>
                      <span style={{ fontWeight: 700, color: s.pct >= 75 ? '#10b981' : '#ef4444', minWidth: 40 }}>{s.pct}%</span>
                    </div>
                  </td>
                </tr>
              ))}
              {data.summary.length === 0 && <tr><td colSpan="4" style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>No data yet</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
