"""
backend/routers/performance.py
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from database import get_db, col_performance
from models import PerformanceSnapshotRequest, PerformanceResponse
from services.performance_service import compute_performance

log    = logging.getLogger("backend.routers.performance")
router = APIRouter()


@router.post(
    "/performance",
    response_model=PerformanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_performance(body: PerformanceSnapshotRequest):
    db = get_db()

    try:
        scored = compute_performance(body)
    except Exception as exc:
        log.error("Score computation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute performance score.")

    doc = scored.model_dump(mode="json")
    doc["session_id"] = body.session_id

    try:
        result = await col_performance(db).insert_one(doc)
        log.info("Performance saved _id=%s session=%s score=%.1f", result.inserted_id, body.session_id, scored.form_score)
    except Exception as exc:
        log.error("MongoDB insert failed: %s", exc)

    return scored


@router.get("/performance/{session_id}", response_model=PerformanceResponse)
async def get_performance(session_id: str):
    db  = get_db()
    doc = await col_performance(db).find_one(
        {"session_id": session_id},
        sort=[("recorded_at", -1)],
    )

    if doc is None:
        raise HTTPException(status_code=404, detail=f"No performance data for session '{session_id}'.")

    doc.pop("_id", None)
    return doc
