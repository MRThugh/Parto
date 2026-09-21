# parto/tools/move.py
"""
Parto v0.3.0 - Canvas Pan & Move Tool
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QMouseEvent
from .base import BaseTool


class MoveTool(BaseTool):
    """Tool allowing interactive click-and-drag panning of the canvas viewport."""

    name: str = "Move"
    cursor_shape: Qt.CursorShape = Qt.OpenHandCursor

    def __init__(self):
        self._is_dragging: bool = False
        self._last_screen_pos: QPoint = QPoint()

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() in (Qt.LeftButton, Qt.MiddleButton):
            self._is_dragging = True
            self._last_screen_pos = event.pos()
            canvas.setCursor(Qt.ClosedHandCursor)
            return True
        return False

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if self._is_dragging:
            delta = event.pos() - self._last_screen_pos
            self._last_screen_pos = event.pos()
            canvas.horizontalScrollBar().setValue(canvas.horizontalScrollBar().value() - delta.x())
            canvas.verticalScrollBar().setValue(canvas.verticalScrollBar().value() - delta.y())
            return True
        return False

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if self._is_dragging:
            self._is_dragging = False
            canvas.setCursor(Qt.OpenHandCursor)
            return True
        return False
