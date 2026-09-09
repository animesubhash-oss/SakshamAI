"""MongoDB authentication and accessibility-profile persistence for app_v3."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import bcrypt
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "sakshamai")

_client: MongoClient | None = None


def _database():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    database = _client[MONGODB_DATABASE]
    database.users.create_index([("username", ASCENDING)], unique=True)
    database.accessibility_profiles.create_index([("user_id", ASCENDING)], unique=True)
    return database


def initialize_auth_store() -> None:
    """Create indexes and fail clearly if MongoDB is unavailable."""
    database = _database()
    database.command("ping")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_user(username: str, password: str) -> str:
    normalized = username.strip().lower()
    if not normalized:
        raise ValueError("Enter a username or email address.")
    if len(password) < 8 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        raise ValueError("Use at least 8 characters, including a letter and a number.")

    database = _database()
    user_id = None
    try:
        result = database.users.insert_one(
            {
                "username": normalized,
                "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                "created_at": _now(),
            }
        )
        user_id = str(result.inserted_id)
        database.accessibility_profiles.insert_one(
            {
                "user_id": user_id,
                "visual_impairment": False,
                "hearing_impairment": False,
                "motor_impairment": False,
                "speech_difficulty": False,
                "cognitive_learning_difficulty": False,
                "other_notes": "",
                "disclosed": False,
                "updated_at": _now(),
            }
        )
        return user_id
    except DuplicateKeyError as error:
        if user_id:
            database.users.delete_one({"_id": result.inserted_id})
        raise ValueError("That username or email is already registered.") from error


def verify_login(username: str, password: str) -> dict[str, str] | None:
    normalized = username.strip().lower()
    user = _database().users.find_one({"username": normalized})
    if not user:
        return None
    password_hash = str(user.get("password_hash", "")).encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        return None
    return {"id": str(user["_id"]), "username": str(user["username"])}


def get_accessibility_profile(user_id: str) -> dict[str, Any]:
    profile = _database().accessibility_profiles.find_one(
        {"user_id": user_id},
        {"_id": 0, "user_id": 0, "updated_at": 0},
    )
    if not profile:
        return {
            "visual_impairment": False,
            "hearing_impairment": False,
            "motor_impairment": False,
            "speech_difficulty": False,
            "cognitive_learning_difficulty": False,
            "other_notes": "",
            "disclosed": False,
        }
    return profile


def update_accessibility_profile(user_id: str, **profile: Any) -> None:
    allowed = {
        "visual_impairment",
        "hearing_impairment",
        "motor_impairment",
        "speech_difficulty",
        "cognitive_learning_difficulty",
        "other_notes",
        "disclosed",
    }
    values = {key: profile.get(key, False) for key in allowed}
    values["other_notes"] = str(values.get("other_notes") or "").strip()[:1000]
    values["updated_at"] = _now()
    _database().accessibility_profiles.update_one(
        {"user_id": user_id},
        {"$set": values, "$setOnInsert": {"user_id": user_id}},
        upsert=True,
    )
