# parto/brush/engine/renderer.py
"""
Parto Brush System — Raster Renderer
Interpolates and composites brush dabs onto RGBA image buffers.
Pure Python, Pillow and NumPy. Zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import math
from typing import Optional, Tuple, Any
from PIL import Image
import numpy as np
from ..models.settings import BrushSettings
from .dab import DabGenerator


class BrushRenderer:
    """
    Handles dab rasterization and pixel compositing onto target RGBA image buffers.
    Supports continuous interpolation, custom spacing, opacity falloff, and eraser mode.
    """

    def __init__(self, dab_generator: Optional[DabGenerator] = None):
        self._generator = dab_generator or DabGenerator()

    # --- Backward-Compatible Cache Inspection ---

    @property
    def _cached_dab(self) -> Optional[Image.Image]:
        return self._generator._cached_dab

    @_cached_dab.setter
    def _cached_dab(self, val: Optional[Image.Image]) -> None:
        self._generator._cached_dab = val

    @property
    def _cached_dab_key(self) -> Optional[Tuple[Any, ...]]:
        return self._generator._cached_key

    @_cached_dab_key.setter
    def _cached_dab_key(self, val: Optional[Tuple[Any, ...]]) -> None:
        self._generator._cached_key = val

    def invalidate_cache(self) -> None:
        """Clear cached dab raster buffer."""
        self._generator.invalidate()

    def get_dab(self, settings: BrushSettings) -> Image.Image:
        """Retrieve circular dab buffer matching current settings."""
        return self._generator.generate_dab(settings)

    def render_segment(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> bool:
        """
        Interpolate and stamp dabs along the path between (x1, y1) and (x2, y2).
        Returns True if any dab was stamped within target image bounds.
        """
        if settings.opacity <= 0.0 or settings.size <= 0:
            return False
        if getattr(settings, "flow", 1.0) <= 0.0:
            return False
        is_eraser = getattr(settings, "is_eraser", False)
        if not is_eraser and settings.color[3] <= 0:
            return False

        dab = self.get_dab(settings)
        D = dab.width
        R = D / 2.0

        dist = math.hypot(x2 - x1, y2 - y1)
        spacing = getattr(settings, "spacing", 0.25)
        step = max(1.0, R * max(0.05, spacing * 2.0))
        num_steps = max(1, int(math.ceil(dist / step)))

        W, H = target_image.size
        stamped_any = False

        for i in range(num_steps + 1):
            t = float(i) / float(num_steps) if num_steps > 0 else 0.0
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t

            px = int(round(cx - R))
            py = int(round(cy - R))

            if px + D <= 0 or px >= W or py + D <= 0 or py >= H:
                continue

            sx1 = max(0, -px)
            sy1 = max(0, -py)
            sx2 = min(D, W - px)
            sy2 = min(D, H - py)

            if sx2 <= sx1 or sy2 <= sy1:
                continue

            dest_box = (px + sx1, py + sy1, px + sx2, py + sy2)
            dab_crop = dab.crop((sx1, sy1, sx2, sy2))

            if is_eraser:
                dest_crop = target_image.crop(dest_box)
                dest_arr = np.array(dest_crop)
                dab_arr = np.array(dab_crop)
                dab_alpha = dab_arr[:, :, 3].astype(np.float32) / 255.0
                dest_arr[:, :, 3] = (
                    dest_arr[:, :, 3].astype(np.float32) * (1.0 - dab_alpha)
                ).clip(0, 255).astype(np.uint8)
                erased_patch = Image.fromarray(dest_arr, mode="RGBA")
                target_image.paste(erased_patch, (px + sx1, py + sy1))
                stamped_any = True
            else:
                dest = (px + sx1, py + sy1)
                target_image.alpha_composite(dab_crop, dest=dest)
                stamped_any = True

        return stamped_any
