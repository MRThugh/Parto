# parto/tools/brush.py
"""
Parto v0.3.0 - Freehand Brush Tool for Active Layer
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any, Optional
from PIL import ImageDraw
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QPainter, QPen, QColor
from .base import BaseTool


class BrushTool(BaseTool):
    """Tool allowing freehand drawing on the active layer."""

    name: str = "Brush"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def __init__(self):
        self.color = (2, 132, 199, 255)  # RGBA
        self.size = 8
        self._is_drawing: bool = False
        self._last_pt: Optional[QPointF] = None
        self._before_snap: Optional[Any] = None

    @property
    def radius(self) -> int:
        return self.size // 2

    @radius.setter
    def radius(self, value: int):
        self.size = max(1, int(value) * 2)

    def start_stroke(self, pt: Any, layer: Any):
        self._is_drawing = True
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        self._last_pt = p
        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")
        draw = ImageDraw.Draw(layer.image)
        r = max(1, self.size // 2)
        draw.ellipse([p.x() - r, p.y() - r, p.x() + r, p.y() + r], fill=self.color)

    def continue_stroke(self, pt: Any, layer: Any):
        if not self._is_drawing or self._last_pt is None:
            return
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")
        draw = ImageDraw.Draw(layer.image)
        r = max(1, self.size // 2)
        draw.line([(self._last_pt.x(), self._last_pt.y()), (p.x(), p.y())], fill=self.color, width=self.size)
        draw.ellipse([p.x() - r, p.y() - r, p.x() + r, p.y() + r], fill=self.color)
        self._last_pt = p

    def end_stroke(self, doc: Any):
        self._is_drawing = False
        self._last_pt = None
        if hasattr(doc, "invalidate_composite"):
            doc.invalidate_composite()
        if hasattr(doc, "set_modified"):
            doc.set_modified(True)
        if hasattr(doc, "_record_operation"):
            snap = getattr(self, "_before_snap", None) or (doc._create_snapshot() if hasattr(doc, "_create_snapshot") else None)
            doc._record_operation(f"Brush Stroke ({self.size}px)", snap or doc._create_snapshot())
        elif hasattr(doc, "history"):
            from ..history.commands import SnapshotCommand
            doc.history.push(SnapshotCommand(f"Brush Stroke", doc, lambda s: None, None, None))

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() != Qt.LeftButton:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image or not doc.active_layer:
            return False

        self._is_drawing = True
        self._last_pt = scene_pos
        self._before_snap = doc._create_snapshot()

        # Draw initial circle point
        self._draw_stroke(doc, scene_pos, scene_pos)
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if not self._is_drawing or self._last_pt is None:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.active_layer:
            return False

        self._draw_stroke(doc, self._last_pt, scene_pos)
        self._last_pt = scene_pos
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton and self._is_drawing:
            self._is_drawing = False
            self._last_pt = None
            doc = getattr(canvas, "document", None)
            if doc:
                doc.invalidate_composite()
                doc.set_modified(True)
                if self._before_snap:
                    doc._record_operation(f"Brush Stroke ({self.size}px)", self._before_snap)
                    self._before_snap = None
                canvas.update_composite_pixmap()
            return True
        return False

    def _draw_stroke(self, doc: Any, p1: QPointF, p2: QPointF):
        layer = doc.active_layer
        if not layer or not layer.image:
            return

        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")

        draw = ImageDraw.Draw(layer.image)
        # Offset point by layer position if shifted
        ox, oy = layer.offset_x, layer.offset_y
        x1, y1 = p1.x() - ox, p1.y() - oy
        x2, y2 = p2.x() - ox, p2.y() - oy

        r = max(1, self.size // 2)
        draw.line([(x1, y1), (x2, y2)], fill=self.color, width=self.size)
        draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=self.color)
