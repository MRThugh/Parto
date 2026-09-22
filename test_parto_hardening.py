# test_parto_hardening.py
"""
Parto v0.3.0 - Hardening, Stabilization & Single-Source-of-Truth Test Suite
Verifies:
1. Document and LayerStack unified state representation.
2. EditorEngine delegation to Document without state duplication.
3. Alpha channel preservation across all filters (blur, sharpen, edge_detect, emboss, sepia, invert, grayscale).
4. Palette image robustness.
5. Error handling and boundary conditions.
Author: Ali Kamrani (MRThugh)
"""

import os
import pytest
from PIL import Image
import numpy as np

from parto.editor.document import Document
from parto.editor.engine import EditorEngine
from parto.image.layers import Layer, LayerStack
from parto.image.filters import (
    apply_filter,
    filter_grayscale,
    filter_sepia,
    filter_invert,
    filter_blur,
    filter_sharpen,
    filter_edge_detect,
    filter_emboss,
    SUPPORTED_FILTERS,
)


@pytest.fixture
def transparent_test_image():
    """Create a 100x100 test image with distinct alpha channel."""
    arr = np.zeros((100, 100, 4), dtype=np.uint8)
    # Red quadrant with 255 alpha
    arr[0:50, 0:50] = [255, 0, 0, 255]
    # Green quadrant with 128 alpha
    arr[0:50, 50:100] = [0, 255, 0, 128]
    # Blue quadrant with 64 alpha
    arr[50:100, 0:50] = [0, 0, 255, 64]
    # Transparent quadrant with 0 alpha
    arr[50:100, 50:100] = [0, 0, 0, 0]
    return Image.fromarray(arr, mode="RGBA")


# ============================================================================
# 1. DOCUMENT & LAYERSTACK SINGLE SOURCE OF TRUTH
# ============================================================================

def test_document_layerstack_identity():
    """Verify Document delegates layer management authoritatively to LayerStack."""
    doc = Document()
    doc.new_document(400, 300)
    assert doc.has_image
    assert len(doc.layer_stack) == 1
    assert doc.layers is doc.layer_stack.layers
    assert doc.active_layer is doc.layer_stack.active_layer

    # Add a layer through document
    lay2 = doc.add_layer("Overlay")
    assert len(doc.layer_stack) == 2
    assert doc.layer_stack.active_index == 1
    assert doc.active_layer == lay2

    # Duplicate active layer
    dup = doc.duplicate_active_layer()
    assert len(doc.layer_stack) == 3
    assert doc.active_layer == dup

    # Remove active layer
    assert doc.remove_active_layer() is True
    assert len(doc.layer_stack) == 2


def test_document_layerstack_dimensions_on_transform():
    """Verify LayerStack dimensions sync during resize and crop."""
    doc = Document()
    doc.new_document(400, 200)
    assert doc.layer_stack.width == 400
    assert doc.layer_stack.height == 200

    # Resize
    doc.resize_document(200, 100)
    assert doc.width == 200
    assert doc.height == 100
    assert doc.layer_stack.width == 200
    assert doc.layer_stack.height == 100

    # Crop
    doc.crop_document((10, 10, 60, 50))
    assert doc.width == 50
    assert doc.height == 40
    assert doc.layer_stack.width == 50
    assert doc.layer_stack.height == 40


# ============================================================================
# 2. EDITORENGINE DELEGATION & ZERO-STATE-DUPLICATION
# ============================================================================

def test_engine_delegates_to_document():
    """Verify EditorEngine acts as a direct proxy to Document."""
    doc = Document()
    doc.new_document(150, 120)
    engine = EditorEngine(document=doc)

    assert engine.document is doc
    assert engine.current_image is not None
    assert engine.current_image.size == (150, 120)

    # Engine transformation modifies Document state
    engine.rotate_left()
    assert doc.width == 120
    assert doc.height == 150
    assert engine.current_image.size == (120, 150)

    # Undo through engine restores Document state
    assert engine.can_undo is True
    assert engine.undo() is True
    assert doc.width == 150
    assert doc.height == 120
    assert engine.current_image.size == (150, 120)


def test_engine_history_stack_access():
    """Verify EditorEngine undo_stack and redo_stack reflect Document history."""
    doc = Document()
    doc.new_document(100, 100)
    engine = EditorEngine(document=doc, max_history=10)

    assert len(engine.undo_stack) == 0
    assert len(engine.redo_stack) == 0

    engine.rotate_right()
    assert len(engine.undo_stack) == 1
    assert engine.can_undo is True

    engine.undo()
    assert len(engine.undo_stack) == 0
    assert len(engine.redo_stack) == 1
    assert engine.can_redo is True

    engine.redo()
    assert len(engine.undo_stack) == 1
    assert len(engine.redo_stack) == 0


# ============================================================================
# 3. ALPHA CHANNEL PRESERVATION IN FILTERS
# ============================================================================

@pytest.mark.parametrize("filter_name", [
    "grayscale",
    "sepia",
    "invert",
    "blur",
    "sharpen",
    "edge_detect",
    "emboss",
])
def test_filter_preserves_alpha(transparent_test_image, filter_name):
    """Verify that all supported filters retain full alpha transparency fidelity."""
    original_alpha = np.array(transparent_test_image.split()[-1])
    filtered = apply_filter(transparent_test_image, filter_name)

    assert filtered.mode == "RGBA", f"Filter {filter_name} lost RGBA mode"
    filtered_alpha = np.array(filtered.split()[-1])

    # Ensure alpha was not discarded or replaced with solid 255
    assert np.array_equal(filtered_alpha, original_alpha), f"Filter {filter_name} modified the alpha channel"


def test_palette_image_filter_handling():
    """Verify palette mode images are filtered without errors."""
    img = Image.new("P", (50, 50))
    for f in SUPPORTED_FILTERS:
        res = apply_filter(img, f)
        assert res is not None
        assert res.size == (50, 50)


# ============================================================================
# 4. ERROR HANDLING & BOUNDARY STABILITY
# ============================================================================

def test_document_load_missing_file_raises():
    """Verify Document.load_file with raise_on_error=True raises FileNotFoundError."""
    doc = Document()
    with pytest.raises(FileNotFoundError):
        doc.load_file("/non/existent/path/parto_test.png", raise_on_error=True)


def test_engine_save_empty_raises():
    """Verify EditorEngine.save_image on empty document raises ValueError."""
    doc = Document()
    engine = EditorEngine(document=doc)
    with pytest.raises(ValueError, match="No active image"):
        engine.save_image("/tmp/unused.png")
