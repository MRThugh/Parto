# tests/unit/test_compositing.py
"""
Unit Tests — Image Rendering & Layer Compositing Engine
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import numpy as np
import pytest
from PIL import Image
from parto.image.layers import Layer, compose_layers


def test_compositing_layer_ordering():
    """Verify layers composite strictly from bottom (index 0) to top (index N-1)."""
    l0 = Layer(name="Bottom", image=Image.new("RGBA", (10, 10), (255, 0, 0, 255)))
    l1 = Layer(name="Middle", image=Image.new("RGBA", (10, 10), (0, 255, 0, 255)))
    l2 = Layer(name="Top", image=Image.new("RGBA", (10, 10), (0, 0, 255, 255)))

    # All opaque: top layer (Blue) covers everything
    comp = compose_layers([l0, l1, l2], (10, 10))
    assert comp.getpixel((0, 0)) == (0, 0, 255, 255)


def test_compositing_visibility_toggle():
    """Verify hidden layers contribute zero pixels to composite."""
    l0 = Layer(name="Bottom", image=Image.new("RGBA", (10, 10), (255, 0, 0, 255)))
    l1 = Layer(name="Top", image=Image.new("RGBA", (10, 10), (0, 255, 0, 255)), visible=False)

    comp = compose_layers([l0, l1], (10, 10))
    # Top is hidden -> result is pure Red from Bottom
    assert comp.getpixel((0, 0)) == (255, 0, 0, 255)


def test_compositing_layer_opacity_scaling():
    """Verify layer opacity scales the alpha channel before blending."""
    l0 = Layer(name="WhiteBg", image=Image.new("RGBA", (10, 10), (255, 255, 255, 255)))
    # Black layer with 50% opacity (0.5)
    l1 = Layer(name="Black50", image=Image.new("RGBA", (10, 10), (0, 0, 0, 255)), opacity=0.5)

    comp = compose_layers([l0, l1], (10, 10))
    px = comp.getpixel((0, 0))
    # 255 * (1 - 0.5) = ~127
    assert abs(px[0] - 127) <= 1
    assert abs(px[1] - 127) <= 1
    assert abs(px[2] - 127) <= 1
    assert px[3] == 255


def test_compositing_clipping_and_offsets():
    """Verify layers rendered with offsets and canvas boundaries."""
    canvas_size = (20, 20)
    bg = Layer(image=Image.new("RGBA", canvas_size, (0, 0, 0, 255)))
    # 10x10 Red box placed at offset (5, 5)
    box = Layer(image=Image.new("RGBA", (10, 10), (255, 0, 0, 255)), offset_x=5, offset_y=5)

    comp = compose_layers([bg, box], canvas_size)

    # Outside box
    assert comp.getpixel((0, 0)) == (0, 0, 0, 255)
    assert comp.getpixel((19, 19)) == (0, 0, 0, 255)

    # Inside box
    assert comp.getpixel((5, 5)) == (255, 0, 0, 255)
    assert comp.getpixel((14, 14)) == (255, 0, 0, 255)


def test_compositing_source_image_immutability():
    """Verify compositing does not mutate the original layer image buffers."""
    source_img = Image.new("RGBA", (8, 8), (50, 100, 150, 200))
    original_bytes = source_img.tobytes()

    lay = Layer(image=source_img, opacity=0.7, blend_mode="multiply")
    _ = compose_layers([lay], (8, 8))

    # Original image buffer must be strictly untouched
    assert source_img.tobytes() == original_bytes
    assert lay.image.tobytes() == original_bytes
