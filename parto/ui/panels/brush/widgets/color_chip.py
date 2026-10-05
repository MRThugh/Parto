# parto/ui/panels/brush/widgets/color_chip.py
"""
Parto Brush Studio — Interactive Color Swatch Chip Button
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Tuple, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import QToolButton, QWidget


class ColorChipButton(QToolButton):
    """
    Custom tool button for displaying active color with checkerboard transparency underlay.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._rgba: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self._border_color: str = "#3f3f46"

    def set_rgba(self, rgba: Tuple[int, int, int, int], border_color: str = "#3f3f46") -> None:
        self._rgba = rgba
        self._border_color = border_color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)

        # Subtle checkerboard for alpha
        if self._rgba[3] < 255:
            check_size = 4
            c1 = QColor(220, 220, 220)
            c2 = QColor(160, 160, 160)
            for x in range(rect.left(), rect.right(), check_size):
                for y in range(rect.top(), rect.bottom(), check_size):
                    is_even = ((x // check_size) + (y // check_size)) % 2 == 0
                    painter.fillRect(
                        x, y,
                        min(check_size, rect.right() - x + 1),
                        min(check_size, rect.bottom() - y + 1),
                        c1 if is_even else c2,
                    )

        r, g, b, a = self._rgba
        painter.setBrush(QBrush(QColor(r, g, b, a)))
        painter.setPen(QPen(QColor(self._border_color), 1.0))
        painter.drawRoundedRect(rect, 4, 4)
        painter.end()
