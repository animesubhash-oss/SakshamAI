"""Import bridge between the NiceGUI interface and the existing backend.

The backend lives in folders whose names are not importable as packages
(``chatbot-voice``, ``gemini-core``), so every service module calls
:func:`prepare_backend` before importing.  Nothing here re-implements backend
behaviour - it only makes the existing modules reachable.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

logger = logging.getLogger("sakshamai.ui")

ROOT = Path(__file__).resolve().parents[2]
CHATBOT_DIR = ROOT / "chatbot-voice"
GEMINI_DIR = ROOT / "gemini-core"
GEMINI_MODULE = GEMINI_DIR / "gemini_core.py"

_prepared = False


class BackendError(RuntimeError):
    """A backend failure already phrased for a student to read."""

    def __init__(self, message: str, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or message


def prepare_backend() -> None:
    """Put the backend folders on ``sys.path`` and load the ``.env`` files."""
    global _prepared
    if _prepared:
        return

    for folder in (ROOT, CHATBOT_DIR, GEMINI_DIR):
        if folder.is_dir() and str(folder) not in sys.path:
            sys.path.insert(0, str(folder))

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(CHATBOT_DIR / ".env")
    _prepared = True


_gemini_module: ModuleType | None = None


def gemini_core() -> ModuleType:
    """Load ``gemini-core/gemini_core.py`` (its folder name is not a package)."""
    global _gemini_module
    if _gemini_module is not None:
        return _gemini_module

    prepare_backend()
    spec = importlib.util.spec_from_file_location("saksham_gemini_core", GEMINI_MODULE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load the study generator at {GEMINI_MODULE}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _gemini_module = module
    return module


def backend_status() -> dict[str, object]:
    """Facts about the backend, used by the Settings sheet - no guessing."""
    prepare_backend()
    status: dict[str, object] = {
        "model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        "gemini_key": bool(os.getenv("GEMINI_API_KEY")),
        "voice_key": bool(os.getenv("ELEVENLABS_API_KEY")),
        "microphones": [],
        "microphone_index": os.getenv("MIC_DEVICE_INDEX", "0"),
        "voice_ready": False,
    }
    try:
        from voice.stt import list_microphones

        status["microphones"] = list_microphones()
        status["voice_ready"] = bool(status["microphones"]) and bool(status["voice_key"])
    except Exception as error:  # pragma: no cover - depends on local audio stack
        logger.warning("Microphone list unavailable: %s", error)
    return status
