# parto/document/models/document_state.py
"""
Parto Document Subsystem — Pure State Model
Author: Ali Kamrani (MRThugh)

Encapsulates authoritative document state: canvas dimensions, layer stack,
file path, and modification lifecycle.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
from PIL import Image

from ...image.layers import Layer, LayerStack


class DocumentState:
    """
    Authoritative state container for a single Parto document.
    Maintains canvas dimensions, layer collection, filepath, and dirty tracking.
    """

    def __init__(self, width: int = 0, height: int = 0):
        self._width: int = max(0, int(width))
        self._height: int = max(0, int(height))
        self.layer_stack: LayerStack = LayerStack(max(1, self._width or 1), max(1, self._height or 1))
        self._filepath: Optional[str] = None
        self._is_modified: bool = False

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, val: int) -> None:
        self._width = max(1, int(val))
        self.layer_stack.width = self._width

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, val: int) -> None:
        self._height = max(1, int(val))
        self.layer_stack.height = self._height

    @property
    def dimensions(self) -> Tuple[int, int]:
        return (self._width, self._height)

    def set_dimensions(self, width: int, height: int) -> None:
        """Set width and height simultaneously and update layer stack."""
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self.layer_stack.width = self._width
        self.layer_stack.height = self._height

    @property
    def filepath(self) -> Optional[str]:
        return self._filepath

    @filepath.setter
    def filepath(self, path: Optional[str]) -> None:
        self._filepath = path

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @is_modified.setter
    def is_modified(self, val: bool) -> None:
        self._is_modified = bool(val)

    @property
    def layers(self) -> List[Layer]:
        return self.layer_stack.layers

    @property
    def active_layer_index(self) -> int:
        return self.layer_stack.active_index

    def set_active_layer_index(self, index: int) -> bool:
        return self.layer_stack.set_active_index(index)

    @property
    def active_layer(self) -> Optional[Layer]:
        return self.layer_stack.active_layer

    @property
    def has_image(self) -> bool:
        return len(self.layer_stack) > 0 and self._width > 0 and self._height > 0

    def reset(
        self,
        width: int = 1920,
        height: int = 1080,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        initial_image: Optional[Image.Image] = None,
        filepath: Optional[str] = None,
    ) -> None:
        """Reset state to a fresh document with a single base layer."""
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self._filepath = filepath
        self._is_modified = False
        self.layer_stack = LayerStack(self._width, self._height)

        if initial_image is not None:
            base_img = initial_image.copy()
            if base_img.mode != "RGBA":
                base_img = base_img.convert("RGBA")
        else:
            base_img = Image.new("RGBA", (self._width, self._height), fill_color)

        self.layer_stack.add_layer(base_img, name="Background")
