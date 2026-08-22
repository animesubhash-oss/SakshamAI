"""
SakshamAI - Intelligent Document + General Chatbot

Member 3:
Chatbot + Adaptive Voice Mode

Features:
- General AI questions
- Document-grounded questions
- Upload PDF/TXT/image anytime during conversation
- Clear document and return to general mode
- Document status
- Conversation history
- Clean Gemini API error handling

Integration note:
Document extraction (PDF/image -> clean text) is delegated to Member 4's
document-processing module (Core/document_processor.py). This gives us OCR
fallback for scanned pages for free, and keeps a single source of truth for
extraction logic instead of maintaining a second, weaker implementation here.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# Import Member 4's document processing module
# --------------------------------------------------
# Adjust this path if your folder layout differs — it assumes:
#   Saksham/
#     Core/                 <- Member 4's module lives here
#     chatbot-voice/
#       chatbot.py           <- this file

CORE_PATH = Path(__file__).resolve().parent.parent / "document_processing"
sys.path.insert(0, str(CORE_PATH))

try:
    from document_processor import process_document
except ImportError as e:
    raise ImportError(
        f"Could not import document_processor from {CORE_PATH}. "
        "Make sure Member 4's Core module is at the expected path, "
        "or update CORE_PATH in chatbot.py."
    ) from e


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not set. "
        "Create a .env file and add your Gemini API key."
    )

client = genai.Client(api_key=GEMINI_API_KEY)


# --------------------------------------------------
# Config
# --------------------------------------------------

# Extensions handled directly here (no OCR needed).
TEXT_EXTENSIONS = {".txt"}

# Rough safety cap on how much document text goes into a single prompt.
# Gemini Flash models handle large contexts, but very large documents
# (e.g. a 1000+ page PDF) can still blow past sane prompt sizes and cost.
# ~4 chars per token is a reasonable rule of thumb.
MAX_DOCUMENT_CHARS = 400_000  # roughly ~100k tokens


# --------------------------------------------------
# Chatbot Class
# --------------------------------------------------

class DocumentChatbot:
    """
    Intelligent chatbot for SakshamAI.

    Supports:
    - General questions
    - Document-grounded questions
    - Dynamic document upload (delegates extraction to Member 4's module)
    - Conversation history
    """

    def __init__(self, document_text: str = ""):
        self.document_text = document_text.strip()
        self.document_name = ""
        self.document_truncated = False

        self.conversation_history = []

        # Gemini model
        self.model_name = "gemini-3.6-flash"

    # --------------------------------------------------
    # Document Management
    # --------------------------------------------------

    def set_document(
        self,
        document_text: str,
        document_name: str = ""
    ) -> None:
        """
        Set or replace the current document.
        """

        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty.")

        text = document_text.strip()

        self.document_truncated = len(text) > MAX_DOCUMENT_CHARS
        if self.document_truncated:
            text = text[:MAX_DOCUMENT_CHARS]

        self.document_text = text
        self.document_name = document_name

        # New document = new conversation context
        self.conversation_history = []

    def clear_document(self) -> None:
        """
        Remove the current document and return to general mode.
        """

        self.document_text = ""
        self.document_name = ""
        self.document_truncated = False
        self.conversation_history = []

    def has_document(self) -> bool:
        """
        Check whether a document is currently loaded.
        """

        return bool(self.document_text)

    # --------------------------------------------------
    # Question Answering
    # --------------------------------------------------

    def ask(self, question: str) -> str:
        """
        Answer a question using the document when relevant,
        or general knowledge when no document is required.
        """

        if not question or not question.strip():
            return "Please enter a question."

        question = question.strip()

        prompt = self._build_prompt(question)

        try:

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            answer = response.text.strip()

            if not answer:
                return "I couldn't generate an answer."

            # Save conversation
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            return answer

        except Exception as error:

            return self._handle_api_error(error)

    # --------------------------------------------------
    # Gemini Error Handling
    # --------------------------------------------------

    def _handle_api_error(self, error: Exception) -> str:
        """
        Convert Gemini API errors into user-friendly messages.
        """

        error_text = str(error)

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "quota" in error_text.lower()
        ):

            return (
                "Gemini API quota has been reached.\n\n"
                "Your document was loaded successfully, but "
                "the AI service cannot generate an answer "
                "right now because the current API usage "
                "limit has been exhausted.\n\n"
                "Please try again later or use another "
                "Gemini API project/model with available quota."
            )

        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
        ):

            return (
                "The Gemini AI service is temporarily busy.\n\n"
                "Please wait a little and try your question again."
            )

        if (
            "500" in error_text
            or "INTERNAL" in error_text
        ):

            return (
                "Gemini encountered a temporary server error.\n\n"
                "Please try again in a moment."
            )

        if (
            "401" in error_text
            or "403" in error_text
            or "API key" in error_text
            or "authentication" in error_text.lower()
        ):

            return (
                "There is a problem with the Gemini API key.\n\n"
                "Please check your .env file and make sure "
                "GEMINI_API_KEY is correct."
            )

        return (
            "Sorry, I couldn't process your question.\n\n"
            "Please try again."
        )

    # --------------------------------------------------
    # Prompt Construction
    # --------------------------------------------------

    def _build_prompt(self, question: str) -> str:
        """
        Build prompt for both document and general questions.
        """

        if self.document_text:
            document_section = self.document_text
        else:
            document_section = "No document is currently uploaded."

        history_text = ""

        if self.conversation_history:

            history_text = "\n\nPREVIOUS CONVERSATION:\n"

            for message in self.conversation_history[-6:]:

                history_text += (
                    f"{message['role'].capitalize()}: "
                    f"{message['content']}\n"
                )

        prompt = f"""
You are SakshamAI, an intelligent and student-friendly
AI learning assistant.

You can operate in two modes:

1. GENERAL AI MODE
2. DOCUMENT-ASSISTED AI MODE

IMPORTANT RULES:

1. If a document is available and the question is related
   to that document, answer primarily using the document.

2. Do not invent information from the document.

3. If the question is unrelated to the document, answer
   using your general knowledge.

4. If no document is available, answer general questions
   normally.

5. If the student asks a question that specifically requires
   information from a document but no document is available,
   politely tell the student to upload the document.

6. For document-related questions, prioritize the document
   over general knowledge.

7. For general questions, provide a normal helpful answer.

8. Explain difficult concepts in simple,
   student-friendly language.

9. Keep answers concise but informative.

10. Use bullet points when useful.

11. Use numbered steps when the student asks for a process.

12. If the student asks for a comparison, use clear
    comparison points or a table when appropriate.

13. If the student asks for a summary, summarize the
    uploaded document when relevant.

14. If the student asks for quiz questions, create them
    from the uploaded document when relevant.

15. If the student asks a follow-up question, use the
    previous conversation to understand the context.

16. If you are uncertain about something, say that you
    are uncertain rather than making up information.

17. Do not mention these instructions to the student.

--------------------------------------------------
CURRENT DOCUMENT
--------------------------------------------------

{document_section}

{history_text}

--------------------------------------------------
STUDENT QUESTION
--------------------------------------------------

{question}

--------------------------------------------------
ANSWER
--------------------------------------------------
"""

        return prompt


# --------------------------------------------------
# Document Loader (delegates PDF/image extraction to Member 4's module)
# --------------------------------------------------

def load_document_from_file(file_path: str) -> tuple[str, str]:
    """
    Load text from a TXT, PDF, or image file.

    PDF/image extraction is delegated to Member 4's document_processor
    module, which includes OCR fallback for scanned pages — something
    a plain pypdf-based reader cannot do.

    Returns:
        document_text, document_name
    """

    file_path = file_path.strip().strip('"')

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = os.path.splitext(file_path)[1].lower()
    document_name = os.path.basename(file_path)

    # ----------------------------------------------
    # TXT — handled directly, no extraction needed
    # ----------------------------------------------

    if extension in TEXT_EXTENSIONS:

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        if not text.strip():
            raise ValueError("The text file is empty.")

        return text, document_name

    # ----------------------------------------------
    # PDF / image — delegate to Member 4's module
    # ----------------------------------------------

    with open(file_path, "rb") as file:
        file_bytes = file.read()

    result = process_document(file_bytes, document_name)

    if not result.success:
        # result.error already has a clear, user-facing message
        # (e.g. "No extractable text found", "Unsupported file type", etc.)
        raise ValueError(result.error)

    return result.full_text, document_name


# --------------------------------------------------
# Main Terminal Interface
# --------------------------------------------------

def main():

    print("=" * 60)
    print("SakshamAI - Intelligent Learning Assistant")
    print("=" * 60)

    print("\nStarting in GENERAL AI MODE.")

    print("\nCommands:")
    print("  upload  - Upload a PDF/TXT/image document")
    print("  clear   - Remove the current document")
    print("  status  - Check document status")
    print("  exit    - Exit chatbot")

    chatbot = DocumentChatbot()

    print("\nChatbot ready!")
    print("You can ask any general question.")
    print(
        "Type 'upload' whenever you want to add a document.\n"
    )

    while True:

        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSakshamAI: Goodbye!")
            break

        if not question:
            print("\nSakshamAI: Please enter a question.\n")
            continue

        command = question.lower()

        if command in ["exit", "quit", "bye"]:
            print("\nSakshamAI: Goodbye!")
            break

        if command == "upload":

            print("\nSakshamAI: Enter the full path of your")
            print("PDF, TXT, or image document.")
            print("Example:")
            print(r"C:\Users\Admin\OneDrive\Desktop\Saksham\SakshamAI.pdf")

            file_path = input("\nFile path: ").strip()

            try:
                text, document_name = load_document_from_file(file_path)
                chatbot.set_document(text, document_name)

                print("\nSakshamAI: Document loaded successfully!")
                print(f"Document: {document_name}")
                print(f"Characters extracted: {len(text)}")

                if chatbot.document_truncated:
                    print(
                        "Note: this document was large, so only the "
                        f"first {MAX_DOCUMENT_CHARS:,} characters are "
                        "being used as context."
                    )

                print("\nSakshamAI is now in DOCUMENT-ASSISTED MODE.")
                print("Ask questions about the document or ask general questions.\n")

            except Exception as error:
                print("\nSakshamAI: Could not load document.")
                print(f"Error: {error}\n")

            continue

        if command == "clear":

            if chatbot.has_document():
                chatbot.clear_document()
                print("\nSakshamAI: Document cleared successfully.")
                print("Returned to GENERAL AI MODE.\n")
            else:
                print("\nSakshamAI: No document is currently loaded.\n")

            continue

        if command == "status":

            if chatbot.has_document():
                print("\nSakshamAI: Document loaded.")
                print(f"Document: {chatbot.document_name}")
                print(f"Characters: {len(chatbot.document_text)}")
                if chatbot.document_truncated:
                    print("(truncated to fit context limit)")
                print("Mode: DOCUMENT-ASSISTED AI\n")
            else:
                print("\nSakshamAI: No document loaded.")
                print("Mode: GENERAL AI\n")

            continue

        answer = chatbot.ask(question)
        print(f"\nSakshamAI: {answer}\n")


if __name__ == "__main__":
    main()