"""
backend/services/performance_service.py
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

# FIX #3: was `from models import ...`
# When uvicorn runs from backend/, `models` resolves correctly as backend/models.py.
# No change needed to the import itself — this file is already correct.
# (Included in the fix package to confirm it's untouched and working.)
from models import PerformanceSnapshotRequest, PerformanceResponse

_GRADE_MAP = [(90, "A"), (80, "B"), (65, "C"), (50, "D"), (0, "F")]


def _grade(score: float) -> str:
    for threshold, letter in _GRADE_MAP:
        if score >= threshold:
            return letter
    return "F"


def _elbow_rom_score(angle: float) -> float:
    angle = max(0.0, min(180.0, angle))
    if angle >= 140:
        return 100.0
    if angle >= 90:
        return 50.0 + (angle - 90.0) / 50.0 * 50.0
    return max(0.0, angle / 90.0 * 50.0)


def _rep_reward(reps: int) -> float:
    if reps <= 0:
        return 0.0
    return min(100.0, math.log1p(reps) / math.log1p(20) * 100.0)


def compute_performance(req: PerformanceSnapshotRequest) -> PerformanceResponse:
    c_elbow = _elbow_rom_score(req.elbow_angle) * 0.35
    s_score = float(req.straightness_score) if req.straightness_score is not None else 50.0
    c_body  = min(100.0, max(0.0, s_score)) * 0.25
    f_score = float(req.form_score) if req.form_score is not None else 60.0
    c_form  = min(100.0, max(0.0, f_score)) * 0.25
    c_reps  = _rep_reward(req.reps) * 0.15

    composite = round(c_elbow + c_body + c_form + c_reps, 1)
    composite = min(100.0, max(0.0, composite))

    feedback = list(req.feedback)
    if composite < 50 and not feedback:
        feedback.append("Focus on controlled movement and full range of motion.")
    if req.straightness_score is not None and req.straightness_score < 60:
        feedback.append("Keep your body straight — tighten your core.")

    return PerformanceResponse(
        session_id         = req.session_id,
        reps               = req.reps,
        elbow_angle        = req.elbow_angle,
        body_angle         = req.body_angle,
        straightness_score = req.straightness_score,
        form_score         = composite,
        performance_grade  = _grade(composite),
        feedback           = feedback,
        recorded_at        = datetime.now(timezone.utc),
    )
