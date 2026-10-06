# parto/actions/builtins/application.py
"""
Parto Architecture 2.0 — Built-in Application Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_application_actions() -> List[Action]:
    return [
        Action(
            id="app.command_palette",
            name="Command Palette...",
            description="Open searchable command palette",
            category=ActionCategory.APPLICATION,
            default_shortcut="Ctrl+Shift+P",
            icon_name="search",
            handler=lambda ctx: ctx.window.action_show_command_palette() if ctx.window else None,
        ),
        Action(
            id="app.shortcuts",
            name="Keyboard Shortcuts...",
            description="Show keyboard shortcut cheat sheet",
            category=ActionCategory.HELP,
            default_shortcut="Ctrl+/",
            icon_name="help",
            handler=lambda ctx: ctx.window.action_show_shortcuts() if ctx.window else None,
        ),
        Action(
            id="app.about",
            name="About Parto",
            description="About Parto image editor",
            category=ActionCategory.HELP,
            default_shortcut="F1",
            icon_name="info",
            handler=lambda ctx: ctx.window.action_show_about() if ctx.window else None,
        ),
        Action(
            id="app.exit",
            name="Exit",
            description="Exit Parto application",
            category=ActionCategory.APPLICATION,
            default_shortcut="Ctrl+Q",
            icon_name="power",
            handler=lambda ctx: ctx.window.close() if ctx.window else None,
        ),
        Action(
            id="app.toggle_fullscreen",
            name="Toggle Fullscreen",
            description="Toggle fullscreen viewing mode",
            category=ActionCategory.VIEW,
            default_shortcut="F11",
            handler=lambda ctx: ctx.window.action_toggle_fullscreen() if ctx.window else None,
        ),
    ]
