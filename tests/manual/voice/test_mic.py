import audioop
import os

import speech_recognition as sr
from stt import transcribe_audio

MIC_DEVICE_INDEX = int(os.getenv("MIC_DEVICE_INDEX", "9"))

recognizer = sr.Recognizer()

print("=" * 60)
print("SakshamAI Microphone Test")
print("=" * 60)
print(f"Using microphone device: {MIC_DEVICE_INDEX}")
print()
print("Speak clearly after the message appears.")
print("You have 10 seconds to start speaking.")
print()

try:
    with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:

        print("Adjusting for background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print()
        print("🎤 Speak now...")
        
        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=7
        )

        raw_audio = audio.get_raw_data()
        print(
            f"Captured {len(raw_audio) / (audio.sample_rate * audio.sample_width):.1f}s "
            f"(RMS {audioop.rms(raw_audio, audio.sample_width)}, "
            f"peak {audioop.max(raw_audio, audio.sample_width)})"
        )

    print()
    print("Processing speech with ElevenLabs...")

    audio_file = "mic_input.wav"
    with open(audio_file, "wb") as recording:
        recording.write(audio.get_wav_data())

    text = transcribe_audio(audio_file)

    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print("You said:", text)
    print("=" * 60)

except sr.WaitTimeoutError:
    print()
    print("ERROR: No speech detected within 10 seconds.")

except Exception as error:
    print()
    print("ERROR:")
    print(type(error).__name__, error)