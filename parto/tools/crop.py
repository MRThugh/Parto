# parto/tools/crop.py
"""
Parto v0.3.0 - Professional Interactive Crop Tool
Rule-of-thirds guides, sleek dimming mask, aspect ratio constraints, and robust handles.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any, Optional, Tuple
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QMouseEvent,
    QKeyEvent,
    QPainter,
    QPen,
    QColor,
    QBrush,
)
from .base import BaseTool
from ..editor.selection import SelectionBox


class CropTool(BaseTool):
    """
    Interactive Crop tool featuring bounds clamping, 8 handle interactions,
    rule-of-thirds grid lines, aspect ratio constraints, and dark mask overlay.
    """

    name: str = "Crop"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def __init__(self):
        self.selection = SelectionBox()
        self._active_handle: Optional[str] = None
        self._drag_start_pos: QPointF = QPointF()
        self._drag_start_rect: QRectF = QRectF()
        self._is_moving_box: bool = False
        self._is_active: bool = False

    def activate(self, canvas: Any) -> None:
        self._is_active = True
        doc = getattr(canvas, "document", None)
        if doc and doc.has_image:
            # Initialize crop box to 85% centered in image
            margin_x = doc.width * 0.08
            margin_y = doc.height * 0.08
            w = doc.width - 2 * margin_x
            h = doc.height - 2 * margin_y
            self.selection.rect = QRectF(margin_x, margin_y, w, h)
        else:
            self.selection.rect = QRectF(0, 0, 100, 100)

        canvas.setCursor(Qt.CrossCursor)
        canvas.viewport().update()

    def deactivate(self, canvas: Any) -> None:
        self._is_active = False
        self._active_handle = None
        self._is_moving_box = False
        canvas.viewport().update()

    def set_aspect_ratio(self, ratio_str: str, canvas: Any) -> None:
        """Update aspect ratio constraint ('free', '1:1', '4:3', '16:9', '3:2')."""
        self.selection.set_aspect_ratio(ratio_str)
        doc = getattr(canvas, "document", None)
        if doc and doc.has_image:
            self.selection.clamp_to_bounds(QRectF(0, 0, doc.width, doc.height))
        canvas.viewport().update()

    def get_crop_rect(self) -> Tuple[int, int, int, int]:
        """Returns integer (left, top, right, bottom) for cropping."""
        r = self.selection.rect.normalized()
        return (int(r.left()), int(r.top()), int(r.right()), int(r.bottom()))

    def _get_cursor_for_handle(self, handle: Optional[str]) -> Qt.CursorShape:
        if handle in ("tl", "br"):
            return Qt.SizeFDiagCursor
        elif handle in ("tr", "bl"):
            return Qt.SizeBDiagCursor
        elif handle in ("tc", "bc"):
            return Qt.SizeVerCursor
        elif handle in ("lc", "rc"):
            return Qt.SizeHorCursor
        return Qt.CrossCursor

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() != Qt.LeftButton:
            return False

        handle = self.selection.hit_test_handle(scene_pos)
        if handle:
            self._active_handle = handle
            self._drag_start_pos = scene_pos
            self._drag_start_rect = QRectF(self.selection.rect)
            canvas.setCursor(self._get_cursor_for_handle(handle))
            return True

        if self.selection.rect.contains(scene_pos):
            self._is_moving_box = True
            self._active_handle = None
            self._drag_start_pos = scene_pos
            self._drag_start_rect = QRectF(self.selection.rect)
            canvas.setCursor(Qt.SizeAllCursor)
            return True

        # Click outside: start drawing new crop box
        self._active_handle = "br"
        self._drag_start_pos = scene_pos
        self.selection.rect = QRectF(scene_pos.x(), scene_pos.y(), 1, 1)
        self._drag_start_rect = QRectF(self.selection.rect)
        canvas.viewport().update()
        return True

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        doc = getattr(canvas, "document", None)
        bounds = QRectF(0, 0, doc.width, doc.height) if doc and doc.has_image else QRectF()

        if self._is_moving_box:
            delta = scene_pos - self._drag_start_pos
            new_r = QRectF(self._drag_start_rect)
            new_r.translate(delta.x(), delta.y())
            self.selection.rect = new_r
            self.selection.clamp_to_bounds(bounds)
            canvas.viewport().update()
            return True

        if self._active_handle:
            delta = scene_pos - self._drag_start_pos
            sr = self._drag_start_rect
            r = QRectF(sr)

            h = self._active_handle
            if "l" in h:
                r.setLeft(min(sr.right() - 20, sr.left() + delta.x()))
            if "r" in h:
                r.setRight(max(sr.left() + 20, sr.right() + delta.x()))
            if "t" in h:
                r.setTop(min(sr.bottom() - 20, sr.top() + delta.y()))
            if "b" in h:
                r.setBottom(max(sr.top() + 20, sr.bottom() + delta.y()))

            self.selection.rect = r
            if self.selection.aspect_ratio:
                self.selection.apply_aspect_ratio()
            self.selection.clamp_to_bounds(bounds)
            canvas.viewport().update()
            return True

        # Hover cursor update
        handle = self.selection.hit_test_handle(scene_pos)
        if handle:
            canvas.setCursor(self._get_cursor_for_handle(handle))
        elif self.selection.rect.contains(scene_pos):
            canvas.setCursor(Qt.SizeAllCursor)
        else:
            canvas.setCursor(Qt.CrossCursor)

        return False

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton:
            self._active_handle = None
            self._is_moving_box = False
            self.selection.rect = self.selection.rect.normalized()
            doc = getattr(canvas, "document", None)
            if doc and doc.has_image:
                self.selection.clamp_to_bounds(QRectF(0, 0, doc.width, doc.height))
            canvas.viewport().update()
            return True
        return False

    def key_press(self, event: QKeyEvent, canvas: Any) -> bool:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            mw = getattr(canvas, "main_window", None)
            if mw and hasattr(mw, "apply_crop"):
                mw.apply_crop()
            return True
        elif event.key() == Qt.Key_Escape:
            mw = getattr(canvas, "main_window", None)
            if mw and hasattr(mw, "cancel_crop"):
                mw.cancel_crop()
            return True
        return False

    def paint_overlay(self, painter: QPainter, canvas: Any) -> None:
        """Render dimmed surrounding mask, rule-of-thirds grid, boundary outline, and handles."""
        if not self._is_active:
            return

        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image:
            return

        doc_rect = QRectF(0, 0, doc.width, doc.height)
        crop_r = self.selection.rect.normalized()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        # 1. Dim outer region
        mask_color = QColor(0, 0, 0, 140)
        # Top
        painter.fillRect(QRectF(0, 0, doc.width, crop_r.top()), mask_color)
        # Bottom
        painter.fillRect(QRectF(0, crop_r.bottom(), doc.width, doc.height - crop_r.bottom()), mask_color)
        # Left
        painter.fillRect(QRectF(0, crop_r.top(), crop_r.left(), crop_r.height()), mask_color)
        # Right
        painter.fillRect(QRectF(crop_r.right(), crop_r.top(), doc.width - crop_r.right(), crop_r.height()), mask_color)

        # 2. Rule-of-thirds grid
        grid_pen = QPen(QColor(255, 255, 255, 90))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)

        w3 = crop_r.width() / 3.0
        h3 = crop_r.height() / 3.0

        # Verticals
        x1, x2 = crop_r.left() + w3, crop_r.left() + 2 * w3
        painter.drawLine(QPointF(x1, crop_r.top()), QPointF(x1, crop_r.bottom()))
        painter.drawLine(QPointF(x2, crop_r.top()), QPointF(x2, crop_r.bottom()))

        # Horizontals
        y1, y2 = crop_r.top() + h3, crop_r.top() + 2 * h3
        painter.drawLine(QPointF(crop_r.left(), y1), QPointF(crop_r.right(), y1))
        painter.drawLine(QPointF(crop_r.left(), y2), QPointF(crop_r.right(), y2))

        # 3. Main crop box border
        box_pen = QPen(QColor(2, 132, 199))  # Parto Sky primary color
        box_pen.setWidth(2)
        painter.setPen(box_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(crop_r)

        # 4. Corner and center handles
        painter.setRenderHint(QPainter.Antialiasing, True)
        handle_fill = QBrush(QColor("#ffffff"))
        handle_pen = QPen(QColor(2, 132, 199))
        handle_pen.setWidth(2)
        painter.setPen(handle_pen)
        painter.setBrush(handle_fill)

        for _, handle_rect in self.selection.get_handles():
            painter.drawRoundedRect(handle_rect, 2, 2)

        painter.restore()
