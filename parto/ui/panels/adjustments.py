# parto/ui/panels/adjustments.py
"""
Parto v0.4.0 - Live Color Adjustments Dock Panel
Author: Ali Kamrani (MRThugh)
Integrated with Localization Subsystem.
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
from parto.localization import t


class AdjustmentDock(QDockWidget):
    """
    Dockable side panel for Brightness, Contrast, Saturation, and Sharpness controls.
    """
    adjustments_applied = Signal(float, float, float, float)
    preview_requested = Signal(float, float, float, float)
    reset_preview_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(t("panel.adjustments.title", default="Adjustments"), parent)
        self.setObjectName("AdjustmentDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._init_ui()

    def _init_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Sliders group
        self.group = QGroupBox(t("panel.adjustments.title", default="Color Tuning"), container)
        g_layout = QVBoxLayout(self.group)
        g_layout.setSpacing(12)

        # Brightness (-100 to 100)
        self.b_lbl, self.b_slider, self.b_val_label = self._create_slider_row(
            t("panel.adjustments.brightness", default="Brightness") + ":", g_layout
        )
        # Contrast (-100 to 100)
        self.c_lbl, self.c_slider, self.c_val_label = self._create_slider_row(
            t("panel.adjustments.contrast", default="Contrast") + ":", g_layout
        )
        # Saturation (-100 to 100)
        self.s_lbl, self.s_slider, self.s_val_label = self._create_slider_row(
            t("panel.adjustments.saturation", default="Saturation") + ":", g_layout
        )
        # Sharpness (-100 to 100)
        self.sh_lbl, self.sh_slider, self.sh_val_label = self._create_slider_row(
            t("filter.sharpen", default="Sharpness") + ":", g_layout
        )

        layout.addWidget(self.group)

        # Compare Button
        self.compare_btn = QPushButton(t("panel.adjustments.compare", default="Hold to Compare Original"), container)
        self.compare_btn.pressed.connect(self._on_compare_pressed)
        self.compare_btn.released.connect(self._on_compare_released)
        layout.addWidget(self.compare_btn)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.reset_btn = QPushButton(t("panel.adjustments.reset", default="Reset All"), container)
        self.reset_btn.clicked.connect(self.reset_all)
        btn_layout.addWidget(self.reset_btn)

        self.apply_btn = QPushButton(t("panel.adjustments.apply", default="Apply"), container)
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

        return lbl, slider, val_lbl

    def _on_slider_changed(self, val: int, label: QLabel):
        label.setText(f"{val}%")
        self._emit_preview()

    def _emit_preview(self):
        b = self.b_slider.value() / 100.0
        c = self.c_slider.value() / 100.0
        s = self.s_slider.value() / 100.0
        sh = self.sh_slider.value() / 100.0
        self.preview_requested.emit(b, c, s, sh)

    def _on_compare_pressed(self):
        self.reset_preview_requested.emit()

    def _on_compare_released(self):
        self._emit_preview()

    def _on_apply(self):
        b = self.b_slider.value() / 100.0
        c = self.c_slider.value() / 100.0
        s = self.s_slider.value() / 100.0
        sh = self.sh_slider.value() / 100.0
        self.adjustments_applied.emit(b, c, s, sh)

    def reset_all(self):
        for s in (self.b_slider, self.c_slider, self.s_slider, self.sh_slider):
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)

        for l in (self.b_val_label, self.c_val_label, self.s_val_label, self.sh_val_label):
            l.setText("0%")

        self.reset_preview_requested.emit()

    def retranslate_ui(self):
        """Update texts when application language changes."""
        self.setWindowTitle(t("panel.adjustments.title", default="Adjustments"))
        if hasattr(self, "group"):
            self.group.setTitle(t("panel.adjustments.title", default="Color Tuning"))
        if hasattr(self, "b_lbl"):
            self.b_lbl.setText(t("panel.adjustments.brightness", default="Brightness") + ":")
        if hasattr(self, "c_lbl"):
            self.c_lbl.setText(t("panel.adjustments.contrast", default="Contrast") + ":")
        if hasattr(self, "s_lbl"):
            self.s_lbl.setText(t("panel.adjustments.saturation", default="Saturation") + ":")
        if hasattr(self, "sh_lbl"):
            self.sh_lbl.setText(t("filter.sharpen", default="Sharpness") + ":")
        if hasattr(self, "compare_btn"):
            self.compare_btn.setText(t("panel.adjustments.compare", default="Hold to Compare Original"))
        if hasattr(self, "reset_btn"):
            self.reset_btn.setText(t("panel.adjustments.reset", default="Reset All"))
        if hasattr(self, "apply_btn"):
            self.apply_btn.setText(t("panel.adjustments.apply", default="Apply"))
