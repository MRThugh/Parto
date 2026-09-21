# parto/image/transforms.py
"""
Parto v0.3.0 - Image Transformation Routines
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple
from PIL import Image


def rotate_90(image: Image.Image, clockwise: bool = True) -> Image.Image:
    """Rotate image by 90 degrees clockwise or counter-clockwise."""
    method = Image.Transpose.ROTATE_270 if clockwise else Image.Transpose.ROTATE_90
    return image.transpose(method)


def rotate_180(image: Image.Image) -> Image.Image:
    """Rotate image by 180 degrees."""
    return image.transpose(Image.Transpose.ROTATE_180)


def rotate_custom(image: Image.Image, angle_degrees: float, expand: bool = True) -> Image.Image:
    """Rotate image by arbitrary angle degrees."""
    resample = getattr(Image, "Resampling", Image).BICUBIC
    return image.rotate(-angle_degrees, resample=resample, expand=expand)


def flip_horizontal(image: Image.Image) -> Image.Image:
    """Flip image horizontally (left to right)."""
    return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def flip_vertical(image: Image.Image) -> Image.Image:
    """Flip image vertically (top to bottom)."""
    return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def resize_image(
    image: Image.Image,
    width: int,
    height: int,
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """Resize image with high-quality resampling (default Lanczos)."""
    w = max(1, int(width))
    h = max(1, int(height))
    return image.resize((w, h), resample=resample)


def crop_image(image: Image.Image, rect: Tuple[int, int, int, int]) -> Image.Image:
    """
    Crop image to rectangle (left, top, right, bottom).
    Clamps bounds safely within [0, 0, width, height].
    """
    left, top, right, bottom = rect
    x1 = max(0, min(int(left), image.width - 1))
    y1 = max(0, min(int(top), image.height - 1))
    x2 = max(x1 + 1, min(int(right), image.width))
    y2 = max(y1 + 1, min(int(bottom), image.height))
    return image.crop((x1, y1, x2, y2))
