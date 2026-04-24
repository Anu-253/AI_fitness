"""
backend/counters/squat_counter.py
-----------------------------------
Squat rep counter using MediaPipe landmarks.
Tracks knee angle: STANDING (> 160°) → SQUAT (< 90°) → STANDING.
"""

import numpy as np

try:
    import mediapipe as mp
    _PoseLandmark = mp.solutions.pose.PoseLandmark
except Exception:
    _PoseLandmark = None


# ── Per-instance state ────────────────────────────────────────────────────────

_state = {
    "reps":       0,
    "stage":      None,   # "standing" | "squat" | None
    "form_score": 0.0,
    "feedback":   [],
}


def reset():
    _state["reps"]       = 0
    _state["stage"]      = None
    _state["form_score"] = 0.0
    _state["feedback"]   = []


def _angle(a, b, c) -> float:
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = abs(np.degrees(radians))
    return 360 - angle if angle > 180 else angle


def process(landmarks) -> dict:
    """
    Squat counter using knee angle (hip → knee → ankle).
    STANDING = knee angle > 160°
    SQUAT    = knee angle < 90°
    Rep counted on: standing → squat → back to standing.
    """
    lm = landmarks

    # Use left leg as primary (right as backup)
    l_hip   = lm[_PoseLandmark.LEFT_HIP.value]
    l_knee  = lm[_PoseLandmark.LEFT_KNEE.value]
    l_ankle = lm[_PoseLandmark.LEFT_ANKLE.value]

    r_hip   = lm[_PoseLandmark.RIGHT_HIP.value]
    r_knee  = lm[_PoseLandmark.RIGHT_KNEE.value]
    r_ankle = lm[_PoseLandmark.RIGHT_ANKLE.value]

    l_angle = _angle(l_hip, l_knee, l_ankle)
    r_angle = _angle(r_hip, r_knee, r_ankle)
    avg_angle = (l_angle + r_angle) / 2.0

    feedback = []

    # ── Rep state machine ─────────────────────────────────────────────────
    if avg_angle > 160:
        if _state["stage"] == "squat":
            _state["reps"] += 1
            feedback.append(f"Rep {_state['reps']} complete!")
        _state["stage"] = "standing"

    if avg_angle < 90:
        _state["stage"] = "squat"

    # ── Back straightness check (shoulder-hip-knee) ───────────────────────
    try:
        l_shoulder = lm[_PoseLandmark.LEFT_SHOULDER.value]
        back_angle = _angle(l_shoulder, l_hip, l_knee)
        if back_angle < 150:
            feedback.append("Keep your chest up and back straight.")
    except Exception:
        pass

    # ── Knee symmetry check ───────────────────────────────────────────────
    if abs(l_angle - r_angle) > 15:
        feedback.append("Try to keep both knees even.")

    if not feedback:
        if _state["stage"] == "standing":
            feedback.append("Squat down — bend your knees past 90°.")
        elif _state["stage"] == "squat":
            feedback.append("Drive up through your heels to stand.")
        else:
            feedback.append(f"Knee angle: {int(avg_angle)}° — stand in front of the camera.")

    # ── Form score ────────────────────────────────────────────────────────
    symmetry   = max(0.0, 100.0 - abs(l_angle - r_angle))
    # ROM: reward going below 90° (deeper squat = better ROM score)
    depth_score = min(100.0, max(0.0, (160.0 - avg_angle) / 70.0 * 100.0))
    form_score  = round(symmetry * 0.5 + depth_score * 0.5, 1)

    _state["form_score"] = form_score
    _state["feedback"]   = feedback

    return {
        "reps":        _state["reps"],
        "form_score":  form_score,
        "feedback":    feedback,
        "left_angle":  round(l_angle, 1),
        "right_angle": round(r_angle, 1),
        "stage":       _state["stage"],
    }


def get_reps() -> int:
    return _state["reps"]
