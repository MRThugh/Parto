# parto/actions/builtins/layers.py
"""
Parto Architecture 2.0 — Built-in Layer Actions
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action, ActionCategory, ActionContext


def create_layer_actions() -> List[Action]:
    return [
        Action(
            id="layer.create",
            name="New Layer",
            description="Add a new blank layer above active layer",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+Shift+N",
            icon_name="layer-add",
            is_enabled_fn=lambda ctx: ctx.has_document,
            handler=lambda ctx: ctx.document.add_layer() if ctx.document else None,
        ),
        Action(
            id="layer.delete",
            name="Delete Layer",
            description="Remove active layer from stack",
            category=ActionCategory.LAYER,
            default_shortcut="Delete",
            icon_name="layer-delete",
            is_enabled_fn=lambda ctx: ctx.has_document and len(ctx.document.layers) > 1,
            handler=lambda ctx: ctx.document.remove_active_layer() if ctx.document else None,
        ),
        Action(
            id="layer.duplicate",
            name="Duplicate Layer",
            description="Duplicate active layer",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+J",
            icon_name="layer-duplicate",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.active_layer is not None,
            handler=lambda ctx: ctx.document.duplicate_active_layer() if ctx.document else None,
        ),
        Action(
            id="layer.move_up",
            name="Move Layer Up",
            description="Move active layer up in stack order",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+]",
            icon_name="layer-up",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.document.active_layer_index < len(ctx.document.layers) - 1,
            handler=lambda ctx: ctx.document.move_layer_up() if ctx.document else None,
        ),
        Action(
            id="layer.move_down",
            name="Move Layer Down",
            description="Move active layer down in stack order",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+[",
            icon_name="layer-down",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.document.active_layer_index > 0,
            handler=lambda ctx: ctx.document.move_layer_down() if ctx.document else None,
        ),
        Action(
            id="layer.merge_down",
            name="Merge Down",
            description="Merge active layer with layer below",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+E",
            icon_name="layer-merge",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.document.active_layer_index > 0 and len(ctx.document.layers) > 1,
            handler=lambda ctx: ctx.document.merge_down() if ctx.document else None,
        ),
        Action(
            id="layer.toggle_visibility",
            name="Toggle Layer Visibility",
            description="Show or hide the currently active layer",
            category=ActionCategory.LAYER,
            default_shortcut="Ctrl+,",
            icon_name="eye",
            is_enabled_fn=lambda ctx: ctx.has_document and ctx.active_layer is not None,
            handler=lambda ctx: ctx.document.set_layer_visible(
                ctx.document.active_layer_index, not ctx.active_layer.visible
            ) if ctx.document and ctx.active_layer else None,
        ),
    ]
