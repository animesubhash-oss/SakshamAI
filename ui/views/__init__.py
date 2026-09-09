"""Views package for the SakshamAI NiceGUI frontend.

This module centralizes view registration so pages can be discovered and loaded
without each caller having to know the exact module path.

Example:
    from ui.views import get_view_module, list_views
    print(list_views())
    home_view = get_view_module("home")
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["VIEW_MODULES", "list_views", "get_view_module"]

VIEW_MODULES: dict[str, str] = {
    "home": "ui.views.home",
    "documents": "ui.views.documents",
    "chat": "ui.views.chat",
    "notes": "ui.views.notes",
    "quiz": "ui.views.quiz",
    "flashcards": "ui.views.flashcards",
}


def list_views() -> tuple[str, ...]:
    """Return the registered view names."""
    return tuple(VIEW_MODULES.keys())


def get_view_module(view_name: str) -> Any:
    """Import and return a view module by its registered name.

    Args:
        view_name: One of the keys in VIEW_MODULES.

    Raises:
        KeyError: If the requested view name is not registered.
        ImportError: If the view module file does not exist or cannot be imported.
    """
    normalized = view_name.strip().lower()
    module_path = VIEW_MODULES.get(normalized)
    if module_path is None:
        available = ", ".join(sorted(VIEW_MODULES))
        raise KeyError(f"Unknown view '{view_name}'. Available views: {available}")

    try:
        return import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ImportError(
            f"View module '{module_path}' was not found. "
            "Create the corresponding file under ui/views/ or update VIEW_MODULES."
        ) from exc
