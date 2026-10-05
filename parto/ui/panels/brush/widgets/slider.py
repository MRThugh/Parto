# parto/ui/panels/brush/widgets/slider.py
"""
Parto Brush Studio — Precision Slider & SpinBox Row Widget
Clean, unified numeric control combining a smooth slider and precise spinbox.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QSizePolicy,
)
from parto.themes.manager import get_theme_manager


class LabeledSliderSpinRow(QWidget):
    """
    Precision control row pairing an interactive slider with an editable spinbox.
    Maintains synchronized bidirectional value tracking.
    """

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        min_val: int,
        max_val: int,
        suffix: str = "",
        default_val: int = 1,
        tooltip: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._min_val = min_val
        self._max_val = max_val
        self._updating = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(label, self)
        self.label.setFixedWidth(70)
        self.label.setStyleSheet("font-size: 11px; font-weight: 500;")
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.slider)

        self.spin = QSpinBox(self)
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(default_val)
        self.spin.setSuffix(suffix)
        self.spin.setFixedWidth(78)
        self.spin.setAlignment(Qt.AlignRight)
        layout.addWidget(self.spin)

        if tooltip:
            self.setToolTip(tooltip)
            self.label.setToolTip(tooltip)
            self.slider.setToolTip(tooltip)
            self.spin.setToolTip(tooltip)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spin.valueChanged.connect(self._on_spin_changed)

    def _on_slider_changed(self, val: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.spin.setValue(val)
        self._updating = False
        self.valueChanged.emit(val)

    def _on_spin_changed(self, val: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(val)
        self._updating = False
        self.valueChanged.emit(val)

    def value(self) -> int:
        return self.slider.value()

    def setValue(self, val: int) -> None:
        clamped = max(self._min_val, min(self._max_val, int(val)))
        if self.slider.value() != clamped or self.spin.value() != clamped:
            self._updating = True
            self.slider.setValue(clamped)
            self.spin.setValue(clamped)
            self._updating = False
