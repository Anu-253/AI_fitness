import React, { useState, useEffect } from 'react';
import { Dumbbell, Zap, Activity, Target, TrendingUp, Camera, Brain, Shield, ChevronRight, Play } from 'lucide-react';
import Chatbot from "../components/Chatbot";
const FEATURES = [
  {
    icon: Camera,
    title: 'Live Pose Detection',
    desc: 'MediaPipe AI tracks your body in real-time via webcam — no wearables needed.',
    color: '#00e5a0',
  },
  {
    icon: Brain,
    title: 'Smart Form Coaching',
    desc: 'Get instant posture corrections and grade your form on every rep.',
    color: '#4da6ff',
  },
  {
    icon: Activity,
    title: 'Rep Counter',
    desc: 'Automatic, accurate rep counting for curls, push-ups and squats.',
    color: '#ffb347',
  },
  {
    icon: TrendingUp,
    title: 'Progress Analytics',
    desc: 'Track your improvement over time with detailed charts and trends.',
    color: '#ff6b9d',
  },
  {
    icon: Target,
    title: 'Diet Planner',
    desc: 'Personalised nutrition plans based on your BMI, goal and activity level.',
    color: '#a78bfa',
  },
  {
    icon: Shield,
    title: 'Habit Tracker',
    desc: 'Monitor sleep, hydration and stress to build a consistent fitness routine.',
    color: '#34d399',
  },
];

const STATS = [
  { value: '3+', label: 'Exercises Tracked' },
  { value: 'Real-time', label: 'AI Feedback' },
  { value: '100%', label: 'Free & Open Source' },
  { value: 'Zero', label: 'Hardware Needed' },
];

function AnimatedCounter({ target, suffix = '' }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (typeof target !== 'number') return;
    let start = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(start);
    }, 40);
    return () => clearInterval(timer);
  }, [target]);
  return <span>{typeof target === 'number' ? count + suffix : target}</span>;
}

export default function LandingPage({ onGetStarted }) {
  const [hoveredFeature, setHoveredFeature] = useState(null);
  const [showVideo, setShowVideo] = useState(false);

  return (
    <div style={{
      minHeight: '100vh',
      background: '#080c0f',
      fontFamily: 'DM Sans, sans-serif',
      color: '#e8f0f8',
      overflowX: 'hidden',
    }}>

      {/* ── NAV ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(8,12,15,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(0,229,160,0.08)',
        padding: '0 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        height: 64,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg,#00e5a0,#00b87a)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(0,229,160,0.4)',
          }}>
            <Dumbbell size={18} color="#080c0f" />
          </div>
          <span style={{
            fontFamily: 'Orbitron, monospace', fontSize: 13,
            color: '#00e5a0', letterSpacing: '0.15em', fontWeight: 700,
          }}>AI FITNESS</span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={onGetStarted}
            style={{
              padding: '8px 20px', borderRadius: 8,
              border: '1px solid rgba(0,229,160,0.3)',
              background: 'transparent', color: '#00e5a0',
              fontFamily: 'Orbitron, monospace', fontSize: 10,
              letterSpacing: '0.1em', cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,229,160,0.08)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
          >
            LOGIN
          </button>
          <button
            onClick={onGetStarted}
            style={{
              padding: '8px 20px', borderRadius: 8, border: 'none',
              background: 'linear-gradient(135deg,#00e5a0,#00b87a)',
              color: '#080c0f', fontFamily: 'Orbitron, monospace', fontSize: 10,
              letterSpacing: '0.1em', fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(0,229,160,0.35)',
            }}
          >
            GET STARTED
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section style={{
        minHeight: '90vh',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        textAlign: 'center', padding: '60px 24px',
        position: 'relative',
      }}>
        {/* background glow blobs */}
        <div style={{
          position: 'absolute', top: '10%', left: '20%',
          width: 400, height: 400, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,229,160,0.07) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', bottom: '15%', right: '15%',
          width: 350, height: 350, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(77,166,255,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '6px 16px', borderRadius: 100,
          background: 'rgba(0,229,160,0.08)',
          border: '1px solid rgba(0,229,160,0.2)',
          marginBottom: 28,
        }}>
          <Zap size={12} color="#00e5a0" />
          <span style={{ fontSize: 12, color: '#00e5a0', letterSpacing: '0.1em', fontFamily: 'Orbitron, monospace' }}>
            AI-POWERED · REAL-TIME · FREE
          </span>
        </div>

        <h1 style={{
          fontFamily: 'Orbitron, monospace',
          fontSize: 'clamp(32px, 6vw, 72px)',
          fontWeight: 900, lineHeight: 1.1,
          letterSpacing: '0.04em',
          maxWidth: 800, marginBottom: 24,
        }}>
          YOUR <span style={{ color: '#00e5a0' }}>AI PERSONAL</span>
          <br />TRAINER
        </h1>

        <p style={{
          fontSize: 18, color: '#6b8a9e', maxWidth: 560,
          lineHeight: 1.7, marginBottom: 40,
        }}>
          Real-time pose detection via your webcam. Instant rep counting,
          form correction & progress analytics — no gym equipment required.
        </p>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            onClick={onGetStarted}
            style={{
              padding: '14px 36px', borderRadius: 12, border: 'none',
              background: 'linear-gradient(135deg,#00e5a0,#00b87a)',
              color: '#080c0f', fontFamily: 'Orbitron, monospace', fontSize: 12,
              letterSpacing: '0.15em', fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 8px 32px rgba(0,229,160,0.4)',
              display: 'flex', alignItems: 'center', gap: 10,
              transition: 'transform 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            START TRAINING FREE <ChevronRight size={16} />
          </button>
          <button
            onClick={() => setShowVideo(true)}
            style={{
              padding: '14px 36px', borderRadius: 12,
              border: '1px solid rgba(255,255,255,0.12)',
              background: 'rgba(255,255,255,0.04)',
              color: '#e8f0f8', fontFamily: 'Orbitron, monospace', fontSize: 12,
              letterSpacing: '0.12em', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 10,
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(0,229,160,0.3)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)'; }}
          >
            <Play size={14} /> HOW IT WORKS
          </button>
        </div>

        {/* hero visual */}
        <div style={{
          marginTop: 64, width: '100%', maxWidth: 800,
          background: 'linear-gradient(180deg, rgba(0,229,160,0.04) 0%, transparent 100%)',
          border: '1px solid rgba(0,229,160,0.1)',
          borderRadius: 24, padding: 32,
          position: 'relative',
        }}>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16,
          }}>
            {[
              { label: 'REPS', value: '24', color: '#00e5a0', icon: Activity },
              { label: 'FORM SCORE', value: '92', color: '#4da6ff', icon: Target },
              { label: 'GRADE', value: 'A+', color: '#ffb347', icon: Zap },
            ].map(({ label, value, color, icon: Icon }) => (
              <div key={label} style={{
                background: 'rgba(255,255,255,0.02)',
                border: `1px solid ${color}22`,
                borderRadius: 16, padding: '20px 16px', textAlign: 'center',
              }}>
                <Icon size={20} color={color} style={{ marginBottom: 8 }} />
                <div style={{ fontSize: 32, fontWeight: 900, color, fontFamily: 'Orbitron, monospace' }}>
                  {value}
                </div>
                <div style={{ fontSize: 11, color: '#4a6270', letterSpacing: '0.1em', marginTop: 4 }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
          <div style={{
            marginTop: 20, padding: '12px 16px',
            background: 'rgba(0,229,160,0.05)', borderRadius: 10,
            fontSize: 12, color: '#00e5a0', textAlign: 'center', letterSpacing: '0.05em',
          }}>
            🎯 Keep elbows close to body · Slow down the descent for better gains
          </div>
        </div>
      </section>

      {/* ── STATS BAR ── */}
      <section style={{
        background: 'rgba(0,229,160,0.03)',
        borderTop: '1px solid rgba(0,229,160,0.08)',
        borderBottom: '1px solid rgba(0,229,160,0.08)',
        padding: '40px 40px',
      }}>
        <div style={{
          maxWidth: 900, margin: '0 auto',
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 24,
        }}>
          {STATS.map(({ value, label }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{
                fontFamily: 'Orbitron, monospace', fontSize: 28, fontWeight: 900,
                color: '#00e5a0', marginBottom: 6,
              }}>
                {value}
              </div>
              <div style={{ fontSize: 13, color: '#4a6270' }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section style={{ padding: '80px 40px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <h2 style={{
            fontFamily: 'Orbitron, monospace', fontSize: 28,
            fontWeight: 900, letterSpacing: '0.08em',
            color: '#e8f0f8', marginBottom: 12,
          }}>
            EVERYTHING YOU NEED
          </h2>
          <p style={{ color: '#4a6270', fontSize: 15, maxWidth: 480, margin: '0 auto' }}>
            A complete AI fitness stack. Just open your browser and start moving.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 20,
        }}>
          {FEATURES.map(({ icon: Icon, title, desc, color }, i) => (
            <div
              key={title}
              onMouseEnter={() => setHoveredFeature(i)}
              onMouseLeave={() => setHoveredFeature(null)}
              style={{
                background: hoveredFeature === i
                  ? `rgba(${color === '#00e5a0' ? '0,229,160' : color === '#4da6ff' ? '77,166,255' : '255,179,71'},0.06)`
                  : 'rgba(255,255,255,0.02)',
                border: `1px solid ${hoveredFeature === i ? color + '30' : 'rgba(255,255,255,0.06)'}`,
                borderRadius: 20, padding: 28,
                transition: 'all 0.25s',
                cursor: 'default',
              }}
            >
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: color + '15',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: 16,
              }}>
                <Icon size={20} color={color} />
              </div>
              <h3 style={{
                fontFamily: 'Orbitron, monospace', fontSize: 12,
                letterSpacing: '0.12em', color: '#e8f0f8',
                marginBottom: 8,
              }}>
                {title}
              </h3>
              <p style={{ fontSize: 13, color: '#4a6270', lineHeight: 1.6 }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section style={{
        padding: '80px 40px',
        background: 'rgba(0,229,160,0.02)',
        borderTop: '1px solid rgba(0,229,160,0.06)',
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{
            fontFamily: 'Orbitron, monospace', fontSize: 24,
            fontWeight: 900, letterSpacing: '0.08em',
            marginBottom: 48,
          }}>
            HOW IT WORKS
          </h2>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 8,
          }}>
            {[
              { step: '01', title: 'Create Account', desc: 'Sign up for free in under 30 seconds', color: '#00e5a0' },
              { step: '02', title: 'Allow Camera', desc: 'Grant webcam access to enable pose tracking', color: '#4da6ff' },
              { step: '03', title: 'Pick Exercise', desc: 'Choose curl, push-up, or squat and hit start', color: '#ffb347' },
              { step: '04', title: 'Train Smarter', desc: 'Get live feedback and track your progress', color: '#ff6b9d' },
            ].map(({ step, title, desc, color }, i) => (
              <React.Fragment key={step}>
                <div style={{ padding: '24px 16px', textAlign: 'center' }}>
                  <div style={{
                    fontFamily: 'Orbitron, monospace', fontSize: 11,
                    color, letterSpacing: '0.1em', marginBottom: 12, opacity: 0.7,
                  }}>
                    STEP {step}
                  </div>
                  <div style={{
                    width: 48, height: 48, borderRadius: '50%',
                    background: color + '15', border: `2px solid ${color}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 16px',
                    fontFamily: 'Orbitron, monospace', fontSize: 16, fontWeight: 900, color,
                  }}>
                    {i + 1}
                  </div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>{title}</h3>
                  <p style={{ fontSize: 12, color: '#4a6270', lineHeight: 1.6 }}>{desc}</p>
                </div>
                {i < 3 && (
                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#1e3040', fontSize: 20, padding: '0 4px',
                  }}>
                    →
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{
        padding: '80px 40px', textAlign: 'center',
      }}>
        <div style={{
          maxWidth: 600, margin: '0 auto',
          background: 'linear-gradient(135deg, rgba(0,229,160,0.06) 0%, rgba(77,166,255,0.04) 100%)',
          border: '1px solid rgba(0,229,160,0.15)',
          borderRadius: 32, padding: '56px 40px',
        }}>
          <div style={{
            width: 64, height: 64, borderRadius: 18, margin: '0 auto 20px',
            background: 'linear-gradient(135deg,#00e5a0,#00b87a)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 32px rgba(0,229,160,0.4)',
          }}>
            <Dumbbell size={28} color="#080c0f" />
          </div>
          <h2 style={{
            fontFamily: 'Orbitron, monospace', fontSize: 22,
            fontWeight: 900, letterSpacing: '0.08em', marginBottom: 12,
          }}>
            READY TO TRAIN SMARTER?
          </h2>
          <p style={{ color: '#4a6270', fontSize: 14, marginBottom: 32, lineHeight: 1.7 }}>
            Join for free. No credit card, no equipment,
            no excuses. Just open your webcam and start.
          </p>
          <button
            onClick={onGetStarted}
            style={{
              padding: '14px 48px', borderRadius: 12, border: 'none',
              background: 'linear-gradient(135deg,#00e5a0,#00b87a)',
              color: '#080c0f', fontFamily: 'Orbitron, monospace', fontSize: 12,
              letterSpacing: '0.15em', fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 8px 32px rgba(0,229,160,0.4)',
              transition: 'transform 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            CREATE FREE ACCOUNT →
          </button>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{
        borderTop: '1px solid rgba(255,255,255,0.06)',
        padding: '24px 40px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Dumbbell size={14} color="#00e5a0" />
          <span style={{ fontFamily: 'Orbitron, monospace', fontSize: 11, color: '#00e5a0', letterSpacing: '0.1em' }}>
            AI FITNESS
          </span>
        </div>
        <span style={{ fontSize: 12, color: '#2a3a48' }}>
          Powered by MediaPipe · FastAPI · React
        </span>
      </footer>

      {/* ── VIDEO MODAL ── */}
      {showVideo && (
        <div
          onClick={() => setShowVideo(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 24,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#111820', borderRadius: 24, padding: 40,
              border: '1px solid rgba(0,229,160,0.15)',
              maxWidth: 520, width: '100%', textAlign: 'center',
            }}
          >
            <h3 style={{
              fontFamily: 'Orbitron, monospace', color: '#00e5a0',
              letterSpacing: '0.12em', marginBottom: 16,
            }}>HOW IT WORKS</h3>
            <div style={{ color: '#6b8a9e', lineHeight: 1.8, fontSize: 14, marginBottom: 24 }}>
              <p>1️⃣ <strong style={{ color: '#e8f0f8' }}>Backend</strong> runs on port 8000 using FastAPI + MediaPipe</p>
              <p>2️⃣ <strong style={{ color: '#e8f0f8' }}>Webcam feed</strong> is processed server-side every second</p>
              <p>3️⃣ <strong style={{ color: '#e8f0f8' }}>Pose landmarks</strong> are analysed for reps + form score</p>
              <p>4️⃣ <strong style={{ color: '#e8f0f8' }}>React UI</strong> polls the API and shows live feedback</p>
            </div>
            <button
              onClick={() => setShowVideo(false)}
              style={{
                padding: '10px 32px', borderRadius: 10, border: 'none',
                background: 'rgba(0,229,160,0.15)', color: '#00e5a0',
                fontFamily: 'Orbitron, monospace', fontSize: 10,
                letterSpacing: '0.1em', cursor: 'pointer',
              }}
            >
              GOT IT
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
