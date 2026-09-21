# parto/ui/panels/adjustments.py
"""
Parto v0.3.0 - Live Color Adjustments Dock Panel
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QGroupBox,
)


class AdjustmentDock(QDockWidget):
    """
    Dockable side panel for Brightness, Contrast, Saturation, and Sharpness controls.
    """
    adjustments_applied = Signal(float, float, float, float)
    preview_requested = Signal(float, float, float, float)
    reset_preview_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Adjustments", parent)
        self.setObjectName("AdjustmentDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._init_ui()

    def _init_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Sliders group
        group = QGroupBox("Color Tuning", container)
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(12)

        # Brightness (-100 to 100)
        self.b_slider, self.b_val_label = self._create_slider_row("Brightness:", g_layout)
        # Contrast (-100 to 100)
        self.c_slider, self.c_val_label = self._create_slider_row("Contrast:", g_layout)
        # Saturation (-100 to 100)
        self.s_slider, self.s_val_label = self._create_slider_row("Saturation:", g_layout)
        # Sharpness (-100 to 100)
        self.sh_slider, self.sh_val_label = self._create_slider_row("Sharpness:", g_layout)

        layout.addWidget(group)

        # Compare Button
        self.compare_btn = QPushButton("Hold to Compare Original", container)
        self.compare_btn.pressed.connect(self._on_compare_pressed)
        self.compare_btn.released.connect(self._on_compare_released)
        layout.addWidget(self.compare_btn)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        reset_btn = QPushButton("Reset All", container)
        reset_btn.clicked.connect(self.reset_all)
        btn_layout.addWidget(reset_btn)

        self.apply_btn = QPushButton("Apply", container)
        self.apply_btn.setObjectName("PrimaryAction")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        self.setWidget(container)

    def _create_slider_row(self, label_text: str, parent_layout: QVBoxLayout):
        header_row = QHBoxLayout()
        lbl = QLabel(label_text, self)
        lbl.setStyleSheet("font-weight: 500; font-size: 12px;")
        val_lbl = QLabel("0%", self)
        val_lbl.setStyleSheet("font-size: 11px; opacity: 0.8;")
        header_row.addWidget(lbl)
        header_row.addStretch()
        header_row.addWidget(val_lbl)
        parent_layout.addLayout(header_row)

        slider = QSlider(Qt.Horizontal, self)
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.valueChanged.connect(lambda v, l=val_lbl: self._on_slider_changed(v, l))
        parent_layout.addWidget(slider)

        return slider, val_lbl

    def _on_slider_changed(self, val: int, label: QLabel):
        prefix = "+" if val > 0 else ""
        label.setText(f"{prefix}{val}%")
        b, c, s, sh = self._get_factors()
        self.preview_requested.emit(b, c, s, sh)

    def _get_factors(self):
        # Maps -100..0..100 to 0.0..1.0..2.0
        b = 1.0 + (self.b_slider.value() / 100.0)
        c = 1.0 + (self.c_slider.value() / 100.0)
        s = 1.0 + (self.s_slider.value() / 100.0)
        sh = 1.0 + (self.sh_slider.value() / 100.0)
        return max(0.0, b), max(0.0, c), max(0.0, s), max(0.0, sh)

    def _on_apply(self):
        b, c, s, sh = self._get_factors()
        self.adjustments_applied.emit(b, c, s, sh)
        self.reset_all()

    def _on_compare_pressed(self):
        self.reset_preview_requested.emit()

    def _on_compare_released(self):
        b, c, s, sh = self._get_factors()
        self.preview_requested.emit(b, c, s, sh)

    def reset_all(self):
        # Block signals temporarily to prevent multiple emits
        self.b_slider.blockSignals(True)
        self.c_slider.blockSignals(True)
        self.s_slider.blockSignals(True)
        self.sh_slider.blockSignals(True)
        self.b_slider.setValue(0)
        self.c_slider.setValue(0)
        self.s_slider.setValue(0)
        self.sh_slider.setValue(0)
        self.b_val_label.setText("0%")
        self.c_val_label.setText("0%")
        self.s_val_label.setText("0%")
        self.sh_val_label.setText("0%")
        self.b_slider.blockSignals(False)
        self.c_slider.blockSignals(False)
        self.s_slider.blockSignals(False)
        self.sh_slider.blockSignals(False)
        self.reset_preview_requested.emit()
