# parto/editor/geometry.py
"""
Parto v0.3.0 - Unified Coordinate Transformation & Geometry Engine
Distinguishes between Canvas-space coordinates and Layer-local coordinates.
Provides authoritative geometry transformations for Crop, Resize, Rotate, and Flip.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple, Optional, Any
from PIL import Image

from ..image.transforms import (
    rotate_90,
    rotate_180,
    flip_horizontal,
    flip_vertical,
    resize_image,
)


def layer_canvas_bounds(layer: Any) -> Tuple[int, int, int, int]:
    """Return layer bounding box in Canvas space: (x1, y1, x2, y2)."""
    x1 = int(layer.offset_x)
    y1 = int(layer.offset_y)
    x2 = x1 + int(layer.width)
    y2 = y1 + int(layer.height)
    return x1, y1, x2, y2


def canvas_to_layer_coords(cx: float, cy: float, layer: Any) -> Tuple[float, float]:
    """Convert Canvas-space coordinate to Layer-local space."""
    return cx - layer.offset_x, cy - layer.offset_y


def layer_to_canvas_coords(lx: float, ly: float, layer: Any) -> Tuple[float, float]:
    """Convert Layer-local coordinate to Canvas space."""
    return lx + layer.offset_x, ly + layer.offset_y


def rect_intersection(
    r1: Tuple[int, int, int, int],
    r2: Tuple[int, int, int, int],
) -> Optional[Tuple[int, int, int, int]]:
    """
    Compute intersection between two rectangles (x1, y1, x2, y2).
    Returns None if there is no overlap.
    """
    ix1 = max(r1[0], r2[0])
    iy1 = max(r1[1], r2[1])
    ix2 = min(r1[2], r2[2])
    iy2 = min(r1[3], r2[3])

    if ix2 > ix1 and iy2 > iy1:
        return ix1, iy1, ix2, iy2
    return None


def transform_layer_crop(
    layer: Any,
    crop_rect: Tuple[int, int, int, int],
) -> None:
    """
    Crop layer by transforming Canvas-space crop rectangle into Layer-local coordinates.
    Correctly updates layer image and offset.
    Preserves visibility, opacity, blend mode, and ordering.
    """
    cx1, cy1, cx2, cy2 = crop_rect
    lx1, ly1, lx2, ly2 = layer_canvas_bounds(layer)

    intersect = rect_intersection((cx1, cy1, cx2, cy2), (lx1, ly1, lx2, ly2))

    if intersect is not None:
        ix1, iy1, ix2, iy2 = intersect
        # Convert intersection to layer-local coordinates
        local_x1 = max(0, ix1 - lx1)
        local_y1 = max(0, iy1 - ly1)
        local_x2 = min(layer.width, ix2 - lx1)
        local_y2 = min(layer.height, iy2 - ly1)

        if local_x2 > local_x1 and local_y2 > local_y1:
            layer.image = layer.image.crop((local_x1, local_y1, local_x2, local_y2))
            layer.offset_x = ix1 - cx1
            layer.offset_y = iy1 - cy1
            return

    # Layer is completely outside crop area: preserve layer as empty 1x1 transparent image
    layer.image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    layer.offset_x = lx1 - cx1
    layer.offset_y = ly1 - cy1


def transform_layer_resize(
    layer: Any,
    old_canvas_size: Tuple[int, int],
    new_canvas_size: Tuple[int, int],
    resample: int = Image.Resampling.LANCZOS,
) -> None:
    """
    Scale layer dimensions and position proportionally when document is resized.
    """
    old_w, old_h = old_canvas_size
    new_w, new_h = new_canvas_size

    if old_w <= 0 or old_h <= 0:
        return

    scale_x = new_w / float(old_w)
    scale_y = new_h / float(old_h)

    new_lw = max(1, int(round(layer.width * scale_x)))
    new_lh = max(1, int(round(layer.height * scale_y)))

    layer.image = resize_image(layer.image, new_lw, new_lh, resample=resample)
    layer.offset_x = int(round(layer.offset_x * scale_x))
    layer.offset_y = int(round(layer.offset_y * scale_y))


def transform_layer_rotate_90(
    layer: Any,
    canvas_width: int,
    canvas_height: int,
    clockwise: bool = True,
) -> None:
    """
    Rotate layer image by 90° and transform its offset relative to canvas bounds.
    """
    ox = layer.offset_x
    oy = layer.offset_y
    lw = layer.width
    lh = layer.height

    if clockwise:
        layer.offset_x = canvas_height - oy - lh
        layer.offset_y = ox
        layer.image = rotate_90(layer.image, clockwise=True)
    else:
        layer.offset_x = oy
        layer.offset_y = canvas_width - ox - lw
        layer.image = rotate_90(layer.image, clockwise=False)


def transform_layer_rotate_180(
    layer: Any,
    canvas_width: int,
    canvas_height: int,
) -> None:
    """
    Rotate layer image 180° and transform its offset relative to canvas bounds.
    """
    layer.offset_x = canvas_width - layer.offset_x - layer.width
    layer.offset_y = canvas_height - layer.offset_y - layer.height
    layer.image = rotate_180(layer.image)


def transform_layer_flip_horizontal(
    layer: Any,
    canvas_width: int,
) -> None:
    """
    Mirror layer horizontally across the vertical document axis.
    """
    layer.offset_x = canvas_width - layer.offset_x - layer.width
    layer.image = flip_horizontal(layer.image)


def transform_layer_flip_vertical(
    layer: Any,
    canvas_height: int,
) -> None:
    """
    Mirror layer vertically across the horizontal document axis.
    """
    layer.offset_y = canvas_height - layer.offset_y - layer.height
    layer.image = flip_vertical(layer.image)
