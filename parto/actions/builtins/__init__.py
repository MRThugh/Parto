# parto/actions/builtins/__init__.py
"""
Parto Architecture 2.0 — Built-in Action Catalog & Registration
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List
from ..action import Action
from ..registry import ActionRegistry, get_action_registry

from .application import create_application_actions
from .document import create_document_actions
from .history import create_history_actions
from .canvas import create_canvas_actions
from .brush import create_brush_actions
from .layers import create_layer_actions
from .selection import create_selection_actions
from .transform import create_transform_actions
from .view import create_view_actions
from .filters import create_filter_actions


def get_all_builtin_actions() -> List[Action]:
    """Assemble all default system actions."""
    actions: List[Action] = []
    actions.extend(create_application_actions())
    actions.extend(create_document_actions())
    actions.extend(create_history_actions())
    actions.extend(create_canvas_actions())
    actions.extend(create_brush_actions())
    actions.extend(create_layer_actions())
    actions.extend(create_selection_actions())
    actions.extend(create_transform_actions())
    actions.extend(create_view_actions())
    actions.extend(create_filter_actions())
    return actions


def register_all_builtins(registry: ActionRegistry) -> None:
    """Populate ActionRegistry with all default actions and compatibility aliases."""
    for action in get_all_builtin_actions():
        registry.register(action)

    # Backward-compatibility aliases for legacy shortcut/action IDs
    aliases = {
        "file_new": "document.new",
        "file_open": "document.open",
        "file_save": "document.save",
        "file_save_as": "document.save_as",
        "file_export": "document.export",
        "file_info": "document.properties",
        "file_exit": "app.exit",
        "edit_undo": "history.undo",
        "edit_redo": "history.redo",
        "edit_crop": "transform.crop",
        "edit_resize": "transform.resize",
        "view_zoom_in": "canvas.zoom_in",
        "view_zoom_out": "canvas.zoom_out",
        "view_zoom_fit": "canvas.zoom_fit",
        "view_zoom_100": "canvas.zoom_actual",
        "view_fullscreen": "app.toggle_fullscreen",
        "view_layers": "view.toggle_layers",
        "view_adjustments": "view.toggle_adjustments",
        "view_brush": "brush.toggle_studio",
        "brush_studio": "brush.toggle_studio",
        "img_rot_cw": "transform.rotate_cw",
        "img_rot_ccw": "transform.rotate_ccw",
        "img_rot_180": "transform.rotate_180",
        "img_flip_h": "transform.flip_h",
        "img_flip_v": "transform.flip_v",
        "tool_move": "tool.move",
        "tool_crop": "tool.crop",
        "tool_brush": "tool.brush",
        "tool_eyedropper": "tool.eyedropper",
        "layer_new": "layer.create",
        "layer_add": "layer.create",
        "layer_dup": "layer.duplicate",
        "layer_duplicate": "layer.duplicate",
        "layer_del": "layer.delete",
        "layer_delete": "layer.delete",
        "layer_up": "layer.move_up",
        "layer_dn": "layer.move_down",
        "layer_down": "layer.move_down",
        "layer_mrg": "layer.merge_down",
        "layer_merge": "layer.merge_down",
        "layer_visibility": "layer.toggle_visibility",
        "layer_toggle_visibility": "layer.toggle_visibility",
    }
    for alias, canonical in aliases.items():
        registry.register_alias(alias, canonical)
