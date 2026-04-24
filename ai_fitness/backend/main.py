"""
backend/main.py
---------------
FastAPI application entry point.
Run with:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_db, close_db
from routers import performance, workout, analytics, diet, habit, auth, analyze

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("backend.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting AI Gym & Fitness Assistant API ...")
    await connect_db()
    yield
    await close_db()
    log.info("Shutdown complete.")


app = FastAPI(
    title="AI Gym & Fitness Assistant",
    description="Real-time fitness tracking API with MediaPipe pose detection.",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api", tags=["Auth"])
app.include_router(performance.router, prefix="/api", tags=["Performance"])
app.include_router(workout.router,     prefix="/api", tags=["Workout"])
app.include_router(analytics.router,   prefix="/api", tags=["Analytics"])
app.include_router(diet.router,        prefix="/api", tags=["Diet"])
app.include_router(habit.router,       prefix="/api", tags=["Habit"])
app.include_router(analyze.router,     prefix="/api", tags=["AI Analyze"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "AI Gym & Fitness Assistant API v2.1"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
