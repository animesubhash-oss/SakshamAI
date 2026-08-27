import speech_recognition as sr


def get_default_microphone_index():
    microphones = sr.Microphone.list_microphone_names()
    if not microphones:
        return None

    preferred_names = ["default", "built-in", "internal", "microphone"]

    for index, name in enumerate(microphones):
        lowered = name.lower()
        if any(keyword in lowered for keyword in preferred_names):
            return index

    return 0


def listen_for_speech(recognizer, device_index=None):
    mic = sr.Microphone(device_index=device_index) if device_index is not None else sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening... Speak now.")
        return recognizer.listen(source, timeout=10, phrase_time_limit=10)


def main():
    recognizer = sr.Recognizer()

    print("Available microphones:")
    microphones = sr.Microphone.list_microphone_names()
    for index, name in enumerate(microphones):
        print(f"{index}: {name}")

    selected_index = get_default_microphone_index()
    if selected_index is not None:
        print(f"\nUsing microphone index: {selected_index}")
    else:
        print("\nNo microphones found.")
        return

    try:
        audio = listen_for_speech(recognizer, device_index=selected_index)
        print("Recording captured.")
        print("Recognizing...")

        text = recognizer.recognize_google(audio)
        print("\nYou said:")
        print(text)

    except sr.WaitTimeoutError:
        print("No speech detected within the timeout period.")
    except sr.UnknownValueError:
        print("Could not understand the audio.")
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
    except OSError as e:
        print(f"Microphone error: {e}")


if __name__ == "__main__":
    main()