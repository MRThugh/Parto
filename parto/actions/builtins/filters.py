# parto/actions/builtins/filters.py
"""
Parto Architecture 2.0 — Built-in Filter Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_filter_actions() -> List[Action]:
    return [
        Action(
            id="filter.gallery",
            name="Filter Gallery...",
            description="Open photographic filter gallery dialog",
            category=ActionCategory.FILTER,
            default_shortcut="Ctrl+F",
            icon_name="filters",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.active_layer is not None,
            handler=lambda ctx: ctx.window.action_show_filter_gallery() if ctx.window else None,
        ),
        Action(
            id="filter.remove_background",
            name="Remove Background",
            description="Isolate subject by automatically clearing background",
            category=ActionCategory.FILTER,
            icon_name="scissors",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.active_layer is not None,
            handler=lambda ctx: ctx.window.apply_remove_background() if ctx.window else None,
        ),
    ]
