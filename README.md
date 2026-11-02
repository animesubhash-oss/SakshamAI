# SakshamAI

**AI-powered assistive learning platform for differently-abled students.**
*"Learning should adapt to the learner, not the other way around."*

SakshamAI lets a student upload study material (PDFs, scans, photos of notes) and turns it into content they can use: simplified notes, quizzes, flashcards, and a chatbot that answers questions about the uploaded document, with voice input/output and per-user accessibility settings.

Built as a college team project (CEP Topic 39).

## Features

- **Document upload**: PDF, PNG, JPG/JPEG, WEBP, BMP, TIFF
- **Text extraction**: native PDF text via `pdfplumber`, with automatic OCR fallback (`Tesseract` + `PyMuPDF` page rendering) for scanned pages and images
- **AI study material** (Google Gemini): simplified notes, quizzes, flashcards, generated from prompt templates in `gemini-core/prompts/`
- **Document-grounded chatbot**: ask questions about the uploaded document, or general questions
- **Voice mode**: speech-to-text (ElevenLabs `scribe_v1`) and text-to-speech (ElevenLabs `eleven_multilingual_v2`)
- **Accounts and accessibility profiles**: bcrypt-hashed passwords, MongoDB storage with a local fallback, and a profile that adapts the interface
- **Streamlit UI** with dedicated accessibility styles (`ui/styles/accessibility.css`)

## Architecture

```text
Upload ──> document_processing ──> clean structured text
                                        │
                     ┌──────────────────┴───────────────────┐
                     ▼                                      ▼
               gemini-core                            chatbot-voice
        (notes / quiz / flashcards)          (document Q&A + STT/TTS voice)
                     └──────────────────┬───────────────────┘
                                        ▼
                                   ui (Streamlit)
                            + auth_mongo (users, profiles)
```

| Module | Responsibility |
|---|---|
| `document_processing/` | File-type detection, PDF/image extraction, OCR fallback, text cleaning, optional FastAPI wrapper (`POST /extract`, `GET /health`) |
| `gemini-core/` | Gemini client and prompt-driven generation of notes, quizzes, flashcards |
| `chatbot-voice/` | Document-grounded chatbot, microphone capture, speech-to-text, text-to-speech |
| `ui/` | Streamlit app, login, services layer, session state, accessibility styling |
| `tests/` | Unit tests for the chatbot, document processor and text cleaner; manual microphone/voice checks |

## Tech stack

Python 3.11+, Streamlit, Google Gemini (`google-genai`), Tesseract OCR (`pytesseract`), `pdfplumber`, PyMuPDF, ElevenLabs, MongoDB (`pymongo`), bcrypt, FastAPI (optional extraction service)

## Getting started

```powershell
git clone https://github.com/animesubhash-oss/SakshamAI.git
cd SakshamAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r document_processing\requirements.txt
python -m pip install -r gemini-core\requirements.txt
python -m pip install -r chatbot-voice\requirements.txt
Copy-Item .env.example .env
```

Add your own API keys to `.env`. Never commit `.env`, `.sakshamai_auth_store.json`, passwords, or API keys. The local auth store and generated MP3 files are ignored by Git; do not share the auth store because it contains personal profile data and password hashes.

Install the Tesseract executable separately (on Windows, use the Tesseract installer and add its directory to `PATH`; on macOS, use `brew install tesseract`; on Debian/Ubuntu, use `sudo apt install tesseract-ocr`).

`.env`:

```env
GEMINI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
MIC_DEVICE_INDEX=0
# optional
MONGODB_URI=mongodb://127.0.0.1:27017
```

Run the app from the project root:

```powershell
streamlit run ui\app_v3.py
```

Run the tests:

```powershell
python -m pytest tests\chatbot tests\document_processing
```

## Current status and known limitations

- OCR quality depends on scan clarity and installed Tesseract language packs; only English is configured by default.
- Voice mode needs a working microphone and an ElevenLabs API key.
- Generated notes, quizzes and flashcards come from an LLM and can contain mistakes; they should be checked against the source material.
- The UI has not yet been evaluated with real differently-abled users. The accessibility settings follow common guidance but are untested with assistive-technology users.
- `ui/` contains earlier iterations (`app.py`, `app_v2.py`); `app_v3.py` is the current entry point.

## License

No license file is currently included, so the project does not explicitly grant permission to use or redistribute its contents.
