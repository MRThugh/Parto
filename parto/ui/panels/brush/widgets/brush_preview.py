# parto/ui/panels/brush/widgets/brush_preview.py
"""
Parto Brush Studio — Dynamic Brush Preview Widget
Renders live dab and simulated stroke preview with precise hardness, angle, and roundness.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import math
from typing import Tuple, Optional
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen,
    QRadialGradient,
    QPainterPath,
)
from PySide6.QtWidgets import QWidget
from parto.themes.manager import get_theme_manager


class StudioBrushPreviewWidget(QWidget):
    """
    Interactive live preview widget demonstrating current brush tip, falloff,
    angle, roundness, opacity, and color.
    """

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("StudioBrushPreviewWidget")
        self.setFixedSize(54, 54)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Brush Tip Preview (Click to select Color)")

        self._size: int = 12
        self._opacity: float = 1.0
        self._hardness: float = 0.8
        self._color: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self._angle: float = 0.0
        self._roundness: float = 1.0

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def update_preview(
        self,
        size: int,
        opacity: float,
        hardness: float,
        color: Tuple[int, int, int, int],
        angle: float = 0.0,
        roundness: float = 1.0,
    ) -> None:
        self._size = max(1, int(size))
        self._opacity = max(0.0, min(1.0, float(opacity)))
        self._hardness = max(0.0, min(1.0, float(hardness)))
        self._color = color
        self._angle = float(angle) % 360.0
        self._roundness = max(0.01, min(1.0, float(roundness)))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        pal = get_theme_manager().get_palette()
        border_col = QColor(pal.get("border_subtle", "#3f3f46"))
        bg_col = QColor(pal.get("surface_sunken", "#18181b"))

        # Background container
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.0))
        painter.drawRoundedRect(rect, 6, 6)

        cx = rect.center().x()
        cy = rect.center().y()

        # Scale preview radius
        max_r = (min(rect.width(), rect.height()) - 10) / 2.0
        radius_x = 2.0 + (min(500, self._size) / 500.0) * (max_r - 2.0)
        radius_y = radius_x * self._roundness

        painter.save()
        painter.translate(cx, cy)
        if abs(self._angle) > 0.01:
            painter.rotate(self._angle)

        r, g, b, a = self._color
        effective_alpha = int(round(a * self._opacity))

        grad = QRadialGradient(0, 0, radius_x)
        inner_ratio = max(0.0, min(1.0, self._hardness))
        inner_color = QColor(r, g, b, effective_alpha)
        edge_color = QColor(r, g, b, 0)

        if inner_ratio >= 0.98:
            grad.setColorAt(0.0, inner_color)
            grad.setColorAt(0.95, inner_color)
            grad.setColorAt(1.0, edge_color)
        else:
            grad.setColorAt(0.0, inner_color)
            grad.setColorAt(inner_ratio, inner_color)
            grad.setColorAt(1.0, edge_color)

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-radius_x, -radius_y, radius_x * 2, radius_y * 2))
        painter.restore()

        painter.end()
