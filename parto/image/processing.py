# parto/image/processing.py
"""
Parto v0.3.0 - Image Processing & Color Adjustments
NumPy-accelerated and Pillow-enhanced adjustments preserving alpha transparency.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PIL import Image, ImageEnhance
import numpy as np


def apply_color_adjustments(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> Image.Image:
    """
    Apply brightness, contrast, saturation, and sharpness adjustments to an image.
    Fully preserves transparency (RGBA/LA).
    """
    if image is None:
        return image

    has_alpha = image.mode in ("RGBA", "LA")
    alpha_channel: Optional[Image.Image] = None

    if has_alpha:
        img_rgb = image.convert("RGB")
        alpha_channel = image.split()[-1]
    else:
        img_rgb = image.convert("RGB")

    # Brightness
    if abs(brightness - 1.0) > 0.001:
        enhancer = ImageEnhance.Brightness(img_rgb)
        img_rgb = enhancer.enhance(max(0.0, brightness))

    # Contrast
    if abs(contrast - 1.0) > 0.001:
        enhancer = ImageEnhance.Contrast(img_rgb)
        img_rgb = enhancer.enhance(max(0.0, contrast))

    # Saturation / Color
    if abs(saturation - 1.0) > 0.001:
        enhancer = ImageEnhance.Color(img_rgb)
        img_rgb = enhancer.enhance(max(0.0, saturation))

    # Sharpness
    if abs(sharpness - 1.0) > 0.001:
        enhancer = ImageEnhance.Sharpness(img_rgb)
        img_rgb = enhancer.enhance(max(0.0, sharpness))

    # Re-attach alpha if present
    if has_alpha and alpha_channel is not None:
        r, g, b = img_rgb.split()
        return Image.merge("RGBA", (r, g, b, alpha_channel))

    return img_rgb
