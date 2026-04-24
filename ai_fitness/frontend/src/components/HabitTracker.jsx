import React, { useState } from 'react';
import { logHabit } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { Loader } from 'lucide-react';

const inputStyle = {
  width: '100%', background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
  padding: '11px 14px', color: '#e8f0f8', fontSize: 13,
  outline: 'none', boxSizing: 'border-box',
};

const labelStyle = {
  fontSize: 10, color: '#4a6270', fontFamily: 'Orbitron, monospace',
  letterSpacing: '0.08em', display: 'block', marginBottom: 6,
};

export default function HabitTracker() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    workout_done: false, water_glasses: 6, sleep_hours: 7,
    steps: 5000, mood: 'neutral', notes: '',
  });
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    setLoading(true); setError(null);
    try {
      const res = await logHabit({
        ...form,
        water_glasses: parseInt(form.water_glasses),
        sleep_hours:   parseFloat(form.sleep_hours),
        steps:         parseInt(form.steps),
        user_id:       user?.user_id || 'default_user',
      });
      setResult(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to log habit.');
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = result
    ? result.habit_score >= 75 ? '#00e5a0' : result.habit_score >= 50 ? '#ffb347' : '#ff4d6d'
    : '#00e5a0';

  return (
    <div style={{ fontFamily: 'DM Sans, sans-serif' }}>
      {/* Workout done toggle */}
      <div style={{ marginBottom: 14 }}>
        <label style={labelStyle}>WORKOUT TODAY?</label>
        <div style={{ display: 'flex', gap: 8 }}>
          {[true, false].map(v => (
            <button
              key={String(v)}
              onClick={() => set('workout_done', v)}
              style={{
                flex: 1, padding: '10px 0', borderRadius: 10, border: 'none', cursor: 'pointer',
                background: form.workout_done === v ? 'rgba(0,229,160,0.12)' : 'rgba(255,255,255,0.03)',
                color: form.workout_done === v ? '#00e5a0' : '#4a6270',
                fontFamily: 'Orbitron, monospace', fontSize: 10, letterSpacing: '0.08em',
                borderBottom: form.workout_done === v ? '2px solid #00e5a0' : '2px solid transparent',
              }}
            >
              {v ? 'YES' : 'NO'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div>
          <label style={labelStyle}>WATER (glasses)</label>
          <input type="number" min={0} max={20} value={form.water_glasses} onChange={e => set('water_glasses', e.target.value)} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>SLEEP (hours)</label>
          <input type="number" min={0} max={24} step={0.5} value={form.sleep_hours} onChange={e => set('sleep_hours', e.target.value)} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>STEPS</label>
          <input type="number" min={0} value={form.steps} onChange={e => set('steps', e.target.value)} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>MOOD</label>
          <select value={form.mood} onChange={e => set('mood', e.target.value)} style={inputStyle}>
            {['great','good','neutral','tired','bad'].map(m => (
              <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>NOTES (optional)</label>
        <input value={form.notes} onChange={e => set('notes', e.target.value)} placeholder="How did today go?" style={inputStyle} />
      </div>

      {error && (
        <div style={{ padding: '10px 14px', marginBottom: 14, background: 'rgba(255,77,109,0.08)', border: '1px solid rgba(255,77,109,0.25)', borderRadius: 10, fontSize: 13, color: '#ff4d6d' }}>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit} disabled={loading}
        style={{
          width: '100%', padding: '13px 0', borderRadius: 12, border: 'none',
          background: 'linear-gradient(135deg, #00e5a0, #00b87a)', color: '#080c0f',
          fontFamily: 'Orbitron, monospace', fontSize: 11, letterSpacing: '0.15em',
          fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1,
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          boxShadow: '0 4px 20px rgba(0,229,160,0.3)',
        }}
      >
        {loading && <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} />}
        {loading ? 'SAVING…' : 'LOG TODAY\'S HABITS'}
      </button>

      {result && (
        <div style={{ marginTop: 24, background: '#0f1923', border: '1px solid rgba(0,229,160,0.12)', borderRadius: 14, padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 36, fontWeight: 900, color: scoreColor, fontFamily: 'Orbitron, monospace' }}>
                {result.habit_score}
              </div>
              <div style={{ fontSize: 9, color: '#4a6270', fontFamily: 'Orbitron, monospace', letterSpacing: '0.08em' }}>HABIT SCORE</div>
            </div>
            <div style={{ flex: 1, fontSize: 13, color: '#8ab4c4', lineHeight: 1.5 }}>
              {result.behavior_prediction}
            </div>
          </div>

          {result.tips?.map((tip, i) => (
            <div key={i} style={{ fontSize: 12, color: '#4a6270', padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              💡 {tip}
            </div>
          ))}
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
