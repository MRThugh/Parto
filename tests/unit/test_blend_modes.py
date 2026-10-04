# tests/unit/test_blend_modes.py
"""
Unit Tests — Blend Mode Compositing & Mathematical Rigor
Author & Maintainer: Ali Kamrani (علی کامرانی)

Tests deterministic 2x2 and 4x4 RGBA swatches against exact mathematical formulas:
- Normal (Source-Over)
- Multiply: B(Cb, Cs) = Cb * Cs
- Screen: B(Cb, Cs) = 1 - (1 - Cb) * (1 - Cs)
- Overlay: B(Cb, Cs) = 2 * Cb * Cs if Cb < 0.5 else 1 - 2 * (1 - Cb) * (1 - Cs)
- Darken: B(Cb, Cs) = min(Cb, Cs)
- Lighten: B(Cb, Cs) = max(Cb, Cs)
"""

import numpy as np
import pytest
from PIL import Image
from parto.image.layers import LayerStack, compose_layers, Layer


def test_blend_mode_normal_source_over():
    """Verify standard alpha compositing (source-over) for normal blend mode."""
    # Red background (255, 0, 0, 255)
    base = Layer(image=Image.new("RGBA", (2, 2), (255, 0, 0, 255)), blend_mode="normal")
    # 50% semi-transparent Blue top (0, 0, 255, 128)
    top = Layer(image=Image.new("RGBA", (2, 2), (0, 0, 255, 128)), blend_mode="normal")

    comp = compose_layers([base, top], (2, 2))
    px = comp.getpixel((0, 0))

    # Expected: Red*(1 - 128/255) ~ 127, Green=0, Blue=128, Alpha=255
    assert abs(px[0] - 127) <= 1
    assert px[1] == 0
    assert abs(px[2] - 128) <= 1
    assert px[3] == 255


def test_blend_mode_multiply_opaque():
    """
    Verify Multiply blend mode with opaque layers:
    Formula: Out = Base * Top / 255
    (200, 100, 50) * (128, 128, 128) / 255 = (100, 50, 25)
    """
    stack = LayerStack(2, 2)
    stack.add_layer(Image.new("RGBA", (2, 2), (200, 100, 50, 255)), name="Base", blend_mode="normal")
    stack.add_layer(Image.new("RGBA", (2, 2), (128, 128, 128, 255)), name="Top", blend_mode="multiply")

    comp = stack.composite()
    px = comp.getpixel((0, 0))

    expected_r = int(round(200 * 128 / 255))
    expected_g = int(round(100 * 128 / 255))
    expected_b = int(round(50 * 128 / 255))

    assert abs(px[0] - expected_r) <= 1
    assert abs(px[1] - expected_g) <= 1
    assert abs(px[2] - expected_b) <= 1
    assert px[3] == 255


def test_blend_mode_screen_opaque():
    """
    Verify Screen blend mode with opaque layers:
    Formula: Out = 255 - ((255 - Base) * (255 - Top) / 255)
    """
    base_color = (100, 150, 200)
    top_color = (80, 120, 160)

    stack = LayerStack(2, 2)
    stack.add_layer(Image.new("RGBA", (2, 2), base_color + (255,)), name="Base", blend_mode="normal")
    stack.add_layer(Image.new("RGBA", (2, 2), top_color + (255,)), name="Top", blend_mode="screen")

    comp = stack.composite()
    px = comp.getpixel((0, 0))

    expected = tuple(
        int(round(255 - ((255 - b) * (255 - t) / 255.0)))
        for b, t in zip(base_color, top_color)
    )

    for i in range(3):
        assert abs(px[i] - expected[i]) <= 1
    assert px[3] == 255


def test_blend_mode_overlay_opaque():
    """
    Verify Overlay blend mode:
    If Base < 128: 2 * Base * Top / 255
    If Base >= 128: 255 - 2 * (255 - Base) * (255 - Top) / 255
    """
    stack = LayerStack(2, 2)
    # Channel 0: 64 (< 128), Channel 1: 192 (>= 128)
    stack.add_layer(Image.new("RGBA", (2, 2), (64, 192, 128, 255)), name="Base", blend_mode="normal")
    stack.add_layer(Image.new("RGBA", (2, 2), (100, 100, 100, 255)), name="Top", blend_mode="overlay")

    comp = stack.composite()
    px = comp.getpixel((0, 0))

    # Channel 0: 2 * 64 * 100 / 255 ~ 50
    exp_r = int(round(2.0 * (64 / 255.0) * (100 / 255.0) * 255.0))
    # Channel 1: 255 - 2 * (255 - 192) * (255 - 100) / 255 ~ 178
    exp_g = int(round((1.0 - 2.0 * (1.0 - 192 / 255.0) * (1.0 - 100 / 255.0)) * 255.0))

    assert abs(px[0] - exp_r) <= 1
    assert abs(px[1] - exp_g) <= 1
    assert px[3] == 255


def test_blend_mode_darken_and_lighten():
    """Verify Darken (min) and Lighten (max) per-channel blending."""
    stack = LayerStack(2, 2)
    stack.add_layer(Image.new("RGBA", (2, 2), (180, 50, 120, 255)), name="Base", blend_mode="normal")
    stack.add_layer(Image.new("RGBA", (2, 2), (100, 150, 80, 255)), name="Top", blend_mode="darken")

    comp_darken = stack.composite()
    px_dark = comp_darken.getpixel((0, 0))
    assert px_dark == (100, 50, 80, 255)

    # Change to lighten
    stack[1].blend_mode = "lighten"
    comp_lighten = stack.composite()
    px_light = comp_lighten.getpixel((0, 0))
    assert px_light == (180, 150, 120, 255)


def test_blend_mode_transparent_backdrop_preserves_top():
    """
    Verify Porter-Duff W3C composite over transparent backdrop (alpha=0)
    preserves source image values without clipping to black.
    """
    stack = LayerStack(4, 4)
    # Transparent base
    stack.add_layer(Image.new("RGBA", (4, 4), (0, 0, 0, 0)), name="Base", blend_mode="normal")
    # Top with multiply mode
    stack.add_layer(Image.new("RGBA", (4, 4), (200, 120, 40, 200)), name="Top", blend_mode="multiply")

    comp = stack.composite()
    px = comp.getpixel((0, 0))

    assert abs(px[0] - 200) <= 1
    assert abs(px[1] - 120) <= 1
    assert abs(px[2] - 40) <= 1
    assert abs(px[3] - 200) <= 1
