import React from 'react';
import WorkoutCamera from './WorkoutCamera';

export default function WorkoutCard({ onWorkoutEnd }) {
  return (
    <div
      style={{
        background: '#0f1923',
        border: '1px solid rgba(0,229,160,0.1)',
        borderRadius: 16,
        padding: 24,
        fontFamily: 'DM Sans, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 18 }}>
        <h2
          style={{
            fontFamily: 'Orbitron, monospace',
            fontSize: 13,
            color: '#00e5a0',
            letterSpacing: '0.12em',
            margin: '0 0 4px',
          }}
        >
          WORKOUT
        </h2>
        <p style={{ fontSize: 12, color: '#3d5568', margin: 0 }}>
          Live camera pose tracking
        </p>
      </div>

      {/* ✅ Simplified: Directly use working component */}
      <WorkoutCamera />
    </div>
  );
}