# parto/document/engine/compositing_engine.py
"""
Parto Document Subsystem — Compositing Engine
Author: Ali Kamrani (MRThugh)

Coordinates layer compositing, caching, and non-destructive preview rendering.
Delegates raw blending to parto.image.layers.compose_layers.
"""

from __future__ import annotations
from typing import Optional, Tuple
from PIL import Image

from ...image.layers import LayerStack, compose_layers
from ...image.processing import apply_color_adjustments
from ...image.filters import apply_filter


class CompositingEngine:
    """
    Manages composite generation and cached composite invalidation for a Document.
    """

    def __init__(self):
        self._cached_composite: Optional[Image.Image] = None

    def invalidate(self) -> None:
        """Clear cached composite rendering."""
        self._cached_composite = None

    def get_composite(self, layer_stack: LayerStack, width: int, height: int) -> Optional[Image.Image]:
        """
        Returns the composite rendering of all visible layers.
        Uses cached composite when available.
        """
        if len(layer_stack) == 0 or width <= 0 or height <= 0:
            return None
        if self._cached_composite is None:
            self._cached_composite = layer_stack.composite()
        return self._cached_composite

    def get_adjusted_preview(
        self,
        layer_stack: LayerStack,
        canvas_size: Tuple[int, int],
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Optional[Image.Image]:
        """
        Return preview composite of active layer adjusted without mutating document state.
        """
        active_idx = layer_stack.active_index
        if active_idx < 0 or active_idx >= len(layer_stack):
            return None

        preview_layers = []
        for i, lay in enumerate(layer_stack):
            if i == active_idx and lay.visible:
                adj_img = apply_color_adjustments(
                    lay.image,
                    brightness=brightness,
                    contrast=contrast,
                    saturation=saturation,
                    sharpness=sharpness,
                )
                preview_lay = lay.clone()
                preview_lay.image = adj_img
                preview_layers.append(preview_lay)
            else:
                preview_layers.append(lay)

        return compose_layers(preview_layers, canvas_size)

    def get_filter_preview(
        self,
        layer_stack: LayerStack,
        canvas_size: Tuple[int, int],
        filter_name: str,
    ) -> Optional[Image.Image]:
        """
        Return preview composite with filter applied to active layer without mutating document state.
        """
        active_idx = layer_stack.active_index
        if active_idx < 0 or active_idx >= len(layer_stack):
            return None

        preview_layers = []
        for i, lay in enumerate(layer_stack):
            if i == active_idx and lay.visible:
                filt_img = apply_filter(lay.image, filter_name)
                preview_lay = lay.clone()
                preview_lay.image = filt_img
                preview_layers.append(preview_lay)
            else:
                preview_layers.append(lay)

        return compose_layers(preview_layers, canvas_size)
