# tests/regression/test_merge_down_visibility.py
"""
Regression Tests — Merge Down Visibility Combinations & Composite Invariance
Author & Maintainer: Ali Kamrani (علی کامرانی)

Validates all 4 visibility combinations during Merge Down:
1. Visible Upper over Visible Lower
2. Hidden Upper over Visible Lower (Critical regression scenario)
3. Visible Upper over Hidden Lower
4. Hidden Upper over Hidden Lower
"""

import numpy as np
import pytest
from PIL import Image

from parto.image.layers import LayerStack


def test_merge_down_visible_upper_visible_lower():
    """Both visible: layers flatten together and result remains visible."""
    stack = LayerStack(4, 4)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L0")
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 128)), name="L1")

    comp_before = stack.composite()
    merged = stack.merge_down(1)
    assert merged is not None
    assert merged.visible is True

    comp_after = stack.composite()
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1


def test_merge_down_hidden_upper_visible_lower_normal():
    """
    Hidden upper layer: contributes zero pixels to the visible composite.
    The merged layer preserves the lower layer's appearance.
    """
    stack = LayerStack(4, 4)
    # L0: Blue background
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 0, 255, 255)), name="L0")
    # L1: Visible lower (Red)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L1")
    # L2: Hidden upper (Green)
    l2 = stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L2")
    l2.visible = False

    comp_before = stack.composite()
    # Before merge: L2 is hidden -> composite is pure Red
    assert comp_before.getpixel((0, 0)) == (255, 0, 0, 255)

    merged = stack.merge_down(2)
    assert merged is not None
    assert merged.visible is True

    comp_after = stack.composite()
    # After merge: must still be pure Red
    assert comp_after.getpixel((0, 0)) == (255, 0, 0, 255)


def test_critical_regression_hidden_upper_lower_non_normal_blend_mode():
    """
    CRITICAL REGRESSION SCENARIO:
    Upper layer is HIDDEN, Lower layer has NON-NORMAL blend mode (e.g. multiply).
    Merging upper into lower must preserve the exact visual composite before and after merge.
    Lower layer must KEEP its blend mode so it continues to blend properly with layers beneath it!
    """
    stack = LayerStack(4, 4)
    # L0: Gray background (128, 128, 128, 255)
    stack.add_layer(Image.new("RGBA", (4, 4), (128, 128, 128, 255)), name="L0", blend_mode="normal")
    # L1: Red multiply layer (255, 0, 0, 255)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L1", blend_mode="multiply")
    # L2: Hidden normal upper layer (0, 255, 0, 255)
    l2 = stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L2", blend_mode="normal")
    l2.visible = False

    comp_before = stack.composite()
    # Gray (128) * Red (255, 0, 0) / 255 = (128, 0, 0, 255)
    assert comp_before.getpixel((0, 0)) == (128, 0, 0, 255)

    merged = stack.merge_down(2)
    assert merged is not None
    assert merged.visible is True
    # Merged layer must retain multiply blend mode
    assert merged.blend_mode == "multiply"

    comp_after = stack.composite()
    # Visual appearance must be strictly preserved
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1, f"Visual mismatch on hidden upper + multiply lower: diff={diff}"
    assert comp_after.getpixel((0, 0)) == (128, 0, 0, 255)


def test_merge_down_visible_upper_hidden_lower():
    """
    Visible upper over hidden lower: lower contributed no pixels,
    so merged layer adopts upper's pixels, blend mode, and becomes visible.
    """
    stack = LayerStack(4, 4)
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 255, 255, 255)), name="L0")
    l1 = stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L1")
    l1.visible = False
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L2", blend_mode="multiply")

    comp_before = stack.composite()
    merged = stack.merge_down(2)
    assert merged.visible is True
    assert merged.blend_mode == "multiply"

    comp_after = stack.composite()
    diff = np.max(np.abs(np.array(comp_before, dtype=np.int16) - np.array(comp_after, dtype=np.int16)))
    assert diff <= 1


def test_merge_down_both_hidden():
    """Both hidden: internal buffers composite but resulting layer remains hidden."""
    stack = LayerStack(4, 4)
    l0 = stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 255)), name="L0")
    l0.visible = False
    l1 = stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), name="L1")
    l1.visible = False

    merged = stack.merge_down(1)
    assert merged.visible is False
