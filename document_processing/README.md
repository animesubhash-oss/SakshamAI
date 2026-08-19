# Document Processing Module

## Purpose

Extract educational content from documents and return clean, structured text for the Gemini core. This module does not generate notes, quizzes, flashcards, chatbot responses, or voice output.

## Supported formats

- PDF, including native text and scanned pages through OCR fallback
- PNG, JPG/JPEG, WEBP, BMP, and TIFF images through OCR

## Installation

```bash
pip install -r requirements.txt
```

Tesseract OCR must also be installed on the host system for scanned PDFs and images. Its language packs control the values accepted by `ocr_lang`.

## Python usage

```python
from pathlib import Path
from document_processor import process_document

result = process_document(Path("AI.pdf").read_bytes(), "AI.pdf")
structured_document = result.to_dict()
```

`process_document` accepts file bytes and a filename. The result contains:

- `filename`
- `file_type`
- `page_count`
- `content`, a list of `{page, text}` objects
- `full_text`
- extraction metadata, warnings, and errors

## Pipeline

1. `document_processor.py` detects the file type and coordinates processing.
2. `pdf_processor.py` extracts PDF pages and uses OCR for empty or scanned pages.
3. `image_processor.py` extracts text from image uploads with OCR.
4. `text_cleaner.py` performs conservative whitespace and extraction-artifact cleanup.
5. `document_models.py` provides the stable result format consumed by other modules.

The cleaner preserves headings, paragraphs, and educational wording. It removes only common extraction noise such as repeated spaces, excess blank lines, and lone page-number lines.

## HTTP service

The optional `api.py` wrapper exposes the same result through `POST /extract` and `GET /health`:

```bash
uvicorn api:app --reload --port 8001
```

## Limitations

- OCR quality depends on scan clarity and the installed Tesseract language packs.
- Only PDF and image files are currently supported.
- This module extracts and structures content; Gemini core owns all AI-generated learning materials.
