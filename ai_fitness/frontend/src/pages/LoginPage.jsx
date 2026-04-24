import React, { useState } from 'react';
import { Dumbbell, Loader, User, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ onBack }) {
  const { login, register, guestLogin } = useAuth();
  const [mode,     setMode]     = useState('login');
  const [username, setUsername] = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const handleSubmit = async () => {
    if (!username || !password) { setError('Username and password are required.'); return; }
    setLoading(true);
    setError(null);
    try {
      if (mode === 'login') {
        await login(username, password);
      } else {
        if (!email) { setError('Email is required for registration.'); setLoading(false); return; }
        await register(username, email, password);
      }
    } catch (e) {
      setError(e?.response?.data?.detail || (mode === 'login' ? 'Login failed.' : 'Registration failed.'));
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%', background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 10, padding: '12px 14px',
    color: '#e8f0f8', fontSize: 14, outline: 'none',
    transition: 'border-color 0.2s', boxSizing: 'border-box',
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#080c0f',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'DM Sans, sans-serif', padding: 24,
    }}>
      <div style={{
        width: '100%', maxWidth: 400, background: '#111820',
        border: '1px solid rgba(0,229,160,0.12)',
        borderRadius: 24, padding: 40,
        boxShadow: '0 0 60px rgba(0,229,160,0.08)',
      }}>
        {/* Back button */}
        {onBack && (
          <button
            onClick={onBack}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'none', border: 'none', color: '#4a6270',
              fontSize: 12, cursor: 'pointer', marginBottom: 20, padding: 0,
              fontFamily: 'DM Sans, sans-serif',
              transition: 'color 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = '#00e5a0'; }}
            onMouseLeave={e => { e.currentTarget.style.color = '#4a6270'; }}
          >
            <ArrowLeft size={14} /> Back to home
          </button>
        )}

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, margin: '0 auto 14px',
            background: 'linear-gradient(135deg, #00e5a0, #00b87a)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 24px rgba(0,229,160,0.4)',
          }}>
            <Dumbbell size={26} color="#080c0f" />
          </div>
          <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 16, color: '#00e5a0', letterSpacing: '0.15em', margin: 0 }}>
            AI FITNESS
          </h1>
          <p style={{ color: '#3d5568', fontSize: 12, marginTop: 4 }}>LIVE POSE TRACKING</p>
        </div>

        {/* Mode tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {['login', 'register'].map(m => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(null); }}
              style={{
                flex: 1, padding: '10px 0',
                borderRadius: 10, border: 'none',
                background: mode === m ? 'rgba(0,229,160,0.12)' : 'transparent',
                color: mode === m ? '#00e5a0' : '#3d5568',
                fontFamily: 'Orbitron, monospace', fontSize: 10, letterSpacing: '0.1em',
                cursor: 'pointer', transition: 'all 0.2s',
                borderBottom: mode === m ? '2px solid #00e5a0' : '2px solid transparent',
              }}
            >
              {m.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
          <input
            placeholder="Username"
            value={username} onChange={e => setUsername(e.target.value)}
            style={inputStyle}
            onFocus={e => e.target.style.borderColor = 'rgba(0,229,160,0.4)'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
          />
          {mode === 'register' && (
            <input
              placeholder="Email"
              type="email"
              value={email} onChange={e => setEmail(e.target.value)}
              style={inputStyle}
              onFocus={e => e.target.style.borderColor = 'rgba(0,229,160,0.4)'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
          )}
          <input
            placeholder="Password"
            type="password"
            value={password} onChange={e => setPassword(e.target.value)}
            style={inputStyle}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            onFocus={e => e.target.style.borderColor = 'rgba(0,229,160,0.4)'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
          />
        </div>

        {error && (
          <div style={{
            padding: '10px 14px', marginBottom: 16,
            background: 'rgba(255,77,109,0.08)', border: '1px solid rgba(255,77,109,0.25)',
            borderRadius: 10, fontSize: 13, color: '#ff4d6d',
          }}>
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit} disabled={loading}
          style={{
            width: '100%', padding: '13px 0', borderRadius: 12, border: 'none',
            background: 'linear-gradient(135deg, #00e5a0, #00b87a)',
            color: '#080c0f', fontFamily: 'Orbitron, monospace', fontSize: 11,
            letterSpacing: '0.15em', fontWeight: 700,
            boxShadow: '0 4px 20px rgba(0,229,160,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            opacity: loading ? 0.6 : 1, cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >
          {loading && <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} />}
          {loading ? 'CONNECTING…' : mode === 'login' ? 'LOGIN' : 'CREATE ACCOUNT'}
        </button>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '18px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.06)' }} />
          <span style={{ color: '#3d5568', fontSize: 11 }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.06)' }} />
        </div>

        {/* Guest */}
        <button
          onClick={guestLogin}
          style={{
            width: '100%', padding: '12px 0', borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.08)', background: 'transparent',
            color: '#7a94a8', fontFamily: 'Orbitron, monospace', fontSize: 10,
            letterSpacing: '0.12em', cursor: 'pointer', transition: 'all 0.2s',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(0,229,160,0.3)'; e.currentTarget.style.color = '#00e5a0'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = '#7a94a8'; }}
        >
          <User size={13} /> CONTINUE AS GUEST
        </button>

        <p style={{ textAlign: 'center', fontSize: 11, color: '#3d5568', marginTop: 18, lineHeight: 1.6 }}>
          Backend must be running on <span style={{ color: '#00e5a0' }}>localhost:8000</span>
        </p>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
