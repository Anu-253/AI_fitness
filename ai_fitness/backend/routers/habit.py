"""
backend/routers/habit.py
"""
import logging
from datetime import datetime, date, timezone, timedelta

from fastapi import APIRouter, HTTPException

from database import get_db
from models import HabitLogRequest, HabitResponse, HabitHistoryResponse
from services.habit_service import compute_habit_score, predict_behavior

log    = logging.getLogger("backend.routers.habit")
router = APIRouter()


def _generate_tips(body: HabitLogRequest, score: int):
    tips = []
    if not body.workout_done:
        tips.append("Try a 20-minute workout today — even a short session counts!")
    if body.water_glasses < 8:
        tips.append(f"You had {body.water_glasses} glasses of water. Aim for at least 8.")
    if body.sleep_hours < 7:
        tips.append(f"You slept {body.sleep_hours:.1f}h. 7-9 hours supports muscle recovery.")
    if body.steps < 7000:
        tips.append(f"Only {body.steps:,} steps today — try to hit 7,000+.")
    if body.mood in ("tired", "bad"):
        tips.append("Your mood is low — rest is part of fitness. Don't skip recovery.")
    if score >= 80:
        tips.append("Excellent day! Keep up the momentum.")
    elif score >= 60:
        tips.append("Good effort today. Small improvements each day add up.")
    return tips


@router.post("/habit", response_model=HabitResponse)
async def log_habit(body: HabitLogRequest):
    db    = get_db()
    today = date.today().isoformat()
    now   = datetime.now(timezone.utc)

    score      = compute_habit_score(body)
    prediction = predict_behavior(body, score)
    tips       = _generate_tips(body, score)

    doc = {
        "user_id":             body.user_id,
        "date":                today,
        "workout_done":        body.workout_done,
        "water_glasses":       body.water_glasses,
        "sleep_hours":         body.sleep_hours,
        "steps":               body.steps,
        "mood":                body.mood,
        "notes":               body.notes,
        "habit_score":         score,
        "behavior_prediction": prediction,
        "tips":                tips,
        "logged_at":           now,
    }

    await db["habit_logs"].update_one(
        {"user_id": body.user_id, "date": today},
        {"$set": doc},
        upsert=True,
    )

    return HabitResponse(
        user_id=body.user_id, date=today, workout_done=body.workout_done,
        water_glasses=body.water_glasses, sleep_hours=body.sleep_hours,
        steps=body.steps, mood=body.mood, habit_score=score,
        behavior_prediction=prediction, tips=tips, logged_at=now,
    )


@router.get("/habit/{user_id}", response_model=HabitResponse)
async def get_today_habit(user_id: str):
    db    = get_db()
    today = date.today().isoformat()
    doc   = await db["habit_logs"].find_one({"user_id": user_id, "date": today})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No habit log for today.")
    doc.pop("_id", None)
    return doc


@router.get("/habit/{user_id}/streak", response_model=HabitHistoryResponse)
async def get_streak(user_id: str):
    db     = get_db()
    cursor = db["habit_logs"].find({"user_id": user_id}, sort=[("date", -1)], limit=60)
    logs   = await cursor.to_list(length=60)
    if not logs:
        raise HTTPException(status_code=404, detail="No habit logs found.")

    streak     = 0
    dates_seen = {l["date"] for l in logs}
    check_date = date.today()

    while True:
        ds = check_date.isoformat()
        if ds in dates_seen:
            matching = next((l for l in logs if l["date"] == ds), None)
            if matching and matching.get("habit_score", 0) >= 50:
                streak     += 1
                check_date -= timedelta(days=1)
                continue
        break

    scores  = [l.get("habit_score", 0) for l in logs]
    avg_sc  = round(sum(scores) / len(scores), 1) if scores else 0.0
    history = []
    for l in logs:
        l.pop("_id", None)
        history.append(l)

    return HabitHistoryResponse(
        user_id=user_id, streak_days=streak, avg_score=avg_sc, history=history
    )
