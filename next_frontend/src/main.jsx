import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './AuthContext.jsx'

const originalFetch = window.fetch;
window.fetch = async function (...args) {
  let [resource, config] = args;
  const token = localStorage.getItem('token');
  if (token && resource.toString().startsWith('http://localhost:8000')) {
    config = config || {};
    config.headers = { ...config.headers, 'Authorization': `Bearer ${token}` };
  }
  return originalFetch(resource, config);
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
