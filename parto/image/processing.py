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


def remove_background(
    image: Optional[Image.Image],
    tolerance: int = 28,
    feather_radius: int = 2,
) -> Optional[Image.Image]:
    """
    Remove the background from an image based on corner-sampled color distance and tolerance,
    with anti-aliased edge feathering.

    :param image: Input PIL Image
    :param tolerance: Color distance threshold (0 - 255) for background detection
    :param feather_radius: Radius for Gaussian alpha mask edge feathering (0 - 50)
    :return: RGBA PIL Image with transparent background
    """
    if image is None:
        return None

    from PIL import ImageFilter

    rgba = image.convert("RGBA")
    w, h = rgba.size
    if w == 0 or h == 0:
        return rgba

    # Sample corner pixels as candidate background colors
    corners = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
    ]

    arr = np.array(rgba)
    rgb = arr[:, :, :3].astype(np.float32)
    existing_alpha = arr[:, :, 3].astype(np.float32)

    corner_colors = [rgb[y, x] for x, y in corners]

    # Find minimum distance to any corner color across pixels
    min_dists = np.full((h, w), 1e9, dtype=np.float32)
    for c in corner_colors:
        dist = np.sqrt(np.sum((rgb - c) ** 2, axis=2))
        min_dists = np.minimum(min_dists, dist)

    # Pixels with distance > tolerance belong to the foreground
    # 255 = keep (foreground), 0 = remove (background)
    tol = max(1.0, float(tolerance))
    foreground_mask = (min_dists > tol).astype(np.float32) * 255.0

    # Combine with any preexisting alpha transparency
    combined_alpha = np.minimum(existing_alpha, foreground_mask).astype(np.uint8)

    alpha_mask_img = Image.fromarray(combined_alpha, mode="L")

    # Edge feathering via Gaussian blur on the alpha mask
    if feather_radius > 0:
        rad = max(0.5, float(feather_radius))
        alpha_mask_img = alpha_mask_img.filter(ImageFilter.GaussianBlur(radius=rad))

    r, g, b, _ = rgba.split()
    return Image.merge("RGBA", (r, g, b, alpha_mask_img))

