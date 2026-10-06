# parto/commands/brush.py
"""
Parto Architecture 2.0 — Brush Commands
Author: Ali Kamrani (MRThugh)

Reversible domain command for raster brush strokes.
Stores only the delta or target layer image buffer, preventing wasteful
deep cloning of unaffected layers or large multi-layer composites.
"""

from __future__ import annotations
from typing import Optional, Any
from PIL import Image
from .base import Command


class PaintStrokeCommand(Command):
    """
    Command representing a committed brush stroke on a specific layer.
    
    Guarantees:
    - Memory-safe: Stores pre-stroke and post-stroke image buffers solely
      for the target painted layer. Unaffected layers are not duplicated.
    - Exact pixel round-trip restoration between initial and final states.
    - Decoupled from Qt GUI widgets.
    """

    def __init__(
        self,
        target_document: Any,
        layer: Any,
        before_image: Image.Image,
        after_image: Image.Image,
        name: str = "Paint Stroke",
        stroke_size: int = 10,
    ):
        super().__init__(
            name=name or f"Brush Stroke ({stroke_size}px)",
            id="brush.paint_stroke",
            description=f"Paint stroke on {getattr(layer, 'name', 'Layer')}",
        )
        self.target_document = target_document
        self.layer = layer
        self.before_image: Image.Image = before_image.copy()
        self.after_image: Image.Image = after_image.copy()
        self.stroke_size = stroke_size

    def can_execute(self) -> bool:
        return (
            self.layer is not None
            and hasattr(self.layer, "image")
            and self.before_image is not None
            and self.after_image is not None
        )

    def _invalidate(self) -> None:
        if self.target_document and hasattr(self.target_document, "invalidate_composite"):
            self.target_document.invalidate_composite()

    def execute(self) -> None:
        if self.layer and hasattr(self.layer, "image"):
            self.layer.image = self.after_image.copy()
        self._invalidate()

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        if self.layer and hasattr(self.layer, "image"):
            self.layer.image = self.before_image.copy()
        self._invalidate()
