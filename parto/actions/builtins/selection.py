# parto/actions/builtins/selection.py
"""
Parto Architecture 2.0 — Built-in Selection Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_selection_actions() -> List[Action]:
    return [
        Action(
            id="selection.select_all",
            name="Select All",
            description="Select entire canvas boundary",
            category=ActionCategory.SELECTION,
            default_shortcut="Ctrl+A",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.select_all() if ctx.canvas and hasattr(ctx.canvas, "select_all") else None,
        ),
        Action(
            id="selection.deselect",
            name="Deselect",
            description="Deselect active selection area",
            category=ActionCategory.SELECTION,
            default_shortcut="Ctrl+D",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.deselect() if ctx.canvas and hasattr(ctx.canvas, "deselect") else None,
        ),
        Action(
            id="selection.invert",
            name="Invert Selection",
            description="Invert current selection bounds",
            category=ActionCategory.SELECTION,
            default_shortcut="Ctrl+Shift+I",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.invert_selection() if ctx.canvas and hasattr(ctx.canvas, "invert_selection") else None,
        ),
    ]
