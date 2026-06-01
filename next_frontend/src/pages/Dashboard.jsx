import { Users, CheckCircle, XCircle, CalendarX2 } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard({ stats, user }) {
  const isStudent = user?.role === 'student';
  const pct = stats.total > 0 ? Math.round((stats.present / stats.total) * 100) : 0;
  const alerts = isStudent ? [] : (stats.students?.filter(s => s.pct !== undefined && s.pct < 75) || []);
  const analytics = stats.student_analytics;
  
  const overallPct = analytics?.total_sessions > 0 ? Math.round((analytics.total_attended / analytics.total_sessions) * 100) : 0;
  const pieData = [
    { name: 'Attended', value: analytics?.total_attended || 0 },
    { name: 'Missed', value: (analytics?.total_sessions || 0) - (analytics?.total_attended || 0) }
  ];
  const COLORS = ['#22c55e', '#ef4444'];

  return (
    <>
      {/* Alert Banner */}
      {alerts.length > 0 && (
        <div style={{ background: '#fef3c7', border: '1px solid #f59e0b', borderRadius: 10, padding: '12px 20px', marginBottom: 20, color: '#92400e', fontWeight: 600 }}>
          ⚠️ {alerts.length} student(s) below 75% attendance threshold
        </div>
      )}

      {/* Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header"><span>{isStudent ? "My Profile" : "Total Enrolled"}</span><Users size={20} /></div>
          <h2>{isStudent ? (stats.total > 0 ? 'Active' : 'Unenrolled') : stats.total}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>{isStudent ? "Face Data Status" : "Database records"}</p>
        </div>
        <div className="metric-card">
          <div className="metric-header"><span>{isStudent ? "My Status Today" : "Present Today"}</span><CheckCircle size={20} /></div>
          <h2 style={{ color: 'var(--success)' }}>{isStudent ? (stats.present > 0 ? "Present" : "—") : stats.present}</h2>
          <p style={{ color: 'var(--success)', fontSize: 13, fontWeight: 600 }}>{isStudent ? "Attendance marked" : "Attendance marked"}</p>
        </div>
        <div className="metric-card">
          <div className="metric-header"><span>{isStudent ? "Missed Today" : "Absent Today"}</span><XCircle size={20} /></div>
          <h2 style={{ color: 'var(--danger)' }}>{isStudent ? (stats.total > 0 && stats.present === 0 ? "Absent" : "—") : stats.absent}</h2>
          <p style={{ color: 'var(--danger)', fontSize: 13, fontWeight: 600 }}>{isStudent ? "Not marked" : "Pending"}</p>
        </div>
        <div className="metric-card">
          <div className="metric-header"><span>{isStudent ? "Daily Completion" : "Today Rate"}</span></div>
          <h2 style={{ color: pct >= 75 ? 'var(--success)' : 'var(--danger)' }}>{pct}%</h2>
          <div style={{ height: 6, background: 'var(--bg-hover)', borderRadius: 3, marginTop: 8 }}>
            <div style={{ height: '100%', width: `${pct}%`, background: pct >= 75 ? 'var(--success)' : 'var(--danger)', borderRadius: 3, transition: 'width 0.5s' }} />
          </div>
        </div>
      </div>

      {isStudent && analytics ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24, marginTop: 24 }}>
          {/* Lifetime Percentage Chart */}
          <div className="metric-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "8px", color: "var(--text-main)", alignSelf: 'flex-start' }}>Overall Attendance</div>
            <div style={{ position: 'relative', width: 200, height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" stroke="none">
                    {pieData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-main)' }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-main)' }}>{overallPct}%</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: '50%', background: COLORS[0] }}/> <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Attended ({analytics.total_attended})</span></div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: '50%', background: COLORS[1] }}/> <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Missed ({analytics.total_sessions - analytics.total_attended})</span></div>
            </div>
          </div>

          {/* Monthly Trend Bar Chart */}
          <div className="metric-card">
            <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Monthly Trend</div>
            <div style={{ width: '100%', height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.monthly_trend}>
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} allowDecimals={false} />
                  <Tooltip cursor={{ fill: 'var(--bg-hover)' }} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-main)' }} />
                  <Bar dataKey="attended" name="Attended" fill="var(--success)" radius={[4, 4, 0, 0]} barSize={30} />
                  <Bar dataKey="missed" name="Missed" fill="var(--danger)" radius={[4, 4, 0, 0]} barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          {/* Missed Classes */}
          <div className="metric-card" style={{ gridColumn: '1 / -1' }}>
            <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Missed Classes</div>
            <div className="feed-list">
              {analytics.missed_sessions?.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>Perfect attendance! No missed classes found.</div>
              ) : (
                analytics.missed_sessions?.map((item, idx) => (
                  <div className="feed-item" key={idx}>
                    <div className="user-info">
                      <div className="avatar" style={{ background: '#fef2f2', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <CalendarX2 size={18} />
                      </div>
                      <div>
                        <h4 style={{ fontSize: 15, fontWeight: 600 }}>
                          {item.subject_name || item.subject_id}
                          {item.count > 1 && <span style={{ fontSize: 13, color: 'var(--danger)', marginLeft: 8 }}>(x{item.count})</span>}
                        </h4>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{item.date} • {item.faculty}</p>
                      </div>
                    </div>
                    <div className="badge danger">Absent</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Original Recent Activity for Admins/Teachers */
        <div className="metric-card" style={{ marginTop: 24 }}>
          <div className="metric-title" style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--text-main)" }}>Recent Activity</div>
          <div className="feed-list">
            {stats.feed?.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>No attendance recorded today. Start a session.</div>
            ) : (
              stats.feed?.map((item, idx) => (
                <div className="feed-item" key={idx}>
                  <div className="user-info">
                    <div className="avatar" style={{ background: `hsl(${idx * 60}, 60%, 50%)`, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                      {item.name?.[0]?.toUpperCase()}
                    </div>
                    <div>
                      <h4 style={{ fontSize: 15, fontWeight: 600 }}>{item.name}</h4>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{item.time}</p>
                    </div>
                  </div>
                  <div className="badge success">{item.status}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </>
  );
}
