"""Centralised, per-browser-session state for the SakshamAI study workspace.

Everything the interface renders comes from one :class:`StudySession` instance
that is created once per connected client.  Components never keep their own
copies of application data - they read from here and ask the shell to re-render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Phase = Literal["empty", "loading", "ready", "error"]


@dataclass
class StudyDocument:
    """A document that has been extracted and is ready to study."""

    name: str
    text: str
    file_type: str = "text"
    page_count: int = 0
    native_pages: int = 0
    ocr_pages: int = 0
    warnings: list[str] = field(default_factory=list)
    truncated: bool = False
    seconds: float = 0.0
    source: str = "upload"

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def kind_label(self) -> str:
        return {"pdf": "PDF", "image": "Image", "text": "Text"}.get(self.file_type, "Document")

    @property
    def extraction_label(self) -> str:
        if self.ocr_pages and self.native_pages:
            return f"{self.native_pages} page(s) read directly, {self.ocr_pages} scanned with OCR"
        if self.ocr_pages:
            return f"{self.ocr_pages} page(s) scanned with OCR"
        if self.native_pages:
            return f"{self.native_pages} page(s) read directly"
        return "Text provided directly"


@dataclass
class Exchange:
    """One question and its answer in the study conversation."""

    question: str
    answer: str = ""
    phase: Phase = "loading"
    error: str = ""
    grounded_in: str = ""
    from_voice: bool = False


@dataclass
class QuizItem:
    number: int
    stem: str
    options: dict[str, str]
    correct: str
    chosen: str | None = None
    checked: bool = False

    @property
    def is_right(self) -> bool:
        return self.checked and self.chosen == self.correct


@dataclass
class Flashcard:
    number: int
    question: str
    answer: str
    revealed: bool = False
    difficult: bool = False


@dataclass
class Preferences:
    theme: str = "paper"  # paper | night | contrast
    text_size: str = "standard"  # standard | large | larger
    reduce_motion: bool = False
    speak_replies: bool = True  # read answers aloud in Voice Mode


@dataclass
class VoiceState:
    phase: str = "idle"  # idle | listening | transcribing | thinking | speaking | error
    heard: str = ""
    answer: str = ""
    message: str = ""


@dataclass
class StudySession:
    """All state for one student's session."""

    view: str = "start"  # start | workspace
    mode: str = "overview"  # overview | ask | notes | quiz | cards
    page: str = "home"
    authenticated: bool = False
    auth_mode: str = "login"
    auth_user_id: int | None = None
    username: str = ""
    auth_expires_at: float = 0.0
    accessibility_profile: dict[str, object] = field(default_factory=dict)
    accessibility_settings_open: bool = False
    voice_mode: bool = False
    stt_phrase_seconds: int = 12

    document: StudyDocument | None = None
    library: list[StudyDocument] = field(default_factory=list)
    document_phase: Phase = "empty"
    document_error: str = ""
    document_name: str = ""
    document_result: Any | None = None
    chat_history: list[dict[str, str]] = field(default_factory=list)
    last_error: str = ""

    chatbot: Any = None
    exchanges: list[Exchange] = field(default_factory=list)
    asking: bool = False

    notes: str = ""
    notes_phase: Phase = "empty"
    notes_error: str = ""

    quiz: list[QuizItem] | str = field(default_factory=list)
    quiz_phase: Phase = "empty"
    quiz_error: str = ""
    quiz_index: int = 0
    quiz_done: bool = False

    cards: list[Flashcard] = field(default_factory=list)
    cards_phase: Phase = "empty"
    cards_error: str = ""
    card_index: int = 0
    hard_only: bool = False
    flashcards: str = ""

    voice: VoiceState = field(default_factory=VoiceState)
    preferences: Preferences = field(default_factory=Preferences)

    _document_text_override: str = ""

    # ---------------------------------------------------------------- helpers
    @property
    def document_text(self) -> str:
        if self.document is not None:
            return self.document.text
        return self._document_text_override

    @document_text.setter
    def document_text(self, value: str) -> None:
        text = value or ""
        self._document_text_override = text
        if self.document is None:
            self.document = StudyDocument(name=self.document_name or "Pasted text", text=text, file_type="text")
        else:
            self.document.text = text

    @property
    def has_document(self) -> bool:
        return self.document is not None

    @property
    def quiz_item(self) -> QuizItem | None:
        if not self.quiz:
            return None
        return self.quiz[min(self.quiz_index, len(self.quiz) - 1)]

    @property
    def visible_cards(self) -> list[Flashcard]:
        if self.hard_only:
            return [card for card in self.cards if card.difficult]
        return self.cards

    @property
    def current_card(self) -> Flashcard | None:
        deck = self.visible_cards
        if not deck:
            return None
        return deck[min(self.card_index, len(deck) - 1)]

    @property
    def quiz_score(self) -> int:
        return sum(1 for item in self.quiz if item.is_right)

    def clear_study_material(self) -> None:
        """Generated material belongs to one document - drop it when it changes."""
        self.notes, self.notes_phase, self.notes_error = "", "empty", ""
        self.quiz, self.quiz_phase, self.quiz_error = [], "empty", ""
        self.quiz_index, self.quiz_done = 0, False
        self.cards, self.cards_phase, self.cards_error = [], "empty", ""
        self.card_index, self.hard_only = 0, False

    def reset_quiz_answers(self) -> None:
        for item in self.quiz:
            item.chosen, item.checked = None, False
        self.quiz_index, self.quiz_done = 0, False

    def start_fresh(self) -> None:
        self.view = "start"
        self.mode = "overview"
        self.document = None
        self.document_phase, self.document_error = "empty", ""
        self.chatbot = None
        self.exchanges = []
        self.asking = False
        self.voice = VoiceState()
        self.clear_study_material()

    def clear_authentication(self) -> None:
        """Clear account and profile state without deleting local study data."""
        self.authenticated = False
        self.auth_user_id = None
        self.username = ""
        self.auth_expires_at = 0.0
        self.accessibility_profile = {}
        self.accessibility_settings_open = False
        self.voice_mode = False
        self.stt_phrase_seconds = 12


app_state = StudySession()
