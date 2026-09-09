"""Loading, error and empty states.

Every state says in words what is happening; the animation is decoration only,
so switching motion off never hides information.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from .elements import action


def working(message: str) -> ui.element:
    """An honest, single-stage loading state - no invented progress bars."""
    block = ui.element("div").classes("sk-working")
    block.props('role="status" aria-live="polite"')
    with block:
        dots = ui.element("div").classes("sk-dots")
        dots.props('aria-hidden="true"')
        with dots:
            for _ in range(3):
                ui.element("span")
        ui.label(message)
    return block


def problem(
    message: str,
    detail: str = "",
    retry: Callable[..., Any] | None = None,
    retry_label: str = "Try again",
) -> ui.element:
    """A friendly failure. Technical detail is collapsed, never a traceback."""
    block = ui.element("div").classes("sk-problem")
    block.props('role="alert"')
    with block:
        with ui.element("div").classes("sk-problem-title"):
            ui.label("!").props('aria-hidden="true"')
            ui.label("Something went wrong")
        ui.label(message).classes("sk-text")
        if retry is not None:
            with ui.element("div").classes("sk-flash-nav"):
                action(retry_label, retry, kind="primary", small=True)
        if detail:
            with ui.expansion("Technical detail").classes("w-full").props("dense"):
                ui.label(detail).classes("sk-meta").style("word-break:break-word")
    return block


def empty(
    title: str,
    message: str,
    button_label: str = "",
    on_click: Callable[..., Any] | None = None,
    glyph: str = "",
) -> ui.element:
    """What to do next when there is nothing to show yet."""
    block = ui.element("div").classes("sk-empty")
    with block:
        ui.label(title).classes("sk-heading")
        ui.label(message).classes("sk-text")
        if button_label and on_click is not None:
            action(button_label, on_click, kind="primary", glyph=glyph)
    return block


def toast(message: str, *, kind: str = "positive") -> None:
    """A short confirmation. Never used to report anything important on its own."""
    ui.notify(message, type=kind, position="bottom", timeout=2600)
