# parto/layers/models/layer_stack.py
"""
Parto Layers Subsystem — LayerStack Domain Collection
Author: Ali Kamrani (MRThugh)

Self-contained layer collection managing stacking order, active layer selection,
and composite generation. Serves as the single authoritative owner of layer ordering
and membership in a document.
"""

from __future__ import annotations
from typing import Any, List, Optional
from PIL import Image

from .layer import Layer
from ..engine.compositor import compose_layers
from ..operations.merger import merge_down_layers


class LayerStack:
    """
    Authoritative collection of ordered layers for an image document.
    
    Invariants:
    - Layers are ordered from bottom (index 0) to top (index len - 1).
    - Active index is either -1 (empty) or 0 <= active_index < len.
    - Adding, inserting, duplicating, or removing updates the active layer index safely.
    """

    def __init__(self, width: int, height: int):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self._layers: List[Layer] = []
        self._active_index: int = -1

    def __len__(self) -> int:
        return len(self._layers)

    def __iter__(self):
        return iter(self._layers)

    def __getitem__(self, index: int) -> Layer:
        return self._layers[index]

    @property
    def layers(self) -> List[Layer]:
        """Direct access to the ordered list of Layer instances."""
        return self._layers

    @property
    def active_index(self) -> int:
        """Current active layer index, or -1 if empty."""
        return self._active_index

    @property
    def active_layer(self) -> Optional[Layer]:
        """Currently active Layer instance, or None if stack is empty."""
        if 0 <= self._active_index < len(self._layers):
            return self._layers[self._active_index]
        return None

    def set_active_index(self, index: int) -> bool:
        """Update active layer index within valid bounds."""
        if 0 <= index < len(self._layers):
            self._active_index = index
            return True
        elif not self._layers:
            self._active_index = -1
            return True
        return False

    def get_layer_by_id(self, layer_id: str) -> Optional[Layer]:
        """Lookup layer by its unique ID string."""
        for lay in self._layers:
            if lay.id == layer_id:
                return lay
        return None

    def find_index(self, layer_id: str) -> int:
        """Return stack index of layer with given ID, or -1 if not found."""
        for idx, lay in enumerate(self._layers):
            if lay.id == layer_id:
                return idx
        return -1

    def add_layer(self, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
        """Append a new or existing layer to the top of the stack and activate it."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
            for k, v in kwargs.items():
                if hasattr(layer, k):
                    setattr(layer, k, v)
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            layer = Layer(name=name, image=img, **kwargs)
        self._layers.append(layer)
        self._active_index = len(self._layers) - 1
        return layer

    def insert_layer(self, index: int, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
        """Insert a layer at the specified index and activate it."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
            for k, v in kwargs.items():
                if hasattr(layer, k):
                    setattr(layer, k, v)
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            elif isinstance(img, (tuple, list)):
                img = Image.new("RGBA", (self.width, self.height), tuple(img))
            layer = Layer(name=name, image=img, **kwargs)
        target_idx = max(0, min(index, len(self._layers)))
        self._layers.insert(target_idx, layer)
        self._active_index = target_idx
        return layer

    def duplicate_layer(self, index: int) -> Optional[Layer]:
        """Duplicate layer at index and insert it directly above."""
        if 0 <= index < len(self._layers):
            src = self._layers[index]
            dup = src.duplicate()
            self._layers.insert(index + 1, dup)
            self._active_index = index + 1
            return dup
        return None

    def remove_layer(self, index: int) -> Optional[Layer]:
        """Remove layer at index and maintain correct active layer selection."""
        if 0 <= index < len(self._layers):
            removed = self._layers.pop(index)
            if not self._layers:
                self._active_index = -1
            elif self._active_index > index:
                self._active_index -= 1
            elif self._active_index == index:
                self._active_index = min(index, len(self._layers) - 1)
            return removed
        return None

    def move_layer(self, from_idx: int, to_idx: int) -> bool:
        """Move layer from from_idx to to_idx and update active index."""
        if from_idx == to_idx and 0 <= from_idx < len(self._layers):
            return True
        if 0 <= from_idx < len(self._layers) and 0 <= to_idx < len(self._layers):
            layer = self._layers.pop(from_idx)
            self._layers.insert(to_idx, layer)
            if self._active_index == from_idx:
                self._active_index = to_idx
            elif from_idx < self._active_index <= to_idx:
                self._active_index -= 1
            elif to_idx <= self._active_index < from_idx:
                self._active_index += 1
            return True
        return False

    def move_layer_down(self, index: int) -> bool:
        """Move layer downward (towards bottom/background)."""
        if 0 < index < len(self._layers):
            return self.move_layer(index, index - 1)
        return False

    def move_layer_up(self, index: int) -> bool:
        """Move layer upward (towards top of stack)."""
        if 0 <= index < len(self._layers) - 1:
            return self.move_layer(index, index + 1)
        return False

    def merge_down(self, index: int) -> Optional[Layer]:
        """
        Merge layer at index into the layer beneath it.
        Delegates to merge_down_layers domain operation.
        """
        return merge_down_layers(self, index)

    def clear(self) -> None:
        """Clear all layers from stack."""
        self._layers.clear()
        self._active_index = -1

    def clone(self, preserve_ids: bool = True) -> LayerStack:
        """Create a deep snapshot clone of the entire layer stack."""
        new_stack = LayerStack(self.width, self.height)
        new_stack._layers = [lay.clone(preserve_id=preserve_ids) for lay in self._layers]
        new_stack._active_index = self._active_index
        return new_stack

    def composite(self) -> Image.Image:
        """Render composite image of all visible layers."""
        return compose_layers(self._layers, (self.width, self.height))

    def __repr__(self) -> str:
        return (
            f"LayerStack(count={len(self._layers)}, size={self.width}x{self.height}, "
            f"active_index={self._active_index})"
        )
