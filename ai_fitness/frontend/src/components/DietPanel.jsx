import React, { useState } from 'react';
import { getDietPlan } from '../utils/api';
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

export default function DietPanel() {
  const { user } = useAuth();
  const [form, setForm] = useState({ weight_kg: '', height_cm: '', age: '', gender: 'male', activity_level: 'moderate', goal: 'maintain' });
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.weight_kg || !form.height_cm || !form.age) { setError('Please fill in all fields.'); return; }
    setLoading(true); setError(null);
    try {
      const res = await getDietPlan({
        ...form,
        weight_kg: parseFloat(form.weight_kg),
        height_cm: parseFloat(form.height_cm),
        age:       parseInt(form.age),
        user_id:   user?.user_id || 'default_user',
      });
      setResult(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to compute diet plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: 'DM Sans, sans-serif' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        {[['weight_kg', 'WEIGHT (kg)'], ['height_cm', 'HEIGHT (cm)'], ['age', 'AGE']].map(([k, lbl]) => (
          <div key={k}>
            <label style={labelStyle}>{lbl}</label>
            <input type="number" value={form[k]} onChange={e => set(k, e.target.value)} style={inputStyle} />
          </div>
        ))}
        <div>
          <label style={labelStyle}>GENDER</label>
          <select value={form.gender} onChange={e => set('gender', e.target.value)} style={inputStyle}>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        <div>
          <label style={labelStyle}>ACTIVITY</label>
          <select value={form.activity_level} onChange={e => set('activity_level', e.target.value)} style={inputStyle}>
            {['sedentary','light','moderate','active','very_active'].map(a => (
              <option key={a} value={a}>{a.replace('_', ' ')}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={labelStyle}>GOAL</label>
          <select value={form.goal} onChange={e => set('goal', e.target.value)} style={inputStyle}>
            <option value="lose">Lose weight</option>
            <option value="maintain">Maintain</option>
            <option value="gain">Gain muscle</option>
          </select>
        </div>
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
        {loading ? 'COMPUTING…' : 'GET MY DIET PLAN'}
      </button>

      {result && (
        <div style={{ marginTop: 28 }}>
          {/* Macros */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 20 }}>
            {[
              { label: 'TARGET KCAL', value: result.target_calories },
              { label: 'PROTEIN (g)',  value: result.protein_g },
              { label: 'CARBS (g)',    value: result.carbs_g },
            ].map(({ label, value }) => (
              <div key={label} style={{ background: '#0f1923', border: '1px solid rgba(0,229,160,0.1)', borderRadius: 12, padding: '14px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 9, color: '#4a6270', fontFamily: 'Orbitron, monospace', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#00e5a0', fontFamily: 'Orbitron, monospace' }}>{value}</div>
              </div>
            ))}
          </div>

          <div style={{ marginBottom: 8, fontSize: 11, color: '#4a6270' }}>
            BMI: <span style={{ color: '#00e5a0' }}>{result.bmi}</span> ({result.bmi_category}) · TDEE: <span style={{ color: '#e8f4f0' }}>{result.tdee} kcal</span>
          </div>

          {/* Foods */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
            {[['✅ Eat', result.foods_to_eat, '#00e5a0'], ['❌ Avoid', result.foods_to_avoid, '#ff4d6d']].map(([title, foods, color]) => (
              <div key={title} style={{ background: '#0f1923', border: `1px solid ${color}22`, borderRadius: 12, padding: 14 }}>
                <div style={{ fontSize: 11, color, marginBottom: 8, fontWeight: 600 }}>{title}</div>
                {foods?.map(f => <div key={f} style={{ fontSize: 12, color: '#8ab4c4', marginBottom: 3 }}>• {f}</div>)}
              </div>
            ))}
          </div>

          {/* Tips */}
          {result.recommendations?.map((r, i) => (
            <div key={i} style={{ fontSize: 12, color: '#4a6270', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              💡 {r}
            </div>
          ))}
        </div>
      )}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
