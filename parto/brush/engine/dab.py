# parto/brush/engine/dab.py
"""
Parto Brush System — Dab Generation and Caching
Pure Python, NumPy and Pillow rasterization. Zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Tuple, Any
import numpy as np
from PIL import Image
from ..models.settings import BrushSettings


class DabGenerator:
    """
    Renders high-quality circular brush dabs with configurable radial hardness falloff.
    Caches the most recently generated dab for rapid successive stamping.
    """

    def __init__(self):
        self._cached_dab: Optional[Image.Image] = None
        self._cached_key: Optional[Tuple[Any, ...]] = None

    def invalidate(self) -> None:
        """Clear cached dab buffer."""
        self._cached_dab = None
        self._cached_key = None

    def generate_dab(self, settings: BrushSettings) -> Image.Image:
        """
        Generate or retrieve a cached circular brush dab RGBA buffer.
        """
        flow = getattr(settings, "flow", 1.0)
        is_eraser = getattr(settings, "is_eraser", False)
        key = (
            settings.size,
            round(settings.hardness, 2),
            round(settings.opacity, 3),
            round(flow, 3),
            settings.color,
            is_eraser,
        )

        if self._cached_dab is not None and self._cached_key == key:
            return self._cached_dab

        D = max(1, settings.size)
        R = D / 2.0
        y, x = np.ogrid[:D, :D]
        dist = np.hypot(x - (R - 0.5), y - (R - 0.5))

        inner_r = R * max(0.0, min(1.0, settings.hardness))
        mask = np.zeros((D, D), dtype=np.float32)

        if R <= inner_r or R <= 0.5:
            mask[dist <= R] = 1.0
        else:
            mask[dist <= inner_r] = 1.0
            falloff = (dist > inner_r) & (dist <= R)
            mask[falloff] = 1.0 - (dist[falloff] - inner_r) / (R - inner_r)

        effective_alpha = settings.color[3] * settings.opacity * flow
        alpha_channel = (mask * effective_alpha).clip(0, 255).astype(np.uint8)

        dab_arr = np.zeros((D, D, 4), dtype=np.uint8)
        dab_arr[:, :, 0] = settings.color[0]
        dab_arr[:, :, 1] = settings.color[1]
        dab_arr[:, :, 2] = settings.color[2]
        dab_arr[:, :, 3] = alpha_channel

        self._cached_dab = Image.fromarray(dab_arr, mode="RGBA")
        self._cached_key = key
        return self._cached_dab
