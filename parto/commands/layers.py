# parto/commands/layers.py
"""
Parto Architecture 2.0 — Layer Commands
Author: Ali Kamrani (MRThugh)

Reversible domain commands for layer stack manipulation:
creation, deletion, duplication, reordering, merge-down, opacity, and visibility.
Interacts with explicit Layer and LayerStack domain models without GUI coupling.
"""

from __future__ import annotations
from typing import Optional, Any, List
from .base import Command, MergeableCommand
from ..layers.models.layer import Layer
from ..layers.models.layer_stack import LayerStack


def _invalidate(doc_or_stack: Any) -> None:
    """Helper to safely invalidate compositing cache on document, controller, or stack."""
    if hasattr(doc_or_stack, "invalidate_composite"):
        doc_or_stack.invalidate_composite()
    elif hasattr(doc_or_stack, "notify_state_changed"):
        doc_or_stack.notify_state_changed()
    elif hasattr(doc_or_stack, "engine") and hasattr(doc_or_stack.engine, "compositing"):
        doc_or_stack.engine.compositing.invalidate()
    elif hasattr(doc_or_stack, "_engine") and hasattr(doc_or_stack._engine, "compositing"):
        doc_or_stack._engine.compositing.invalidate()
    if hasattr(doc_or_stack, "layer_selection_changed") and hasattr(doc_or_stack, "active_layer_index"):
        doc_or_stack.layer_selection_changed.emit(doc_or_stack.active_layer_index)


def _get_stack(target: Any) -> LayerStack:
    """Extract authoritative LayerStack from target (Document, DocumentController, DocumentState, or LayerStack)."""
    if isinstance(target, LayerStack):
        return target
    if hasattr(target, "layer_stack") and isinstance(target.layer_stack, LayerStack):
        return target.layer_stack
    if hasattr(target, "_state") and hasattr(target._state, "layer_stack") and isinstance(target._state.layer_stack, LayerStack):
        return target._state.layer_stack
    if hasattr(target, "state") and hasattr(target.state, "layer_stack") and isinstance(target.state.layer_stack, LayerStack):
        return target.state.layer_stack
    raise TypeError(f"Target {target} does not expose an authoritative LayerStack")


class CreateLayerCommand(Command):
    """Command that adds a new layer to the layer stack at a specific index."""

    def __init__(self, target: Any, layer: Layer, index: int = -1):
        super().__init__(
            name=f"Add {layer.name}",
            id="layer.create",
            description=f"Add layer {layer.name}",
        )
        self.target = target
        self.layer = layer
        self.index = index
        self._inserted_index: int = index

    def execute(self) -> None:
        stack = _get_stack(self.target)
        if self.index < 0 or self.index >= len(stack):
            self._inserted_index = len(stack)
            stack.add_layer(self.layer)
        else:
            self._inserted_index = self.index
            stack.insert_layer(self.index, self.layer)
        _invalidate(self.target)

    def redo(self) -> None:
        stack = _get_stack(self.target)
        if self.layer not in stack.layers:
            target_idx = min(self._inserted_index, len(stack))
            stack.insert_layer(target_idx, self.layer)
        _invalidate(self.target)

    def undo(self) -> None:
        stack = _get_stack(self.target)
        if self.layer in stack.layers:
            idx = stack.layers.index(self.layer)
            stack.remove_layer(idx)
        _invalidate(self.target)


class DeleteLayerCommand(Command):
    """Command that removes a layer from the layer stack, with exact index restoration."""

    def __init__(self, target: Any, layer: Layer, index: int = -1):
        super().__init__(
            name=f"Delete {layer.name}",
            id="layer.delete",
            description=f"Delete layer {layer.name}",
        )
        self.target = target
        self.layer = layer
        self.index = index

    def can_execute(self) -> bool:
        stack = _get_stack(self.target)
        return len(stack) > 1 and self.layer in stack.layers

    def execute(self) -> None:
        stack = _get_stack(self.target)
        if self.layer in stack.layers:
            idx = stack.layers.index(self.layer)
            self.index = idx
            stack.remove_layer(idx)
        _invalidate(self.target)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        stack = _get_stack(self.target)
        insert_idx = max(0, min(self.index, len(stack)))
        stack.insert_layer(insert_idx, self.layer)
        _invalidate(self.target)


class DuplicateLayerCommand(Command):
    """Command that duplicates an existing layer directly above it."""

    def __init__(self, target: Any, original_layer: Layer, duplicated_layer: Optional[Layer] = None, index: int = -1):
        super().__init__(
            name=f"Duplicate {original_layer.name}",
            id="layer.duplicate",
            description=f"Duplicate {original_layer.name}",
        )
        self.target = target
        self.original_layer = original_layer
        self.duplicated_layer = duplicated_layer if duplicated_layer is not None else original_layer.duplicate()
        self.index = index

    def execute(self) -> None:
        stack = _get_stack(self.target)
        if self.index < 0 and self.original_layer in stack.layers:
            self.index = stack.layers.index(self.original_layer)
        insert_idx = min(self.index + 1, len(stack))
        stack.insert_layer(insert_idx, self.duplicated_layer)
        _invalidate(self.target)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        stack = _get_stack(self.target)
        if self.duplicated_layer in stack.layers:
            idx = stack.layers.index(self.duplicated_layer)
            stack.remove_layer(idx)
        _invalidate(self.target)


class MoveLayerCommand(Command):
    """Command that changes layer order within the stack."""

    def __init__(self, target: Any, from_index: int, to_index: int):
        super().__init__(
            name="Move Layer",
            id="layer.move",
            description=f"Move layer from index {from_index} to {to_index}",
        )
        self.target = target
        self.from_index = from_index
        self.to_index = to_index

    def can_execute(self) -> bool:
        stack = _get_stack(self.target)
        return (
            0 <= self.from_index < len(stack)
            and 0 <= self.to_index < len(stack)
            and self.from_index != self.to_index
        )

    def execute(self) -> None:
        stack = _get_stack(self.target)
        stack.move_layer(self.from_index, self.to_index)
        _invalidate(self.target)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        stack = _get_stack(self.target)
        stack.move_layer(self.to_index, self.from_index)
        _invalidate(self.target)


class MergeDownCommand(Command):
    """
    Command that merges the active layer with the layer directly below it.
    Preserves exact layer clones for reliable undo restoration.
    """

    def __init__(
        self,
        target: Any,
        upper_index: int,
        upper_layer: Optional[Layer] = None,
        lower_layer: Optional[Layer] = None,
        merged_layer: Optional[Layer] = None,
    ):
        stack = _get_stack(target)
        if upper_layer is None and 0 < upper_index < len(stack):
            upper_layer = stack[upper_index]
        if lower_layer is None and 0 < upper_index < len(stack):
            lower_layer = stack[upper_index - 1]

        u_name = upper_layer.name if upper_layer else "Layer"
        l_name = lower_layer.name if lower_layer else "Layer"

        super().__init__(
            name=f"Merge {u_name} Down",
            id="layer.merge_down",
            description=f"Merge layer {u_name} down into {l_name}",
        )
        self.target = target
        self.upper_index = upper_index
        self.lower_index = upper_index - 1
        self.upper_layer = upper_layer.clone() if upper_layer else None
        self.lower_layer = lower_layer.clone() if lower_layer else None
        self.merged_layer = merged_layer.clone() if merged_layer else None

    def execute(self) -> None:
        stack = _get_stack(self.target)
        if self.merged_layer is not None:
            self.redo()
            return
        # Ensure upper and lower are captured if not set
        if self.upper_layer is None and 0 < self.upper_index < len(stack):
            self.upper_layer = stack[self.upper_index].clone()
        if self.lower_layer is None and 0 < self.upper_index < len(stack):
            self.lower_layer = stack[self.lower_index].clone()
        if 0 < self.upper_index < len(stack):
            res = stack.merge_down(self.upper_index)
            if res is not None:
                self.merged_layer = res.clone()
        _invalidate(self.target)

    def redo(self) -> None:
        stack = _get_stack(self.target)
        # Remove replaced layers if present
        layers = stack._layers
        new_layers = []
        replaced = False
        for i, lay in enumerate(layers):
            if self.lower_layer and lay.id == self.lower_layer.id:
                if self.merged_layer:
                    new_layers.append(self.merged_layer.clone())
                replaced = True
            elif self.upper_layer and lay.id == self.upper_layer.id:
                continue
            else:
                new_layers.append(lay)
        if not replaced and self.merged_layer and 0 <= self.lower_index < len(layers):
            layers[self.lower_index:self.upper_index + 1] = [self.merged_layer.clone()]
        else:
            stack._layers = new_layers
        stack.set_active_index(min(self.lower_index, len(stack) - 1))
        _invalidate(self.target)

    def undo(self) -> None:
        stack = _get_stack(self.target)
        layers = stack._layers
        # Replace merged layer with original lower and upper layers
        new_layers = []
        replaced = False
        for lay in layers:
            if self.merged_layer and lay.id == self.merged_layer.id:
                if self.lower_layer:
                    new_layers.append(self.lower_layer.clone())
                if self.upper_layer:
                    new_layers.append(self.upper_layer.clone())
                replaced = True
            else:
                new_layers.append(lay)
        if not replaced and 0 <= self.lower_index < len(layers):
            to_restore = []
            if self.lower_layer:
                to_restore.append(self.lower_layer.clone())
            if self.upper_layer:
                to_restore.append(self.upper_layer.clone())
            layers[self.lower_index:self.lower_index + 1] = to_restore
        else:
            stack._layers = new_layers
        stack.set_active_index(self.upper_index)
        _invalidate(self.target)


class ChangeLayerOpacityCommand(MergeableCommand):
    """
    Command that changes opacity of a layer.
    Supports command coalescing so continuous slider changes merge into one history entry.
    """

    def __init__(
        self,
        target: Any,
        layer: Layer,
        old_opacity: float,
        new_opacity: float,
    ):
        super().__init__(
            name="Change Layer Opacity",
            id="layer.change_opacity",
            description=f"Set opacity of {layer.name} to {int(new_opacity * 100)}%",
        )
        self.target = target
        self.layer = layer
        self.old_opacity = float(old_opacity)
        self.new_opacity = float(new_opacity)

    def can_merge(self, other: Command) -> bool:
        return (
            isinstance(other, ChangeLayerOpacityCommand)
            and other.layer is self.layer
        )

    def merge_with(self, other: Command) -> bool:
        if self.can_merge(other):
            assert isinstance(other, ChangeLayerOpacityCommand)
            self.new_opacity = other.new_opacity
            self.description = f"Set opacity of {self.layer.name} to {int(self.new_opacity * 100)}%"
            self.merge_count += 1
            return True
        return False

    def execute(self) -> None:
        self.layer.set_opacity(self.new_opacity)
        _invalidate(self.target)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        self.layer.set_opacity(self.old_opacity)
        _invalidate(self.target)


class ToggleLayerVisibilityCommand(Command):
    """Command that toggles or sets visibility of a layer."""

    def __init__(
        self,
        target: Any,
        layer: Layer,
        old_visible: bool,
        new_visible: bool,
    ):
        super().__init__(
            name="Toggle Layer Visibility",
            id="layer.toggle_visibility",
            description=f"Set visibility of {layer.name} to {new_visible}",
        )
        self.target = target
        self.layer = layer
        self.old_visible = bool(old_visible)
        self.new_visible = bool(new_visible)

    def execute(self) -> None:
        self.layer.visible = self.new_visible
        _invalidate(self.target)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        self.layer.visible = self.old_visible
        _invalidate(self.target)


class RenameLayerCommand(Command):
    """Command that renames a layer."""

    def __init__(self, target: Any, layer: Layer, old_name: str, new_name: str):
        super().__init__(
            name="Rename Layer",
            id="layer.rename",
            description=f"Rename layer from '{old_name}' to '{new_name}'",
        )
        self.target = target
        self.layer = layer
        self.old_name = old_name
        self.new_name = new_name

    def execute(self) -> None:
        self.layer.name = self.new_name

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        self.layer.name = self.old_name
