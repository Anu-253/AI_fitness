import React, { useEffect, useState, useCallback } from 'react';
import { getWorkoutHistory, deleteWorkout, deleteAllHistory } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { Trash2 } from 'lucide-react';

export default function HistoryChart() {
  const { user }   = useAuth();
  const userId     = user?.user_id || localStorage.getItem('fitness_user_id') || 'default_user';
  const [sessions, setSessions] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [deleting, setDeleting] = useState(null); // session_id being deleted

  const load = useCallback(() => {
    setLoading(true);
    getWorkoutHistory(userId, 10)
      .then(r => { setSessions(r.data.sessions || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (sessionId) => {
    setDeleting(sessionId);
    try {
      await deleteWorkout(sessionId);
      setSessions(prev => prev.filter(s => s._id !== sessionId && s.session_id !== sessionId));
    } catch (e) {
      console.error('Delete failed:', e);
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('Delete ALL workout history? This cannot be undone.')) return;
    setLoading(true);
    try {
      await deleteAllHistory(userId);
      setSessions([]);
    } catch (e) {
      console.error('Delete all failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const maxReps = Math.max(...sessions.map(s => s.total_reps || 0), 1);

  return (
    <div style={{
      background: '#0f1923', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 16, padding: 24, fontFamily: 'DM Sans, sans-serif', minHeight: 240,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ fontFamily: 'Orbitron, monospace', fontSize: 13, color: '#e8f4f0', letterSpacing: '0.12em', margin: 0 }}>
          RECENT SESSIONS
        </h2>
        {sessions.length > 0 && (
          <button
            onClick={handleDeleteAll}
            title="Delete all history"
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              background: 'rgba(255,77,109,0.08)', border: '1px solid rgba(255,77,109,0.2)',
              borderRadius: 8, padding: '5px 10px', color: '#ff4d6d',
              fontSize: 11, cursor: 'pointer', fontFamily: 'Orbitron, monospace',
              letterSpacing: '0.06em',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,77,109,0.18)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,77,109,0.08)'}
          >
            <Trash2 size={11} /> CLEAR ALL
          </button>
        )}
      </div>

      {loading && <div style={{ color: '#3d5568', fontSize: 13 }}>Loading history...</div>}

      {!loading && sessions.length === 0 && (
        <div style={{ color: '#3d5568', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
          No completed workouts yet. Start your first session!
        </div>
      )}

      {!loading && sessions.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {sessions.slice(0, 8).map((s, i) => {
            const sid = s._id || s.session_id || String(i);
            const isDeleting = deleting === sid;
            return (
              <div key={sid} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {/* Exercise label */}
                <div style={{ width: 90, fontSize: 11, color: '#4a6270', flexShrink: 0 }}>
                  {s.exercise_type?.replace(/_/g, ' ') || 'Workout'}
                </div>
                {/* Bar */}
                <div style={{ flex: 1, height: 8, background: '#080c0f', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 4,
                    width: `${Math.max(4, ((s.total_reps || 0) / maxReps) * 100)}%`,
                    background: 'linear-gradient(90deg, #00e5a0, #00b87a)',
                    transition: 'width 0.6s ease',
                  }} />
                </div>
                {/* Rep count */}
                <div style={{ width: 36, fontSize: 12, color: '#8ab4c4', textAlign: 'right', flexShrink: 0, fontFamily: 'Orbitron, monospace' }}>
                  {s.total_reps || 0}
                </div>
                {/* Delete button */}
                <button
                  onClick={() => handleDelete(sid)}
                  disabled={isDeleting}
                  title="Delete this session"
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: '#3d5568', padding: '2px 4px', borderRadius: 4,
                    opacity: isDeleting ? 0.4 : 1, transition: 'color 0.2s',
                    flexShrink: 0,
                  }}
                  onMouseEnter={e => e.currentTarget.style.color = '#ff4d6d'}
                  onMouseLeave={e => e.currentTarget.style.color = '#3d5568'}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 14, fontSize: 11, color: '#3d5568' }}>
        Showing last {sessions.length} sessions · reps per session
      </div>
    </div>
  );
}
