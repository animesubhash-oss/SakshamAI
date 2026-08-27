import os
import tempfile
from pathlib import Path

import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

MICROPHONE_INDEX = int(os.getenv("MIC_DEVICE_INDEX", "0"))
VOICE_RECORD_TIMEOUT_SECONDS = int(os.getenv("VOICE_RECORD_TIMEOUT_SECONDS", "10"))
VOICE_PHRASE_SECONDS = int(os.getenv("VOICE_PHRASE_SECONDS", "12"))


def _get_client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set in chatbot-voice/.env"
        )
    return ElevenLabs(api_key=api_key)


# ============================================================
# MICROPHONE VALIDATION
# ============================================================

def list_microphones():
    try:
        return sr.Microphone.list_microphone_names()
    except Exception:
        return []


def validate_microphone_index(index: int):
    names = list_microphones()
    if not names:
        raise ValueError(
            "No microphones were detected. Please check that your microphone is connected and accessible."
        )

    if index < 0 or index >= len(names):
        raise ValueError(
            f"Configured MIC_DEVICE_INDEX={index} is invalid. "
            f"Available microphones: {names}"
        )

    return True


# ============================================================
# RECORD AUDIO
# ============================================================

def record_audio(filename=None, duration_limit=None):
    validate_microphone_index(MICROPHONE_INDEX)

    if duration_limit is None:
        duration_limit = VOICE_PHRASE_SECONDS

    if filename is None:
        temp_dir = tempfile.gettempdir()
        handle, filename = tempfile.mkstemp(
            suffix=".wav",
            prefix="sakshamai_input_",
            dir=temp_dir,
        )
        os.close(handle)

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = max(300, recognizer.energy_threshold)
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.4

    print("\nCalibrating microphone...")

    try:
        with sr.Microphone(
            device_index=MICROPHONE_INDEX,
            sample_rate=16000,
        ) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening... Speak now!")

            try:
                audio = recognizer.listen(
                    source,
                    timeout=VOICE_RECORD_TIMEOUT_SECONDS,
                    phrase_time_limit=duration_limit,
                )
            except sr.WaitTimeoutError:
                print("No speech detected.")
                return None
            except KeyboardInterrupt:
                print("\nMicrophone input interrupted by user.")
                return None

    except KeyboardInterrupt:
        print("\nMicrophone input interrupted by user.")
        return None
    except Exception as error:
        print(f"Microphone error: {error}")
        return None

    print("Recording captured.")

    try:
        with open(filename, "wb") as file:
            file.write(audio.get_wav_data())
    except Exception as error:
        print(f"Could not save audio file: {error}")
        return None

    print(f"Audio saved: {filename}")
    return filename


# ============================================================
# ELEVENLABS SPEECH-TO-TEXT
# ============================================================

def transcribe_audio(filename):
    print("Sending audio to ElevenLabs...")
    print("Recognizing...")

    try:
        client = _get_client()
        with open(filename, "rb") as audio_file:
            result = client.speech_to_text.convert(
                model_id="scribe_v1",
                file=audio_file,
                language_code="en",
            )

        text = result.text.strip()
        if not text:
            print("ElevenLabs returned empty transcription.")
            return None
        return text

    except Exception as error:
        print("\nElevenLabs STT error:")
        print(error)
        return None


# ============================================================
# TEMP FILE CLEANUP
# ============================================================

def cleanup_temp_file(file_path):
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SakshamAI - ElevenLabs Speech-to-Text")
    print("=" * 60)

    audio_file = record_audio()
    if audio_file:
        text = transcribe_audio(audio_file)
        cleanup_temp_file(audio_file)

        print("\n" + "=" * 60)
        if text:
            print("TRANSCRIPTION:")
            print(text)
        else:
            print("Speech could not be transcribed.")

        print("=" * 60)