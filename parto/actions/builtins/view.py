# parto/actions/builtins/view.py
"""
Parto Architecture 2.0 — Built-in View & Dock Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_view_actions() -> List[Action]:
    return [
        Action(
            id="view.toggle_layers",
            name="Layers Panel",
            description="Toggle Layers Panel visibility",
            category=ActionCategory.VIEW,
            default_shortcut="F7",
            icon_name="layers",
            checkable=True,
            handler=lambda ctx: ctx.window.toggle_layers_dock() if ctx.window else None,
        ),
        Action(
            id="view.toggle_adjustments",
            name="Adjustments Panel",
            description="Toggle Live Adjustments Panel visibility",
            category=ActionCategory.VIEW,
            default_shortcut="F8",
            icon_name="adjust",
            checkable=True,
            handler=lambda ctx: ctx.window.toggle_adjustments_dock() if ctx.window else None,
        ),
        Action(
            id="view.toggle_brush",
            name="Brush Studio",
            description="Toggle Brush Studio Panel visibility",
            category=ActionCategory.VIEW,
            default_shortcut="F9",
            icon_name="brush",
            checkable=True,
            handler=lambda ctx: ctx.window.toggle_brush_dock() if ctx.window else None,
        ),
    ]
