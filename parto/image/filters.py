# parto/image/filters.py
"""
Parto v0.3.0 - Photographic & Visual Filters
NumPy-vectorized transformations preserving transparency.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, List
from PIL import Image, ImageFilter
import numpy as np

SUPPORTED_FILTERS: List[str] = [
    "grayscale",
    "sepia",
    "invert",
    "blur",
    "sharpen",
    "edge_detect",
    "emboss",
]


def filter_grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale while preserving alpha transparency."""
    if image.mode in ("RGBA", "LA"):
        alpha = image.split()[-1]
        gray = image.convert("L").convert("RGB")
        r, g, b = gray.split()
        return Image.merge("RGBA", (r, g, b, alpha))
    return image.convert("L").convert("RGB")


def filter_sepia(image: Image.Image) -> Image.Image:
    """NumPy-vectorized warm photographic Sepia filter preserving alpha."""
    has_alpha = image.mode in ("RGBA", "LA")
    alpha_channel: Optional[Image.Image] = None

    if has_alpha:
        alpha_channel = image.split()[-1]
        rgb = image.convert("RGB")
    else:
        rgb = image.convert("RGB")

    arr = np.array(rgb, dtype=np.float32)
    # Sepia transformation matrix
    # [R, G, B] * matrix.T
    sepia_matrix = np.array(
        [
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131],
        ],
        dtype=np.float32,
    )

    sepia_arr = np.dot(arr, sepia_matrix.T)
    np.clip(sepia_arr, 0, 255, out=sepia_arr)
    sepia_img = Image.fromarray(sepia_arr.astype(np.uint8), mode="RGB")

    if has_alpha and alpha_channel is not None:
        r, g, b = sepia_img.split()
        return Image.merge("RGBA", (r, g, b, alpha_channel))

    return sepia_img


def filter_invert(image: Image.Image) -> Image.Image:
    """Invert image colors (negative) while keeping alpha channel untouched."""
    has_alpha = image.mode in ("RGBA", "LA")
    alpha_channel: Optional[Image.Image] = None

    if has_alpha:
        alpha_channel = image.split()[-1]
        rgb = image.convert("RGB")
    else:
        rgb = image.convert("RGB")

    arr = np.array(rgb, dtype=np.uint8)
    inv_arr = 255 - arr
    inv_img = Image.fromarray(inv_arr, mode="RGB")

    if has_alpha and alpha_channel is not None:
        r, g, b = inv_img.split()
        return Image.merge("RGBA", (r, g, b, alpha_channel))

    return inv_img


def filter_blur(image: Image.Image, radius: float = 2.0) -> Image.Image:
    """Gaussian blur filter."""
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def filter_sharpen(image: Image.Image) -> Image.Image:
    """Sharpen filter."""
    return image.filter(ImageFilter.SHARPEN)


def filter_edge_detect(image: Image.Image) -> Image.Image:
    """Edge detection filter."""
    return image.filter(ImageFilter.FIND_EDGES)


def filter_emboss(image: Image.Image) -> Image.Image:
    """Emboss filter."""
    return image.filter(ImageFilter.EMBOSS)


def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
    """Dispatch filter application by name."""
    fn = filter_name.lower().strip()
    if fn == "grayscale":
        return filter_grayscale(image)
    elif fn == "sepia":
        return filter_sepia(image)
    elif fn == "invert":
        return filter_invert(image)
    elif fn == "blur":
        return filter_blur(image)
    elif fn == "sharpen":
        return filter_sharpen(image)
    elif fn in ("edge_detect", "edge", "find_edges"):
        return filter_edge_detect(image)
    elif fn == "emboss":
        return filter_emboss(image)
    return image
