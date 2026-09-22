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
    QToolButton,
    QColorDialog,
    QFrame,
    QSizePolicy,
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
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        # Title
        title_label = QLabel("Brush:", self)
        title_label.setStyleSheet("font-weight: 600; font-size: 11px;")
        layout.addWidget(title_label)

        def _make_separator():
            sep = QFrame(self)
            sep.setFrameShape(QFrame.VLine)
            sep.setFrameShadow(QFrame.Sunken)
            return sep

        layout.addWidget(_make_separator())

        # 1. Size Control (1 - 200 px)
        lbl_size = QLabel("Size:", self)
        lbl_size.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_size)

        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setRange(1, 200)
        self.slider_size.setValue(8)
        self.slider_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_size.setMinimumWidth(40)
        self.slider_size.setMaximumWidth(120)
        layout.addWidget(self.slider_size)

        self.spin_size = QSpinBox(self)
        self.spin_size.setRange(1, 200)
        self.spin_size.setValue(8)
        self.spin_size.setSuffix(" px")
        self.spin_size.setFixedWidth(72)
        self.spin_size.setAlignment(Qt.AlignRight)
        layout.addWidget(self.spin_size)

        self.slider_size.valueChanged.connect(self.spin_size.setValue)
        self.spin_size.valueChanged.connect(self.slider_size.setValue)
        self.slider_size.valueChanged.connect(self._on_size_slider_changed)

        layout.addWidget(_make_separator())

        # 2. Opacity Control (1 - 100 %)
        lbl_op = QLabel("Opacity:", self)
        lbl_op.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_op)

        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setRange(1, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_opacity.setMinimumWidth(40)
        self.slider_opacity.setMaximumWidth(120)
        layout.addWidget(self.slider_opacity)

        self.spin_opacity = QSpinBox(self)
        self.spin_opacity.setRange(1, 100)
        self.spin_opacity.setValue(100)
        self.spin_opacity.setSuffix(" %")
        self.spin_opacity.setFixedWidth(72)
        self.spin_opacity.setAlignment(Qt.AlignRight)
        layout.addWidget(self.spin_opacity)

        self.slider_opacity.valueChanged.connect(self.spin_opacity.setValue)
        self.spin_opacity.valueChanged.connect(self.slider_opacity.setValue)
        self.slider_opacity.valueChanged.connect(self._on_opacity_slider_changed)

        layout.addWidget(_make_separator())

        # 3. Hardness Control (0 - 100 %)
        lbl_hard = QLabel("Hardness:", self)
        lbl_hard.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_hard)

        self.slider_hardness = QSlider(Qt.Horizontal, self)
        self.slider_hardness.setRange(0, 100)
        self.slider_hardness.setValue(80)
        self.slider_hardness.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_hardness.setMinimumWidth(40)
        self.slider_hardness.setMaximumWidth(120)
        layout.addWidget(self.slider_hardness)

        self.spin_hardness = QSpinBox(self)
        self.spin_hardness.setRange(0, 100)
        self.spin_hardness.setValue(80)
        self.spin_hardness.setSuffix(" %")
        self.spin_hardness.setFixedWidth(72)
        self.spin_hardness.setAlignment(Qt.AlignRight)
        layout.addWidget(self.spin_hardness)

        self.slider_hardness.valueChanged.connect(self.spin_hardness.setValue)
        self.spin_hardness.valueChanged.connect(self.slider_hardness.setValue)
        self.slider_hardness.valueChanged.connect(self._on_hardness_slider_changed)

        layout.addWidget(_make_separator())

        # 4. Color Swatch & Picker
        self.color_chip = QToolButton(self)
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
            btn = QToolButton(self)
            btn.setFixedSize(14, 14)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_col})")
            btn.setStyleSheet(
                f"background-color: {hex_col}; border: 1px solid #71717a; border-radius: 3px;"
            )
            btn.clicked.connect(lambda _, c=hex_col: self._set_color_from_hex(c))
            layout.addWidget(btn)

        # Swap Button (X)
        self.swap_btn = QToolButton(self)
        self.swap_btn.setText("⇄")
        self.swap_btn.setFixedSize(22, 22)
        self.swap_btn.setToolTip("Swap Foreground / Background Color (X)")
        self.swap_btn.clicked.connect(self._on_swap_colors)
        layout.addWidget(self.swap_btn)

        # Reset Button (D)
        self.reset_btn = QToolButton(self)
        self.reset_btn.setText("D")
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
        clamped = max(1, min(200, int(size)))
        if self.slider_size.value() != clamped:
            self.slider_size.blockSignals(True)
            self.spin_size.blockSignals(True)
            self.slider_size.setValue(clamped)
            self.spin_size.setValue(clamped)
            self.slider_size.blockSignals(False)
            self.spin_size.blockSignals(False)

    def set_opacity(self, opacity: float):
        pct = max(1, min(100, int(round(float(opacity) * 100))))
        if self.slider_opacity.value() != pct:
            self.slider_opacity.blockSignals(True)
            self.spin_opacity.blockSignals(True)
            self.slider_opacity.setValue(pct)
            self.spin_opacity.setValue(pct)
            self.slider_opacity.blockSignals(False)
            self.spin_opacity.blockSignals(False)

    def set_hardness(self, hardness: float):
        pct = max(0, min(100, int(round(float(hardness) * 100))))
        if self.slider_hardness.value() != pct:
            self.slider_hardness.blockSignals(True)
            self.spin_hardness.blockSignals(True)
            self.slider_hardness.setValue(pct)
            self.spin_hardness.setValue(pct)
            self.slider_hardness.blockSignals(False)
            self.spin_hardness.blockSignals(False)

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
