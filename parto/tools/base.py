# parto/tools/base.py
"""
Parto v0.3.0 - Abstract Canvas Tool Base Class
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any, Optional
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent, QPainter


class BaseTool:
    """Abstract base class for all interactive editor tools."""

    name: str = "Base"
    cursor_shape: Qt.CursorShape = Qt.ArrowCursor

    def activate(self, canvas: Any) -> None:
        """Called when this tool is selected."""
        canvas.setCursor(self.cursor_shape)

    def deactivate(self, canvas: Any) -> None:
        """Called when switching away from this tool."""
        pass

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        """Handle mouse press. Return True if event was handled."""
        return False

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        """Handle mouse move. Return True if event was handled."""
        return False

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        """Handle mouse release. Return True if event was handled."""
        return False

    def key_press(self, event: QKeyEvent, canvas: Any) -> bool:
        """Handle key press. Return True if event was handled."""
        return False

    def paint_overlay(self, painter: QPainter, canvas: Any) -> None:
        """Paint interactive visual overlays (handles, grids, outlines) on canvas."""
        pass
