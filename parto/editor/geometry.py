# parto/editor/geometry.py
"""
Parto — Geometry Compatibility Shim
Author: Ali Kamrani (MRThugh)

Maintains 100% backward-compatible imports by re-exporting coordinate transformations
and layer geometry math from the parto.document.geometry domain module.
"""

from ..document.geometry import (
    layer_canvas_bounds,
    canvas_to_layer_coords,
    layer_to_canvas_coords,
    rect_intersection,
    transform_layer_crop,
    transform_layer_resize,
    transform_layer_rotate_90,
    transform_layer_rotate_180,
    transform_layer_flip_horizontal,
    transform_layer_flip_vertical,
)

__all__ = [
    "layer_canvas_bounds",
    "canvas_to_layer_coords",
    "layer_to_canvas_coords",
    "rect_intersection",
    "transform_layer_crop",
    "transform_layer_resize",
    "transform_layer_rotate_90",
    "transform_layer_rotate_180",
    "transform_layer_flip_horizontal",
    "transform_layer_flip_vertical",
]
