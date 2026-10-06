# parto/commands/transform.py
"""
Parto Architecture 2.0 — Transform Commands
Author: Ali Kamrani (MRThugh)

Reversible commands for canvas and layer geometric transformations:
Rotate, Flip, Resize, and Crop.
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image
from .base import Command


class RotateCommand(Command):
    """Command that rotates all layers and dimensions of a document."""

    def __init__(
        self,
        document: Any,
        clockwise: bool = True,
        is_180: bool = False,
    ):
        if is_180:
            name = "Rotate 180°"
        elif clockwise:
            name = "Rotate 90° CW"
        else:
            name = "Rotate 90° CCW"
        super().__init__(name=name, id="transform.rotate")
        self.document = document
        self.clockwise = clockwise
        self.is_180 = is_180
        # Capture pre-state snapshot for fallback
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def _apply_domain(self, clockwise: bool, is_180: bool) -> None:
        if hasattr(self.document, "apply_rotate_domain"):
            self.document.apply_rotate_domain(clockwise=clockwise, is_180=is_180)
        elif hasattr(self.document, "_controller") and hasattr(self.document._controller, "apply_rotate_domain"):
            self.document._controller.apply_rotate_domain(clockwise=clockwise, is_180=is_180)
        elif is_180:
            self.document.rotate_180_document()
        else:
            self.document.rotate_document(clockwise=clockwise)

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self._apply_domain(self.clockwise, self.is_180)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self._apply_domain(self.clockwise, self.is_180)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
        elif self.is_180:
            self._apply_domain(True, True)
        else:
            # Reverse 90 deg rotation
            self._apply_domain(not self.clockwise, False)


class FlipCommand(Command):
    """Command that flips document horizontally or vertically."""

    def __init__(self, document: Any, horizontal: bool = True):
        name = "Flip Horizontal" if horizontal else "Flip Vertical"
        super().__init__(name=name, id="transform.flip")
        self.document = document
        self.horizontal = horizontal
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def _apply_domain(self, horizontal: bool) -> None:
        if hasattr(self.document, "apply_flip_domain"):
            self.document.apply_flip_domain(horizontal=horizontal)
        elif hasattr(self.document, "_controller") and hasattr(self.document._controller, "apply_flip_domain"):
            self.document._controller.apply_flip_domain(horizontal=horizontal)
        elif horizontal:
            self.document.flip_horizontal_document()
        else:
            self.document.flip_vertical_document()

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self._apply_domain(self.horizontal)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self._apply_domain(self.horizontal)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
        else:
            self._apply_domain(self.horizontal)


class ResizeCommand(Command):
    """Command that resizes canvas and scales all layers with offset awareness."""

    def __init__(
        self,
        document: Any,
        new_width: int,
        new_height: int,
        resample: int = Image.Resampling.LANCZOS,
    ):
        super().__init__(
            name=f"Resize ({new_width} × {new_height})",
            id="transform.resize",
        )
        self.document = document
        self.new_width = new_width
        self.new_height = new_height
        self.resample = resample
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def _apply_domain(self, nw: int, nh: int, resample: int) -> None:
        if hasattr(self.document, "apply_resize_domain"):
            self.document.apply_resize_domain(nw, nh, resample)
        elif hasattr(self.document, "_controller") and hasattr(self.document._controller, "apply_resize_domain"):
            self.document._controller.apply_resize_domain(nw, nh, resample)
        else:
            self.document.resize_document(nw, nh, resample=resample)

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self._apply_domain(self.new_width, self.new_height, self.resample)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self._apply_domain(self.new_width, self.new_height, self.resample)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)


class CropCommand(Command):
    """Command that crops document to specified rectangle."""

    def __init__(self, document: Any, crop_rect: Tuple[int, int, int, int]):
        super().__init__(name="Crop Canvas", id="transform.crop")
        self.document = document
        self.crop_rect = crop_rect
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def _apply_domain(self, rect: Tuple[int, int, int, int]) -> None:
        if hasattr(self.document, "apply_crop_domain"):
            self.document.apply_crop_domain(rect)
        elif hasattr(self.document, "_controller") and hasattr(self.document._controller, "apply_crop_domain"):
            self.document._controller.apply_crop_domain(rect)
        else:
            self.document.crop_document(rect)

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self._apply_domain(self.crop_rect)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self._apply_domain(self.crop_rect)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
