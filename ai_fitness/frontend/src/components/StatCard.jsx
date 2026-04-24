import React from 'react';

export default function StatCard({ icon: Icon, label, value, sub, color = 'var(--accent, #00e5a0)', accent }) {
  return (
    <div style={{
      background: '#0f1923', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, padding: '20px 18px',
      borderTop: accent ? `2px solid ${color}` : '2px solid transparent',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        {Icon && <Icon size={16} color={color} />}
        <span style={{ fontSize: 10, color: '#4a6270', fontFamily: 'Orbitron, monospace', letterSpacing: '0.08em' }}>
          {label}
        </span>
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: '#e8f4f0', marginBottom: 4, fontFamily: 'Orbitron, monospace' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: '#3d5568' }}>{sub}</div>}
    </div>
  );
}
