# parto/brush/engine/brush_engine.py
"""
Parto Brush System — Brush Engine Protocol and Implementation
Defines high-level rendering contract decoupled from UI and Qt events.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Protocol, runtime_checkable
from PIL import Image
from ..models.settings import BrushSettings
from ..models.stroke import StrokePoint
from .renderer import BrushRenderer


@runtime_checkable
class IBrushEngine(Protocol):
    """
    Contract for brush rendering engines.
    Allows introducing alternative engines (texture, vector, procedural) in future.
    """

    def render_point(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        point: StrokePoint,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> bool:
        """Render a single initial point/dab onto the target image."""
        ...

    def render_segment(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        p1: StrokePoint,
        p2: StrokePoint,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> bool:
        """Render interpolated segment between two consecutive stroke points."""
        ...

    def invalidate(self) -> None:
        """Clear cached resources."""
        ...


class RasterBrushEngine:
    """
    Standard high-performance raster brush engine for Parto.
    Transforms stroke points into raster modifications on target image buffers.
    """

    def __init__(self, renderer: BrushRenderer | None = None):
        self.renderer: BrushRenderer = renderer or BrushRenderer()

    def render_point(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        point: StrokePoint,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> bool:
        local_x = point.x - offset_x
        local_y = point.y - offset_y
        return self.renderer.render_segment(
            target_image, settings, local_x, local_y, local_x, local_y
        )

    def render_segment(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        p1: StrokePoint,
        p2: StrokePoint,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> bool:
        x1 = p1.x - offset_x
        y1 = p1.y - offset_y
        x2 = p2.x - offset_x
        y2 = p2.y - offset_y
        return self.renderer.render_segment(
            target_image, settings, x1, y1, x2, y2
        )

    def invalidate(self) -> None:
        self.renderer.invalidate_cache()
