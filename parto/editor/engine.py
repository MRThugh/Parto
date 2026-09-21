# parto/editor/engine.py
"""
Parto v0.3.0 - Image Processing Engine
High-level engine coordinating image transformations, filter previews, and undo/redo stacks.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
from typing import Optional, Tuple, List
from PIL import Image

from ..image.transforms import (
    rotate_90,
    rotate_180,
    flip_horizontal,
    flip_vertical,
    resize_image,
    crop_image,
)
from ..image.processing import apply_color_adjustments
from ..image.filters import apply_filter
from ..image.export import save_image_file


class EditorEngine:
    """
    Decoupled processing engine maintaining active image data, original baseline,
    and snapshot history.
    """

    def __init__(self, max_history: int = 30):
        self.max_history: int = max_history
        self._current_image: Optional[Image.Image] = None
        self._original_image: Optional[Image.Image] = None
        self._filepath: Optional[str] = None

        self._undo_stack: List[Image.Image] = []
        self._redo_stack: List[Image.Image] = []

    @property
    def current_image(self) -> Optional[Image.Image]:
        return self._current_image

    @property
    def original_image(self) -> Optional[Image.Image]:
        return self._original_image

    @property
    def filepath(self) -> Optional[str]:
        return self._filepath

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_stack(self) -> List[Image.Image]:
        return self._undo_stack

    @property
    def redo_stack(self) -> List[Image.Image]:
        return self._redo_stack

    def load_image(self, filepath: str) -> None:
        """Load image into engine from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Try HEIF if present
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass

        img = Image.open(filepath)
        img.load()  # Read pixel data immediately to trigger corruption errors early

        self._current_image = img.copy()
        self._original_image = img.copy()
        self._filepath = filepath
        self._undo_stack.clear()
        self._redo_stack.clear()

    def set_image(self, image: Image.Image, filepath: Optional[str] = None):
        """Directly set the working image in memory."""
        self._current_image = image.copy()
        self._original_image = image.copy()
        self._filepath = filepath
        self._undo_stack.clear()
        self._redo_stack.clear()

    def save_image(self, filepath: str, img_format: Optional[str] = None, quality: int = 95) -> None:
        """Save active image safely to destination path."""
        if self._current_image is None:
            raise ValueError("No active image to save")

        target = filepath
        if img_format and not os.path.splitext(filepath)[1]:
            target = f"{filepath}.{img_format.lower()}"

        success, err = save_image_file(self._current_image, target, quality=quality)
        if not success:
            raise IOError(f"Failed to save image: {err}")

    def _push_undo(self):
        if self._current_image is not None:
            self._undo_stack.append(self._current_image.copy())
            if len(self._undo_stack) > self.max_history:
                self._undo_stack.pop(0)
            self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack or self._current_image is None:
            return False
        self._redo_stack.append(self._current_image.copy())
        self._current_image = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack or self._current_image is None:
            return False
        self._undo_stack.append(self._current_image.copy())
        self._current_image = self._redo_stack.pop()
        return True

    # Transformations
    def rotate_left(self):
        if self._current_image:
            self._push_undo()
            self._current_image = rotate_90(self._current_image, clockwise=False)

    def rotate_right(self):
        if self._current_image:
            self._push_undo()
            self._current_image = rotate_90(self._current_image, clockwise=True)

    def rotate_180(self):
        if self._current_image:
            self._push_undo()
            self._current_image = rotate_180(self._current_image)

    def flip_horizontal(self):
        if self._current_image:
            self._push_undo()
            self._current_image = flip_horizontal(self._current_image)

    def flip_vertical(self):
        if self._current_image:
            self._push_undo()
            self._current_image = flip_vertical(self._current_image)

    def crop(self, box: Tuple[int, int, int, int]):
        if self._current_image:
            self._push_undo()
            self._current_image = crop_image(self._current_image, box)

    def resize(self, width: int, height: int, resample: int = Image.Resampling.LANCZOS):
        if self._current_image:
            self._push_undo()
            self._current_image = resize_image(self._current_image, width, height, resample=resample)

    # Adjustments
    def get_adjusted_preview(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Optional[Image.Image]:
        if not self._current_image:
            return None
        return apply_color_adjustments(
            self._current_image,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )

    def apply_adjustments(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ):
        if self._current_image:
            res = self.get_adjusted_preview(brightness, contrast, saturation, sharpness)
            if res is not None:
                self._push_undo()
                self._current_image = res

    # Filters
    def get_filter_preview(self, filter_name: str) -> Optional[Image.Image]:
        if not self._current_image:
            return None
        return apply_filter(self._current_image, filter_name)

    def apply_filter(self, filter_name: str):
        if self._current_image:
            res = self.get_filter_preview(filter_name)
            if res is not None:
                self._push_undo()
                self._current_image = res
