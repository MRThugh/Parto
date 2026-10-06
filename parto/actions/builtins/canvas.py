# parto/actions/builtins/canvas.py
"""
Parto Architecture 2.0 — Built-in Canvas & Navigation Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_canvas_actions() -> List[Action]:
    return [
        Action(
            id="canvas.zoom_in",
            name="Zoom In",
            description="Increase canvas zoom",
            category=ActionCategory.VIEW,
            default_shortcut="Ctrl+=",
            icon_name="zoom_in",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.zoom_in() if ctx.canvas else None,
        ),
        Action(
            id="canvas.zoom_out",
            name="Zoom Out",
            description="Decrease canvas zoom",
            category=ActionCategory.VIEW,
            default_shortcut="Ctrl+-",
            icon_name="zoom_out",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.zoom_out() if ctx.canvas else None,
        ),
        Action(
            id="canvas.zoom_fit",
            name="Fit on Screen",
            description="Fit entire image inside view",
            category=ActionCategory.VIEW,
            default_shortcut="Ctrl+0",
            icon_name="zoom_fit",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.zoom_fit() if ctx.canvas else None,
        ),
        Action(
            id="canvas.zoom_actual",
            name="Actual Pixels (100%)",
            description="View image at 1:1 scale",
            category=ActionCategory.VIEW,
            default_shortcut="Ctrl+1",
            icon_name="zoom_actual",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.canvas.zoom_actual() if ctx.canvas else None,
        ),
        # Interactive Tools
        Action(
            id="tool.move",
            name="Move Tool",
            description="Select Move & Pan tool",
            category=ActionCategory.APPLICATION,
            default_shortcut="V",
            icon_name="tool_move",
            checkable=True,
            handler=lambda ctx: ctx.window.action_tool_move() if ctx.window else None,
        ),
        Action(
            id="tool.crop",
            name="Crop Tool",
            description="Select Canvas Crop tool",
            category=ActionCategory.APPLICATION,
            default_shortcut="C",
            icon_name="tool_crop",
            checkable=True,
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_tool_crop() if ctx.window else None,
        ),
        Action(
            id="tool.brush",
            name="Brush Tool",
            description="Select Brush Painting tool",
            category=ActionCategory.BRUSH,
            default_shortcut="B",
            icon_name="tool_brush",
            checkable=True,
            handler=lambda ctx: ctx.window.action_tool_brush() if ctx.window else None,
        ),
        Action(
            id="tool.eyedropper",
            name="Eyedropper Tool",
            description="Sample color from canvas pixel",
            category=ActionCategory.APPLICATION,
            default_shortcut="I",
            icon_name="tool_eyedropper",
            checkable=True,
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.window.action_tool_eyedropper() if ctx.window else None,
        ),
    ]
