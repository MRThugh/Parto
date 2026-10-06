# parto/commands/filters.py
"""
Parto Architecture 2.0 — Filter & Color Commands
Author: Ali Kamrani (MRThugh)

Reversible commands for photographic filters, color adjustments,
and background removal targeting individual layer image buffers.
"""

from __future__ import annotations
from typing import Optional, Any
from PIL import Image
from .base import Command


def _invalidate(target: Any) -> None:
    if hasattr(target, "invalidate_composite"):
        target.invalidate_composite()


class ApplyFilterCommand(Command):
    """Command that applies a named image filter to the active layer."""

    def __init__(self, target_document: Any, layer: Any, filter_name: str):
        super().__init__(
            name=f"Filter ({filter_name.title()})",
            id=f"filter.{filter_name.lower()}",
            description=f"Apply {filter_name.title()} filter",
        )
        self.target_document = target_document
        self.layer = layer
        self.filter_name = filter_name
        self.before_image: Image.Image = layer.image.copy() if layer and layer.image else None
        self.after_image: Optional[Image.Image] = None

    def execute(self) -> None:
        if self.after_image is None and self.before_image is not None:
            from ..image.filters import apply_filter
            self.after_image = apply_filter(self.before_image, self.filter_name)
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def redo(self) -> None:
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def undo(self) -> None:
        if self.layer and self.before_image is not None:
            self.layer.image = self.before_image.copy()
        _invalidate(self.target_document)


class ColorAdjustmentsCommand(Command):
    """Command that applies brightness, contrast, saturation, and sharpness adjustments."""

    def __init__(
        self,
        target_document: Any,
        layer: Any,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ):
        super().__init__(
            name="Color Adjustments",
            id="filter.color_adjustments",
            description="Apply color adjustments to active layer",
        )
        self.target_document = target_document
        self.layer = layer
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.sharpness = sharpness
        self.before_image: Image.Image = layer.image.copy() if layer and layer.image else None
        self.after_image: Optional[Image.Image] = None

    def execute(self) -> None:
        if self.after_image is None and self.before_image is not None:
            from ..image.processing import apply_color_adjustments
            self.after_image = apply_color_adjustments(
                self.before_image,
                brightness=self.brightness,
                contrast=self.contrast,
                saturation=self.saturation,
                sharpness=self.sharpness,
            )
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def redo(self) -> None:
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def undo(self) -> None:
        if self.layer and self.before_image is not None:
            self.layer.image = self.before_image.copy()
        _invalidate(self.target_document)


class RemoveBackgroundCommand(Command):
    """Command that removes the background of the active layer."""

    def __init__(
        self,
        target_document: Any,
        layer: Any,
        tolerance: int = 28,
        feather_radius: int = 2,
    ):
        super().__init__(
            name="Remove Background",
            id="filter.remove_background",
            description="Remove background from active layer",
        )
        self.target_document = target_document
        self.layer = layer
        self.tolerance = tolerance
        self.feather_radius = feather_radius
        self.before_image: Image.Image = layer.image.copy() if layer and layer.image else None
        self.after_image: Optional[Image.Image] = None

    def execute(self) -> None:
        if self.after_image is None and self.before_image is not None:
            from ..image.processing import remove_background
            self.after_image = remove_background(
                self.before_image,
                tolerance=self.tolerance,
                feather_radius=self.feather_radius,
            )
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def redo(self) -> None:
        if self.layer and self.after_image is not None:
            self.layer.image = self.after_image.copy()
        _invalidate(self.target_document)

    def undo(self) -> None:
        if self.layer and self.before_image is not None:
            self.layer.image = self.before_image.copy()
        _invalidate(self.target_document)
