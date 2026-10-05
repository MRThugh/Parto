# parto/document/engine/document_engine.py
"""
Parto Document Subsystem — Document Engine Facade
Author: Ali Kamrani (MRThugh)

Coordinates domain transformations, layer raster operations, and compositing.
"""

from __future__ import annotations
from typing import Optional, Tuple
from PIL import Image

from .transform_engine import TransformEngine
from .compositing_engine import CompositingEngine
from ...layers import Layer, LayerStack
from ...image.processing import apply_color_adjustments, remove_background
from ...image.filters import apply_filter, FILTER_MAP


class DocumentEngine:
    """
    Coordinates domain operations for a Document:
    transforms, filters, color adjustments, background removal, and compositing.
    """

    def __init__(self):
        self.transforms: TransformEngine = TransformEngine()
        self.compositing: CompositingEngine = CompositingEngine()

    def apply_filter(self, layer: Layer, filter_name: str) -> bool:
        """Apply photographic filter to layer image. Returns True if applied."""
        if layer is None or layer.image is None:
            return False
        if filter_name.lower() not in FILTER_MAP:
            return False
        layer.image = apply_filter(layer.image, filter_name)
        return True

    def apply_color_adjustments(
        self,
        layer: Layer,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> bool:
        """Apply color adjustments to layer image. Returns False if 0% change (no-op)."""
        if layer is None or layer.image is None:
            return False
        if (
            abs(brightness - 1.0) < 1e-4
            and abs(contrast - 1.0) < 1e-4
            and abs(saturation - 1.0) < 1e-4
            and abs(sharpness - 1.0) < 1e-4
        ):
            return False
        layer.image = apply_color_adjustments(
            layer.image,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )
        return True

    def remove_background(
        self,
        layer: Layer,
        tolerance: int = 28,
        feather_radius: int = 2,
    ) -> bool:
        """Remove background from layer image."""
        if layer is None or layer.image is None:
            return False
        layer.image = remove_background(
            layer.image,
            tolerance=tolerance,
            feather_radius=feather_radius,
        )
        return True
