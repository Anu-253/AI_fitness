"""
backend/routers/diet.py
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from database import get_db
from models import DietRequest, DietResponse
from services.diet_service import compute_diet

log    = logging.getLogger("backend.routers.diet")
router = APIRouter()


@router.post("/diet", response_model=DietResponse)
async def post_diet(body: DietRequest):
    db = get_db()
    try:
        plan = compute_diet(body)
    except Exception as exc:
        log.error("Diet computation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Could not compute diet plan.")

    doc = plan.model_dump()
    doc["user_id"]    = body.user_id
    doc["created_at"] = datetime.now(timezone.utc)
    try:
        await db["diet_plans"].insert_one(doc)
    except Exception as exc:
        log.error("Failed to save diet plan: %s", exc)

    return plan


@router.get("/diet/{user_id}/latest", response_model=DietResponse)
async def get_latest_diet(user_id: str):
    db  = get_db()
    doc = await db["diet_plans"].find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)],
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"No diet plan found for user '{user_id}'.")
    doc.pop("_id", None)
    doc.pop("created_at", None)
    return doc
