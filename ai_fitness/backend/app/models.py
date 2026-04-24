"""
backend/models.py
------------------
Pydantic v2 models. Python 3.9 compatible (uses typing.List/Optional/Dict).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

class PerformanceSnapshotRequest(BaseModel):
    session_id:         str
    reps:               int            = Field(default=0, ge=0)
    elbow_angle:        float          = Field(default=0.0, ge=0.0, le=360.0)
    body_angle:         Optional[float] = None
    straightness_score: Optional[int]  = None
    form_score:         Optional[float] = None
    feedback:           List[str]      = Field(default_factory=list)


class PerformanceResponse(BaseModel):
    session_id:         str
    reps:               int
    elbow_angle:        float
    body_angle:         Optional[float]
    straightness_score: Optional[int]
    form_score:         float
    performance_grade:  str
    feedback:           List[str]
    recorded_at:        datetime

    @field_validator("recorded_at", mode="before")
    @classmethod
    def coerce_recorded_at(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Workout
# ---------------------------------------------------------------------------

class StartWorkoutRequest(BaseModel):
    user_id:       str = "default_user"
    exercise_type: str = "bicep_curl"
    notes:         Optional[str] = None
    duration_sec:  Optional[int] = None


class WorkoutSessionResponse(BaseModel):
    session_id:    str
    user_id:       str
    exercise_type: str
    started_at:    datetime
    status:        str
    notes:         Optional[str] = None


class EndWorkoutRequest(BaseModel):
    session_id:   str
    reps:         int   = 0
    form_score:   float = 0.0
    duration_sec: int   = 0


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AnalyticsResponse(BaseModel):
    user_id:              str
    total_sessions:       int
    total_reps:           int
    avg_form_score:       float
    best_form_score:      float
    avg_reps_per_session: float
    sessions:             List[Dict]
    trend:                str = "stable"
    avg_score:            float = 0.0
    best_score:           float = 0.0

    @field_validator("avg_score", mode="before")
    @classmethod
    def set_avg_score(cls, v):
        return v

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Diet
# ---------------------------------------------------------------------------

class DietRequest(BaseModel):
    user_id:        str
    weight_kg:      float
    height_cm:      float
    age:            int
    gender:         str          = "male"
    activity_level: str          = "moderate"
    goal:           str          = "maintain"


class DietResponse(BaseModel):
    user_id:         str
    bmi:             float
    bmi_category:    str
    bmr:             float
    tdee:            float
    target_calories: float
    protein_g:       float
    carbs_g:         float
    fat_g:           float
    recommendations: List[str]
    foods_to_eat:    List[str]
    foods_to_avoid:  List[str]


# ---------------------------------------------------------------------------
# Habit
# ---------------------------------------------------------------------------

class HabitLogRequest(BaseModel):
    user_id:       str
    workout_done:  bool  = False
    water_glasses: int   = 0
    sleep_hours:   float = 7.0
    steps:         int   = 0
    mood:          str   = "neutral"
    notes:         Optional[str] = None


class HabitResponse(BaseModel):
    user_id:             str
    date:                str
    workout_done:        bool
    water_glasses:       int
    sleep_hours:         float
    steps:               int
    mood:                str
    habit_score:         int
    behavior_prediction: str
    tips:                List[str]
    logged_at:           datetime

    @field_validator("logged_at", mode="before")
    @classmethod
    def coerce_logged_at(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class HabitHistoryResponse(BaseModel):
    user_id:     str
    streak_days: int
    avg_score:   float
    history:     List[Dict]
