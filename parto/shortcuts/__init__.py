# parto/shortcuts/__init__.py
"""Parto shortcut registration and management."""

from .manager import ShortcutManager, ShortcutDefinition, get_shortcut_manager

__all__ = [
    "ShortcutManager",
    "ShortcutDefinition",
    "get_shortcut_manager",
]
