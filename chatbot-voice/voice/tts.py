import os
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

# --------------------------------------------------
# ElevenLabs Client
# --------------------------------------------------

def _get_client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. Add it to chatbot-voice/.env"
        )
    return ElevenLabs(api_key=api_key)


def _delete_file(file_path: Path) -> None:
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass


# --------------------------------------------------
# Text-to-Speech
# --------------------------------------------------

def speak(text: str, save_audio: bool = False) -> bool:
    """
    Convert text to speech using ElevenLabs and play it immediately.
    Every call uses a unique temp file to avoid collisions.
    """

    if not text or not text.strip():
        return False

    print("SakshamAI is speaking...")

    try:
        client = _get_client()
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
    except Exception as error:
        print(f"TTS error: {error}")
        return False

    if save_audio:
        output_file = PROJECT_ROOT / "voice_output.mp3"
    else:
        file_handle, temp_path = tempfile.mkstemp(
            suffix=".mp3",
            prefix="sakshamai_voice_",
            dir=tempfile.gettempdir(),
        )
        os.close(file_handle)
        output_file = Path(temp_path)

    cleanup_after_playback = True
    try:
        with open(output_file, "wb") as file:
            for chunk in audio:
                file.write(chunk)

        print(f"Audio ready: {output_file}")

        if hasattr(os, "startfile"):
            os.startfile(str(output_file))
            cleanup_after_playback = False
            cleanup_timer = threading.Timer(
                60,
                _delete_file,
                args=(output_file,),
            )
            cleanup_timer.daemon = True
            cleanup_timer.start()
        else:
            raise RuntimeError("No supported playback backend is available.")
        return True
    except Exception as error:
        print(f"Playback error: {error}")
        return False
    finally:
        if not save_audio and cleanup_after_playback:
            _delete_file(output_file)


if __name__ == "__main__":
    speak("Hello, I am SakshamAI. How can I help you today?")