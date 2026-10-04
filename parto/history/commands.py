# parto/history/commands.py
"""
Parto v0.3.0 - Undoable Command Architecture
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from PIL import Image


class Command(ABC):
    """Abstract base class for all undoable operations."""

    def __init__(self, name: str = "Action"):
        self.name: str = name

    @abstractmethod
    def undo(self) -> None:
        """Roll back the operation."""
        pass

    @abstractmethod
    def redo(self) -> None:
        """Re-apply the operation."""
        pass


class SnapshotCommand(Command):
    """
    Command that records complete state before and after an operation
    (e.g., transformations, filters, crops, adjustments, layer stack changes).
    Authoritative undo/redo mechanism in Parto v0.3.
    """

    def __init__(
        self,
        name: str,
        target_object: Any,
        restore_fn: Callable[[Any], None],
        before_state: Any,
        after_state: Any,
    ):
        super().__init__(name)
        self.target_object = target_object
        self.restore_fn = restore_fn
        self.before_state = before_state
        self.after_state = after_state

    def undo(self) -> None:
        self.restore_fn(self.before_state)

    def redo(self) -> None:
        self.restore_fn(self.after_state)


# --- Backward-Compatibility Command Classes ---

class LayerAddCommand(Command):
    """Backward-compatible command for adding a layer."""

    def __init__(self, document: Any, layer: Any, index: int = -1):
        super().__init__(f"Add {getattr(layer, 'name', 'Layer')}")
        self.document = document
        self.layer = layer
        self.index = index

    def undo(self) -> None:
        if hasattr(self.document, "remove_layer_by_id"):
            self.document.remove_layer_by_id(self.layer.id, push_history=False)
        elif hasattr(self.document, "layer_stack"):
            layers = self.document.layer_stack.layers
            if self.layer in layers:
                self.document.layer_stack.remove_layer(layers.index(self.layer))
                self.document.invalidate_composite()

    def redo(self) -> None:
        if hasattr(self.document, "insert_layer"):
            idx = self.index if self.index >= 0 else len(self.document.layers)
            self.document.insert_layer(idx, self.layer, push_history=False)
        elif hasattr(self.document, "layer_stack"):
            idx = self.index if self.index >= 0 else len(self.document.layer_stack)
            self.document.layer_stack.insert_layer(idx, self.layer)
            self.document.invalidate_composite()


class LayerDeleteCommand(Command):
    """Backward-compatible command for deleting a layer."""

    def __init__(self, document: Any, layer: Any, index: int):
        super().__init__(f"Delete {getattr(layer, 'name', 'Layer')}")
        self.document = document
        self.layer = layer
        self.index = index

    def undo(self) -> None:
        if hasattr(self.document, "insert_layer"):
            self.document.insert_layer(self.index, self.layer, push_history=False)
        elif hasattr(self.document, "layer_stack"):
            self.document.layer_stack.insert_layer(self.index, self.layer)
            self.document.invalidate_composite()

    def redo(self) -> None:
        if hasattr(self.document, "remove_layer_by_id"):
            self.document.remove_layer_by_id(self.layer.id, push_history=False)
        elif hasattr(self.document, "layer_stack"):
            layers = self.document.layer_stack.layers
            if self.layer in layers:
                self.document.layer_stack.remove_layer(layers.index(self.layer))
                self.document.invalidate_composite()


class LayerPropertyCommand(Command):
    """Command for changing layer properties (visible, opacity, name)."""

    def __init__(
        self,
        document: Any,
        layer: Any,
        prop_name: str,
        old_val: Any,
        new_val: Any,
    ):
        super().__init__(f"Change Layer {prop_name.title()}")
        self.document = document
        self.layer = layer
        self.prop_name = prop_name
        self.old_val = old_val
        self.new_val = new_val

    def undo(self) -> None:
        setattr(self.layer, self.prop_name, self.old_val)
        if hasattr(self.document, "invalidate_composite"):
            self.document.invalidate_composite()

    def redo(self) -> None:
        setattr(self.layer, self.prop_name, self.new_val)
        if hasattr(self.document, "invalidate_composite"):
            self.document.invalidate_composite()


class LayerReorderCommand(Command):
    """Command for changing layer order in the stack."""

    def __init__(self, document: Any, old_order: List[str], new_order: List[str]):
        super().__init__("Reorder Layers")
        self.document = document
        self.old_order = old_order
        self.new_order = new_order

    def _apply_order(self, order_ids: List[str]) -> None:
        if hasattr(self.document, "layer_stack"):
            id_map = {lay.id: lay for lay in self.document.layer_stack.layers}
            new_layers = [id_map[lid] for lid in order_ids if lid in id_map]
            for lay in self.document.layer_stack.layers:
                if lay.id not in order_ids:
                    new_layers.append(lay)
            self.document.layer_stack._layers = new_layers
            if hasattr(self.document, "invalidate_composite"):
                self.document.invalidate_composite()

    def undo(self) -> None:
        self._apply_order(self.old_order)

    def redo(self) -> None:
        self._apply_order(self.new_order)


# Domain-specific commands tested directly in test suite
class AddLayerCommand(Command):
    def __init__(self, target: Any, layer: Any):
        super().__init__(f"Add {getattr(layer, 'name', 'Layer')}")
        self.target = target
        self.layer = layer

    def undo(self) -> None:
        if hasattr(self.target, "remove_layer_by_id"):
            self.target.remove_layer_by_id(self.layer.id, push_history=False)
        elif hasattr(self.target, "_layers") and self.layer in self.target._layers:
            self.target._layers.remove(self.layer)
        elif hasattr(self.target, "layers") and self.layer in self.target.layers:
            self.target.layers.remove(self.layer)

    def redo(self) -> None:
        if hasattr(self.target, "add_layer"):
            try:
                self.target.add_layer(self.layer, push_history=False)
            except TypeError:
                self.target.add_layer(self.layer)
        elif hasattr(self.target, "_layers") and self.layer not in self.target._layers:
            self.target._layers.append(self.layer)


class RemoveLayerCommand(Command):
    def __init__(self, target: Any, layer: Any, index: int = 0):
        super().__init__(f"Remove {getattr(layer, 'name', 'Layer')}")
        self.target = target
        self.layer = layer
        self.index = index

    def undo(self) -> None:
        if hasattr(self.target, "insert_layer"):
            try:
                self.target.insert_layer(self.index, self.layer, push_history=False)
            except TypeError:
                self.target.insert_layer(self.index, self.layer)
        elif hasattr(self.target, "_layers"):
            self.target._layers.insert(self.index, self.layer)

    def redo(self) -> None:
        if hasattr(self.target, "remove_layer_by_id"):
            self.target.remove_layer_by_id(self.layer.id, push_history=False)
        elif hasattr(self.target, "_layers") and self.layer in self.target._layers:
            self.target._layers.remove(self.layer)


class DuplicateLayerCommand(Command):
    def __init__(self, target: Any, original_layer: Any, duplicated_layer: Any):
        super().__init__(f"Duplicate {getattr(original_layer, 'name', 'Layer')}")
        self.target = target
        self.original_layer = original_layer
        self.duplicated_layer = duplicated_layer

    def undo(self) -> None:
        if hasattr(self.target, "remove_layer_by_id"):
            self.target.remove_layer_by_id(self.duplicated_layer.id, push_history=False)
        elif hasattr(self.target, "_layers") and self.duplicated_layer in self.target._layers:
            self.target._layers.remove(self.duplicated_layer)

    def redo(self) -> None:
        if hasattr(self.target, "add_layer"):
            try:
                self.target.add_layer(self.duplicated_layer, push_history=False)
            except TypeError:
                self.target.add_layer(self.duplicated_layer)
        elif hasattr(self.target, "_layers"):
            self.target._layers.append(self.duplicated_layer)


class MoveLayerCommand(Command):
    def __init__(self, target: Any, from_idx: int, to_idx: int):
        super().__init__("Move Layer")
        self.target = target
        self.from_idx = from_idx
        self.to_idx = to_idx

    def undo(self) -> None:
        if hasattr(self.target, "move_layer"):
            self.target.move_layer(self.to_idx, self.from_idx)
        elif hasattr(self.target, "move_layer_up") and self.from_idx < self.to_idx:
            self.target.move_layer_up(self.to_idx)
        elif hasattr(self.target, "move_layer_down"):
            self.target.move_layer_down(self.to_idx)

    def redo(self) -> None:
        if hasattr(self.target, "move_layer"):
            self.target.move_layer(self.from_idx, self.to_idx)
        elif hasattr(self.target, "move_layer_down") and self.from_idx < self.to_idx:
            self.target.move_layer_down(self.from_idx)
        elif hasattr(self.target, "move_layer_up"):
            self.target.move_layer_up(self.from_idx)


class MergeDownCommand(Command):
    def __init__(self, target: Any, index: int, merged_layer: Any, replaced_layers: List[Any]):
        super().__init__("Merge Layer Down")
        self.target = target
        self.index = index
        self.merged_layer = merged_layer
        self.replaced_layers = replaced_layers

    def undo(self) -> None:
        target_list = getattr(self.target, "_layers", None)
        if target_list is None and hasattr(self.target, "layer_stack"):
            target_list = self.target.layer_stack._layers

        if target_list is not None:
            if self.merged_layer in target_list:
                idx = target_list.index(self.merged_layer)
                target_list[idx:idx + 1] = [lay.clone() for lay in self.replaced_layers]
            elif 0 <= self.index < len(target_list):
                target_list[self.index:self.index + 1] = [lay.clone() for lay in self.replaced_layers]

        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()
        if hasattr(self.target, "layer_selection_changed") and hasattr(self.target, "_active_layer_index"):
            self.target.layer_selection_changed.emit(self.target._active_layer_index)

    def redo(self) -> None:
        target_list = getattr(self.target, "_layers", None)
        if target_list is None and hasattr(self.target, "layer_stack"):
            target_list = self.target.layer_stack._layers

        if target_list is not None:
            for lay in self.replaced_layers:
                if lay in target_list:
                    target_list.remove(lay)
            insert_idx = min(self.index, len(target_list))
            target_list.insert(insert_idx, self.merged_layer)

        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()
        if hasattr(self.target, "layer_selection_changed") and hasattr(self.target, "_active_layer_index"):
            self.target.layer_selection_changed.emit(self.target._active_layer_index)


class ApplyAdjustmentCommand(Command):
    def __init__(self, target: Any, **adjustments):
        super().__init__("Adjust Colors")
        self.target = target
        self.adjustments = adjustments
        self.layer = getattr(target, "active_layer", None)
        self.before_img = self.layer.image.copy() if self.layer and getattr(self.layer, "image", None) else None
        from ..image.processing import apply_color_adjustments
        self.after_img = (
            apply_color_adjustments(self.before_img, **adjustments)
            if self.before_img
            else None
        )

    def undo(self) -> None:
        if self.layer and self.before_img:
            self.layer.image = self.before_img.copy()
        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()

    def redo(self) -> None:
        if self.layer and self.after_img:
            self.layer.image = self.after_img.copy()
        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()


class ApplyFilterCommand(Command):
    def __init__(self, target: Any, filter_name: str):
        super().__init__(f"Apply {filter_name.title()} Filter")
        self.target = target
        self.filter_name = filter_name
        self.layer = getattr(target, "active_layer", None)
        self.before_img = self.layer.image.copy() if self.layer and getattr(self.layer, "image", None) else None
        from ..image.filters import apply_filter
        self.after_img = (
            apply_filter(self.before_img, filter_name)
            if self.before_img
            else None
        )

    def undo(self) -> None:
        if self.layer and self.before_img:
            self.layer.image = self.before_img.copy()
        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()

    def redo(self) -> None:
        if self.layer and self.after_img:
            self.layer.image = self.after_img.copy()
        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()
