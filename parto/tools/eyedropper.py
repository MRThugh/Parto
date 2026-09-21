# parto/tools/eyedropper.py
"""
Parto v0.3.0 - Eyedropper Color Picker Tool
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent
from .base import BaseTool


class EyedropperTool(BaseTool):
    """Tool allowing sampling of RGB/RGBA pixel color under cursor."""

    name: str = "Eyedropper"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def sample_color(self, x: int, y: int, doc: Any):
        comp = doc.get_composite() if hasattr(doc, "get_composite") else None
        if comp is None and hasattr(doc, "active_layer") and doc.active_layer:
            comp = doc.active_layer.image
        if comp and 0 <= x < comp.width and 0 <= y < comp.height:
            return comp.getpixel((x, y))
        return (0, 0, 0, 255)

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton:
            self._pick_color(scene_pos, canvas)
            return True
        return False

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.buttons() & Qt.LeftButton:
            self._pick_color(scene_pos, canvas)
            return True
        return False

    def _pick_color(self, scene_pos: QPointF, canvas: Any):
        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image:
            return

        x, y = int(scene_pos.x()), int(scene_pos.y())
        if 0 <= x < doc.width and 0 <= y < doc.height:
            comp = doc.get_composite()
            if comp:
                pixel = comp.getpixel((x, y))
                if isinstance(pixel, (tuple, list)):
                    r = pixel[0]
                    g = pixel[1] if len(pixel) > 1 else r
                    b = pixel[2] if len(pixel) > 2 else r
                    a = pixel[3] if len(pixel) > 3 else 255
                    canvas.pixel_inspected.emit(x, y, r, g, b, a)
                    mw = getattr(canvas, "main_window", None)
                    if mw and hasattr(mw, "set_brush_color"):
                        mw.set_brush_color((r, g, b, a))
