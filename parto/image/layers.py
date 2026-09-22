# parto/image/layers.py
"""
Parto v0.3.0 - Multi-Layer Image Architecture
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import uuid
from typing import List, Tuple, Optional
from PIL import Image
import numpy as np


class Layer:
    """
    A single image layer in a document.
    Maintains image data (RGBA), visibility, opacity, blend mode, and offset.
    """

    def __init__(
        self,
        arg1: Any = None,
        arg2: Any = None,
        name: Optional[str] = None,
        image: Optional[Image.Image] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
        offset_x: int = 0,
        offset_y: int = 0,
        layer_id: Optional[str] = None,
    ):
        self.id: str = layer_id or str(uuid.uuid4())[:8]

        actual_image = image
        actual_name = name

        for arg in (arg1, arg2):
            if isinstance(arg, Image.Image):
                actual_image = arg
            elif isinstance(arg, str):
                actual_name = arg

        if actual_name is None:
            actual_name = "Layer"

        self.name: str = actual_name
        self.visible: bool = visible
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.blend_mode: str = blend_mode
        self.offset_x: int = int(offset_x)
        self.offset_y: int = int(offset_y)

        if actual_image is not None:
            if actual_image.mode != "RGBA":
                self.image: Image.Image = actual_image.convert("RGBA")
            else:
                self.image = actual_image.copy()
        else:
            self.image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    def clone(self, preserve_id: bool = True, preserve_name: bool = True) -> Layer:
        """Create a deep copy of this layer, preserving name and id by default for snapshots."""
        return Layer(
            name=self.name if preserve_name else f"{self.name} (Copy)",
            image=self.image.copy(),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            layer_id=self.id if preserve_id else None,
        )

    def duplicate(self) -> Layer:
        """Create an intentional user-facing duplicate with a new ID and (Copy) name suffix."""
        return self.clone(preserve_id=False, preserve_name=False)

    def set_opacity(self, value: float):
        self.opacity = max(0.0, min(1.0, float(value)))


def compose_layers(
    layers: List[Layer],
    canvas_size: Tuple[int, int],
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    """
    Composite an ordered stack of layers into a single output image.
    Layers are processed from index 0 (bottom) to index N-1 (top).
    """
    cw, ch = canvas_size
    if cw <= 0 or ch <= 0:
        return Image.new("RGBA", (1, 1), bg_color)

    composite = Image.new("RGBA", (cw, ch), bg_color)

    visible_layers = [lay for lay in layers if lay.visible and lay.opacity > 0.0]
    if not visible_layers:
        return composite

    for lay in visible_layers:
        layer_img = lay.image
        if layer_img is None or layer_img.width <= 0 or layer_img.height <= 0:
            continue

        # Adjust alpha by layer opacity if opacity < 1.0
        if lay.opacity < 0.999:
            r, g, b, a = layer_img.split()
            # Fast alpha scaling with point LUT
            alpha_lut = [int(v * lay.opacity) for v in range(256)]
            a = a.point(alpha_lut)
            adjusted_layer = Image.merge("RGBA", (r, g, b, a))
        else:
            adjusted_layer = layer_img

        pos = (lay.offset_x, lay.offset_y)
        composite.alpha_composite(adjusted_layer, dest=pos)

    return composite


class LayerStack:
    """
    Self-contained layer collection managing stacking order, active layer,
    and composite generation. Serves as the single authoritative layer state.
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
        return self._layers

    @property
    def active_index(self) -> int:
        return self._active_index

    @property
    def active_layer(self) -> Optional[Layer]:
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

    def add_layer(self, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
        """Append a new or existing layer to the top of the stack and activate it."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            layer = Layer(name=name, image=img)
        self._layers.append(layer)
        self._active_index = len(self._layers) - 1
        return layer

    def insert_layer(self, index: int, image_or_layer: Any = None, name: str = "Layer") -> Layer:
        """Insert a layer at the specified index."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            layer = Layer(name=name, image=img)
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
        """Remove layer at index and clamp active index."""
        if 0 <= index < len(self._layers):
            removed = self._layers.pop(index)
            if self._active_index >= len(self._layers):
                self._active_index = len(self._layers) - 1
            return removed
        return None

    def move_layer_down(self, index: int) -> bool:
        """Move layer downward (towards bottom/background)."""
        if 0 < index < len(self._layers):
            self._layers[index], self._layers[index - 1] = self._layers[index - 1], self._layers[index]
            if self._active_index == index:
                self._active_index = index - 1
            elif self._active_index == index - 1:
                self._active_index = index
            return True
        return False

    def move_layer_up(self, index: int) -> bool:
        """Move layer upward (towards top of stack)."""
        if 0 <= index < len(self._layers) - 1:
            self._layers[index], self._layers[index + 1] = self._layers[index + 1], self._layers[index]
            if self._active_index == index:
                self._active_index = index + 1
            elif self._active_index == index + 1:
                self._active_index = index
            return True
        return False

    def merge_down(self, index: int) -> Optional[Layer]:
        """Merge layer at index into the layer beneath it."""
        if index <= 0 or index >= len(self._layers):
            return None
        lower = self._layers[index - 1]
        upper = self._layers[index]
        comp = compose_layers([lower, upper], (self.width, self.height))
        lower.image = comp
        self._layers.pop(index)
        self._active_index = index - 1
        return lower

    def clear(self) -> None:
        """Clear all layers."""
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

