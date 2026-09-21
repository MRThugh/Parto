# parto/ui/statusbar.py
"""
Parto v0.3.0 - Rich Editor Status Bar with Real-Time Pixel & Coordinate Telemetry
Theme-aware swatches, coordinates, resolution, aspect ratio, megapixels, and zoom level.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QStatusBar,
    QLabel,
    QWidget,
    QHBoxLayout,
    QFrame,
)
from ..themes.manager import get_theme_manager


class EditorStatusBar(QStatusBar):
    """
    Status bar displaying active coordinates, sampled pixel color swatches,
    resolution, aspect ratio, megapixels, and zoom level.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("EditorStatusBar")
        self.setSizeGripEnabled(False)

        self._current_rgba = None
        self._init_widgets()
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _get_border_color(self) -> str:
        return get_theme_manager().get_semantic_color("border", "#3f3f46")

    def _init_widgets(self):
        # 1. Cursor coordinate telemetry
        self.coord_label = QLabel("—", self)
        self.coord_label.setMinimumWidth(110)
        self.addPermanentWidget(self.coord_label)

        # 2. Pixel color swatch and value
        color_container = QWidget(self)
        c_layout = QHBoxLayout(color_container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(6)

        border = self._get_border_color()
        self.color_swatch = QFrame(self)
        self.color_swatch.setFixedSize(14, 14)
        self.color_swatch.setStyleSheet(f"background-color: transparent; border: 1px solid {border}; border-radius: 2px;")
        c_layout.addWidget(self.color_swatch)

        self.color_label = QLabel("RGB: —", self)
        self.color_label.setMinimumWidth(140)
        c_layout.addWidget(self.color_label)

        self.addPermanentWidget(color_container)

        # 3. Dimensions & Megapixels
        self.dim_label = QLabel("No Image", self)
        self.dim_label.setMinimumWidth(180)
        self.addPermanentWidget(self.dim_label)

        # 4. Zoom percentage
        self.zoom_label = QLabel("100%", self)
        self.zoom_label.setMinimumWidth(55)
        self.zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.addPermanentWidget(self.zoom_label)

    def _on_theme_changed(self, _: str):
        if self._current_rgba:
            r, g, b, a = self._current_rgba
            self.set_pixel_color(r, g, b, a)
        else:
            self.clear_pixel_telemetry()

    def set_coordinates(self, x: int, y: int):
        self.coord_label.setText(f"X: {x}, Y: {y}")

    def set_pixel_color(self, r: int, g: int, b: int, a: int):
        self._current_rgba = (r, g, b, a)
        border = self._get_border_color()
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        self.color_swatch.setStyleSheet(
            f"background-color: rgba({r},{g},{b},{a/255.0:.2f}); border: 1px solid {border}; border-radius: 2px;"
        )
        self.color_label.setText(f"{hex_color} ({r},{g},{b})")

    def clear_pixel_telemetry(self):
        self._current_rgba = None
        border = self._get_border_color()
        self.coord_label.setText("—")
        self.color_swatch.setStyleSheet(f"background-color: transparent; border: 1px solid {border}; border-radius: 2px;")
        self.color_label.setText("RGB: —")

    def set_image_info(self, width: int, height: int, aspect_ratio: str, megapixels: str):
        if width > 0 and height > 0:
            self.dim_label.setText(f"{width} × {height} px  ({aspect_ratio}, {megapixels})")
        else:
            self.dim_label.setText("No Image")

    def set_zoom(self, factor: float):
        pct = int(round(factor * 100))
        self.zoom_label.setText(f"{pct}%")
