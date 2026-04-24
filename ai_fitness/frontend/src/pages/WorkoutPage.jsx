/**
 * WorkoutPage.jsx
 * ---------------
 * Workout page with exercise type selector wired to useWorkout hook.
 */

import React, { useState } from "react";
import { useWorkout } from "../hooks/useWorkout"; 
import Chatbot from "./components/Chatbot";// adjust path if needed

export default function WorkoutPage() {
  // Selected exercise — passed into hook so backend knows which counter to use
  const [selectedExercise, setSelectedExercise] = useState("bicep_curl");

  const {
    videoRef,
    canvasRef,
    reps,
    formScore,
    feedback,
    leftAngle,
    rightAngle,
    isRunning,
    isSaving,
    error,
    lastSaved,
    startWorkout,
    stopWorkout,
  } = useWorkout(selectedExercise); // ← dynamic, not hardcoded

  const formColor =
    formScore >= 70 ? "#4ade80" : formScore >= 40 ? "#facc15" : "#f87171";

  const exerciseLabels = {
    bicep_curl: "Bicep Curl",
    push_up:    "Push Up",
    squat:      "Squat",
  };

  return (
    <div style={styles.page}>

      {/* ── LEFT PANEL: Workout ─────────────────────────────────────── */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <h2 style={styles.cardTitle}>WORKOUT</h2>
          <p style={styles.cardSub}>Live camera pose tracking</p>
        </div>

        {/* Exercise selector — disabled while workout is running */}
        <select
          value={selectedExercise}
          onChange={(e) => setSelectedExercise(e.target.value)}
          disabled={isRunning}
          style={{
            ...styles.dropdown,
            opacity: isRunning ? 0.5 : 1,
            cursor:  isRunning ? "not-allowed" : "pointer",
          }}
        >
          <option value="bicep_curl">Bicep Curl</option>
          <option value="push_up">Push Up</option>
          <option value="squat">Squat</option>
        </select>

        {/* Camera feed */}
        <div style={styles.videoWrapper}>
          {isRunning && (
            <span style={styles.liveBadge}>● LIVE</span>
          )}
          {isRunning && (
            <span style={styles.exerciseBadge}>
              {exerciseLabels[selectedExercise]}
            </span>
          )}
          <video ref={videoRef} style={styles.video} muted playsInline />
          {/* Hidden canvas used to snapshot frames */}
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>

        {/* Start / Stop button */}
        {!isRunning ? (
          <button style={styles.btnStart} onClick={startWorkout}>
            ▶ Start Workout
          </button>
        ) : (
          <button
            style={styles.btnStop}
            onClick={stopWorkout}
            disabled={isSaving}
          >
            {isSaving ? "Saving…" : "■ Stop Workout"}
          </button>
        )}

        {/* Stats row */}
        <div style={styles.statsRow}>
          <div style={styles.statBox}>
            <div style={styles.statLabel}>REPS</div>
            <div style={styles.statValue}>{reps}</div>
          </div>
          <div style={styles.statBox}>
            <div style={styles.statLabel}>FORM SCORE</div>
            <div style={{ ...styles.statValue, color: formColor }}>
              {formScore}%
            </div>
          </div>
          <div style={styles.statBox}>
            <div style={styles.statLabel}>LEFT °</div>
            <div style={styles.statValue}>{leftAngle}</div>
          </div>
          <div style={styles.statBox}>
            <div style={styles.statLabel}>RIGHT °</div>
            <div style={styles.statValue}>{rightAngle}</div>
          </div>
        </div>

        {/* Feedback */}
        {feedback.length > 0 && (
          <div style={styles.feedbackBox}>
            <div style={styles.feedbackLabel}>FEEDBACK</div>
            {feedback.map((f, i) => (
              <div key={i} style={styles.feedbackItem}>
                › {f}
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && <div style={styles.errorBox}>{error}</div>}

        {/* Save confirmation */}
        {lastSaved && !isRunning && (
          <div style={styles.savedBox}>
            ✓ Session saved! ID: {lastSaved.slice(-8)}
          </div>
        )}
      </div>
    
    </div>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────
const styles = {
  page: {
    display: "flex",
    gap: "24px",
    padding: "24px",
    background: "#0f172a",
    minHeight: "100vh",
    color: "#f1f5f9",
    fontFamily: "'Inter', sans-serif",
  },
  card: {
    background: "#1e293b",
    borderRadius: "12px",
    padding: "24px",
    flex: 1,
    maxWidth: "520px",
  },
  cardHeader: { marginBottom: "16px" },
  cardTitle: {
    color: "#4ade80",
    fontSize: "14px",
    fontWeight: 700,
    letterSpacing: "2px",
    margin: 0,
  },
  cardSub: { color: "#94a3b8", fontSize: "13px", margin: "4px 0 0" },

  dropdown: {
    width: "100%",
    padding: "10px 12px",
    background: "#0f172a",
    color: "#f1f5f9",
    border: "1px solid #334155",
    borderRadius: "8px",
    fontSize: "14px",
    marginBottom: "16px",
    outline: "none",
  },

  videoWrapper: {
    position: "relative",
    borderRadius: "8px",
    overflow: "hidden",
    background: "#0f172a",
    marginBottom: "16px",
    minHeight: "200px",
  },
  liveBadge: {
    position: "absolute",
    top: "10px",
    left: "10px",
    background: "rgba(0,0,0,0.6)",
    color: "#4ade80",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    zIndex: 10,
  },
  exerciseBadge: {
    position: "absolute",
    top: "10px",
    right: "10px",
    background: "rgba(0,0,0,0.6)",
    color: "#facc15",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "12px",
    zIndex: 10,
    fontWeight: 600,
  },
  video: {
    width: "100%",
    display: "block",
    borderRadius: "8px",
  },

  btnStart: {
    width: "100%",
    padding: "14px",
    background: "#4ade80",
    color: "#0f172a",
    border: "none",
    borderRadius: "8px",
    fontSize: "15px",
    fontWeight: 700,
    cursor: "pointer",
    marginBottom: "16px",
  },
  btnStop: {
    width: "100%",
    padding: "14px",
    background: "#ef4444",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "15px",
    fontWeight: 700,
    cursor: "pointer",
    marginBottom: "16px",
  },

  statsRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gap: "10px",
    marginBottom: "16px",
  },
  statBox: {
    background: "#0f172a",
    borderRadius: "8px",
    padding: "12px 8px",
    textAlign: "center",
  },
  statLabel: {
    color: "#64748b",
    fontSize: "10px",
    fontWeight: 600,
    letterSpacing: "1px",
    marginBottom: "4px",
  },
  statValue: {
    color: "#f1f5f9",
    fontSize: "22px",
    fontWeight: 700,
  },

  feedbackBox: {
    background: "#0f172a",
    borderRadius: "8px",
    padding: "12px 16px",
    marginBottom: "12px",
  },
  feedbackLabel: {
    color: "#64748b",
    fontSize: "10px",
    fontWeight: 600,
    letterSpacing: "1px",
    marginBottom: "8px",
  },
  feedbackItem: {
    color: "#cbd5e1",
    fontSize: "13px",
    marginBottom: "4px",
  },

  errorBox: {
    background: "#450a0a",
    border: "1px solid #ef4444",
    color: "#fca5a5",
    borderRadius: "8px",
    padding: "10px 14px",
    fontSize: "13px",
    marginBottom: "10px",
  },
  savedBox: {
    background: "#052e16",
    border: "1px solid #4ade80",
    color: "#86efac",
    borderRadius: "8px",
    padding: "10px 14px",
    fontSize: "13px",
  },
};
