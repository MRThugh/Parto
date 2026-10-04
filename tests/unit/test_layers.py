# tests/unit/test_layers.py
"""
Unit Tests — Layer & LayerStack Model
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PIL import Image
from parto.image.layers import Layer, LayerStack, SUPPORTED_BLEND_MODES


def test_layer_initialization_defaults():
    """Verify Layer initializes with proper default attributes and RGBA image mode."""
    img = Image.new("RGB", (30, 20), (255, 128, 0))
    layer = Layer(name="Base", image=img)

    assert layer.name == "Base"
    assert layer.width == 30
    assert layer.height == 20
    assert layer.image.mode == "RGBA"
    assert layer.visible is True
    assert layer.opacity == 1.0
    assert layer.blend_mode == "normal"
    assert layer.offset_x == 0
    assert layer.offset_y == 0
    assert len(layer.id) > 0


def test_layer_opacity_clamping():
    """Verify opacity is strictly clamped within [0.0, 1.0]."""
    layer = Layer(name="OpacityTest")
    layer.set_opacity(1.5)
    assert layer.opacity == 1.0

    layer.set_opacity(-0.5)
    assert layer.opacity == 0.0

    layer.set_opacity(0.42)
    assert abs(layer.opacity - 0.42) < 1e-4


def test_layer_clone_vs_duplicate():
    """
    Verify clone() preserves ID and name by default (for internal history snapshots),
    while duplicate() creates a new ID and appends ' (Copy)' to name.
    """
    orig = Layer(name="Foreground", image=Image.new("RGBA", (10, 10), (1, 2, 3, 4)))
    
    cloned = orig.clone()
    assert cloned.id == orig.id
    assert cloned.name == orig.name
    assert cloned.image is not orig.image
    assert cloned.image.tobytes() == orig.image.tobytes()

    duplicated = orig.duplicate()
    assert duplicated.id != orig.id
    assert duplicated.name == "Foreground (Copy)"
    assert duplicated.image is not orig.image
    assert duplicated.image.tobytes() == orig.image.tobytes()


def test_layerstack_lifecycle_and_indexing():
    """Verify LayerStack operations, length, indexing, and active index maintenance."""
    stack = LayerStack(100, 100)
    assert len(stack) == 0
    assert stack.active_index == -1
    assert stack.active_layer is None

    # Add layers
    l0 = stack.add_layer(name="L0")
    assert len(stack) == 1
    assert stack.active_index == 0
    assert stack[0] is l0

    l1 = stack.add_layer(name="L1")
    assert len(stack) == 2
    assert stack.active_index == 1
    assert stack[1] is l1

    # Active index bounds checking
    assert stack.set_active_index(0) is True
    assert stack.active_index == 0
    assert stack.set_active_index(99) is False
    assert stack.active_index == 0

    # Iteration
    names = [lay.name for lay in stack]
    assert names == ["L0", "L1"]

    # Clear
    stack.clear()
    assert len(stack) == 0
    assert stack.active_index == -1


def test_layerstack_remove_maintains_active_index():
    """Verify removing layers properly shifts and clamps active index."""
    stack = LayerStack(50, 50)
    stack.add_layer(name="L0")
    stack.add_layer(name="L1")
    stack.add_layer(name="L2")
    assert stack.active_index == 2

    # Remove active top layer (L2) -> active index becomes 1 (L1)
    removed = stack.remove_layer(2)
    assert removed.name == "L2"
    assert len(stack) == 2
    assert stack.active_index == 1

    # Remove bottom layer (L0) while active is 1 -> active index decrements to 0
    removed_bottom = stack.remove_layer(0)
    assert removed_bottom.name == "L0"
    assert len(stack) == 1
    assert stack.active_index == 0
