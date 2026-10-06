# parto/actions/builtins/transform.py
"""
Parto Architecture 2.0 — Built-in Transform Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_transform_actions() -> List[Action]:
    return [
        Action(
            id="transform.rotate_cw",
            name="Rotate 90° Clockwise",
            description="Rotate image 90 degrees right",
            category=ActionCategory.TRANSFORM,
            default_shortcut="Ctrl+R",
            icon_name="rot_right",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.rotate_document(clockwise=True) if ctx.document else None,
        ),
        Action(
            id="transform.rotate_ccw",
            name="Rotate 90° Counter-Clockwise",
            description="Rotate image 90 degrees left",
            category=ActionCategory.TRANSFORM,
            default_shortcut="Ctrl+Shift+R",
            icon_name="rot_left",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.rotate_document(clockwise=False) if ctx.document else None,
        ),
        Action(
            id="transform.rotate_180",
            name="Rotate 180°",
            description="Rotate image 180 degrees",
            category=ActionCategory.TRANSFORM,
            default_shortcut="Ctrl+Alt+R",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.rotate_180_document() if ctx.document else None,
        ),
        Action(
            id="transform.flip_h",
            name="Flip Horizontal",
            description="Flip image along horizontal axis",
            category=ActionCategory.TRANSFORM,
            icon_name="flip_h",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.flip_horizontal_document() if ctx.document else None,
        ),
        Action(
            id="transform.flip_v",
            name="Flip Vertical",
            description="Flip image along vertical axis",
            category=ActionCategory.TRANSFORM,
            icon_name="flip_v",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.flip_vertical_document() if ctx.document else None,
        ),
        Action(
            id="transform.resize",
            name="Resize Image...",
            description="Resize image dimensions and resolution",
            category=ActionCategory.TRANSFORM,
            default_shortcut="Ctrl+Alt+I",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_resize_image() if ctx.window else None,
        ),
        Action(
            id="transform.crop",
            name="Crop Canvas...",
            description="Interactively crop image canvas boundary",
            category=ActionCategory.TRANSFORM,
            default_shortcut="Shift+C",
            icon_name="tool_crop",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_tool_crop() if ctx.window else None,
        ),
    ]
