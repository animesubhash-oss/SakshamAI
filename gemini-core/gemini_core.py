import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()


# ==========================================
# GEMINI API SETUP
# ==========================================

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


# ==========================================
# LOAD PROMPT
# ==========================================

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def generate_content(prompt):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {e}") from e

# ==========================================
# GENERATE NOTES
# ==========================================

def generate_notes(document_text):

    prompt = load_prompt(PROMPTS_DIR / "notes_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


# ==========================================
# GENERATE QUIZ
# ==========================================

def generate_quiz(document_text):

    prompt = load_prompt(PROMPTS_DIR / "quiz_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


def generate_quiz_for_topic(topic):
    """Create a quiz from a subject chosen by the learner, without a document."""
    prompt = f"""
Create exactly 5 multiple-choice questions about this study topic: {topic}

Rules:
- Make the questions appropriate for a student.
- Each question must have exactly 4 options labelled A, B, C, and D.
- After each question's four options, add exactly one grading line in the form
    Answer: A (or B, C, or D). The application stores this line privately and
    does not display it before the learner submits an answer.
- Use clear, factual language and do not ask trick questions.

Use this format:
Question 1: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A, B, C, or D]

Question 2: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A, B, C, or D]

Question 3: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A, B, C, or D]

Question 4: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A, B, C, or D]

Question 5: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A, B, C, or D]
"""
    return generate_content(prompt)


# ==========================================
# GENERATE FLASHCARDS
# ==========================================

def generate_flashcards(document_text):

    prompt = load_prompt(PROMPTS_DIR / "flashcards_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


def generate_notes_for_topic(topic):
    """Create concise notes from a subject chosen by the learner."""
    return generate_content(
        f"Create clear, student-friendly revision notes about: {topic}. "
        "Use headings and short bullet points. Explain the key ideas accurately."
    )


def generate_flashcards_for_topic(topic):
    """Create revision flashcards from a subject chosen by the learner."""
    return generate_content(
        f"Create 10 concise revision flashcards about: {topic}. "
        "Use exactly this format for each one:\n"
        "Flashcard 1:\nQuestion: [question]\nAnswer: [answer]"
    )


# ==========================================
# TEST DOCUMENT
# ==========================================

text = """
Photosynthesis is the process by which green plants make their food
using sunlight, carbon dioxide, and water. Chlorophyll absorbs sunlight
and helps convert these materials into glucose and oxygen.
"""


# ==========================================
# HALLUCINATION TEST
# ==========================================

hallucination_document = """
Photosynthesis is the process by which green plants make their food
using sunlight, carbon dioxide, and water. Chlorophyll absorbs sunlight
and helps convert these materials into glucose and oxygen.
"""

hallucination_question = "Who discovered photosynthesis?"

hallucination_prompt = f"""
Answer the question using ONLY the information provided in the document.

Rules:
- Do not use outside knowledge.
- Do not guess.
- If the answer is not present in the document, say:
  "Information not available in the document."

Document:
{hallucination_document}

Question:
{hallucination_question}
"""

if __name__ == "__main__":
    notes = generate_notes(text)
    print("\n==============================")
    print("       SIMPLIFIED NOTES")
    print("==============================")
    print(notes)

    quiz = generate_quiz(text)
    print("\n==============================")
    print("       5-QUESTION QUIZ")
    print("==============================")
    print(quiz)

    flashcards = generate_flashcards(text)
    print("\n==============================")
    print("       FLASHCARDS")
    print("==============================")
    print(flashcards)

    response = generate_content(hallucination_prompt)
    print("\n==============================")
    print("       HALLUCINATION TEST")
    print("==============================")
    print(response)
