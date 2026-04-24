"""
backend/routers/analyze.py
--------------------------
POST /api/analyze-frame   — accepts multipart/form-data OR JSON base64
POST /api/analyze-frame/reset — resets rep counter

Self-contained MediaPipe bicep-curl / pushup rep counter.
No external ai_modules dependency.
"""

import base64
import logging
import os
from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

log    = logging.getLogger("backend.routers.analyze")
router = APIRouter()

# ── Exercise counter modules ──────────────────────────────────────────────────
# Each module exposes: process(landmarks) -> dict  and  reset() -> None
import sys, os as _os
_COUNTERS_PATH = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "counters"))
if _COUNTERS_PATH not in sys.path:
    sys.path.insert(0, _COUNTERS_PATH)

import push_up_counter
import squat_counter

# Map exercise_type string → counter module
# bicep_curl uses the existing inline logic (unchanged)
_COUNTER_MAP = {
    "push_up": push_up_counter,
    "squat":   squat_counter,
}

# ── Try to import MediaPipe ──────────────────────────────────────────────────
try:
    import mediapipe as mp
    _mp_pose      = mp.solutions.pose
    _PoseLandmark = mp.solutions.pose.PoseLandmark
    _pose_solver  = _mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    _MP_AVAILABLE = True
    log.info("MediaPipe Pose loaded successfully.")
except Exception as _mp_err:
    _MP_AVAILABLE = False
    log.warning("MediaPipe not available: %s — stub responses will be returned.", _mp_err)


# ── Rep counter state (server-side, per-process) ─────────────────────────────
_rep_state = {
    "reps":       0,
    "stage":      None,   # "up" | "down" | None
    "form_score": 0.0,
    "feedback":   [],
}


def _reset_counter():
    _rep_state["reps"]       = 0
    _rep_state["stage"]      = None
    _rep_state["form_score"] = 0.0
    _rep_state["feedback"]   = []


def _angle(a, b, c) -> float:
    """Angle at joint B formed by points A-B-C (degrees)."""
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = abs(np.degrees(radians))
    return 360 - angle if angle > 180 else angle


def _process_landmarks(landmarks) -> dict:
    """
    Bicep-curl rep counter using left + right arm elbow angle.
    Returns updated reps, form_score, feedback.
    """
    lm = landmarks

    # ── Left arm ────────────────────────────────────────────────────────
    l_shoulder = lm[_PoseLandmark.LEFT_SHOULDER.value]
    l_elbow    = lm[_PoseLandmark.LEFT_ELBOW.value]
    l_wrist    = lm[_PoseLandmark.LEFT_WRIST.value]

    # ── Right arm ───────────────────────────────────────────────────────
    r_shoulder = lm[_PoseLandmark.RIGHT_SHOULDER.value]
    r_elbow    = lm[_PoseLandmark.RIGHT_ELBOW.value]
    r_wrist    = lm[_PoseLandmark.RIGHT_WRIST.value]

    l_angle = _angle(l_shoulder, l_elbow, l_wrist)
    r_angle = _angle(r_shoulder, r_elbow, r_wrist)
    avg_angle = (l_angle + r_angle) / 2.0

    feedback = []

    # ── Rep state machine ────────────────────────────────────────────────
    # DOWN = arm extended  (angle > 160°)
    # UP   = arm curled    (angle < 40°)
    # Rep counted on: DOWN → UP transition

    if avg_angle > 160:
        _rep_state["stage"] = "down"

    if avg_angle < 40 and _rep_state["stage"] == "down":
        _rep_state["stage"]  = "up"
        _rep_state["reps"]  += 1
        feedback.append(f"Rep {_rep_state['reps']} complete!")

    # ── Form feedback ────────────────────────────────────────────────────
    # Check body posture: hip-shoulder-ear alignment
    try:
        l_hip  = lm[_PoseLandmark.LEFT_HIP.value]
        l_ear  = lm[_PoseLandmark.LEFT_EAR.value]
        body_a = _angle(l_hip, l_shoulder, l_ear)
        if body_a < 150:
            feedback.append("Keep your back straight.")
    except Exception:
        pass

    if not feedback:
        if _rep_state["stage"] == "down":
            feedback.append("Curl up to complete a rep.")
        elif _rep_state["stage"] == "up":
            feedback.append("Lower your arm to reset.")
        else:
            feedback.append(f"Angle: {int(avg_angle)}° — get into position.")

    # ── Form score: based on symmetry + ROM ─────────────────────────────
    symmetry   = max(0.0, 100.0 - abs(l_angle - r_angle))
    rom_score  = min(100.0, (160.0 - min(avg_angle, 160.0)) / 160.0 * 100.0)
    form_score = round((symmetry * 0.5 + rom_score * 0.5), 1)
    _rep_state["form_score"] = form_score
    _rep_state["feedback"]   = feedback

    return {
        "reps":       _rep_state["reps"],
        "form_score": form_score,
        "feedback":   feedback,
        "left_angle":  round(l_angle, 1),
        "right_angle": round(r_angle, 1),
        "stage":      _rep_state["stage"],
    }


def _decode_frame(raw_bytes: bytes):
    """Decode raw image bytes → BGR numpy array."""
    arr   = np.frombuffer(raw_bytes, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame


def _run_mediapipe(frame_bgr, exercise_type: str = "bicep_curl") -> dict:
    """Run MediaPipe on a BGR frame, route to correct counter."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = _pose_solver.process(rgb)

    # Normalise exercise_type — unknown types fall back to bicep_curl
    ex = exercise_type.lower().strip() if exercise_type else "bicep_curl"
    if ex not in ("bicep_curl", "push_up", "squat"):
        log.warning("Unknown exercise_type '%s' — defaulting to bicep_curl", ex)
        ex = "bicep_curl"

    if not results.pose_landmarks:
        # Return current rep count for whichever exercise is active
        if ex in _COUNTER_MAP:
            reps = _COUNTER_MAP[ex].get_reps()
        else:
            reps = _rep_state["reps"]
        return {
            "reps":       reps,
            "form_score": 0.0,
            "feedback":   ["No pose detected — make sure your full body is visible."],
            "left_angle":  0.0,
            "right_angle": 0.0,
            "stage":      None,
        }

    lm = results.pose_landmarks.landmark

    # Route to correct counter
    if ex == "push_up":
        return push_up_counter.process(lm)
    elif ex == "squat":
        return squat_counter.process(lm)
    else:
        # bicep_curl — existing inline logic, unchanged
        return _process_landmarks(lm)


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/analyze-frame")
async def analyze_frame(
    # Accept multipart upload with field name "frame" OR "file"
    frame: UploadFile = File(None),
    file:  UploadFile = File(None),
    # Also accept base64 JSON body fallback via Form field
    image: str = Form(None),
    # NEW: exercise type — optional, defaults to bicep_curl
    exercise_type: str = Form("bicep_curl"),
):
    """
    Accepts the webcam frame three ways (in priority order):
      1. multipart field named 'frame'
      2. multipart field named 'file'
      3. form field named 'image' containing a base64 string
    Optional form field 'exercise_type': bicep_curl | push_up | squat
    Returns: { reps, form_score, feedback, left_angle, right_angle, stage }
    """
    raw: bytes = b""

    upload = frame or file
    if upload is not None:
        raw = await upload.read()
    elif image:
        # Strip data-URL prefix if present: "data:image/jpeg;base64,..."
        b64 = image.split(",", 1)[-1] if "," in image else image
        try:
            raw = base64.b64decode(b64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data.")
    else:
        raise HTTPException(
            status_code=422,
            detail="No image provided. Send multipart field 'frame'/'file' or form field 'image'."
        )

    if not raw:
        raise HTTPException(status_code=400, detail="Empty image received.")

    frame_img = _decode_frame(raw)
    if frame_img is None:
        raise HTTPException(status_code=400, detail="Could not decode image. Send JPEG or PNG.")

    # ── Stub when MediaPipe not installed ─────────────────────────────────
    if not _MP_AVAILABLE:
        return JSONResponse({
            "reps":       0,
            "form_score": 0,
            "feedback":   ["MediaPipe not installed on server. Run: pip install mediapipe==0.10.14"],
            "left_angle":  0.0,
            "right_angle": 0.0,
            "stage":      None,
        })

    result = _run_mediapipe(frame_img, exercise_type)
    log.info("analyze-frame exercise=%s reps=%d score=%.1f feedback=%s",
             exercise_type, result["reps"], result["form_score"], result["feedback"])
    return JSONResponse(result)


@router.post("/analyze-frame/reset")
async def reset_counter():
    """Reset rep counter for all exercises — call this when starting a new session."""
    _reset_counter()               # bicep_curl
    push_up_counter.reset()
    squat_counter.reset()
    log.info("All rep counters reset.")
    return {"status": "ok", "reps": 0}
