import React, { useState, useEffect, useCallback } from 'react';
import WorkoutCard from '../components/WorkoutCard';
import HistoryChart from '../components/HistoryChart';
import StatCard from '../components/StatCard';
import Chatbot from '../components/Chatbot';
import { Activity, Zap, Target, TrendingUp } from 'lucide-react';
import { getAnalytics } from '../utils/api';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();
  const userId = user?.user_id || localStorage.getItem('fitness_user_id') || 'default_user';

  const [analytics, setAnalytics] = useState(null);
  const [chartKey,  setChartKey]  = useState(0);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  const loadAnalytics = useCallback(() => {
    setLoading(true);
    setError(null);
    getAnalytics(userId, 30)
      .then(r => {
        setAnalytics(r.data);
        setLoading(false);
      })
      .catch(() => {
        setError('Backend not reachable. Start the backend on port 8000.');
        setLoading(false);
      });
  }, [userId]);

  useEffect(() => { loadAnalytics(); }, [loadAnalytics]);

  const handleWorkoutEnd = () => {
    setTimeout(() => {
      loadAnalytics();
      setChartKey(k => k + 1);
    }, 1200);
  };

  const trend = analytics?.trend || 'stable';
  const trendLabel = { improving: '↑ Improving', declining: '↓ Declining', stable: '→ Stable' }[trend];
  const trendColor = { improving: 'var(--accent)', declining: 'var(--red)', stable: 'var(--amber)' }[trend];

  const username = user?.username || localStorage.getItem('fitness_username') || 'Athlete';

  return (
    <div style={{ padding: '40px 36px' }}>

      {/* Page header */}
      <div style={{ marginBottom: 36 }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 900,
          letterSpacing: '0.1em', color: 'var(--text-primary)', marginBottom: 6,
        }}>
          DASHBOARD
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Welcome back, <span style={{ color: 'var(--accent)' }}>{username}</span> ·
          Live camera → MediaPipe pose detection → real-time rep counting & form scoring.
        </p>
      </div>

      {/* Backend error banner */}
      {error && (
        <div style={{
          padding: '12px 18px', marginBottom: 24,
          background: 'rgba(255,179,71,0.08)', border: '1px solid rgba(255,179,71,0.3)',
          borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--amber)',
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Stats row */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: 16, marginBottom: 32,
      }}>
        <StatCard
          icon={Activity} label="Total Sessions"
          value={loading ? '…' : (analytics?.total_sessions ?? 0)}
          sub="all time" accent
        />
        <StatCard
          icon={Target} label="Avg Score"
          value={loading ? '…' : (analytics ? analytics.avg_score.toFixed(1) : '0')}
          sub="out of 100" accent color="var(--blue)"
        />
        <StatCard
          icon={Zap} label="Best Score"
          value={loading ? '…' : (analytics ? analytics.best_score.toFixed(1) : '0')}
          sub="personal best" color="var(--amber)"
        />
        <StatCard
          icon={TrendingUp} label="Trend"
          value={loading ? '…' : trendLabel}
          sub="recent sessions" color={trendColor}
        />
      </div>

      {/* Main two-column layout */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1.6fr',
        gap: 24, alignItems: 'start',
      }}>
        <WorkoutCard onWorkoutEnd={handleWorkoutEnd} />
        <HistoryChart key={chartKey} />
      </div>

      {/* Info bar */}
      <div style={{
        marginTop: 28, padding: '14px 20px',
        background: 'var(--bg-card)', border: '1px solid var(--border-dim)',
        borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-muted)',
        display: 'flex', gap: 24, flexWrap: 'wrap',
      }}>
        <span>🎯 <strong style={{ color: 'var(--text-secondary)' }}>Live mode:</strong>{' '}
          Camera → MediaPipe → Rep counter → Form scorer → API → Dashboard (updates every 1s)
        </span>
        <span>📸 <strong style={{ color: 'var(--text-secondary)' }}>Needs:</strong>{' '}
          Backend running on <code style={{ color: 'var(--accent)', fontSize: 11 }}>localhost:8000</code> with webcam access
        </span>
      </div>

      {/* Floating fitness chatbot — position:fixed, no layout impact */}
      <Chatbot />

    </div>
  );
}