"""
backend/counters/push_up_counter.py
------------------------------------
Push-up rep counter using MediaPipe landmarks.
Tracks elbow angle: DOWN (bent < 90°) → UP (extended > 160°).
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
    "stage":      None,   # "up" | "down" | None
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
    Push-up counter.
    UP   = arms extended  (avg elbow angle > 160°)
    DOWN = arms bent      (avg elbow angle < 90°)
    Rep counted on: UP → DOWN → UP cycle (counted when returning to UP).
    """
    lm = landmarks

    l_shoulder = lm[_PoseLandmark.LEFT_SHOULDER.value]
    l_elbow    = lm[_PoseLandmark.LEFT_ELBOW.value]
    l_wrist    = lm[_PoseLandmark.LEFT_WRIST.value]

    r_shoulder = lm[_PoseLandmark.RIGHT_SHOULDER.value]
    r_elbow    = lm[_PoseLandmark.RIGHT_ELBOW.value]
    r_wrist    = lm[_PoseLandmark.RIGHT_WRIST.value]

    l_angle = _angle(l_shoulder, l_elbow, l_wrist)
    r_angle = _angle(r_shoulder, r_elbow, r_wrist)
    avg_angle = (l_angle + r_angle) / 2.0

    feedback = []

    # ── Rep state machine ─────────────────────────────────────────────────
    # Stage "up"   = start/top position (arms straight)
    # Stage "down" = bottom position (arms bent)
    # Rep counted when: down → back up

    if avg_angle > 160:
        if _state["stage"] == "down":
            _state["reps"] += 1
            feedback.append(f"Rep {_state['reps']} complete!")
        _state["stage"] = "up"

    if avg_angle < 90:
        _state["stage"] = "down"

    # ── Body alignment check (hip-shoulder angle) ─────────────────────────
    try:
        l_hip   = lm[_PoseLandmark.LEFT_HIP.value]
        l_ankle = lm[_PoseLandmark.LEFT_ANKLE.value]
        body_a  = _angle(l_hip, l_shoulder, l_ankle)
        if body_a < 150:
            feedback.append("Keep your body straight — don't sag your hips.")
    except Exception:
        pass

    # ── Elbow flare check ─────────────────────────────────────────────────
    if abs(l_angle - r_angle) > 20:
        feedback.append("Keep both arms even.")

    if not feedback:
        if _state["stage"] == "up":
            feedback.append("Lower your chest to the floor.")
        elif _state["stage"] == "down":
            feedback.append("Push up to complete the rep.")
        else:
            feedback.append(f"Angle: {int(avg_angle)}° — get into push-up position.")

    # ── Form score ────────────────────────────────────────────────────────
    symmetry   = max(0.0, 100.0 - abs(l_angle - r_angle))
    rom_score  = min(100.0, abs(avg_angle - 90.0) / 70.0 * 100.0)
    form_score = round(symmetry * 0.5 + rom_score * 0.5, 1)

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
