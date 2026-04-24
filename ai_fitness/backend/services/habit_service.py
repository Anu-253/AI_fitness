"""
backend/services/habit_service.py
"""
from __future__ import annotations
from models import HabitLogRequest

_WORKOUT_PTS    = 30
_WATER_MAX_PTS  = 20
_WATER_TARGET   = 8
_SLEEP_MAX_PTS  = 25
_SLEEP_IDEAL_LO = 7.0
_SLEEP_IDEAL_HI = 9.0
_STEPS_MAX_PTS  = 15
_STEPS_TARGET   = 10_000
_MOOD_SCORES    = {"great": 10, "good": 8, "neutral": 5, "tired": 2, "bad": 0}


def compute_habit_score(body: HabitLogRequest) -> int:
    score = 0
    if body.workout_done:
        score += _WORKOUT_PTS
    score += round(min(1.0, body.water_glasses / _WATER_TARGET) * _WATER_MAX_PTS)
    sl = body.sleep_hours
    if _SLEEP_IDEAL_LO <= sl <= _SLEEP_IDEAL_HI:
        score += _SLEEP_MAX_PTS
    elif sl >= 6:
        score += round(_SLEEP_MAX_PTS * 0.6)
    elif sl >= 5:
        score += round(_SLEEP_MAX_PTS * 0.3)
    score += round(min(1.0, body.steps / _STEPS_TARGET) * _STEPS_MAX_PTS)
    score += _MOOD_SCORES.get(body.mood.lower(), 5)
    return min(100, max(0, score))


def predict_behavior(body: HabitLogRequest, score: int) -> str:
    mood = body.mood.lower()
    if score >= 75 and mood in ("great", "good"):
        return "High adherence expected tomorrow — you're building great momentum!"
    if score >= 75:
        return "High adherence expected — keep following your routine."
    if score >= 50 and mood not in ("tired", "bad"):
        return "Moderate adherence expected — try to improve one habit tomorrow."
    if mood in ("tired", "bad"):
        return "Rest day likely — plan lighter activity and prioritise sleep tonight."
    if score >= 30:
        return "Low adherence risk — set one small, concrete goal for tomorrow."
    return "Habit slip detected — restart with a single non-negotiable habit tomorrow."
