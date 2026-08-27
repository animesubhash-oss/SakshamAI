# SakshamAI Backend Debug Branch

SakshamAI is a CEP Topic 39 assistive learning tool for differently-abled
students. This branch contains backend and manual debugging components for
document processing, Gemini learning-content generation, document chat, and
the shared ElevenLabs speech-to-text/text-to-speech path.

## Setup

Use Python 3.11 or newer in a virtual environment. Install each module's
dependencies from the relevant directory:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r document_processing\requirements.txt
python -m pip install -r gemini-core\requirements.txt
python -m pip install -r chatbot-voice\requirements.txt
```

Copy `.env.example` to `.env` and fill in values locally. Never commit `.env`:

```env
GEMINI_API_KEY=
ELEVENLABS_API_KEY=
MIC_DEVICE_INDEX=0
```

The document OCR path also requires the Tesseract system executable. On
Windows, install Tesseract and add its installation directory to `PATH`; on
macOS use `brew install tesseract`; on Debian/Ubuntu use
`sudo apt install tesseract-ocr`.

## Independent Checks

Run the document processor directly with a supported PDF or image:

```powershell
python document_processing\document_processor.py path\to\document.pdf
```

Run the Gemini core demonstrations from its directory. This requires a valid
`GEMINI_API_KEY` and available quota:

```powershell
python gemini-core\gemini_core.py
```

Run the document chatbot independently:

```powershell
python chatbot-voice\chatbot.py
```

Run the manual microphone capture check. It reads `MIC_DEVICE_INDEX`, records
at 16 kHz, and sends the WAV file through ElevenLabs `scribe_v1`:

```powershell
python tests\manual\test_microphone.py
```

Re-transcribe the saved recording through the same production STT helper:

```powershell
python tests\manual\test_google_stt.py
```

The last script is retained as a scratch filename for compatibility; it does
not use Google Web Speech API. Saved local recordings live in
`tests/fixtures/audio/` and are ignored by Git.
