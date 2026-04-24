import { useRef, useEffect, useState, useCallback } from "react";
import Chatbot from "./Chatbot";

const API_BASE = "http://127.0.0.1:8000/api";
const CAPTURE_INTERVAL_MS = 1000;

const EXERCISES = [
  { value: "bicep_curl", label: "Bicep Curl" },
  { value: "push_up",    label: "Push Up"    },
  { value: "squat",      label: "Squat"      },
];

export default function WorkoutCamera() {
  const videoRef    = useRef(null);
  const canvasRef   = useRef(null);
  const intervalRef = useRef(null);
  const streamRef   = useRef(null);
  const startTimeRef = useRef(null);

  const [isActive,   setIsActive]   = useState(false);
  const [isLoading,  setIsLoading]  = useState(false);
  const [error,      setError]      = useState(null);
  const [analyzing,  setAnalyzing]  = useState(false);

  const [exerciseType, setExerciseType] = useState("bicep_curl");

  const [repCount,   setRepCount]   = useState(0);
  const [formScore,  setFormScore]  = useState(null);
  const [feedback,   setFeedback]   = useState([]);

  const repCountRef    = useRef(0);
  const formScoreRef   = useRef(0);
  const exerciseRef    = useRef("bicep_curl");

  useEffect(() => { exerciseRef.current = exerciseType; }, [exerciseType]);

  const captureFrame = useCallback(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
  }, []);

  const analyzeFrame = useCallback(async () => {
    const base64 = captureFrame();
    if (!base64) return;

    setAnalyzing(true);
    try {
      const bytes    = atob(base64);
      const arr      = new Uint8Array(bytes.length);
      for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
      const blob     = new Blob([arr], { type: "image/jpeg" });

      const fd = new FormData();
      fd.append("frame", blob, "frame.jpg");
      fd.append("exercise_type", exerciseRef.current);

      const response = await fetch(`${API_BASE}/analyze-frame`, {
        method: "POST",
        body: fd,
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();

      const r = data.reps      ?? 0;
      const s = data.form_score ?? null;
      setRepCount(r);
      setFormScore(s);
      setFeedback(Array.isArray(data.feedback) ? data.feedback : []);

      repCountRef.current  = r;
      formScoreRef.current = s ?? 0;

    } catch (err) {
      console.error("Analysis error:", err);
    } finally {
      setAnalyzing(false);
    }
  }, [captureFrame]);

  const saveWorkout = useCallback(async () => {
    const durationSec = startTimeRef.current
      ? Math.round((Date.now() - startTimeRef.current) / 1000)
      : 0;

    try {
      await fetch(`${API_BASE}/save-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id:       "default_user",
          exercise_type: exerciseRef.current,
          reps:          repCountRef.current,
          form_score:    formScoreRef.current,
          duration_sec:  durationSec,
        }),
      });
    } catch (err) {
      console.error("Save failed:", err);
    }
  }, []);

  const startCamera = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    setRepCount(0);
    setFormScore(null);
    setFeedback([]);
    repCountRef.current  = 0;
    formScoreRef.current = 0;

    try {
      await fetch(`${API_BASE}/analyze-frame/reset`, { method: "POST" });
    } catch (_) {}

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      startTimeRef.current = Date.now();
      setIsActive(true);
      intervalRef.current = setInterval(analyzeFrame, CAPTURE_INTERVAL_MS);
    } catch (err) {
      setError(
        err.name === "NotAllowedError" ? "Camera permission denied. Please allow camera access." :
        err.name === "NotFoundError"   ? "No camera found. Please connect a webcam." :
        `Camera error: ${err.message}`
      );
    } finally {
      setIsLoading(false);
    }
  }, [analyzeFrame]);

  const stopCamera = useCallback(() => {
    saveWorkout();
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    if (streamRef.current)   { streamRef.current.getTracks().forEach((t) => t.stop()); streamRef.current = null; }
    if (videoRef.current)    videoRef.current.srcObject = null;
    setIsActive(false);
    setRepCount(0);
    setFormScore(null);
    setFeedback([]);
  }, [saveWorkout]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const formScoreColor =
    formScore === null ? "#6b7280" :
    formScore >= 80    ? "#10b981" :
    formScore >= 50    ? "#f59e0b" : "#ef4444";

  return (
    <div className="workout-camera-root">
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* SELECT EXERCISE */}
      <div className="wc-exercise-selector">
        <label className="wc-ex-label" htmlFor="wc-ex-select">Select Exercise</label>
        <select
          id="wc-ex-select"
          className="wc-ex-select"
          value={exerciseType}
          onChange={(e) => setExerciseType(e.target.value)}
          disabled={isActive}
        >
          {EXERCISES.map((ex) => (
            <option key={ex.value} value={ex.value}>{ex.label}</option>
          ))}
        </select>
      </div>

      <div className="wc-video-wrapper">
        <video ref={videoRef} className="wc-video" autoPlay playsInline muted />
        {!isActive && (
          <div className="wc-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.9L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
            </svg>
            <p>Camera starts with workout</p>
          </div>
        )}
        {isActive && (
          <>
            <div className={`wc-live-badge ${analyzing ? "analyzing" : ""}`}>
              <span className="wc-live-dot" />
              {analyzing ? "Analyzing…" : "LIVE"}
            </div>
            <div className="wc-exercise-badge">
              {EXERCISES.find((e) => e.value === exerciseType)?.label}
            </div>
          </>
        )}
      </div>

      {error && <div className="wc-error">{error}</div>}

      <div className="wc-controls">
        {!isActive ? (
          <button className="wc-btn wc-btn-start" onClick={startCamera} disabled={isLoading}>
            {isLoading ? "Starting…" : "▶  Start Workout"}
          </button>
        ) : (
          <button className="wc-btn wc-btn-stop" onClick={stopCamera}>■  Stop Workout</button>
        )}
      </div>

      {isActive && (
        <div className="wc-stats">
          <div className="wc-stat-card">
            <span className="wc-stat-label">Reps</span>
            <span className="wc-stat-value">{repCount}</span>
          </div>
          <div className="wc-stat-card">
            <span className="wc-stat-label">Form Score</span>
            <span className="wc-stat-value" style={{ color: formScoreColor }}>
              {formScore !== null ? `${formScore}%` : "—"}
            </span>
          </div>
        </div>
      )}

      {isActive && feedback.length > 0 && (
        <div className="wc-feedback">
          <p className="wc-feedback-title">Feedback</p>
          <ul className="wc-feedback-list">
            {feedback.map((msg, i) => (
              <li key={i} className="wc-feedback-item">
                <span className="wc-feedback-bullet">›</span> {msg}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Floating fitness chatbot — position: fixed, won't affect layout */}
      <Chatbot />

      <style>{`
        .workout-camera-root { display:flex; flex-direction:column; gap:12px; width:100%; max-width:640px; font-family:inherit; }

        /* ── Exercise selector ── */
        .wc-exercise-selector { display:flex; flex-direction:column; gap:6px; }
        .wc-ex-label { font-size:10px; font-weight:700; letter-spacing:0.12em; color:rgba(0,229,160,0.5); text-transform:uppercase; margin:0; }
        .wc-ex-select { width:100%; padding:11px 14px; border-radius:8px; font-size:14px; font-weight:700; cursor:pointer; border:1px solid rgba(0,229,160,0.25); background:rgba(0,229,160,0.07); color:#00e5a0; outline:none; appearance:none; -webkit-appearance:none; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2300e5a0' stroke-width='2.5'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 14px center; letter-spacing:0.03em; transition:border-color .2s, box-shadow .2s; }
        .wc-ex-select:hover:not(:disabled) { border-color:rgba(0,229,160,0.5); background:rgba(0,229,160,0.11); }
        .wc-ex-select:disabled { opacity:0.35; cursor:not-allowed; }
        .wc-ex-select:focus { border-color:#00e5a0; box-shadow:0 0 0 2px rgba(0,229,160,0.18); }
        .wc-ex-select option { background:#0f1923; color:#fff; padding:8px; }

        /* ── Video ── */
        .wc-video-wrapper { position:relative; width:100%; aspect-ratio:4/3; background:#0d0d0d; border-radius:12px; overflow:hidden; border:1px solid rgba(255,255,255,0.08); }
        .wc-video { width:100%; height:100%; object-fit:cover; transform:scaleX(-1); }
        .wc-placeholder { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; color:rgba(255,255,255,0.3); font-size:14px; }
        .wc-live-badge { position:absolute; top:12px; left:12px; display:flex; align-items:center; gap:6px; background:rgba(0,0,0,0.55); backdrop-filter:blur(6px); border:1px solid rgba(255,255,255,0.1); border-radius:20px; padding:4px 10px; font-size:11px; font-weight:700; letter-spacing:0.08em; color:#fff; text-transform:uppercase; }
        .wc-live-badge.analyzing { color:#fbbf24; }
        .wc-live-dot { width:7px; height:7px; border-radius:50%; background:#10b981; animation:pulse-dot 1.2s ease-in-out infinite; }
        .wc-exercise-badge { position:absolute; top:12px; right:12px; background:rgba(0,0,0,0.55); backdrop-filter:blur(6px); border:1px solid rgba(16,185,129,0.3); border-radius:20px; padding:4px 10px; font-size:11px; font-weight:700; color:#10b981; }
        @keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

        /* ── Rest ── */
        .wc-error { background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:10px 14px; font-size:13px; color:#fca5a5; }
        .wc-controls { display:flex; justify-content:center; }
        .wc-btn { padding:10px 28px; border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; border:none; transition:opacity .2s,transform .1s; }
        .wc-btn:active { transform:scale(0.97); }
        .wc-btn:disabled { opacity:0.5; cursor:not-allowed; }
        .wc-btn-start { background:#10b981; color:#000; }
        .wc-btn-stop { background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.3); }
        .wc-stats { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
        .wc-stat-card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:4px; }
        .wc-stat-label { font-size:11px; text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.4); font-weight:600; }
        .wc-stat-value { font-size:28px; font-weight:700; color:#fff; line-height:1; transition:color .4s; }
        .wc-feedback { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:10px; padding:14px 16px; }
        .wc-feedback-title { font-size:11px; text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.4); font-weight:600; margin:0 0 8px; }
        .wc-feedback-list { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:6px; }
        .wc-feedback-item { font-size:13px; color:rgba(255,255,255,0.75); display:flex; gap:8px; line-height:1.4; }
        .wc-feedback-bullet { color:#10b981; font-weight:700; flex-shrink:0; }
      `}</style>
    </div>
  );
}