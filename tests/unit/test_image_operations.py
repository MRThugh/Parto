# tests/unit/test_image_operations.py
"""
Unit Tests — Image Transformations, Filters & Color Adjustments
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import numpy as np
import pytest
from PIL import Image

from parto.image.transforms import (
    rotate_90,
    rotate_180,
    rotate_custom,
    flip_horizontal,
    flip_vertical,
    resize_image,
    crop_image,
)
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
from parto.image.processing import apply_color_adjustments


def test_transform_rotate_90():
    """Verify 90-degree rotations swap dimensions and position pixels correctly."""
    # 30 wide x 20 high image with top-left red pixel
    img = Image.new("RGBA", (30, 20), (0, 0, 0, 255))
    img.putpixel((0, 0), (255, 0, 0, 255))

    cw = rotate_90(img, clockwise=True)
    assert cw.size == (20, 30)
    # Top-left (0,0) in 30x20 rotated 90 CW ends up at top-right (19, 0)
    assert cw.getpixel((19, 0)) == (255, 0, 0, 255)

    ccw = rotate_90(img, clockwise=False)
    assert ccw.size == (20, 30)
    # Top-left (0,0) rotated 90 CCW ends up at bottom-left (0, 29)
    assert ccw.getpixel((0, 29)) == (255, 0, 0, 255)


def test_transform_rotate_180():
    """Verify 180-degree rotation preserves dimensions and flips coordinates."""
    img = Image.new("RGBA", (40, 20), (0, 0, 0, 255))
    img.putpixel((0, 0), (0, 255, 0, 255))

    rot = rotate_180(img)
    assert rot.size == (40, 20)
    assert rot.getpixel((39, 19)) == (0, 255, 0, 255)


def test_transform_flip_horizontal_and_vertical():
    """Verify horizontal and vertical axis reflections."""
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 255))
    img.putpixel((0, 0), (255, 255, 0, 255))

    h = flip_horizontal(img)
    assert h.size == (20, 20)
    assert h.getpixel((19, 0)) == (255, 255, 0, 255)

    v = flip_vertical(img)
    assert v.size == (20, 20)
    assert v.getpixel((0, 19)) == (255, 255, 0, 255)


def test_transform_resize_image():
    """Verify resize_image with valid dimensions and resampling filters."""
    img = Image.new("RGBA", (50, 50), (100, 150, 200, 255))
    resized = resize_image(img, 100, 75, resample=Image.Resampling.LANCZOS)
    assert resized.size == (100, 75)
    assert resized.mode == "RGBA"

    # Clamping invalid sizes (<=0)
    clamped = resize_image(img, 0, -10)
    assert clamped.size == (1, 1)


def test_transform_crop_image_bounds_clamping():
    """Verify crop bounds clamping to avoid out-of-bounds crashes."""
    img = Image.new("RGBA", (100, 100), (50, 50, 50, 255))
    # Normal crop
    c1 = crop_image(img, (10, 10, 60, 60))
    assert c1.size == (50, 50)

    # Clamped out of bounds
    c2 = crop_image(img, (-20, -20, 200, 200))
    assert c2.size == (100, 100)


def test_photographic_filters_alpha_preservation():
    """Verify all supported filters preserve the alpha channel intact."""
    # 4-quadrant alpha test image
    arr = np.zeros((40, 40, 4), dtype=np.uint8)
    arr[0:20, 0:20] = [200, 100, 50, 255]
    arr[0:20, 20:40] = [100, 200, 50, 128]
    arr[20:40, 0:20] = [50, 100, 200, 64]
    arr[20:40, 20:40] = [0, 0, 0, 0]
    img = Image.fromarray(arr, mode="RGBA")
    orig_alpha = np.array(img)[:, :, 3]

    for filter_name in SUPPORTED_FILTERS:
        filtered = apply_filter(img, filter_name)
        assert filtered.mode == "RGBA"
        filtered_alpha = np.array(filtered)[:, :, 3]
        np.testing.assert_array_equal(
            filtered_alpha,
            orig_alpha,
            err_msg=f"Filter '{filter_name}' altered alpha channel!",
        )


def test_color_adjustments_math():
    """Verify brightness, contrast, saturation, and sharpness adjustments."""
    img = Image.new("RGB", (20, 20), (100, 100, 100))

    # Brightness increase (1.5)
    brighter = apply_color_adjustments(img, brightness=1.5)
    px_b = brighter.getpixel((0, 0))
    assert px_b[0] > 100

    # Brightness decrease (0.5)
    darker = apply_color_adjustments(img, brightness=0.5)
    px_d = darker.getpixel((0, 0))
    assert px_d[0] < 100

    # Neutral adjustments return equivalent pixels
    neutral = apply_color_adjustments(img, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0)
    assert neutral.getpixel((0, 0)) == (100, 100, 100)
