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
    (e.g., transformations, filters, crops, adjustments).
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


class LayerAddCommand(Command):
    """Command for adding a layer."""

    def __init__(self, document: Any, layer: Any, index: int = -1):
        super().__init__(f"Add {layer.name}")
        self.document = document
        self.layer = layer
        self.index = index

    def undo(self) -> None:
        self.document.remove_layer_by_id(self.layer.id, push_history=False)

    def redo(self) -> None:
        self.document.add_layer(self.layer, self.index, push_history=False)


class LayerDeleteCommand(Command):
    """Command for deleting a layer."""

    def __init__(self, document: Any, layer: Any, index: int):
        super().__init__(f"Delete {layer.name}")
        self.document = document
        self.layer = layer
        self.index = index

    def undo(self) -> None:
        self.document.insert_layer(self.index, self.layer, push_history=False)

    def redo(self) -> None:
        self.document.remove_layer_by_id(self.layer.id, push_history=False)


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
        self.document.invalidate_composite()

    def redo(self) -> None:
        setattr(self.layer, self.prop_name, self.new_val)
        self.document.invalidate_composite()


class LayerReorderCommand(Command):
    """Command for changing layer order in the stack."""

    def __init__(self, document: Any, old_order: List[str], new_order: List[str]):
        super().__init__("Reorder Layers")
        self.document = document
        self.old_order = old_order
        self.new_order = new_order

    def undo(self) -> None:
        self.document.reorder_layers_by_ids(self.old_order, push_history=False)

    def redo(self) -> None:
        self.document.reorder_layers_by_ids(self.new_order, push_history=False)


# Domain-specific commands for layers and operations
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
            self.target.insert_layer(self.index, self.layer, push_history=False)
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

    def redo(self) -> None:
        if hasattr(self.target, "add_layer"):
            self.target.add_layer(self.duplicated_layer, push_history=False)


class MoveLayerCommand(Command):
    def __init__(self, target: Any, from_idx: int, to_idx: int):
        super().__init__("Move Layer")
        self.target = target
        self.from_idx = from_idx
        self.to_idx = to_idx

    def undo(self) -> None:
        if hasattr(self.target, "move_layer_up") and self.from_idx < self.to_idx:
            self.target.move_layer_up(self.to_idx)
        elif hasattr(self.target, "move_layer_down"):
            self.target.move_layer_down(self.to_idx)

    def redo(self) -> None:
        if hasattr(self.target, "move_layer_down") and self.from_idx < self.to_idx:
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
        if hasattr(self.target, "_layers"):
            if self.merged_layer in self.target._layers:
                idx = self.target._layers.index(self.merged_layer)
                self.target._layers[idx:idx + 1] = [lay.clone() for lay in self.replaced_layers]
            elif 0 <= self.index < len(self.target._layers):
                self.target._layers[self.index:self.index + 1] = [lay.clone() for lay in self.replaced_layers]
        if hasattr(self.target, "invalidate_composite"):
            self.target.invalidate_composite()
        if hasattr(self.target, "layer_selection_changed") and hasattr(self.target, "_active_layer_index"):
            self.target.layer_selection_changed.emit(self.target._active_layer_index)

    def redo(self) -> None:
        if hasattr(self.target, "_layers"):
            for lay in self.replaced_layers:
                if lay in self.target._layers:
                    self.target._layers.remove(lay)
            insert_idx = min(self.index, len(self.target._layers))
            self.target._layers.insert(insert_idx, self.merged_layer)
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
        self.before_img = self.layer.image.copy() if self.layer else None
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
        self.before_img = self.layer.image.copy() if self.layer else None
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

