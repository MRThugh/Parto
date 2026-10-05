# tests/unit/test_layers_subsystem_architecture.py
"""
Unit Tests — Layers Subsystem Architecture
Author & Maintainer: Ali Kamrani (علی کامرانی)

Tests the clean domain architecture of the Layers subsystem:
- Layer domain model isolation (no Qt, pure python, deep copy, cloning)
- LayerStack domain collection invariants and active layer tracking
- Blender engine mathematical correctness across supported blend modes
- Compositor engine rendering and immutability guarantees
- Merger operations with strict visibility and offset semantics
- 100% backward-compatibility shim via parto.image.layers
"""

import numpy as np
import pytest
from PIL import Image

from parto.layers import (
    Layer,
    LayerStack,
    SUPPORTED_BLEND_MODES,
    compose_layers,
    LayerCompositor,
    blend_mode_composite,
    _blend_mode_composite,
    merge_down_layers,
)
import parto.image.layers as legacy_layers


def test_layer_model_pure_python_and_immutability():
    """Verify Layer is an isolated domain model with proper defaults and RGBA clamping."""
    img = Image.new("RGB", (40, 30), (100, 150, 200))
    layer = Layer(name="ArtLayer", image=img, opacity=0.8, blend_mode="multiply", offset_x=10, offset_y=-5)

    assert layer.name == "ArtLayer"
    assert layer.width == 40
    assert layer.height == 30
    assert layer.image.mode == "RGBA"
    assert layer.visible is True
    assert layer.opacity == 0.8
    assert layer.blend_mode == "multiply"
    assert layer.offset_x == 10
    assert layer.offset_y == -5
    assert len(layer.id) > 0

    # Opacity bounds clamping
    layer.set_opacity(1.5)
    assert layer.opacity == 1.0
    layer.set_opacity(-0.2)
    assert layer.opacity == 0.0

    # Cloning for history snapshots preserves ID and name
    clone = layer.clone()
    assert clone.id == layer.id
    assert clone.name == layer.name
    assert clone.image is not layer.image
    assert clone.image.tobytes() == layer.image.tobytes()

    # Duplicating creates a new ID and '(Copy)' name suffix
    dup = layer.duplicate()
    assert dup.id != layer.id
    assert dup.name == "ArtLayer (Copy)"
    assert dup.image is not layer.image


def test_layer_stack_invariants_and_active_tracking():
    """Verify LayerStack enforces collection invariants and active index tracking."""
    stack = LayerStack(100, 80)
    assert len(stack) == 0
    assert stack.active_index == -1
    assert stack.active_layer is None

    # Add layer
    l0 = stack.add_layer(name="Background")
    assert len(stack) == 1
    assert stack.active_index == 0
    assert stack.active_layer is l0
    assert stack.get_layer_by_id(l0.id) is l0
    assert stack.find_index(l0.id) == 0

    # Add second layer
    l1 = stack.add_layer(name="Subject")
    assert len(stack) == 2
    assert stack.active_index == 1
    assert stack.active_layer is l1

    # Insert layer between
    l_mid = stack.insert_layer(1, name="Midground")
    assert len(stack) == 3
    assert stack.active_index == 1
    assert stack[1] is l_mid

    # Move layer up/down
    assert stack.move_layer_up(1) is True
    assert stack[2] is l_mid
    assert stack.move_layer_down(2) is True
    assert stack[1] is l_mid

    # Duplicate layer
    dup = stack.duplicate_layer(1)
    assert dup is not None
    assert len(stack) == 4
    assert stack.active_index == 2
    assert stack[2] is dup

    # Remove layer at index 2 (active index was 2; next element shifts into index 2)
    removed = stack.remove_layer(2)
    assert removed is dup
    assert len(stack) == 3
    assert stack.active_index == 2

    # Remove top layer at index 2 -> active index clamps to 1
    top_removed = stack.remove_layer(2)
    assert len(stack) == 2
    assert stack.active_index == 1


def test_blender_engine_modes():
    """Verify blend_mode_composite executes supported blend modes over overlapping bounds."""
    base = Image.new("RGBA", (10, 10), (200, 100, 50, 255))
    top = Image.new("RGBA", (10, 10), (100, 100, 100, 255))

    # Test multiply
    base_mult = base.copy()
    blend_mode_composite(base_mult, top, (0, 0), "multiply")
    px = base_mult.getpixel((0, 0))
    expected_r = int(round(200 * 100 / 255))
    assert abs(px[0] - expected_r) <= 1

    # Test screen
    base_screen = base.copy()
    blend_mode_composite(base_screen, top, (0, 0), "screen")
    px_s = base_screen.getpixel((0, 0))
    expected_screen_r = int(round((1.0 - (1.0 - 200/255) * (1.0 - 100/255)) * 255))
    assert abs(px_s[0] - expected_screen_r) <= 1

    # Test darken and lighten
    base_dark = base.copy()
    blend_mode_composite(base_dark, top, (0, 0), "darken")
    assert base_dark.getpixel((0, 0))[0] == 100

    base_light = base.copy()
    blend_mode_composite(base_light, top, (0, 0), "lighten")
    assert base_light.getpixel((0, 0))[0] == 200


def test_compositor_engine_and_immutability():
    """Verify compose_layers renders stacked layers without mutating sources."""
    l0 = Layer(name="Base", image=Image.new("RGBA", (20, 20), (255, 0, 0, 255)))
    l1 = Layer(name="Overlay", image=Image.new("RGBA", (20, 20), (0, 255, 0, 255)), opacity=0.5)

    orig_l0_bytes = l0.image.tobytes()
    orig_l1_bytes = l1.image.tobytes()

    comp = compose_layers([l0, l1], (20, 20))
    assert comp.size == (20, 20)
    assert l0.image.tobytes() == orig_l0_bytes
    assert l1.image.tobytes() == orig_l1_bytes

    # Test LayerCompositor helper
    compositor = LayerCompositor(bg_color=(255, 255, 255, 255))
    comp2 = compositor.composite([l0], (20, 20))
    assert comp2.getpixel((0, 0)) == (255, 0, 0, 255)


def test_merger_operations_semantics():
    """Verify merge_down_layers handles visibility, offsets, and blend mode resets."""
    stack = LayerStack(20, 20)
    l0 = stack.add_layer(Image.new("RGBA", (20, 20), (255, 0, 0, 255)), name="Lower")
    l1 = stack.add_layer(Image.new("RGBA", (10, 10), (0, 0, 255, 255)), name="Upper", offset_x=5, offset_y=5)

    merged = merge_down_layers(stack, 1)
    assert merged is l0
    assert len(stack) == 1
    assert stack.active_index == 0
    assert merged.offset_x == 0
    assert merged.offset_y == 0
    assert merged.opacity == 1.0
    assert merged.blend_mode == "normal"
    assert merged.visible is True

    # Inside merged box (5, 5) -> Blue
    assert merged.image.getpixel((5, 5)) == (0, 0, 255, 255)
    # Outside merged box (0, 0) -> Red
    assert merged.image.getpixel((0, 0)) == (255, 0, 0, 255)


def test_layers_compatibility_shim():
    """Verify that parto.image.layers re-exports identical classes and functions."""
    assert legacy_layers.Layer is Layer
    assert legacy_layers.LayerStack is LayerStack
    assert legacy_layers.compose_layers is compose_layers
    assert legacy_layers.SUPPORTED_BLEND_MODES is SUPPORTED_BLEND_MODES
    assert legacy_layers._blend_mode_composite is _blend_mode_composite
