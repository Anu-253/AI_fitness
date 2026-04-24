"""
backend/routers/analytics.py
"""

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from models import AnalyticsResponse

log    = logging.getLogger("backend.routers.analytics")
router = APIRouter()


@router.get("/analytics/{user_id}", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: str,
    limit:   int = Query(default=20, ge=1, le=100),
):
    db = get_db()

    cursor   = db["workout_sessions"].find(
        {"user_id": user_id, "status": "completed"},
        sort=[("started_at", -1)],
        limit=limit,
    )
    sessions = await cursor.to_list(length=limit)

    if not sessions:
        # Return zeroed analytics rather than 404 so dashboard renders
        return AnalyticsResponse(
            user_id=user_id,
            total_sessions=0,
            total_reps=0,
            avg_form_score=0.0,
            best_form_score=0.0,
            avg_reps_per_session=0.0,
            sessions=[],
            trend="stable",
            avg_score=0.0,
            best_score=0.0,
        )

    session_ids = [str(s["_id"]) for s in sessions]
    total_reps  = sum(s.get("total_reps", 0) for s in sessions)

    perf_cursor = db["performance_scores"].find({"session_id": {"$in": session_ids}})
    perf_docs   = await perf_cursor.to_list(length=10_000)

    form_scores = [p["form_score"] for p in perf_docs if "form_score" in p]
    avg_score   = round(sum(form_scores) / len(form_scores), 1) if form_scores else 0.0
    best_score  = round(max(form_scores), 1)                    if form_scores else 0.0

    session_list = []
    for s in sessions:
        session_list.append({
            "session_id":    str(s["_id"]),
            "exercise_type": s.get("exercise_type", "unknown"),
            "total_reps":    s.get("total_reps", 0),
            "duration_s":    s.get("duration_s", 0.0),
            "started_at":    s["started_at"].isoformat() if isinstance(s.get("started_at"), datetime) else str(s.get("started_at", "")),
        })

    avg_reps = round(total_reps / len(sessions), 1)

    # Simple trend: compare first half vs second half avg scores
    trend = "stable"
    if len(form_scores) >= 4:
        mid   = len(form_scores) // 2
        older = sum(form_scores[mid:]) / (len(form_scores) - mid)
        newer = sum(form_scores[:mid]) / mid
        if newer > older + 5:
            trend = "improving"
        elif newer < older - 5:
            trend = "declining"

    return AnalyticsResponse(
        user_id               = user_id,
        total_sessions        = len(sessions),
        total_reps            = total_reps,
        avg_form_score        = avg_score,
        best_form_score       = best_score,
        avg_reps_per_session  = avg_reps,
        sessions              = session_list,
        trend                 = trend,
        avg_score             = avg_score,
        best_score            = best_score,
    )


@router.get("/analytics/{user_id}/history")
async def get_history(
    user_id: str,
    page:    int = Query(default=1, ge=1),
    size:    int = Query(default=10, ge=1, le=50),
):
    db     = get_db()
    skip   = (page - 1) * size
    cursor = db["workout_sessions"].find(
        {"user_id": user_id, "status": "completed"},
        sort=[("started_at", -1)],
        skip=skip,
        limit=size,
    )
    sessions = await cursor.to_list(length=size)
    total    = await db["workout_sessions"].count_documents({"user_id": user_id, "status": "completed"})

    result = []
    for s in sessions:
        sid    = str(s["_id"])
        scores = await db["performance_scores"].find(
            {"session_id": sid}, {"form_score": 1}
        ).to_list(length=10_000)
        fs = [x["form_score"] for x in scores if "form_score" in x]

        result.append({
            "session_id":    sid,
            "exercise_type": s.get("exercise_type"),
            "total_reps":    s.get("total_reps", 0),
            "duration_s":    s.get("duration_s", 0.0),
            "avg_score":     round(sum(fs) / len(fs), 1) if fs else None,
            "best_score":    round(max(fs), 1)           if fs else None,
            "started_at":    s["started_at"].isoformat() if isinstance(s.get("started_at"), datetime) else "",
        })

    return {"user_id": user_id, "page": page, "size": size, "total": total, "sessions": result}
