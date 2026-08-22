import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


# ==========================================
# GEMINI API SETUP
# ==========================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)


# ==========================================
# LOAD PROMPT
# ==========================================

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def generate_content(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {e}") from e

# ==========================================
# GENERATE NOTES
# ==========================================

def generate_notes(document_text):

    prompt = load_prompt("prompts/notes_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


# ==========================================
# GENERATE QUIZ
# ==========================================

def generate_quiz(document_text):

    prompt = load_prompt("prompts/quiz_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


# ==========================================
# GENERATE FLASHCARDS
# ==========================================

def generate_flashcards(document_text):

    prompt = load_prompt("prompts/flashcards_prompt.txt")
    prompt = prompt.replace("{document_text}", document_text)

    return generate_content(prompt)


# ==========================================
# TEST DOCUMENT
# ==========================================

text = """
Photosynthesis is the process by which green plants make their food
using sunlight, carbon dioxide, and water. Chlorophyll absorbs sunlight
and helps convert these materials into glucose and oxygen.
"""


# ==========================================
# TEST NOTES
# ==========================================

notes = generate_notes(text)

print("\n==============================")
print("       SIMPLIFIED NOTES")
print("==============================")

print(notes)


# ==========================================
# TEST QUIZ
# ==========================================

quiz = generate_quiz(text)

print("\n==============================")
print("       5-QUESTION QUIZ")
print("==============================")

print(quiz)


# ==========================================
# TEST FLASHCARDS
# ==========================================

flashcards = generate_flashcards(text)

print("\n==============================")
print("       FLASHCARDS")
print("==============================")

print(flashcards)


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

response = generate_content(hallucination_prompt)

print("\n==============================")
print("       HALLUCINATION TEST")
print("==============================")

print(response)