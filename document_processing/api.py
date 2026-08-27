"""
SakshamAI — Document Processing API
Owner: Member 4

Thin HTTP wrapper around document_processor.py so Member 2 (Gemini core)
and Member 3 (chatbot) can call this as a service instead of importing
Python directly.

Run:
    uvicorn api:app --reload --port 8001

Endpoints:
    POST /extract        -> upload a PDF/image, get back clean text + metadata
    GET  /health          -> simple liveness check
"""

import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from document_processing.document_processor import process_document

app = FastAPI(
    title="SakshamAI Document Processing Service",
    description="PDF/image upload -> text extraction (native + OCR fallback) -> cleaned text",
    version="1.0.0",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_MB = 20


@app.get("/health")
def health():
    return {"status": "ok", "service": "sakshamai-document-processing"}


@app.post("/extract")
async def extract(file: UploadFile = File(...), ocr_lang: str = "eng"):
    """
    Upload a PDF or image. Returns extracted + cleaned text plus per-page
    metadata (which pages used native extraction vs OCR, warnings, etc).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    contents = await file.read()

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_SIZE_MB} MB.",
        )

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = process_document(contents, file.filename, ocr_lang=ocr_lang)
    return result.to_dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)