"""Manual ElevenLabs STT check using a saved microphone recording.

The filename is retained for compatibility with the original scratch script;
Google Web Speech API is not part of the production architecture.
"""

import importlib.util
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOICE_DIR = PROJECT_ROOT / "chatbot-voice" / "voice"


def transcribe_audio(audio_path):
    spec = importlib.util.spec_from_file_location("sakshamai_stt", VOICE_DIR / "stt.py")
    stt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stt_module)
    return stt_module.transcribe_audio(audio_path)

load_dotenv(PROJECT_ROOT / "chatbot-voice" / ".env")

audio_path = PROJECT_ROOT / "tests" / "fixtures" / "audio" / "speech_recognition_test.wav"

print("Loading speech_recognition_test.wav...")
print("Audio loaded.")
print("Sending to ElevenLabs Speech-to-Text...")

try:
    text = transcribe_audio(str(audio_path))

    print("\nSUCCESS!")
    print("Recognized text:")
    print(text or "No transcription returned.")

except Exception as error:
    print("\nElevenLabs Speech-to-Text request failed:")
    print(error)