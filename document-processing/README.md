# SakshamAI

**CEP Topic 39:** Assistive Learning Tools for Differently-Abled Students
**Team:** 4 members, one module each — see `docs/` for the full plan.

## Project structure

```
sakshamai/
├── document-processing/   Member 4 — PDF/image -> clean text (BUILT, tested, running)
├── gemini-core/            Member 2 — notes / quiz / flashcards prompts
├── chatbot-voice/          Member 3 — grounded chatbot + Adaptive Voice Mode
├── ui/                     Member 4 — main interface, integrates everything
└── docs/                   Project plan, architecture, report material
```

## Build order (per the plan's dependency chain)

1. **document-processing** — done. Native PDF text extraction with OCR
   fallback for scanned pages/images, exposed both as a Python module and a
   FastAPI service (`/extract` endpoint). Tested against native-text PDFs,
   scanned-image PDFs, and raw images.
2. **gemini-core** — next. Takes `document-processing`'s output and generates
   notes/quiz/flashcards.
3. **chatbot-voice** — after gemini-core's prompting patterns are proven out.
4. **ui** — integrates all three into one student session.

## Quick start (document-processing, already working)

```bash
cd document-processing
pip install -r requirements.txt
uvicorn api:app --reload --port 8001
# in another terminal:
curl -X POST http://localhost:8001/extract -F "file=@test_native.pdf"
```

See `document-processing/README.md` for full details, known limitations, and
integration notes for whoever picks up gemini-core next.
