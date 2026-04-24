import React, { useEffect, useState } from 'react';
import { getAnalytics } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import StatCard from '../components/StatCard';
import { Activity, Zap, Target, TrendingUp } from 'lucide-react';

export default function AnalyticsPage() {
  const { user }  = useAuth();
  const userId    = user?.user_id || localStorage.getItem('fitness_user_id') || 'default_user';
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    getAnalytics(userId, 30)
      .then(r => { setData(r.data); setLoading(false); })
      .catch(() => { setError('Could not load analytics.'); setLoading(false); });
  }, [userId]);

  const trend = data?.trend || 'stable';
  const trendLabel = { improving: '↑ Improving', declining: '↓ Declining', stable: '→ Stable' }[trend];
  const trendColor = { improving: '#00e5a0', declining: '#ff4d6d', stable: '#ffb347' }[trend];

  return (
    <div style={{ padding: '40px 36px', fontFamily: 'DM Sans, sans-serif' }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'Orbitron, monospace', fontSize: 22, fontWeight: 900, letterSpacing: '0.12em', color: '#e8f4f0', margin: '0 0 6px' }}>
          ANALYTICS
        </h1>
        <p style={{ color: '#4a6270', fontSize: 13, margin: 0 }}>Your lifetime fitness performance</p>
      </div>

      {error && (
        <div style={{ padding: '12px 18px', marginBottom: 24, background: 'rgba(255,179,71,0.08)', border: '1px solid rgba(255,179,71,0.3)', borderRadius: 12, fontSize: 13, color: '#ffb347' }}>
          ⚠ {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard icon={Activity} label="Total Sessions" value={loading ? '…' : (data?.total_sessions ?? 0)} sub="all time" accent />
        <StatCard icon={Target} label="Avg Score" value={loading ? '…' : (data?.avg_score?.toFixed(1) ?? '0')} sub="out of 100" color="#4da6ff" />
        <StatCard icon={Zap} label="Best Score" value={loading ? '…' : (data?.best_score?.toFixed(1) ?? '0')} sub="personal best" color="#ffb347" />
        <StatCard icon={TrendingUp} label="Trend" value={loading ? '…' : trendLabel} sub="recent sessions" color={trendColor} />
      </div>

      {/* Session table */}
      {!loading && data?.sessions?.length > 0 && (
        <div style={{ background: '#0f1923', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, overflow: 'hidden' }}>
          <div style={{ padding: '18px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
            <h2 style={{ fontFamily: 'Orbitron, monospace', fontSize: 12, color: '#8ab4c4', letterSpacing: '0.1em', margin: 0 }}>
              SESSION HISTORY
            </h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  {['Exercise', 'Reps', 'Duration', 'Date'].map(h => (
                    <th key={h} style={{ padding: '10px 24px', textAlign: 'left', color: '#3d5568', fontFamily: 'Orbitron, monospace', fontSize: 10, letterSpacing: '0.08em', fontWeight: 400, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.sessions.map((s, i) => (
                  <tr key={s.session_id || i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '12px 24px', color: '#e8f4f0' }}>{s.exercise_type?.replace('_', ' ') || 'Workout'}</td>
                    <td style={{ padding: '12px 24px', color: '#00e5a0', fontFamily: 'Orbitron, monospace' }}>{s.total_reps || 0}</td>
                    <td style={{ padding: '12px 24px', color: '#8ab4c4' }}>{s.duration_s ? `${Math.round(s.duration_s)}s` : '-'}</td>
                    <td style={{ padding: '12px 24px', color: '#4a6270', fontSize: 12 }}>{s.started_at ? new Date(s.started_at).toLocaleDateString() : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && (!data?.sessions || data.sessions.length === 0) && !error && (
        <div style={{ textAlign: 'center', padding: 60, color: '#3d5568', fontSize: 14 }}>
          No workout sessions yet. Complete a workout to see analytics.
        </div>
      )}
    </div>
  );
}
