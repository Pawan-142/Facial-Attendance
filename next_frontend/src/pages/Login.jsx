import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { Library, User, Lock, ArrowRight, Moon, Sun } from 'lucide-react';

export default function Login({ theme, setTheme }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await res.json();
      if (!res.ok || data.detail) {
        setError(data.detail || 'Login failed');
      } else {
        login(data.access_token, data.user);
      }
    } catch (err) {
      setError('Could not connect to server');
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', position: 'relative' }}>
      
      {/* Theme Toggle Button */}
      <button 
        onClick={toggleTheme}
        className="btn btn-outline" 
        style={{ position: 'absolute', top: 24, right: 24, padding: '8px 12px', display: 'flex', gap: 8, alignItems: 'center' }}
      >
        {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
        {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
      </button>

      {/* College/Academic Portal Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'var(--primary)', color: 'var(--primary-text)', padding: 16, borderRadius: '50%', marginBottom: 16 }}>
          <Library size={36} />
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>Smart Attendance Portal</h1>
        <p style={{ fontSize: 16, color: 'var(--text-muted)', marginTop: 8 }}>AI-Based Facial Recognition System</p>
      </div>

      {/* Centered Login Card */}
      <div className="metric-card" style={{ width: '100%', maxWidth: 400, padding: 40, boxShadow: '0 10px 25px rgba(0,0,0,0.1)', borderRadius: 16 }}>
        
        <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-main)', marginBottom: 24, textAlign: 'center' }}>Account Login</h2>
        
        {error && (
          <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: 6, marginBottom: 20, fontSize: 14, border: '1px solid #fca5a5', textAlign: 'center' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Roll No / User ID</label>
            <div style={{ position: 'relative', marginTop: 6 }}>
              <User size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input required value={username} onChange={e => setUsername(e.target.value)} className="form-input" placeholder="Enter ID" style={{ paddingLeft: 38 }} />
            </div>
          </div>
          
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Password</label>
            <div style={{ position: 'relative', marginTop: 6 }}>
              <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input required type="password" value={password} onChange={e => setPassword(e.target.value)} className="form-input" placeholder="Enter password" style={{ paddingLeft: 38 }} />
            </div>
          </div>
          
          <button type="submit" disabled={loading} className="btn btn-primary" style={{ marginTop: 8, height: 44, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8 }}>
            {loading ? 'Verifying...' : <>Login <ArrowRight size={16} /></>}
          </button>
        </form>
      </div>

      <div style={{ marginTop: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
        <p>Academic Project Submission</p>
      </div>
    </div>
  );
}
