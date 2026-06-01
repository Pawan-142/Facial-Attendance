import React, { useState, useEffect } from 'react';
import { Camera, Users, LayoutDashboard, Settings, History, Moon, Sun, BookOpen, Calendar, BarChart2, Download, LogOut } from 'lucide-react';
import { useToast, ToastContainer } from './components/Toast';
import { useAuth } from './AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import Subjects from './pages/Subjects';
import Session from './pages/Session';
import Analytics from './pages/Analytics';
import Logs from './pages/Logs';
import Export from './pages/Export';

const API = 'http://localhost:8000';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'teacher', 'student'] },
  { id: 'students',  label: 'Students',  icon: Users, roles: ['admin'] },
  { id: 'subjects',  label: 'Subjects',  icon: BookOpen, roles: ['admin'] },
  { id: 'session',   label: 'Live Session', icon: Camera, roles: ['admin', 'teacher'] },
  { id: 'analytics', label: 'Analytics', icon: BarChart2, roles: ['admin', 'teacher'] },
  { id: 'logs',      label: 'View Logs', icon: History, roles: ['admin', 'teacher', 'student'] },
  { id: 'export',    label: 'Export',    icon: Download, roles: ['admin', 'teacher'] },
  { id: 'settings',  label: 'Settings',  icon: Settings, roles: ['admin'] },
];

function App() {
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [tab, setTab] = useState('dashboard');
  const [stats, setStats] = useState({ total: 0, present: 0, absent: 0, feed: [], students: [], logs: [] });
  const [subjects, setSubjects] = useState([]);
  const { toasts, toast } = useToast();

  useEffect(() => {
    document.documentElement.className = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const fetchAll = async () => {
    if (!user) return;
    try {
      const [s, sub] = await Promise.all([
        fetch(`${API}/api/stats`).then(r => r.json()),
        fetch(`${API}/api/subjects`).then(r => r.json()),
      ]);
      setStats(s);
      setSubjects(sub);
    } catch {}
  };

  useEffect(() => {
    fetchAll();
    const iv = setInterval(fetchAll, 4000);
    return () => clearInterval(iv);
  }, [user]);

  if (!user) {
    return <Login theme={theme} setTheme={setTheme} />;
  }

  const renderPage = () => {
    switch (tab) {
      case 'dashboard':  return <Dashboard stats={stats} user={user} />;
      case 'students':   return user.role === 'admin' ? <Students students={stats.students || []} onRefresh={fetchAll} toast={toast} /> : null;
      case 'subjects':   return user.role === 'admin' ? <Subjects subjects={subjects} onRefresh={fetchAll} toast={toast} /> : null;
      case 'session':    return ['admin', 'teacher'].includes(user.role) ? <Session subjects={subjects} toast={toast} /> : null;
      case 'analytics':  return ['admin', 'teacher'].includes(user.role) ? <Analytics /> : null;
      case 'logs':       return <Logs subjects={subjects} />;
      case 'export':     return ['admin', 'teacher'].includes(user.role) ? <Export /> : null;
      case 'settings':   return user.role === 'admin' ? (
        <div className="metric-card" style={{ maxWidth: '600px' }}>
          <h2 className="metric-title" style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Settings</h2>
          <div style={{ color: 'var(--text-muted)' }}>
            <p><b>Backend API:</b> http://localhost:8000</p>
            <p style={{ marginTop: 12 }}><b>Camera:</b> Default webcam (index 0)</p>
            <p style={{ marginTop: 12 }}><b>Face Model:</b> ArcFace</p>
            <p style={{ marginTop: 12 }}><b>Database:</b> Firebase Firestore</p>
          </div>
        </div>
      ) : null;
      default: return null;
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column' }}>
        <div>
          <div className="sidebar-logo">
            <Camera size={24} color="var(--primary)" />
            VisionTrack
          </div>
          <nav className="sidebar-nav">
            {NAV.filter(n => n.roles.includes(user.role)).map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href="#"
                className={`nav-item ${tab === id ? 'active' : ''}`}
                onClick={e => { e.preventDefault(); setTab(id); }}
              >
                <Icon size={18} /> {label}
              </a>
            ))}
          </nav>
        </div>
        
        <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border)', paddingTop: 16 }}>
          <div style={{ padding: '0 16px 12px', fontSize: 13, color: 'var(--text-muted)' }}>
            Logged in as <b>{user.name || user.sub}</b> <br/>
            <span style={{ textTransform: 'capitalize', fontSize: 12, opacity: 0.7 }}>{user.role} Account</span>
          </div>
          <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')} className="theme-toggle" style={{ width: '100%', justifyContent: 'flex-start' }}>
            {theme === 'light' ? <><Moon size={18} /> Dark Mode</> : <><Sun size={18} /> Light Mode</>}
          </button>
          <button onClick={logout} className="theme-toggle" style={{ width: '100%', justifyContent: 'flex-start', color: '#ef4444', marginTop: 4 }}>
            <LogOut size={18} /> Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <h1 className="page-title" style={{ textTransform: 'capitalize' }}>{NAV.find(n => n.id === tab)?.label}</h1>
            <p className="page-subtitle">VisionTrack AI Attendance System</p>
          </div>
        </header>

        {renderPage()}
      </main>

      <ToastContainer toasts={toasts} />

      <style>{`
        @keyframes slideIn { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
      `}</style>
    </div>
  );
}

export default App;
