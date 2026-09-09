"""Design system loading and the accessibility preferences that change it."""

from __future__ import annotations

from pathlib import Path

from nicegui import ui

from ..state.session_state import Preferences

STYLES = Path(__file__).resolve().parents[1] / "styles"

THEMES = {"paper": "Paper", "night": "Night", "contrast": "High contrast"}
TEXT_SIZES = {"standard": "Standard", "large": "Large", "larger": "Larger"}


def install_styles() -> None:
    """Load the three stylesheets that make up the SakshamAI design system."""
    for sheet in ("theme.css", "components.css", "accessibility.css"):
        ui.add_css(STYLES / sheet, shared=True)


class Appearance:
    """Applies the student's reading preferences to the live page."""

    def __init__(self, preferences: Preferences) -> None:
        self.preferences = preferences
        self.dark = ui.dark_mode(False)

    def apply(self) -> None:
        theme = self.preferences.theme
        ui.query("body").classes(
            add=f"theme-{theme}",
            remove=" ".join(f"theme-{name}" for name in THEMES if name != theme),
        )
        self.dark.value = theme == "night"

        size = self.preferences.text_size
        ui.query("html").classes(
            add="" if size == "standard" else f"size-{size}",
            remove=" ".join(f"size-{name}" for name in TEXT_SIZES if name != size),
        )

        if self.preferences.reduce_motion:
            ui.query("body").classes(add="no-motion")
        else:
            ui.query("body").classes(remove="no-motion")
