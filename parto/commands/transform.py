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
        # Capture pre-state snapshot
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        if self.is_180:
            self.document.rotate_180_document()
        else:
            self.document.rotate_document(clockwise=self.clockwise)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        elif self.is_180:
            self.document.rotate_180_document()
        else:
            self.document.rotate_document(clockwise=self.clockwise)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
        elif self.is_180:
            self.document.rotate_180_document()
        else:
            # Reverse 90 deg rotation
            self.document.rotate_document(clockwise=not self.clockwise)


class FlipCommand(Command):
    """Command that flips document horizontally or vertically."""

    def __init__(self, document: Any, horizontal: bool = True):
        name = "Flip Horizontal" if horizontal else "Flip Vertical"
        super().__init__(name=name, id="transform.flip")
        self.document = document
        self.horizontal = horizontal
        self._before_snap = document.create_snapshot() if hasattr(document, "create_snapshot") else None
        self._after_snap: Optional[Dict[str, Any]] = None

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        if self.horizontal:
            self.document.flip_horizontal_document()
        else:
            self.document.flip_vertical_document()
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        elif self.horizontal:
            self.document.flip_horizontal_document()
        else:
            self.document.flip_vertical_document()

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
        elif self.horizontal:
            self.document.flip_horizontal_document()
        else:
            self.document.flip_vertical_document()


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

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self.document.resize_document(self.new_width, self.new_height, resample=self.resample)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self.document.resize_document(self.new_width, self.new_height, resample=self.resample)

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

    def execute(self) -> None:
        if self._after_snap is not None:
            self.redo()
            return
        self.document.crop_document(self.crop_rect)
        if hasattr(self.document, "create_snapshot"):
            self._after_snap = self.document.create_snapshot()

    def redo(self) -> None:
        if self._after_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._after_snap)
        else:
            self.document.crop_document(self.crop_rect)

    def undo(self) -> None:
        if self._before_snap and hasattr(self.document, "restore_snapshot"):
            self.document.restore_snapshot(self._before_snap)
