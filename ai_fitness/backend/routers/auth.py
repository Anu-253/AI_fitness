"""
backend/routers/auth.py
------------------------
Auth endpoints: register, login, guest, /me
Uses simple token stored in DB (no JWT library needed).
"""

import logging
import secrets
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from database import get_db
from models import RegisterRequest, LoginRequest, TokenResponse

log    = logging.getLogger("backend.routers.auth")
router = APIRouter()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    return secrets.token_hex(32)


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    db = get_db()

    existing = await db["users"].find_one({"username": body.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken.")

    token   = _generate_token()
    user_id = secrets.token_hex(12)

    doc = {
        "user_id":       user_id,
        "username":      body.username,
        "email":         body.email,
        "password_hash": _hash_password(body.password),
        "token":         token,
        "created_at":    datetime.now(timezone.utc),
    }
    await db["users"].insert_one(doc)
    log.info("Registered user: %s", body.username)

    return TokenResponse(access_token=token, user_id=user_id, username=body.username)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    db   = get_db()
    user = await db["users"].find_one({"username": body.username})

    if not user or user.get("password_hash") != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # Refresh token on each login
    token = _generate_token()
    await db["users"].update_one({"_id": user["_id"]}, {"$set": {"token": token}})
    log.info("Login: %s", body.username)

    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        username=user["username"],
    )


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get("/me")
async def get_me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")

    token = authorization.split(" ", 1)[1]
    if token == "guest-no-token":
        return {"user_id": "default_user", "username": "Guest"}

    db   = get_db()
    user = await db["users"].find_one({"token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return {"user_id": user["user_id"], "username": user["username"]}
