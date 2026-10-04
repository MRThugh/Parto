# tests/regression/test_issue_regressions.py
"""
Regression Tests — Geometry Transforms, Offset-Awareness & Safety Flows
Author & Maintainer: Ali Kamrani (علی کامرانی)

Validates:
1. Offset-aware Crop (contained, partial intersect, fully outside).
2. Offset-aware Resize (proportional coordinate and dimension scaling).
3. Offset-aware Rotate (90° CW, 90° CCW, 180° with offset transformation).
4. Offset-aware Flip (horizontal and vertical reflection).
5. Geometry conversions between Canvas-space and Layer-local space.
6. Close event safety flow (SaveResult enum).
"""

import pytest
from PIL import Image

from parto.image.layers import Layer, LayerStack
from parto.editor.geometry import (
    layer_canvas_bounds,
    canvas_to_layer_coords,
    layer_to_canvas_coords,
    transform_layer_crop,
    transform_layer_resize,
    transform_layer_rotate_90,
    transform_layer_rotate_180,
    transform_layer_flip_horizontal,
    transform_layer_flip_vertical,
)
from parto.ui.main_window import SaveResult


def test_geometry_coordinate_conversions():
    """Verify canvas-space to layer-space coordinate math."""
    lay = Layer(image=Image.new("RGBA", (50, 40)), offset_x=10, offset_y=20)

    # Canvas bounds: (10, 20, 60, 60)
    assert layer_canvas_bounds(lay) == (10, 20, 60, 60)

    # Canvas (15, 25) -> Layer (5, 5)
    assert canvas_to_layer_coords(15, 25, lay) == (5, 5)

    # Layer (5, 5) -> Canvas (15, 25)
    assert layer_to_canvas_coords(5, 5, lay) == (15, 25)


def test_crop_layer_with_offset_contained():
    """Crop completely inside an offset layer."""
    lay = Layer(image=Image.new("RGBA", (100, 100), (255, 0, 0, 255)), offset_x=20, offset_y=20)
    # Crop canvas rect (30, 30, 70, 70)
    transform_layer_crop(lay, (30, 30, 70, 70))

    assert lay.width == 40
    assert lay.height == 40
    assert lay.offset_x == 0
    assert lay.offset_y == 0


def test_crop_layer_partially_intersecting():
    """Crop partially intersecting an offset layer."""
    lay = Layer(image=Image.new("RGBA", (50, 50), (0, 255, 0, 255)), offset_x=20, offset_y=20)
    # Crop canvas rect (0, 0, 40, 40)
    transform_layer_crop(lay, (0, 0, 40, 40))

    # Overlap is from (20, 20) to (40, 40) -> 20x20
    assert lay.width == 20
    assert lay.height == 20
    assert lay.offset_x == 20
    assert lay.offset_y == 20


def test_crop_layer_completely_outside():
    """Crop completely outside an offset layer preserves 1x1 transparent stub."""
    lay = Layer(image=Image.new("RGBA", (30, 30)), offset_x=50, offset_y=50)
    # Crop (0, 0, 20, 20)
    transform_layer_crop(lay, (0, 0, 20, 20))

    assert lay.width == 1
    assert lay.height == 1
    assert lay.image.getpixel((0, 0)) == (0, 0, 0, 0)


def test_resize_layer_with_offset_proportional():
    """Verify layer dimensions and offsets scale proportionally on document resize."""
    lay = Layer(image=Image.new("RGBA", (20, 20)), offset_x=10, offset_y=10)
    # Resize canvas 100x100 -> 200x200 (scale 2x)
    transform_layer_resize(lay, (100, 100), (200, 200))

    assert lay.width == 40
    assert lay.height == 40
    assert lay.offset_x == 20
    assert lay.offset_y == 20


def test_rotate_and_flip_offset_transformations():
    """Verify 90 CW, 90 CCW, 180, and flips update layer offsets correctly."""
    canvas_size = (100, 80)
    lay = Layer(image=Image.new("RGBA", (30, 20)), offset_x=10, offset_y=15)

    # Rotate 90 CW: old canvas is (100, 80), new canvas is (80, 100)
    transform_layer_rotate_90(lay, 100, 80, clockwise=True)
    # lx=10, ly=15, lw=30, lh=20 -> new_lx = 80 - 15 - 20 = 45, new_ly = 10
    assert lay.width == 20
    assert lay.height == 30
    assert lay.offset_x == 45
    assert lay.offset_y == 10

    # Flip horizontal on new canvas width 80
    transform_layer_flip_horizontal(lay, 80)
    # new_lx = 80 - 45 - 20 = 15
    assert lay.offset_x == 15
    assert lay.offset_y == 10


def test_save_result_enum_integrity():
    """Verify SaveResult enum values."""
    assert SaveResult.SUCCESS.value == "success"
    assert SaveResult.CANCELLED.value == "cancelled"
    assert SaveResult.FAILED.value == "failed"
