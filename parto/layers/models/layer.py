# parto/layers/models/layer.py
"""
Parto Layers Subsystem — Layer Domain Model
Author: Ali Kamrani (MRThugh)

Pure domain model representing a single layer in a multi-layer image stack.
Maintains raster image data (RGBA), visibility, opacity, blend mode, and positional offsets.
Free from UI or document lifecycle dependencies.
"""

from __future__ import annotations
import uuid
from typing import Any, Optional
from PIL import Image

from .blend_modes import SUPPORTED_BLEND_MODES


class Layer:
    """
    A single raster layer within a multi-layer document or image composition.
    
    Attributes:
        id: Unique identifier for tracking and history snapshots.
        name: User-facing display name of the layer.
        image: Pillow RGBA image buffer containing the layer's pixel content.
        visible: Boolean flag controlling whether the layer contributes to compositing.
        opacity: Floating-point opacity in [0.0, 1.0].
        blend_mode: Blending operation applied against underlying composite ('normal', etc.).
        offset_x: Horizontal pixel displacement relative to canvas origin (0, 0).
        offset_y: Vertical pixel displacement relative to canvas origin (0, 0).
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
        self.visible: bool = bool(visible)
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.blend_mode: str = blend_mode if blend_mode in SUPPORTED_BLEND_MODES else "normal"
        self.offset_x: int = int(offset_x)
        self.offset_y: int = int(offset_y)

        if actual_image is not None:
            if isinstance(actual_image, (tuple, list)):
                self.image: Image.Image = Image.new("RGBA", (100, 100), tuple(actual_image))
            elif actual_image.mode != "RGBA":
                self.image = actual_image.convert("RGBA")
            else:
                self.image = actual_image.copy()
        else:
            self.image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    @property
    def width(self) -> int:
        """Width in pixels of the underlying raster image."""
        return self.image.width

    @property
    def height(self) -> int:
        """Height in pixels of the underlying raster image."""
        return self.image.height

    def set_opacity(self, value: float) -> None:
        """Set opacity strictly clamped within [0.0, 1.0]."""
        self.opacity = max(0.0, min(1.0, float(value)))

    def set_visible(self, visible: bool) -> None:
        """Toggle layer visibility."""
        self.visible = bool(visible)

    def set_offset(self, x: int, y: int) -> None:
        """Set layer positional offset relative to canvas origin."""
        self.offset_x = int(x)
        self.offset_y = int(y)

    def clone(self, preserve_id: bool = True, preserve_name: bool = True) -> Layer:
        """
        Create a deep copy of this layer.
        Preserves ID and name by default for state snapshots and undo/redo operations.
        """
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
        """
        Create an intentional user-facing duplicate with a new unique ID and '(Copy)' name suffix.
        """
        return self.clone(preserve_id=False, preserve_name=False)

    def __repr__(self) -> str:
        return (
            f"Layer(name='{self.name}', id='{self.id}', size={self.width}x{self.height}, "
            f"offset=({self.offset_x}, {self.offset_y}), visible={self.visible}, "
            f"opacity={self.opacity:.2f}, blend='{self.blend_mode}')"
        )
