# parto/editor/viewport.py
"""
Parto v0.3.0 - Viewport & Preview Downsampling Architecture
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple, Optional
from PIL import Image


class ViewportOptimizer:
    """
    Computes optimal display scales for large images and maps coordinates
    between viewport render buffers and underlying full-resolution layers.
    """

    MAX_PREVIEW_DIMENSION = 4096

    @classmethod
    def should_downsample(cls, width: int, height: int) -> bool:
        return width > cls.MAX_PREVIEW_DIMENSION or height > cls.MAX_PREVIEW_DIMENSION

    @classmethod
    def get_preview_scale(cls, width: int, height: int) -> float:
        """Returns 1.0 if image is normal sized, or < 1.0 if downsampling is required."""
        max_dim = max(width, height)
        if max_dim <= cls.MAX_PREVIEW_DIMENSION:
            return 1.0
        return cls.MAX_PREVIEW_DIMENSION / float(max_dim)

    @classmethod
    def create_preview_image(cls, image: Optional[Image.Image]) -> Optional[Image.Image]:
        """Generate high-speed preview representation for large canvases."""
        if image is None:
            return None

        scale = cls.get_preview_scale(image.width, image.height)
        if scale >= 0.999:
            return image

        target_w = max(1, int(image.width * scale))
        target_h = max(1, int(image.height * scale))
        return image.resize((target_w, target_h), Image.Resampling.BILINEAR)

    @classmethod
    def map_to_source(cls, pt: Tuple[float, float], scale: float) -> Tuple[int, int]:
        """Map preview coordinate back to full document source coordinate."""
        if scale <= 0:
            return int(pt[0]), int(pt[1])
        return int(round(pt[0] / scale)), int(round(pt[1] / scale))
