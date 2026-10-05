# parto/document/engine/transform_engine.py
"""
Parto Document Subsystem — Transform Engine
Author: Ali Kamrani (MRThugh)

Coordinates offset-aware geometric transformations across the Document's LayerStack.
Delegates low-level layer math to parto.editor.geometry.
"""

from __future__ import annotations
from typing import Tuple, Optional
from PIL import Image

from ...image.layers import LayerStack
from ..geometry import (
    transform_layer_crop,
    transform_layer_resize,
    transform_layer_rotate_90,
    transform_layer_rotate_180,
    transform_layer_flip_horizontal,
    transform_layer_flip_vertical,
)


class TransformEngine:
    """
    Coordinates geometric operations on a LayerStack:
    rotation, flipping, resizing, and cropping.
    """

    @staticmethod
    def rotate_90(
        layer_stack: LayerStack,
        width: int,
        height: int,
        clockwise: bool = True,
    ) -> Tuple[int, int]:
        """
        Rotate entire document 90 degrees with offset-aware layer transformation.
        Returns the new (width, height).
        """
        new_w, new_h = height, width
        for lay in layer_stack:
            transform_layer_rotate_90(lay, width, height, clockwise=clockwise)
        layer_stack.width = new_w
        layer_stack.height = new_h
        return new_w, new_h

    @staticmethod
    def rotate_180(
        layer_stack: LayerStack,
        width: int,
        height: int,
    ) -> Tuple[int, int]:
        """
        Rotate entire document 180 degrees with offset-aware layer transformation.
        Returns unchanged (width, height).
        """
        for lay in layer_stack:
            transform_layer_rotate_180(lay, width, height)
        return width, height

    @staticmethod
    def flip_horizontal(
        layer_stack: LayerStack,
        width: int,
    ) -> None:
        """Flip document horizontally with offset-aware layer transformation."""
        for lay in layer_stack:
            transform_layer_flip_horizontal(lay, width)

    @staticmethod
    def flip_vertical(
        layer_stack: LayerStack,
        height: int,
    ) -> None:
        """Flip document vertically with offset-aware layer transformation."""
        for lay in layer_stack:
            transform_layer_flip_vertical(lay, height)

    @staticmethod
    def resize(
        layer_stack: LayerStack,
        old_size: Tuple[int, int],
        new_size: Tuple[int, int],
        resample: int = Image.Resampling.LANCZOS,
    ) -> Tuple[int, int]:
        """
        Resize entire document and all layers with offset-aware scaling.
        Returns (new_width, new_height).
        """
        nw, nh = max(1, int(new_size[0])), max(1, int(new_size[1]))
        if (nw, nh) == old_size:
            return old_size

        for lay in layer_stack:
            transform_layer_resize(lay, old_size, (nw, nh), resample=resample)

        layer_stack.width = nw
        layer_stack.height = nh
        return nw, nh

    @staticmethod
    def crop(
        layer_stack: LayerStack,
        current_size: Tuple[int, int],
        rect: Tuple[int, int, int, int],
    ) -> Optional[Tuple[int, int]]:
        """
        Crop entire document to rectangle (left, top, right, bottom).
        Transforms Canvas-space crop rectangle into Layer-local coordinates for every layer.
        Returns (new_width, new_height) if valid crop, or None if crop was no-op or invalid.
        """
        curr_w, curr_h = current_size
        left, top, right, bottom = rect
        x1 = max(0, min(int(left), curr_w))
        y1 = max(0, min(int(top), curr_h))
        x2 = max(0, min(int(right), curr_w))
        y2 = max(0, min(int(bottom), curr_h))

        if x2 <= x1 or y2 <= y1:
            return None  # Invalid crop rectangle: no-op

        new_w = x2 - x1
        new_h = y2 - y1

        if x1 == 0 and y1 == 0 and new_w == curr_w and new_h == curr_h:
            return None  # Full canvas crop: no-op

        clamped_rect = (x1, y1, x2, y2)
        for lay in layer_stack:
            transform_layer_crop(lay, clamped_rect)

        layer_stack.width = new_w
        layer_stack.height = new_h
        return new_w, new_h
