# parto/actions/builtins/brush.py
"""
Parto Architecture 2.0 — Built-in Brush Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_brush_actions() -> List[Action]:
    return [
        Action(
            id="brush.activate",
            name="Brush Tool",
            description="Activate brush painting tool",
            category=ActionCategory.BRUSH,
            default_shortcut="B",
            icon_name="tool_brush",
            checkable=True,
            handler=lambda ctx: ctx.window.action_tool_brush() if ctx.window else None,
        ),
        Action(
            id="brush.toggle_studio",
            name="Brush Studio",
            description="Toggle Brush Studio panel",
            category=ActionCategory.BRUSH,
            default_shortcut="F9",
            icon_name="brush",
            checkable=True,
            handler=lambda ctx: ctx.window.toggle_brush_dock() if ctx.window else None,
        ),
        Action(
            id="brush.focus_presets",
            name="Focus Presets",
            description="Focus preset browser in Brush Studio",
            category=ActionCategory.BRUSH,
            default_shortcut="Ctrl+Shift+B",
            handler=lambda ctx: ctx.window.action_focus_brush_presets() if ctx.window else None,
        ),
        Action(
            id="brush.focus_properties",
            name="Brush Tip Properties",
            description="Focus brush property sliders",
            category=ActionCategory.BRUSH,
            default_shortcut="Alt+B",
            handler=lambda ctx: ctx.window.action_focus_brush_properties() if ctx.window else None,
        ),
        Action(
            id="brush.reset_settings",
            name="Reset Brush Settings",
            description="Reset active brush parameters to defaults",
            category=ActionCategory.BRUSH,
            default_shortcut="Shift+F9",
            handler=lambda ctx: ctx.window.action_reset_brush() if ctx.window else None,
        ),
        Action(
            id="brush.cycle_mode",
            name="Toggle Paint / Eraser Mode",
            description="Switch between drawing and erasing modes",
            category=ActionCategory.BRUSH,
            default_shortcut="Shift+B",
            handler=lambda ctx: ctx.window.action_cycle_brush_mode() if ctx.window else None,
        ),
        Action(
            id="brush.size_up",
            name="Increase Brush Size",
            description="Increase brush diameter by 5px",
            category=ActionCategory.BRUSH,
            default_shortcut="]",
            contexts=["GLOBAL", "CANVAS", "BRUSH"],
            handler=lambda ctx: ctx.window.tool_brush.increase_size(5) if ctx.window and hasattr(ctx.window, "tool_brush") else None,
        ),
        Action(
            id="brush.size_down",
            name="Decrease Brush Size",
            description="Decrease brush diameter by 5px",
            category=ActionCategory.BRUSH,
            default_shortcut="[",
            contexts=["GLOBAL", "CANVAS", "BRUSH"],
            handler=lambda ctx: ctx.window.tool_brush.decrease_size(5) if ctx.window and hasattr(ctx.window, "tool_brush") else None,
        ),
        Action(
            id="brush.swap_colors",
            name="Swap Colors",
            description="Swap foreground and background colors",
            category=ActionCategory.BRUSH,
            default_shortcut="X",
            contexts=["GLOBAL", "CANVAS", "BRUSH"],
            handler=lambda ctx: ctx.window.tool_brush.swap_colors() if ctx.window and hasattr(ctx.window, "tool_brush") else None,
        ),
        Action(
            id="brush.reset_colors",
            name="Default Colors",
            description="Reset colors to Black foreground and White background",
            category=ActionCategory.BRUSH,
            default_shortcut="D",
            contexts=["GLOBAL", "CANVAS", "BRUSH"],
            handler=lambda ctx: ctx.window.tool_brush.reset_default_colors() if ctx.window and hasattr(ctx.window, "tool_brush") else None,
        ),
    ]
