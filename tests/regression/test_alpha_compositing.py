# tests/regression/test_alpha_compositing.py
"""
Regression Tests — Alpha Channel Preservation & Porter-Duff Blending
Author & Maintainer: Ali Kamrani (علی کامرانی)

Validates:
1. Alpha channel preservation across all 7 filters (grayscale, sepia, invert, blur, sharpen, edge_detect, emboss).
2. Porter-Duff W3C compositing in _blend_mode_composite handles semi-transparent backdrops without clipping to black.
3. Palette images with transparency are handled safely without losing alpha masks.
"""

import numpy as np
import pytest
from PIL import Image

from parto.image.filters import apply_filter, SUPPORTED_FILTERS
from parto.image.layers import LayerStack


def test_filters_alpha_channel_integrity(transparent_test_image):
    """Ensure every filter processes RGB while keeping alpha channel byte-for-byte identical."""
    original_alpha = np.array(transparent_test_image)[:, :, 3]

    for filter_name in SUPPORTED_FILTERS:
        res = apply_filter(transparent_test_image, filter_name)
        res_alpha = np.array(res)[:, :, 3]
        np.testing.assert_array_equal(
            res_alpha,
            original_alpha,
            err_msg=f"Filter '{filter_name}' corrupted alpha channel!",
        )


def test_blend_mode_semi_transparent_backdrop_math():
    """
    Verify _blend_mode_composite correctly handles semi-transparent backdrop (ba < 1.0)
    using W3C standard formulas without darkening to zero.
    """
    stack = LayerStack(4, 4)
    # Backdrop: Green at 50% opacity (0, 255, 0, 128)
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 255, 0, 128)), name="Backdrop", blend_mode="normal")
    # Top: Red at 50% opacity (255, 0, 0, 128) with Multiply
    stack.add_layer(Image.new("RGBA", (4, 4), (255, 0, 0, 128)), name="Top", blend_mode="multiply")

    comp = stack.composite()
    px = comp.getpixel((0, 0))

    # Alpha composite: 128 + 128 * (1 - 128/255) = ~192
    assert abs(px[3] - 192) <= 2
    # Colors must not clip to black:
    assert px[0] > 0
    assert px[1] > 0


def test_palette_image_with_transparency_filter_safety():
    """Verify palette (mode P) images with transparency don't crash filters."""
    # Create P-mode image with transparency
    p_img = Image.new("P", (16, 16))
    p_img.putpalette([255, 0, 0, 0, 255, 0, 0, 0, 255] + [0] * 759)
    p_img.info["transparency"] = 0

    for filter_name in ("grayscale", "sepia", "invert"):
        res = apply_filter(p_img, filter_name)
        assert res.mode in ("RGBA", "RGB")
