# tests/regression/test_merge_down_blend_modes.py
"""
Regression Tests — Merge Down Blend Mode Math & Double-Blending Prevention
Author & Maintainer: Ali Kamrani (علی کامرانی)

Validates:
1. Merge Down resets lower.blend_mode = "normal" when both layers are visible,
   preventing the flattened result from double-blending against background layers.
2. Merging upper layer with multiply/screen/overlay bakes into lower normal layer.
3. Undo/Redo restores original blend modes and exact visual composites.
"""

import numpy as np
import pytest
from PIL import Image

from parto.image.layers import LayerStack
from parto.editor.document import Document


def test_merge_down_lower_multiply_preserves_composite():
    """
    Verify merging an upper normal layer into a lower multiply layer does NOT
    re-multiply the flattened result against background layers below.
    """
    stack = LayerStack(4, 4)
    # L0: Green background (0, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L0", blend_mode="normal")
    # L1: Gray multiply layer (128, 128, 128)
    stack.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="L1", blend_mode="multiply")
    # L2: Opaque Red normal layer (255, 0, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L2", blend_mode="normal")

    comp_before = stack.composite()
    assert comp_before.getpixel((0, 0)) == (255, 0, 0, 255)

    merged = stack.merge_down(2)
    assert merged is not None
    assert len(stack) == 2
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1
    assert comp_after.getpixel((0, 0)) == (255, 0, 0, 255)


def test_merge_down_lower_screen_preserves_composite():
    """Merging upper normal layer into lower screen layer preserves appearance over background."""
    stack = LayerStack(4, 4)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 0, 255, 255)), name="L0", blend_mode="normal")
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L1", blend_mode="screen")
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L2", blend_mode="normal")

    comp_before = stack.composite()
    assert comp_before.getpixel((0, 0)) == (0, 255, 0, 255)

    merged = stack.merge_down(2)
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1
    assert comp_after.getpixel((0, 0)) == (0, 255, 0, 255)


def test_merge_down_upper_multiply_lower_normal():
    """Upper layer has multiply mode; merging into lower normal bakes the multiply."""
    stack = LayerStack(4, 4)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 255, 255)), name="L0")
    # Yellow
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 0, 255)), name="L1")
    # Cyan with multiply -> Yellow * Cyan = Green (0, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 255, 255)), name="L2", blend_mode="multiply")

    comp_before = stack.composite()
    assert comp_before.getpixel((0, 0)) == (0, 255, 0, 255)

    merged = stack.merge_down(2)
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1
    assert comp_after.getpixel((0, 0)) == (0, 255, 0, 255)


def test_document_merge_down_undo_redo_preserves_blend_modes():
    """Document undo/redo restores original layer blend modes and pixel fidelity."""
    doc = Document()
    doc.new_document(4, 4)
    doc.layers[0].image = Image.new("RGBA", (4, 4), (0, 255, 0, 255))
    doc.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="MultiplyLayer", blend_mode="multiply")
    doc.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="RedLayer", blend_mode="normal")

    comp_initial = doc.get_composite().copy()

    # Merge Down
    assert doc.merge_down() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].blend_mode == "normal"

    # Undo
    assert doc.undo() is True
    assert len(doc.layers) == 3
    assert doc.layers[1].blend_mode == "multiply"
    assert doc.layers[2].blend_mode == "normal"
    comp_undone = doc.get_composite()
    diff_undone = np.max(np.abs(np.array(comp_initial, dtype=np.int16) - np.array(comp_undone, dtype=np.int16)))
    assert diff_undone <= 1

    # Redo
    assert doc.redo() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].blend_mode == "normal"
