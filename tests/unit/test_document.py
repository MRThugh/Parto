# tests/unit/test_document.py
"""
Unit Tests — Document Architecture & State Model
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PIL import Image
from parto.editor.document import Document
from parto.image.layers import Layer, LayerStack


def test_document_creation_valid_dimensions():
    """Verify document initializes with valid dimensions and a default Background layer."""
    doc = Document()
    doc.new_document(320, 240, fill_color=(255, 255, 255, 255))

    assert doc.width == 320
    assert doc.height == 240
    assert (doc.width, doc.height) == (320, 240)
    assert doc.has_image is True
    assert len(doc.layers) == 1
    assert doc.active_layer is not None
    assert doc.active_layer.name == "Background"
    assert doc.active_layer.image.size == (320, 240)
    assert doc.modified is False


def test_document_layerstack_identity():
    """Verify Document delegates layer stack access authoritatively to LayerStack."""
    doc = Document()
    doc.new_document(100, 100)

    assert isinstance(doc.layer_stack, LayerStack)
    assert doc.layers is doc.layer_stack.layers
    assert doc.active_layer is doc.layer_stack.active_layer
    assert doc.active_layer_index == doc.layer_stack.active_index


def test_document_add_insert_remove_layers():
    """Verify adding, inserting, and deleting layers updates state and active indices."""
    doc = Document()
    doc.new_document(50, 50)
    assert len(doc.layers) == 1
    assert doc.active_layer_index == 0

    # Add second layer
    l1 = doc.add_layer(Image.new("RGBA", (50, 50), (255, 0, 0, 255)), name="RedLayer")
    assert len(doc.layers) == 2
    assert doc.active_layer is l1
    assert doc.active_layer_index == 1

    # Insert third layer at index 1
    l_mid = doc.layer_stack.insert_layer(1, Image.new("RGBA", (50, 50), (0, 255, 0, 255)), name="GreenMid")
    doc.invalidate_composite()
    assert len(doc.layers) == 3
    assert doc.layers[1] is l_mid
    assert doc.active_layer_index == 1

    # Remove active layer
    removed = doc.remove_active_layer()
    assert removed is True
    assert len(doc.layers) == 2
    assert doc.active_layer_index in (0, 1)


def test_document_layer_reordering():
    """Verify moving layers up and down."""
    doc = Document()
    doc.new_document(50, 50)
    doc.add_layer(name="L1")
    doc.add_layer(name="L2")
    assert [lay.name for lay in doc.layers] == ["Background", "L1", "L2"]
    assert doc.active_layer_index == 2

    # Move active layer down (L2 goes from 2 -> 1)
    assert doc.move_layer_down() is True
    assert [lay.name for lay in doc.layers] == ["Background", "L2", "L1"]
    assert doc.active_layer_index == 1

    # Move active layer up (L2 goes from 1 -> 2)
    assert doc.move_layer_up() is True
    assert [lay.name for lay in doc.layers] == ["Background", "L1", "L2"]
    assert doc.active_layer_index == 2


def test_document_dirty_state_lifecycle():
    """Verify clean -> edit -> modified -> undo -> clean cycle."""
    doc = Document()
    doc.new_document(40, 40)
    assert doc.modified is False
    assert doc.is_modified is False

    # Rotate modifies document
    doc.rotate_document()
    assert doc.modified is True
    assert doc.is_modified is True

    # Undo restores clean state
    assert doc.undo() is True
    assert doc.modified is False

    # Redo sets modified again
    assert doc.redo() is True
    assert doc.modified is True


def test_document_empty_and_single_layer_boundaries():
    """Ensure boundary operations do not crash on single-layer or empty documents."""
    doc = Document()
    # Empty doc before initialization
    assert doc.has_image is False
    assert doc.active_layer is None
    assert doc.get_composite() is None
    assert doc.undo() is False
    assert doc.redo() is False
    assert doc.merge_down() is False

    # Initialize single layer
    doc.new_document(20, 20)
    # Cannot merge down single layer
    assert doc.merge_down() is False
    # Cannot move down bottom layer
    assert doc.move_layer_down() is False
    # Cannot move up top single layer
    assert doc.move_layer_up() is False


def test_document_snapshots_and_restoration():
    """Verify snapshot capture and atomic restoration."""
    doc = Document()
    doc.new_document(60, 60, (10, 20, 30, 255))
    doc.add_layer(Image.new("RGBA", (60, 60), (200, 100, 50, 255)), name="Layer 2")

    snap = doc.create_snapshot()
    assert snap["width"] == 60
    assert snap["height"] == 60
    assert len(snap["layer_stack"]) == 2

    # Mutate document
    doc.resize_document(120, 120)
    assert doc.width == 120
    assert doc.height == 120

    # Restore
    doc.restore_snapshot(snap)
    assert doc.width == 60
    assert doc.height == 60
    assert len(doc.layers) == 2
