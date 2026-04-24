import React from 'react';
import { Activity, BarChart2, Utensils, CheckSquare, LogOut, Dumbbell } from 'lucide-react';

const NAV = [
  { key: 'dashboard', label: 'DASHBOARD',  icon: Activity },
  { key: 'analytics', label: 'ANALYTICS',  icon: BarChart2 },
  { key: 'diet',      label: 'DIET',        icon: Utensils },
  { key: 'habits',    label: 'HABITS',      icon: CheckSquare },
];

export default function Sidebar({ active, onNav, user, onLogout }) {
  return (
    <div style={{
      width: 220, minHeight: '100vh', background: '#0a1017',
      borderRight: '1px solid rgba(0,229,160,0.08)',
      display: 'flex', flexDirection: 'column',
      fontFamily: 'DM Sans, sans-serif', flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '28px 20px 24px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #00e5a0, #00b87a)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Dumbbell size={18} color="#080c0f" />
          </div>
          <div>
            <div style={{ fontFamily: 'Orbitron, monospace', fontSize: 11, color: '#00e5a0', letterSpacing: '0.1em' }}>
              AI FITNESS
            </div>
            <div style={{ fontSize: 10, color: '#3d5568', marginTop: 1 }}>POSE TRACKING</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '16px 12px' }}>
        {NAV.map(({ key, label, icon: Icon }) => {
          const isActive = active === key;
          return (
            <button
              key={key}
              onClick={() => onNav(key)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px', marginBottom: 4,
                borderRadius: 10, border: 'none', cursor: 'pointer',
                background: isActive ? 'rgba(0,229,160,0.1)' : 'transparent',
                color: isActive ? '#00e5a0' : '#4a6270',
                fontFamily: 'Orbitron, monospace', fontSize: 10, letterSpacing: '0.08em',
                textAlign: 'left', transition: 'all 0.2s',
                borderLeft: isActive ? '2px solid #00e5a0' : '2px solid transparent',
              }}
              onMouseEnter={e => { if (!isActive) { e.currentTarget.style.color = '#8ab4c4'; e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; } }}
              onMouseLeave={e => { if (!isActive) { e.currentTarget.style.color = '#4a6270'; e.currentTarget.style.background = 'transparent'; } }}
            >
              <Icon size={15} />
              {label}
            </button>
          );
        })}
      </nav>

      {/* User + logout */}
      <div style={{ padding: '16px 12px', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
        <div style={{ fontSize: 12, color: '#4a6270', marginBottom: 10, padding: '0 4px' }}>
          <span style={{ color: '#8ab4c4' }}>{user?.username || 'Guest'}</span>
        </div>
        <button
          onClick={onLogout}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 8,
            padding: '9px 12px', borderRadius: 10, border: 'none',
            background: 'transparent', color: '#4a6270',
            fontFamily: 'Orbitron, monospace', fontSize: 10, letterSpacing: '0.08em',
            cursor: 'pointer', transition: 'all 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#ff4d6d'; e.currentTarget.style.background = 'rgba(255,77,109,0.06)'; }}
          onMouseLeave={e => { e.currentTarget.style.color = '#4a6270'; e.currentTarget.style.background = 'transparent'; }}
        >
          <LogOut size={14} /> LOGOUT
        </button>
      </div>
    </div>
  );
}
