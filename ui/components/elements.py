"""Small building blocks shared by every SakshamAI view.

They are plain semantic elements (``<button>``, ``<span>``) carrying the classes
from ``ui/styles``, so keyboard behaviour, focus and screen-reader labelling come
from the platform instead of being re-invented.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui


def _props(element: ui.element, attributes: dict[str, str]) -> None:
    for key, value in attributes.items():
        if value:
            element.props(f'{key}="{value}"')


def action(
    label: str,
    on_click: Callable[..., Any] | None = None,
    *,
    glyph: str = "",
    kind: str = "default",  # default | primary | quiet
    small: bool = False,
    disabled: bool = False,
    describe: str = "",
    classes: str = "",
) -> ui.element:
    """A labelled button. Text is always visible, so no icon needs decoding."""
    css = ["sk-btn"]
    if kind != "default":
        css.append(f"is-{kind}")
    if small:
        css.append("is-small")
    if classes:
        css.append(classes)

    button = ui.element("button").classes(" ".join(css))
    _props(button, {"type": "button", "aria-label": describe})
    if disabled:
        button.props("disabled")
    with button:
        if glyph:
            ui.label(glyph).classes("sk-tab-glyph").props('aria-hidden="true"')
        ui.label(label)
    if on_click is not None and not disabled:
        button.on("click", on_click)
    return button


def icon_action(
    glyph: str,
    describe: str,
    on_click: Callable[..., Any] | None = None,
    *,
    kind: str = "quiet",
) -> ui.element:
    """An icon-only control. ``describe`` becomes both label and tooltip."""
    css = f"sk-btn is-round is-{kind}" if kind != "default" else "sk-btn is-round"
    button = ui.element("button").classes(css)
    _props(button, {"type": "button", "aria-label": describe})
    with button:
        ui.label(glyph).props('aria-hidden="true"')
        ui.tooltip(describe)
    if on_click is not None:
        button.on("click", on_click)
    return button


def pill(text: str, *, glyph: str = "", tone: str = "") -> ui.element:
    """A status pill. The glyph and the word carry the meaning, not the colour."""
    element = ui.element("span").classes(f"sk-pill {tone}".strip())
    with element:
        if glyph:
            ui.label(glyph).props('aria-hidden="true"')
        ui.label(text)
    return element


def eyebrow(text: str) -> ui.label:
    return ui.label(text).classes("sk-eyebrow")


def sr_only(text: str) -> ui.label:
    return ui.label(text).classes("sk-sr")


def live_region(text: str = "") -> ui.label:
    """A polite live region so state changes are announced, not just shown."""
    label = ui.label(text).classes("sk-sr")
    label.props('role="status" aria-live="polite"')
    return label
