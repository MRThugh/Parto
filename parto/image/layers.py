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

    def clone(self) -> Layer:
        """Create a deep copy of this layer."""
        return Layer(
            name=f"{self.name} (Copy)",
            image=self.image.copy(),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
        )

    def duplicate(self) -> Layer:
        """Alias for clone()."""
        return self.clone()

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
    and composite generation.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._layers: List[Layer] = []
        self._active_index: int = -1

    def __len__(self) -> int:
        return len(self._layers)

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

    def add_layer(self, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
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

    def remove_layer(self, index: int) -> Optional[Layer]:
        if 0 <= index < len(self._layers):
            removed = self._layers.pop(index)
            if self._active_index >= len(self._layers):
                self._active_index = len(self._layers) - 1
            return removed
        return None

    def move_layer_down(self, index: int) -> bool:
        if 0 < index < len(self._layers):
            self._layers[index], self._layers[index - 1] = self._layers[index - 1], self._layers[index]
            if self._active_index == index:
                self._active_index = index - 1
            return True
        return False

    def move_layer_up(self, index: int) -> bool:
        if 0 <= index < len(self._layers) - 1:
            self._layers[index], self._layers[index + 1] = self._layers[index + 1], self._layers[index]
            if self._active_index == index:
                self._active_index = index + 1
            return True
        return False

    def merge_down(self, index: int) -> Optional[Layer]:
        if index <= 0 or index >= len(self._layers):
            return None
        lower = self._layers[index - 1]
        upper = self._layers[index]
        comp = compose_layers([lower, upper], (self.width, self.height))
        lower.image = comp
        self._layers.pop(index)
        self._active_index = index - 1
        return lower

    def composite(self) -> Image.Image:
        return compose_layers(self._layers, (self.width, self.height))

