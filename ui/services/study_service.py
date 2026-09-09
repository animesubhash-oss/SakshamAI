"""Study material: notes, quiz and flashcards.

Generation is done by the untouched ``gemini-core/gemini_core.py``.  Gemini
returns plain text in the shape described by the project's prompt files, so this
module also parses that text into the structures the quiz and flashcard
experiences need.  No prompt or model behaviour is redefined here.
"""

from __future__ import annotations

import logging
import re

from ..state.session_state import Flashcard, QuizItem
from .bootstrap import BackendError, gemini_core

logger = logging.getLogger("sakshamai.ui.study")

_QUESTION = re.compile(r"^\**\s*question\s*(\d+)\s*[:.)-]\s*(.*)$", re.IGNORECASE)
_OPTION = re.compile(r"^\**\s*([A-Da-d])\s*[.)]\s*(.+)$")
_ANSWER = re.compile(r"^\**\s*(?:correct\s+)?answer\s*[:.)-]?\s*\**\s*([A-Da-d]|[1-4])\b", re.IGNORECASE)
_CARD = re.compile(r"^\**\s*flashcard\s*(\d+)\s*[:.)-]?\s*$", re.IGNORECASE)
_CARD_Q = re.compile(r"^\**\s*question\s*[:.)-]\s*(.*)$", re.IGNORECASE)
_CARD_A = re.compile(r"^\**\s*answer\s*[:.)-]\s*(.*)$", re.IGNORECASE)


def _plain(text: str) -> str:
    """Drop the stray markdown emphasis Gemini sometimes adds."""
    return re.sub(r"\*+|_{2,}|`", "", text).strip()


def _choice_letter(value: str) -> str:
    token = value.strip().upper()
    if token in {"A", "B", "C", "D"}:
        return token
    if token in {"1", "2", "3", "4"}:
        return "ABCD"[int(token) - 1]
    return ""


def _generate(kind: str, document_text: str) -> str:
    if not document_text.strip():
        raise BackendError("Add a document first, then SakshamAI can build this.", "no document")

    module = gemini_core()
    builder = {
        "notes": module.generate_notes,
        "quiz": module.generate_quiz,
        "flashcards": module.generate_flashcards,
    }[kind]

    try:
        output = builder(document_text)
    except Exception as error:
        detail = str(error)
        logger.exception("Gemini %s generation failed", kind)
        raise BackendError(_friendly_generation_error(kind, detail), detail) from error

    if not output or not output.strip():
        raise BackendError(f"SakshamAI returned empty {kind}.", "empty response")
    return output.strip()


def build_notes(document_text: str) -> str:
    return _generate("notes", document_text)


def generate_notes(document_text: str) -> str:
    return build_notes(document_text)


def generate_notes_for_topic(topic: str) -> str:
    return _generate_topic("notes", topic)


def build_quiz(document_text: str) -> list[QuizItem]:
    return parse_quiz(_generate("quiz", document_text))


def generate_quiz(document_text: str) -> str:
    return _generate("quiz", document_text)


def generate_quiz_for_topic(topic: str) -> str:
    return _generate_topic("quiz", topic)


def build_flashcards(document_text: str) -> list[Flashcard]:
    return parse_flashcards(_generate("flashcards", document_text))


def generate_flashcards(document_text: str) -> str:
    return _generate("flashcards", document_text)


def generate_flashcards_for_topic(topic: str) -> str:
    return _generate_topic("flashcards", topic)


def _generate_topic(kind: str, topic: str) -> str:
    """Generate material from a learner-entered topic instead of a document."""
    cleaned_topic = topic.strip()
    if len(cleaned_topic) < 2:
        raise BackendError("Enter a topic first, then SakshamAI can create study material.", "missing topic")

    module = gemini_core()
    builder = {
        "notes": module.generate_notes_for_topic,
        "quiz": module.generate_quiz_for_topic,
        "flashcards": module.generate_flashcards_for_topic,
    }[kind]
    try:
        output = builder(cleaned_topic)
    except Exception as error:
        detail = str(error)
        logger.exception("Gemini topic %s generation failed", kind)
        raise BackendError(_friendly_generation_error(kind, detail), detail) from error
    if not output or not output.strip():
        raise BackendError(f"SakshamAI returned empty {kind}.", "empty response")
    return output.strip()


def _friendly_generation_error(kind: str, detail: str) -> str:
    """Turn common Gemini failures into useful messages for the learner."""
    lower = detail.lower()
    if "quota" in lower or "429" in detail or "resource_exhausted" in lower:
        return "Gemini's free API quota is exhausted. Please wait for the quota to reset or use a billing-enabled API key."
    if "api key" in lower or "401" in detail or "403" in detail:
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in chatbot-voice/.env."
    if "404" in detail or "model" in lower and "not found" in lower:
        return "The configured Gemini model was not found. Check GEMINI_MODEL in chatbot-voice/.env."
    if "503" in detail or "unavailable" in lower or "500" in detail:
        return "Gemini is busy right now. Please try again in a moment."
    return f"SakshamAI could not build your {kind}. Check the backend error and try again."


def parse_quiz(raw: str) -> list[QuizItem]:
    """Read the ``Question n: / A-D / Answer:`` shape from quiz_prompt.txt."""
    items: list[QuizItem] = []
    stem = ""
    options: dict[str, str] = {}
    correct = ""

    def flush() -> None:
        if stem and len(options) >= 2 and correct in options:
            items.append(
                QuizItem(number=len(items) + 1, stem=stem, options=dict(options), correct=correct)
            )

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        question = _QUESTION.match(line)
        if question:
            flush()
            stem, options, correct = _plain(question.group(2)), {}, ""
            continue
        option = _OPTION.match(line)
        if option and stem:
            options[option.group(1).upper()] = _plain(option.group(2))
            continue
        answer = _ANSWER.match(line)
        if answer and stem:
            correct = _choice_letter(answer.group(1))
            continue
        if stem and not options:
            stem = f"{stem} {_plain(line)}".strip()

    flush()

    if not items:
        logger.error("Quiz could not be parsed. Raw output:\n%s", raw)
        raise BackendError(
            "SakshamAI's quiz came back in an unexpected shape. Please try again.",
            "quiz parsing failed",
        )
    return items


def parse_flashcards(raw: str) -> list[Flashcard]:
    """Read the ``Flashcard n: / Question: / Answer:`` shape from the prompt."""
    cards: list[Flashcard] = []
    question = ""
    answer_lines: list[str] = []
    reading_answer = False

    def flush() -> None:
        nonlocal question, answer_lines, reading_answer
        text = " ".join(part for part in answer_lines if part).strip()
        if question and text:
            cards.append(Flashcard(number=len(cards) + 1, question=question, answer=text))
        question, answer_lines, reading_answer = "", [], False

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if _CARD.match(line):
            flush()
            continue
        card_question = _CARD_Q.match(line)
        if card_question:
            if reading_answer or question:
                flush()
            question, reading_answer = _plain(card_question.group(1)), False
            continue
        card_answer = _CARD_A.match(line)
        if card_answer:
            answer_lines = [_plain(card_answer.group(1))]
            reading_answer = True
            continue
        if reading_answer:
            answer_lines.append(_plain(line))
        elif question:
            question = f"{question} {_plain(line)}".strip()

    flush()

    if not cards:
        logger.error("Flashcards could not be parsed. Raw output:\n%s", raw)
        raise BackendError(
            "SakshamAI's flashcards came back in an unexpected shape. Please try again.",
            "flashcard parsing failed",
        )
    return cards
