"""Bridge to the existing voice stack (chatbot-voice/voice/stt.py and tts.py).

Recording, ElevenLabs speech-to-text and text-to-speech playback all stay in the
backend exactly as they are.  These wrappers only report state in words the
interface can show, and they never raise raw errors at the UI.

Note: the microphone and the speakers used are the ones attached to the computer
running SakshamAI, because that is how the existing voice modules work.
"""

from __future__ import annotations

import logging

from .bootstrap import BackendError, prepare_backend

logger = logging.getLogger("sakshamai.ui.voice")


def _stt():
    prepare_backend()
    from voice import stt

    return stt


def _tts():
    prepare_backend()
    from voice import tts

    return tts


def microphone_available() -> tuple[bool, str]:
    """Check the microphone without recording anything."""
    try:
        stt = _stt()
        stt.validate_microphone_index(stt.MICROPHONE_INDEX)
        names = stt.list_microphones()
        return True, names[stt.MICROPHONE_INDEX]
    except Exception as error:
        logger.warning("Microphone unavailable: %s", error)
        return False, str(error)


def record_question(duration_limit: int | None = None) -> str:
    """Record from the microphone and return the recorded file path."""
    stt = _stt()
    try:
        path = stt.record_audio(duration_limit=duration_limit)
    except Exception as error:
        logger.exception("Recording failed")
        raise BackendError(
            "SakshamAI could not use the microphone on this computer.", str(error)
        ) from error

    if not path:
        raise BackendError(
            "No speech was heard. Press the microphone and speak clearly.",
            "no speech captured",
        )
    return path


def transcribe(path: str) -> str:
    """Send the recording to the existing ElevenLabs speech-to-text step."""
    stt = _stt()
    try:
        text = stt.transcribe_audio(path)
    except Exception as error:
        logger.exception("Transcription failed")
        raise BackendError("SakshamAI could not turn that recording into text.", str(error)) from error
    finally:
        stt.cleanup_temp_file(path)

    if not text:
        raise BackendError(
            "SakshamAI could not make out any words. Please try again.",
            "empty transcription",
        )
    return text.strip()


def speak(text: str) -> bool:
    """Read text aloud with the existing text-to-speech module."""
    if not text.strip():
        return False
    try:
        return bool(_tts().speak(text, save_audio=False))
    except Exception as error:  # pragma: no cover - depends on local audio
        logger.exception("Playback failed")
        raise BackendError("SakshamAI could not play the audio on this computer.", str(error)) from error
