"""
backend/routers/workout.py
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from database import get_db
from models import StartWorkoutRequest, WorkoutSessionResponse, EndWorkoutRequest

log    = logging.getLogger("backend.routers.workout")
router = APIRouter()


# ---------------------------------------------------------------------------
# SaveSessionRequest — single-call session save (used by frontend on stop)
# ---------------------------------------------------------------------------

class SaveSessionRequest(BaseModel):
    user_id:       str   = "default_user"
    exercise_type: str   = "bicep_curl"
    reps:          int   = 0
    form_score:    float = 0.0
    duration_sec:  int   = 0
    notes:         Optional[str] = None


@router.post("/save-session", status_code=status.HTTP_201_CREATED)
async def save_session(body: SaveSessionRequest):
    """
    Save a completed workout session in a single POST.
    Frontend calls this when the user presses Stop, passing final stats.
    The document is stored with status='completed' so analytics can find it.
    """
    db  = get_db()
    now = datetime.now(timezone.utc)

    doc = {
        "user_id":       body.user_id,
        "exercise_type": body.exercise_type,
        "status":        "completed",           # ← analytics queries filter on this
        "started_at":    now,
        "ended_at":      now,
        "total_reps":    body.reps,
        "form_score":    body.form_score,
        "duration_s":    float(body.duration_sec),
        "notes":         body.notes,
    }

    try:
        result = await db["workout_sessions"].insert_one(doc)
    except Exception as exc:
        log.error("save_session insert failed: %s", exc)
        raise HTTPException(status_code=500, detail="Could not save workout session.")

    # Also write a performance_scores document so /analytics endpoint shows form data
    perf_doc = {
        "session_id": str(result.inserted_id),
        "user_id":    body.user_id,
        "reps":       body.reps,
        "form_score": body.form_score,
        "recorded_at": now,
    }
    try:
        await db["performance_scores"].insert_one(perf_doc)
    except Exception as exc:
        log.warning("performance_scores insert failed (non-fatal): %s", exc)

    log.info("Saved session %s  user=%s  reps=%d  score=%.1f",
             result.inserted_id, body.user_id, body.reps, body.form_score)

    return {
        "session_id":    str(result.inserted_id),
        "user_id":       body.user_id,
        "exercise_type": body.exercise_type,
        "total_reps":    body.reps,
        "form_score":    body.form_score,
        "duration_s":    float(body.duration_sec),
        "status":        "completed",
        "saved_at":      now.isoformat(),
    }


# ---------------------------------------------------------------------------
# Existing endpoints — unchanged
# ---------------------------------------------------------------------------

@router.post("/start-workout", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_workout(body: StartWorkoutRequest):
    db  = get_db()
    doc = {
        "user_id":       body.user_id,
        "exercise_type": body.exercise_type,
        "notes":         body.notes,
        "status":        "active",
        "started_at":    datetime.now(timezone.utc),
        "ended_at":      None,
        "total_reps":    0,
        "duration_s":    0.0,
    }

    try:
        result = await db["workout_sessions"].insert_one(doc)
    except Exception as exc:
        log.error("Failed to insert workout session: %s", exc)
        raise HTTPException(status_code=500, detail="Could not create workout session.")

    log.info("Started session %s for user %s", result.inserted_id, body.user_id)

    return WorkoutSessionResponse(
        session_id    = str(result.inserted_id),
        user_id       = body.user_id,
        exercise_type = body.exercise_type,
        started_at    = doc["started_at"],
        status        = "active",
        notes         = body.notes,
    )


@router.post("/end-workout")
async def end_workout(body: EndWorkoutRequest):
    db = get_db()

    if not ObjectId.is_valid(body.session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    ended_at = datetime.now(timezone.utc)
    result   = await db["workout_sessions"].update_one(
        {"_id": ObjectId(body.session_id), "status": "active"},
        {"$set": {
            "status":     "completed",
            "ended_at":   ended_at,
            "total_reps": body.reps,
            "duration_s": body.duration_sec,
        }},
    )

    if result.matched_count == 0:
        log.warning("Session %s not found or already ended", body.session_id)

    return {
        "session_id": body.session_id,
        "status":     "completed",
        "total_reps": body.reps,
        "duration_s": body.duration_sec,
        "ended_at":   ended_at.isoformat(),
    }


@router.get("/workout/{session_id}")
async def get_workout(session_id: str):
    db = get_db()

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id.")

    doc = await db["workout_sessions"].find_one({"_id": ObjectId(session_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found.")

    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/workout-history")
async def workout_history(
    user_id: str = "default_user",
    limit: int   = Query(default=20, ge=1, le=100),
):
    db     = get_db()
    cursor = db["workout_sessions"].find(
        {"user_id": user_id},
        sort=[("started_at", -1)],
        limit=limit,
    )
    sessions = await cursor.to_list(length=limit)
    for s in sessions:
        s["_id"] = str(s["_id"])
        if "started_at" in s and isinstance(s["started_at"], datetime):
            s["started_at"] = s["started_at"].isoformat()
        if "ended_at" in s and isinstance(s.get("ended_at"), datetime):
            s["ended_at"] = s["ended_at"].isoformat()
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/realtime/frame")
async def realtime_frame(encode: bool = True):
    return {
        "reps": 0,
        "left_angle": 0.0,
        "right_angle": 0.0,
        "form_score": 0.0,
        "pose_visible": False,
        "frame": None,
        "message": "Pose engine not running. Camera feed is browser-side only.",
    }


@router.post("/realtime/reset")
async def realtime_reset():
    return {"status": "ok", "message": "Rep counter reset (stub)."}


@router.delete("/workout/{session_id}")
async def delete_workout(session_id: str):
    db = get_db()

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id.")

    result = await db["workout_sessions"].delete_one({"_id": ObjectId(session_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found.")

    await db["performance_scores"].delete_many({"session_id": session_id})
    log.info("Deleted session %s", session_id)
    return {"status": "deleted", "session_id": session_id}


@router.delete("/workout-history/{user_id}")
async def delete_all_workouts(user_id: str):
    db = get_db()
    result = await db["workout_sessions"].delete_many({"user_id": user_id})
    await db["performance_scores"].delete_many({})
    log.info("Deleted all %d sessions for user %s", result.deleted_count, user_id)
    return {"status": "deleted", "count": result.deleted_count}
