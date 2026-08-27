import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------
# Paths
# --------------------------------------------------

VOICE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = VOICE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --------------------------------------------------
# Environment
# --------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------
# Import chatbot
# --------------------------------------------------

from chatbot import DocumentChatbot


# --------------------------------------------------
# Voice Assistant
# --------------------------------------------------

def speak_with_lock(text: str) -> bool:
    if not text or not text.strip():
        return
    try:
        from .tts import speak
    except ImportError:
        from tts import speak

    return speak(text, save_audio=False)


def parse_mode_choice(choice: str):
    if not choice:
        return None

    text = choice.lower().strip()
    normalized = re.sub(r"[^a-z\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    speech_keywords = {
        "speech mode",
        "voice mode",
        "speech",
        "voice",
        "talk mode",
        "voice assistant mode",
        "audio mode",
    }
    normal_keywords = {
        "normal mode",
        "text mode",
        "normal",
        "text",
        "type mode",
        "chat mode",
        "written mode",
    }

    if normalized in speech_keywords or any(keyword in normalized for keyword in ["speech mode", "voice mode", "speech", "voice"]):
        return "speech"
    if normalized in normal_keywords or any(keyword in normalized for keyword in ["normal mode", "text mode", "normal", "text"]):
        return "normal"
    return None


def is_exit_phrase(question: str) -> bool:
    if not question:
        return False

    text = question.lower().strip()
    return bool(re.search(r"\b(exit|quit|bye|goodbye|stop)\b", text))


def get_mode_selection(max_attempts: int = 3):
    while True:
        print("\nSelect speech mode or normal mode.")
        typed_choice = input("Type 'speech' or 'normal': ").strip().lower()
        parsed_mode = parse_mode_choice(typed_choice)
        if parsed_mode:
            return parsed_mode
        print("Invalid input. Please type 'speech' or 'normal'.")


def main():

    print("=" * 60)
    print("SakshamAI - Adaptive Voice Assistant")
    print("=" * 60)

    print("\nStarting SakshamAI...")

    try:
        chatbot = DocumentChatbot()
        mode = get_mode_selection()

        if mode == "speech":
            try:
                from .stt import cleanup_temp_file, record_audio, transcribe_audio
            except ImportError:
                from stt import cleanup_temp_file, record_audio, transcribe_audio

        if mode == "speech":
            speak_with_lock("Speech mode is enabled. You can ask me anything.")
        else:
            print("Normal mode is enabled. I will reply in text only.")

        while True:
            print("\n" + "-" * 60)

            if mode == "speech":
                audio_file = record_audio(duration_limit=int(os.getenv("VOICE_PHRASE_SECONDS", "12")))

                if not audio_file:
                    print("No speech detected. Please try again.")
                    continue

                question = transcribe_audio(audio_file)
                cleanup_temp_file(audio_file)
            else:
                question = input("You: ").strip()

            if not question:
                print("I could not understand that.")
                if mode == "speech":
                    speak_with_lock("Sorry, I could not understand you. Please try again.")
                continue

            print(f"\nYou: {question}")

            if is_exit_phrase(question):
                if mode == "speech":
                    speak_with_lock("Goodbye. Have a great day!")
                else:
                    print("Goodbye. Have a great day!")
                break

            print("\nSakshamAI is thinking...")
            try:
                answer = chatbot.ask(question)
            except Exception:
                answer = "Sorry, something went wrong, please try again."

            print(f"\nSakshamAI: {answer}")

            if mode == "speech":
                try:
                    if not speak_with_lock(answer):
                        print("Audio playback unavailable; the answer is shown above.")
                except Exception:
                    print("Sorry, something went wrong, please try again.")

    except KeyboardInterrupt:
        print("\nVoice assistant stopped by user.")
        try:
            speak_with_lock("Goodbye. Have a great day!")
        except Exception:
            pass
        print("Exiting cleanly.")


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    main()