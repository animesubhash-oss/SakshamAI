"""MongoDB authentication and accessibility-profile persistence for app_v3."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bcrypt
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "sakshamai")
ROOT = Path(__file__).resolve().parent.parent
AUTH_STORE_FILE = ROOT / ".sakshamai_auth_store.json"

_client: MongoClient | None = None


def _load_auth_store() -> dict[str, list[dict[str, Any]]]:
    if not AUTH_STORE_FILE.exists():
        return {"users": [], "accessibility_profiles": []}
    try:
        data = json.loads(AUTH_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"users": [], "accessibility_profiles": []}
    if not isinstance(data, dict):
        return {"users": [], "accessibility_profiles": []}
    data.setdefault("users", [])
    data.setdefault("accessibility_profiles", [])
    return data


def _save_auth_store(store: dict[str, list[dict[str, Any]]]) -> None:
    AUTH_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_STORE_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    database = _client[MONGODB_DATABASE]
    database.users.create_index([("username", ASCENDING)], unique=True)
    database.accessibility_profiles.create_index([("user_id", ASCENDING)], unique=True)
    return database


def initialize_auth_store() -> None:
    """Create indexes and gracefully use the local fallback if MongoDB is unavailable."""
    try:
        database = _database()
        database.command("ping")
    except Exception:
        # The app can continue with the local JSON-backed fallback store.
        return


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_user_fallback(username: str, password: str) -> str:
    store = _load_auth_store()
    existing_user = next((user for user in store["users"] if user.get("username") == username), None)
    if existing_user:
        raise ValueError("That username or email is already registered.")

    user_id = str(uuid.uuid4())
    store["users"].append(
        {
            "_id": user_id,
            "username": username,
            "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            "created_at": _now_iso(),
        }
    )
    store["accessibility_profiles"].append(
        {
            "user_id": user_id,
            "visual_impairment": False,
            "hearing_impairment": False,
            "motor_impairment": False,
            "speech_difficulty": False,
            "cognitive_learning_difficulty": False,
            "other_notes": "",
            "disclosed": False,
            "updated_at": _now_iso(),
        }
    )
    _save_auth_store(store)
    return user_id


def create_user(username: str, password: str) -> str:
    normalized = username.strip().lower()
    if not normalized:
        raise ValueError("Enter a username or email address.")
    if len(password) < 8 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        raise ValueError("Use at least 8 characters, including a letter and a number.")

    try:
        database = _database()
    except Exception:
        return _create_user_fallback(normalized, password)

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
    except Exception:
        return _create_user_fallback(normalized, password)


def _verify_login_fallback(username: str, password: str) -> dict[str, str] | None:
    store = _load_auth_store()
    user = next((item for item in store["users"] if item.get("username") == username), None)
    if not user:
        return None
    password_hash = str(user.get("password_hash", "")).encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        return None
    return {"id": str(user.get("_id", "")), "username": str(user.get("username", ""))}


def verify_login(username: str, password: str) -> dict[str, str] | None:
    normalized = username.strip().lower()
    try:
        user = _database().users.find_one({"username": normalized})
    except Exception:
        return _verify_login_fallback(normalized, password)
    if not user:
        return None
    password_hash = str(user.get("password_hash", "")).encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash):
        return None
    return {"id": str(user["_id"]), "username": str(user["username"])}


def _get_accessibility_profile_fallback(user_id: str) -> dict[str, Any]:
    store = _load_auth_store()
    profile = next(
        (
            item
            for item in store["accessibility_profiles"]
            if item.get("user_id") == user_id
        ),
        None,
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
    return {
        key: profile.get(key, False)
        for key in (
            "visual_impairment",
            "hearing_impairment",
            "motor_impairment",
            "speech_difficulty",
            "cognitive_learning_difficulty",
            "other_notes",
            "disclosed",
        )
    }


def get_accessibility_profile(user_id: str) -> dict[str, Any]:
    try:
        profile = _database().accessibility_profiles.find_one(
            {"user_id": user_id},
            {"_id": 0, "user_id": 0, "updated_at": 0},
        )
    except Exception:
        return _get_accessibility_profile_fallback(user_id)
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


def _update_accessibility_profile_fallback(user_id: str, **profile: Any) -> None:
    allowed = {
        "visual_impairment",
        "hearing_impairment",
        "motor_impairment",
        "speech_difficulty",
        "cognitive_learning_difficulty",
        "other_notes",
        "disclosed",
    }
    store = _load_auth_store()
    values = {key: profile.get(key, False) for key in allowed}
    values["other_notes"] = str(values.get("other_notes") or "").strip()[:1000]
    values["updated_at"] = _now_iso()

    existing = next(
        (
            item
            for item in store["accessibility_profiles"]
            if item.get("user_id") == user_id
        ),
        None,
    )
    if existing:
        existing.update(values)
    else:
        store["accessibility_profiles"].append({"user_id": user_id, **values})

    _save_auth_store(store)


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
    try:
        _database().accessibility_profiles.update_one(
            {"user_id": user_id},
            {"$set": values, "$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )
    except Exception:
        _update_accessibility_profile_fallback(user_id, **values)
