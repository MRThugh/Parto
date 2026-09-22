# parto/editor/engine.py
"""
Parto v0.3.0 - Image Processing Engine Compatibility Shim
Coordinates image transformations, filter previews, and undo/redo stacks
by delegating to the single authoritative Document state model.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
from typing import Optional, Tuple, List, Any
from PIL import Image

from .document import Document
from ..image.transforms import (
    rotate_90,
    rotate_180,
    flip_horizontal,
    flip_vertical,
    resize_image,
    crop_image,
)
from ..image.processing import apply_color_adjustments, remove_background
from ..image.filters import apply_filter
from ..image.export import save_image_file


class EditorEngine:
    """
    High-level engine coordinating image transformations and previews.
    Delegates all authoritative document and history operations directly to Document,
    eliminating redundant state copies while maintaining full backward-compatibility.
    """

    def __init__(self, document: Optional[Document] = None, max_history: int = 30):
        self.max_history: int = max_history
        self._document: Document = document if document is not None else Document(max_history=max_history)
        self._original_image: Optional[Image.Image] = None

    @property
    def document(self) -> Document:
        """Access the underlying authoritative Document instance."""
        return self._document

    @property
    def current_image(self) -> Optional[Image.Image]:
        """Current composite image of the document."""
        return self._document.get_composite()

    @current_image.setter
    def current_image(self, img: Optional[Image.Image]):
        if img is not None:
            self.set_image(img)

    @property
    def original_image(self) -> Optional[Image.Image]:
        return self._original_image

    @property
    def filepath(self) -> Optional[str]:
        return self._document.filepath

    @property
    def can_undo(self) -> bool:
        return self._document.history.can_undo

    @property
    def can_redo(self) -> bool:
        return self._document.history.can_redo

    @property
    def undo_stack(self) -> List[Any]:
        return self._document.history.undo_stack

    @property
    def redo_stack(self) -> List[Any]:
        return self._document.history.redo_stack

    def load_image(self, filepath: str) -> None:
        """Load image into document from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        success = self._document.load_file(filepath, raise_on_error=True)
        if not success:
            raise IOError(f"Could not load image: {filepath}")

        comp = self._document.get_composite()
        self._original_image = comp.copy() if comp else None

    def set_image(self, image: Image.Image, filepath: Optional[str] = None):
        """Directly set working image in the underlying Document."""
        self._document.new_document(
            width=image.width,
            height=image.height,
            initial_image=image,
        )
        if filepath:
            self._document._filepath = os.path.abspath(filepath)
        self._original_image = image.copy()

    def save_image(self, filepath: str, img_format: Optional[str] = None, quality: int = 95) -> None:
        """Save active composite image to destination path."""
        if not self._document.has_image:
            raise ValueError("No active image to save")

        target = filepath
        if img_format and not os.path.splitext(filepath)[1]:
            target = f"{filepath}.{img_format.lower()}"

        success, err = self._document.save_file(target, quality=quality)
        if not success:
            raise IOError(f"Failed to save image: {err}")

    def undo(self) -> bool:
        return self._document.history.undo()

    def redo(self) -> bool:
        return self._document.history.redo()

    # Transformations
    def rotate_left(self):
        if self._document.has_image:
            self._document.rotate_document(clockwise=False)

    def rotate_right(self):
        if self._document.has_image:
            self._document.rotate_document(clockwise=True)

    def rotate_180(self):
        if self._document.has_image:
            self._document.rotate_180_document()

    def flip_horizontal(self):
        if self._document.has_image:
            self._document.flip_horizontal_document()

    def flip_vertical(self):
        if self._document.has_image:
            self._document.flip_vertical_document()

    def crop(self, box: Tuple[int, int, int, int]):
        if self._document.has_image:
            self._document.crop_document(box)

    def resize(self, width: int, height: int, resample: int = Image.Resampling.LANCZOS):
        if self._document.has_image:
            self._document.resize_document(width, height, resample=resample)

    # Adjustments
    def get_adjusted_preview(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Optional[Image.Image]:
        return self._document.get_adjusted_preview(
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
        if self._document.has_image:
            self._document.apply_color_adjustments(
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                sharpness=sharpness,
            )

    # Filters
    def get_filter_preview(self, filter_name: str) -> Optional[Image.Image]:
        return self._document.get_filter_preview(filter_name)

    def apply_filter(self, filter_name: str):
        if self._document.has_image:
            self._document.apply_filter(filter_name)

    # Background Removal
    def remove_background(self, tolerance: int = 28, feather_radius: int = 2):
        if self._document.has_image:
            self._document.remove_background(tolerance=tolerance, feather_radius=feather_radius)

    def apply_remove_background(self, tolerance: int = 28, feather_radius: int = 2):
        self.remove_background(tolerance=tolerance, feather_radius=feather_radius)

