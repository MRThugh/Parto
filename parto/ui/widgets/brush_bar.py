# parto/ui/widgets/brush_bar.py
"""
Parto v0.3.0 - Professional Interactive Brush Control Bar
Allows live configuration of brush size, opacity, hardness, color selection,
quick palette swatches, and color swapping.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QPushButton,
    QColorDialog,
    QFrame,
)
from parto.themes.manager import get_theme_manager


class BrushBar(QWidget):
    """
    Floating context bar for the Brush Tool.
    Controls:
    - Size slider & spinbox (1 - 200 px)
    - Opacity slider & spinbox (1 - 100 %)
    - Hardness slider & spinbox (0 - 100 %)
    - Interactive color preview chip & QColorDialog trigger
    - Quick palette swatches
    - Color swap button (X) and reset button (D)
    """
    size_changed = Signal(int)
    opacity_changed = Signal(float)
    hardness_changed = Signal(float)
    color_changed = Signal(tuple)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("BrushBar")
        self._color: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self._bg_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
        self._init_ui()
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(8)

        # Title
        title_label = QLabel("Brush:", self)
        title_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(title_label)

        # Separator
        sep1 = QFrame(self)
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep1)

        # 1. Size Control (1 - 200 px)
        lbl_size = QLabel("Size:", self)
        lbl_size.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_size)

        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setRange(1, 200)
        self.slider_size.setValue(8)
        self.slider_size.setFixedWidth(80)
        layout.addWidget(self.slider_size)

        self.spin_size = QSpinBox(self)
        self.spin_size.setRange(1, 200)
        self.spin_size.setValue(8)
        self.spin_size.setSuffix(" px")
        self.spin_size.setFixedWidth(65)
        layout.addWidget(self.spin_size)

        self.slider_size.valueChanged.connect(self.spin_size.setValue)
        self.spin_size.valueChanged.connect(self.slider_size.setValue)
        self.slider_size.valueChanged.connect(self._on_size_slider_changed)

        # Separator
        sep2 = QFrame(self)
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)

        # 2. Opacity Control (1 - 100 %)
        lbl_op = QLabel("Opacity:", self)
        lbl_op.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_op)

        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setRange(1, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.setFixedWidth(70)
        layout.addWidget(self.slider_opacity)

        self.spin_opacity = QSpinBox(self)
        self.spin_opacity.setRange(1, 100)
        self.spin_opacity.setValue(100)
        self.spin_opacity.setSuffix(" %")
        self.spin_opacity.setFixedWidth(60)
        layout.addWidget(self.spin_opacity)

        self.slider_opacity.valueChanged.connect(self.spin_opacity.setValue)
        self.spin_opacity.valueChanged.connect(self.slider_opacity.setValue)
        self.slider_opacity.valueChanged.connect(self._on_opacity_slider_changed)

        # Separator
        sep3 = QFrame(self)
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep3)

        # 3. Hardness Control (0 - 100 %)
        lbl_hard = QLabel("Hardness:", self)
        lbl_hard.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_hard)

        self.slider_hardness = QSlider(Qt.Horizontal, self)
        self.slider_hardness.setRange(0, 100)
        self.slider_hardness.setValue(80)
        self.slider_hardness.setFixedWidth(70)
        layout.addWidget(self.slider_hardness)

        self.spin_hardness = QSpinBox(self)
        self.spin_hardness.setRange(0, 100)
        self.spin_hardness.setValue(80)
        self.spin_hardness.setSuffix(" %")
        self.spin_hardness.setFixedWidth(60)
        layout.addWidget(self.spin_hardness)

        self.slider_hardness.valueChanged.connect(self.spin_hardness.setValue)
        self.spin_hardness.valueChanged.connect(self.slider_hardness.setValue)
        self.slider_hardness.valueChanged.connect(self._on_hardness_slider_changed)

        # Separator
        sep4 = QFrame(self)
        sep4.setFrameShape(QFrame.VLine)
        sep4.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep4)

        # 4. Color Swatch & Picker
        self.color_chip = QPushButton(self)
        self.color_chip.setFixedSize(22, 22)
        self.color_chip.setCursor(Qt.PointingHandCursor)
        self.color_chip.setToolTip("Click to select Brush Color")
        self.color_chip.clicked.connect(self._open_color_dialog)
        self._update_color_chip_style()
        layout.addWidget(self.color_chip)

        # Quick Swatches
        quick_colors = [
            ("#000000", "Black"),
            ("#ffffff", "White"),
            ("#ef4444", "Red"),
            ("#3b82f6", "Blue"),
            ("#22c55e", "Green"),
            ("#eab308", "Yellow"),
        ]
        for hex_col, name in quick_colors:
            btn = QPushButton(self)
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_col})")
            btn.setStyleSheet(
                f"background-color: {hex_col}; border: 1px solid #71717a; border-radius: 3px;"
            )
            btn.clicked.connect(lambda _, c=hex_col: self._set_color_from_hex(c))
            layout.addWidget(btn)

        # Swap Button (X)
        self.swap_btn = QPushButton("⇄", self)
        self.swap_btn.setFixedSize(22, 22)
        self.swap_btn.setToolTip("Swap Foreground / Background Color (X)")
        self.swap_btn.clicked.connect(self._on_swap_colors)
        layout.addWidget(self.swap_btn)

        # Reset Button (D)
        self.reset_btn = QPushButton("D", self)
        self.reset_btn.setFixedSize(22, 22)
        self.reset_btn.setToolTip("Reset to Default Black / White (D)")
        self.reset_btn.clicked.connect(self._on_reset_colors)
        layout.addWidget(self.reset_btn)

        layout.addStretch()

    def _on_size_slider_changed(self, val: int):
        self.size_changed.emit(val)

    def _on_opacity_slider_changed(self, val: int):
        self.opacity_changed.emit(val / 100.0)

    def _on_hardness_slider_changed(self, val: int):
        self.hardness_changed.emit(val / 100.0)

    def _open_color_dialog(self):
        r, g, b, a = self._color
        initial = QColor(r, g, b, a)
        color = QColorDialog.getColor(initial, self, "Select Brush Color", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            rgba = (color.red(), color.green(), color.blue(), color.alpha())
            self.set_color(rgba)
            self.color_changed.emit(rgba)

    def _set_color_from_hex(self, hex_str: str):
        color = QColor(hex_str)
        if color.isValid():
            rgba = (color.red(), color.green(), color.blue(), 255)
            self.set_color(rgba)
            self.color_changed.emit(rgba)

    def _on_swap_colors(self):
        self._color, self._bg_color = self._bg_color, self._color
        self._update_color_chip_style()
        self.color_changed.emit(self._color)

    def _on_reset_colors(self):
        self._color = (0, 0, 0, 255)
        self._bg_color = (255, 255, 255, 255)
        self._update_color_chip_style()
        self.color_changed.emit(self._color)

    def set_color(self, rgba: Tuple[int, int, int, int]):
        self._color = rgba
        self._update_color_chip_style()

    def set_size(self, size: int):
        clamped = max(1, min(200, size))
        self.slider_size.setValue(clamped)

    def set_opacity(self, opacity: float):
        pct = max(1, min(100, int(opacity * 100)))
        self.slider_opacity.setValue(pct)

    def set_hardness(self, hardness: float):
        pct = max(0, min(100, int(hardness * 100)))
        self.slider_hardness.setValue(pct)

    def _update_color_chip_style(self):
        r, g, b, a = self._color
        self.color_chip.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, {a / 255.0:.2f}); "
            f"border: 2px solid #e4e4e7; border-radius: 4px;"
        )

    def _on_theme_changed(self, _: str):
        self._update_color_chip_style()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
