"""Manual microphone/STT check for the production ElevenLabs path.

This is a local debugging script, not a production pipeline implementation.
"""

import os
import importlib.util
from pathlib import Path

import speech_recognition as sr
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOICE_DIR = PROJECT_ROOT / "chatbot-voice" / "voice"


def transcribe_audio(audio_path):
    spec = importlib.util.spec_from_file_location("sakshamai_stt", VOICE_DIR / "stt.py")
    stt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stt_module)
    return stt_module.transcribe_audio(audio_path)

load_dotenv(PROJECT_ROOT / "chatbot-voice" / ".env")

DEVICE_INDEX = int(os.getenv("MIC_DEVICE_INDEX", "0"))
OUTPUT_FILE = PROJECT_ROOT / "tests" / "fixtures" / "audio" / "speech_recognition_test.wav"

recognizer = sr.Recognizer()

print("Using microphone device:", DEVICE_INDEX)

with sr.Microphone(
    device_index=DEVICE_INDEX,
    sample_rate=16000,
    chunk_size=1024
) as source:

    print("Calibrating...")
    recognizer.adjust_for_ambient_noise(source, duration=2)

    print("Listening...")
    
    audio = recognizer.listen(
        source,
        timeout=15,
        phrase_time_limit=10
    )

print("Recording captured.")

# Save exactly what SpeechRecognition captured
with open(OUTPUT_FILE, "wb") as f:
    f.write(audio.get_wav_data())

print(f"Saved: {OUTPUT_FILE}")

print("Recognizing...")

try:
    text = transcribe_audio(str(OUTPUT_FILE))

    print("\nYou said:")
    print(text or "No transcription returned.")

except Exception as error:
    print("\nElevenLabs transcription error:")
    print(error)