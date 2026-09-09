"""Bridge to the existing ``DocumentChatbot`` (chatbot-voice/chatbot.py).

The chatbot keeps its own Gemini session, document context and history, so this
module only creates it, hands documents over, and forwards questions.
"""

from __future__ import annotations

import logging
from typing import Any

from .bootstrap import BackendError, prepare_backend

logger = logging.getLogger("sakshamai.ui.chat")


def create_chatbot() -> Any:
    """Start a chatbot session (general mode until a document is attached)."""
    prepare_backend()
    from chatbot import DocumentChatbot

    try:
        return DocumentChatbot()
    except Exception as error:
        logger.exception("Chatbot could not start")
        message = str(error)
        if "GEMINI_API_KEY" in message:
            friendly = (
                "SakshamAI needs a Gemini API key to answer questions. "
                "Add GEMINI_API_KEY to chatbot-voice/.env and restart."
            )
        else:
            friendly = "SakshamAI could not start the AI session."
        raise BackendError(friendly, message) from error


def attach_document(chatbot: Any, text: str, name: str) -> None:
    """Point an existing chatbot session at a document."""
    try:
        chatbot.set_document(text, name)
    except Exception as error:
        logger.exception("Could not attach the document to the chatbot")
        raise BackendError(
            "SakshamAI could not use this document for questions.", str(error)
        ) from error


def detach_document(chatbot: Any) -> None:
    """Return the chatbot to general study mode."""
    try:
        chatbot.clear_document()
    except Exception as error:  # pragma: no cover - defensive
        logger.warning("Could not clear the document: %s", error)


def ask(chatbot: Any, question: str) -> str:
    """Ask a question. ``DocumentChatbot.ask`` already returns readable errors."""
    answer = chatbot.ask(question)
    if not answer or not answer.strip():
        raise BackendError(
            "SakshamAI did not return an answer. Please try asking again.",
            "empty answer",
        )
    return answer.strip()


def build_chatbot(document_text: str | None = None, document_name: str = "document") -> Any:
    """Compatibility wrapper for the app's legacy entrypoint."""
    bot = create_chatbot()
    if document_text and document_text.strip():
        attach_document(bot, document_text, document_name or "document")
    return bot


def ask_question(chatbot: Any, question: str) -> str:
    """Compatibility wrapper used by the older UI shell."""
    return ask(chatbot, question)
