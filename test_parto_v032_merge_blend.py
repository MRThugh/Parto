# test_parto_v032_merge_blend.py
"""
Parto v0.3.2 - Final Stabilization Pass: Merge Down + Blend Mode Correctness
Author: Ali Kamrani (MRThugh)
Validates:
1. Merge Down when lower layer has non-normal blend mode (multiply, screen, overlay)
   preserves exact rendered composite without double-blending against background.
2. Merge Down resets lower.blend_mode to 'normal' when both layers are visible.
3. Merge Down when lower was hidden and upper visible inherits upper.blend_mode.
4. Merge Down when upper had blend mode composites onto lower and becomes normal.
5. Document Undo/Redo restores original layer blend modes and exact visual composites.
6. Merge Down with non-zero offsets and blend modes preserves visual result.
"""

import numpy as np
import pytest
from PIL import Image

from parto.image.layers import Layer, LayerStack, compose_layers
from parto.editor.document import Document


# ============================================================================
# 1. CORE BUG REGRESSION: LOWER LAYER NON-NORMAL BLEND MODES
# ============================================================================

def test_merge_down_lower_multiply_preserves_composite():
    """
    Demonstrate that merging an upper layer down into a lower layer with
    blend_mode='multiply' does NOT re-multiply the flattened result against the
    background layers below.
    """
    stack = LayerStack(4, 4)

    # L0: Green background (0, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L0", blend_mode="normal")
    # L1: Gray multiply layer (128, 128, 128)
    stack.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="L1", blend_mode="multiply")
    # L2: Opaque Red normal layer (255, 0, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L2", blend_mode="normal")

    # Step 1: Capture composite BEFORE Merge Down
    comp_before = stack.composite()
    # Before merge down, L2 covers L1 completely -> composite must be pure red (255, 0, 0, 255)
    assert comp_before.getpixel((0, 0)) == (255, 0, 0, 255)

    # Step 2: Execute Merge Down on index 2 (merging L2 into L1)
    merged = stack.merge_down(2)
    assert merged is not None
    assert len(stack) == 2
    # The resulting layer must have blend_mode reset to 'normal' to avoid double-blending
    assert merged.blend_mode == "normal"

    # Step 3: Capture composite AFTER Merge Down
    comp_after = stack.composite()

    # Step 4: Validate visual equivalence within pixel tolerance
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1, f"Visual mismatch after merge down: max diff {np.max(diff)}"
    assert comp_after.getpixel((0, 0)) == (255, 0, 0, 255)


def test_merge_down_lower_screen_preserves_composite():
    """
    Merging an upper normal layer down into a lower screen layer preserves
    the rendered appearance over background.
    """
    stack = LayerStack(4, 4)
    # L0: Blue background (0, 0, 255)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 0, 255, 255)), name="L0", blend_mode="normal")
    # L1: Red screen layer (255, 0, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L1", blend_mode="screen")
    # L2: Opaque Green normal layer (0, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L2", blend_mode="normal")

    comp_before = stack.composite()
    assert comp_before.getpixel((0, 0)) == (0, 255, 0, 255)

    merged = stack.merge_down(2)
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1
    assert comp_after.getpixel((0, 0)) == (0, 255, 0, 255)


def test_merge_down_lower_overlay_preserves_composite():
    """
    Merging an upper layer down into a lower overlay layer preserves
    the rendered appearance over background.
    """
    stack = LayerStack(4, 4)
    # L0: Base
    stack.add_layer(Image.new("RGBA", (4, 4), (100, 150, 200, 255)), name="L0", blend_mode="normal")
    # L1: Overlay layer
    stack.add_layer(Image.new("RGBA", (4, 4), (200, 100, 50, 255)), name="L1", blend_mode="overlay")
    # L2: Normal layer
    stack.add_layer(Image.new("RGBA", (4, 4), (50, 200, 100, 255)), name="L2", blend_mode="normal")

    comp_before = stack.composite()
    merged = stack.merge_down(2)
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1


def test_merge_down_upper_multiply_lower_normal_preserves_composite():
    """
    Upper layer has multiply blend mode; merging into lower normal layer
    bakes the multiply effect and resets the merged layer to normal.
    """
    stack = LayerStack(4, 4)
    # L0: White background
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 255, 255)), name="L0", blend_mode="normal")
    # L1: Yellow (255, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 0, 255)), name="L1", blend_mode="normal")
    # L2: Cyan (0, 255, 255), Multiply -> Yellow * Cyan = Green (0, 255, 0)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 255, 255)), name="L2", blend_mode="multiply")

    comp_before = stack.composite()
    assert comp_before.getpixel((0, 0)) == (0, 255, 0, 255)

    merged = stack.merge_down(2)
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1
    assert comp_after.getpixel((0, 0)) == (0, 255, 0, 255)


# ============================================================================
# 2. VISIBILITY & BLEND MODE SEMANTICS
# ============================================================================

def test_merge_down_hidden_lower_preserves_upper_blend_mode():
    """
    When lower is hidden and upper is visible, lower contributes no pixels.
    The resulting layer must inherit upper's blend_mode to preserve its
    blend behavior against layers below.
    """
    stack = LayerStack(4, 4)
    # L0: White background
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 255, 255)), name="L0", blend_mode="normal")
    # L1: Hidden lower layer
    l1 = stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L1", blend_mode="normal")
    l1.visible = False
    # L2: Visible upper layer with multiply
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L2", blend_mode="multiply")

    comp_before = stack.composite()
    merged = stack.merge_down(2)
    assert merged.visible is True
    # Inherits upper's multiply blend mode
    assert merged.blend_mode == "multiply"

    comp_after = stack.composite()
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1


def test_merge_down_with_offsets_and_blend_modes():
    """
    Merging offset layers with blend modes preserves canvas-space positioning
    and rendered output.
    """
    stack = LayerStack(8, 8)
    # L0: White background
    stack.add_layer(Image.new("RGBA", (8, 8), (255, 255, 255, 255)), name="L0", blend_mode="normal")
    # L1: 4x4 layer at offset (1, 1), multiply
    stack.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="L1", offset_x=1, offset_y=1, blend_mode="multiply")
    # L2: 4x4 layer at offset (3, 3), normal
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L2", offset_x=3, offset_y=3, blend_mode="normal")

    comp_before = stack.composite()
    merged = stack.merge_down(2)
    assert merged.offset_x == 0
    assert merged.offset_y == 0
    assert merged.blend_mode == "normal"

    comp_after = stack.composite()
    diff = np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16))
    assert np.max(diff) <= 1


# ============================================================================
# 3. DOCUMENT UNDO / REDO HISTORY RESTORATION
# ============================================================================

def test_document_merge_down_undo_redo_blend_modes():
    """
    Document-level merge down records history and undo accurately restores
    the original layers, their blend modes, and the initial composite.
    """
    doc = Document()
    doc.new_document(4, 4)

    # Initial layer (index 0) - background
    doc.layers[0].image = Image.new("RGBA", (4, 4), (0, 255, 0, 255))
    doc.layers[0].name = "Background"

    # Layer 1: Gray multiply
    l1 = doc.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="MultiplyLayer", blend_mode="multiply")

    # Layer 2: Red normal
    l2 = doc.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="RedLayer", blend_mode="normal")

    comp_initial = doc.get_composite().copy()
    assert comp_initial.getpixel((0, 0)) == (255, 0, 0, 255)

    # Merge Down Layer 2 into Layer 1
    assert doc.merge_down() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].blend_mode == "normal"

    comp_merged = doc.get_composite()
    diff_merged = np.abs(np.array(comp_initial, dtype=np.int16) - np.array(comp_merged, dtype=np.int16))
    assert np.max(diff_merged) <= 1

    # Undo
    assert doc.undo() is True
    assert len(doc.layers) == 3
    assert doc.layers[1].blend_mode == "multiply"
    assert doc.layers[2].blend_mode == "normal"
    comp_undone = doc.get_composite()
    diff_undone = np.abs(np.array(comp_initial, dtype=np.int16) - np.array(comp_undone, dtype=np.int16))
    assert np.max(diff_undone) <= 1

    # Redo
    assert doc.redo() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].blend_mode == "normal"
    comp_redone = doc.get_composite()
    diff_redone = np.abs(np.array(comp_merged, dtype=np.int16) - np.array(comp_redone, dtype=np.int16))
    assert np.max(diff_redone) <= 1
