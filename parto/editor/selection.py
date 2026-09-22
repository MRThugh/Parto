# parto/editor/selection.py
"""
Parto v0.3.0 - Selection & Crop Geometry Math
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple, Optional, List
from PySide6.QtCore import QRectF, QPointF


class SelectionBox:
    """
    Manages selection or crop bounding boxes with aspect ratio constraints,
    boundary clamping, and handle hit testing.
    """

    HANDLE_SIZE = 10

    def __init__(self, rect: Optional[QRectF] = None):
        self.rect: QRectF = rect or QRectF(0, 0, 100, 100)
        self.aspect_ratio: Optional[float] = None  # None = Free

    def init_rect(self, width: float, height: float):
        self.rect = QRectF(0, 0, width, height)

    def set_aspect_ratio(self, ratio_val: str | float | None, max_w: float = 0, max_h: float = 0) -> None:
        """
        Set aspect constraint by string or float.
        """
        if isinstance(ratio_val, (int, float)):
            self.aspect_ratio = float(ratio_val)
        elif isinstance(ratio_val, str):
            key = ratio_val.lower().strip()
            if key in ("free", "none", ""):
                self.aspect_ratio = None
            elif key in ("1:1", "square"):
                self.aspect_ratio = 1.0
            elif key in ("4:3", "standard"):
                self.aspect_ratio = 4.0 / 3.0
            elif key in ("16:9", "widescreen"):
                self.aspect_ratio = 16.0 / 9.0
            elif key in ("3:2", "photo"):
                self.aspect_ratio = 3.0 / 2.0
            else:
                try:
                    parts = key.split(":")
                    if len(parts) == 2:
                        self.aspect_ratio = float(parts[0]) / float(parts[1])
                except (ValueError, ZeroDivisionError):
                    self.aspect_ratio = None
        else:
            self.aspect_ratio = None

        if self.aspect_ratio is not None and not self.rect.isEmpty():
            self.apply_aspect_ratio(max_w, max_h)

    def apply_aspect_ratio(self, max_w: float = 0, max_h: float = 0) -> None:
        if self.aspect_ratio is None or self.rect.isEmpty():
            return
        w = self.rect.width()
        h = self.rect.height()

        new_h = w / self.aspect_ratio
        if max_h > 0 and new_h > max_h:
            new_h = max_h
            w = new_h * self.aspect_ratio

        self.rect.setWidth(w)
        self.rect.setHeight(new_h)

    def get_pixel_rect(self, bound_w: int, bound_h: int) -> Tuple[int, int, int, int]:
        r = self.rect.normalized()
        x1 = max(0, min(int(round(r.left())), bound_w))
        y1 = max(0, min(int(round(r.top())), bound_h))
        x2 = max(0, min(int(round(r.right())), bound_w))
        y2 = max(0, min(int(round(r.bottom())), bound_h))
        return (x1, y1, x2, y2)

    def clamp_to_bounds(self, bounds: QRectF) -> None:
        """Ensure selection box stays entirely inside bounding rectangle."""
        if bounds.isEmpty():
            return

        w = min(self.rect.width(), bounds.width())
        h = min(self.rect.height(), bounds.height())

        x = max(bounds.left(), min(self.rect.left(), bounds.right() - w))
        y = max(bounds.top(), min(self.rect.top(), bounds.bottom() - h))

        self.rect.setRect(x, y, w, h)

    def get_handles(self) -> List[Tuple[str, QRectF]]:
        """Returns list of (handle_name, QRectF) for all 8 resize handles."""
        r = self.rect
        hs = self.HANDLE_SIZE
        half = hs / 2.0

        return [
            ("tl", QRectF(r.left() - half, r.top() - half, hs, hs)),
            ("tc", QRectF(r.center().x() - half, r.top() - half, hs, hs)),
            ("tr", QRectF(r.right() - half, r.top() - half, hs, hs)),
            ("rc", QRectF(r.right() - half, r.center().y() - half, hs, hs)),
            ("br", QRectF(r.right() - half, r.bottom() - half, hs, hs)),
            ("bc", QRectF(r.center().x() - half, r.bottom() - half, hs, hs)),
            ("bl", QRectF(r.left() - half, r.bottom() - half, hs, hs)),
            ("lc", QRectF(r.left() - half, r.center().y() - half, hs, hs)),
        ]

    def hit_test_handle(self, point: QPointF) -> Optional[str]:
        """Check if point hits any resize handle."""
        for name, rect in self.get_handles():
            if rect.contains(point):
                return name
        return None


CropSelection = SelectionBox
