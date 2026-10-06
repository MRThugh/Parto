# parto/actions/builtins/document.py
"""
Parto Architecture 2.0 — Built-in Document Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_document_actions() -> List[Action]:
    return [
        Action(
            id="document.new",
            name="New Canvas...",
            description="Create new empty image canvas",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+N",
            icon_name="new",
            handler=lambda ctx: ctx.window.action_new_canvas() if ctx.window else None,
        ),
        Action(
            id="document.open",
            name="Open Image...",
            description="Open existing image file",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+O",
            icon_name="open",
            handler=lambda ctx: ctx.window.action_open_image() if ctx.window else None,
        ),
        Action(
            id="document.save",
            name="Save",
            description="Save image changes to disk",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+S",
            icon_name="save",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_save_image() if ctx.window else None,
        ),
        Action(
            id="document.save_as",
            name="Save As...",
            description="Save image to a new file",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+Shift+S",
            icon_name="save-as",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_save_as() if ctx.window else None,
        ),
        Action(
            id="document.export",
            name="Export As...",
            description="Export image to WebP, JPEG, PNG, TIFF",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+Shift+E",
            icon_name="export",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_export_image() if ctx.window else None,
        ),
        Action(
            id="document.properties",
            name="Properties & Metadata...",
            description="View image technical specifications",
            category=ActionCategory.FILE,
            default_shortcut="Ctrl+I",
            icon_name="info",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_show_info() if ctx.window else None,
        ),
    ]
