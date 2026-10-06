# parto/actions/builtins/history.py
"""
Parto Architecture 2.0 — Built-in History Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_history_actions() -> List[Action]:
    return [
        Action(
            id="history.undo",
            name="Undo",
            description="Undo last operation",
            category=ActionCategory.EDIT,
            default_shortcut="Ctrl+Z",
            icon_name="undo",
            is_enabled_fn=lambda ctx: ctx.can_undo,
            handler=lambda ctx: ctx.window.action_undo() if ctx.window else (ctx.document.undo() if ctx.document else None),
        ),
        Action(
            id="history.redo",
            name="Redo",
            description="Redo previously undone operation",
            category=ActionCategory.EDIT,
            default_shortcut="Ctrl+Y",
            icon_name="redo",
            is_enabled_fn=lambda ctx: ctx.can_redo,
            handler=lambda ctx: ctx.window.action_redo() if ctx.window else (ctx.document.redo() if ctx.document else None),
        ),
    ]
