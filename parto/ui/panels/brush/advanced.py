# parto/ui/panels/brush/advanced.py
"""
Parto Brush Studio — Advanced & Stroke Dynamics Section
Controls Scatter, Jitter, and Stroke Smoothing / Stabilization.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from parto.brush.models.settings import BrushSettings
from .widgets.slider import LabeledSliderSpinRow
from .widgets.section import CollapsibleSection


class BrushAdvancedSection(QWidget):
    """
    Advanced parameters for organic particle scattering, jitter, and stroke stabilization.
    """

    def __init__(self, settings: BrushSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Advanced & Stroke", collapsed=True, parent=self)
        layout.addWidget(self.section)

        # 1. Stroke Smoothing / Stabilization: 0 to 100 %
        self.row_smoothing = LabeledSliderSpinRow(
            label="Smoothing:",
            min_val=0,
            max_val=100,
            suffix=" %",
            default_val=int(round(getattr(self.settings, "smoothing", 0.0) * 100)),
            tooltip="Stroke stabilization filter reducing hand tremor and line jitter",
            parent=self,
        )
        self.row_smoothing.valueChanged.connect(self._on_smoothing_changed)
        self.section.add_widget(self.row_smoothing)

        # 2. Scatter: 0 to 100 %
        self.row_scatter = LabeledSliderSpinRow(
            label="Scatter:",
            min_val=0,
            max_val=100,
            suffix=" %",
            default_val=int(round(getattr(self.settings, "scatter", 0.0) * 100)),
            tooltip="Random spatial dispersion perpendicular to stroke direction",
            parent=self,
        )
        self.row_scatter.valueChanged.connect(self._on_scatter_changed)
        self.section.add_widget(self.row_scatter)

        # 3. Size Jitter: 0 to 100 %
        self.row_size_jitter = LabeledSliderSpinRow(
            label="Size Jitter:",
            min_val=0,
            max_val=100,
            suffix=" %",
            default_val=int(round(getattr(self.settings, "size_jitter", 0.0) * 100)),
            tooltip="Stochastic variance in dab diameter along the stroke",
            parent=self,
        )
        self.row_size_jitter.valueChanged.connect(self._on_size_jitter_changed)
        self.section.add_widget(self.row_size_jitter)

        # 4. Angle Jitter: 0 to 100 %
        self.row_angle_jitter = LabeledSliderSpinRow(
            label="Angle Jitter:",
            min_val=0,
            max_val=100,
            suffix=" %",
            default_val=int(round(getattr(self.settings, "angle_jitter", 0.0) * 100)),
            tooltip="Random angular deviation per stamped dab",
            parent=self,
        )
        self.row_angle_jitter.valueChanged.connect(self._on_angle_jitter_changed)
        self.section.add_widget(self.row_angle_jitter)

        self.sync_from_settings()

    def sync_from_settings(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            s = self.settings
            self.row_smoothing.setValue(int(round(getattr(s, "smoothing", 0.0) * 100)))
            self.row_scatter.setValue(int(round(getattr(s, "scatter", 0.0) * 100)))
            self.row_size_jitter.setValue(int(round(getattr(s, "size_jitter", 0.0) * 100)))
            self.row_angle_jitter.setValue(int(round(getattr(s, "angle_jitter", 0.0) * 100)))
        finally:
            self._updating = False

    def _on_smoothing_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_smoothing"):
            self.settings.set_smoothing(val / 100.0)

    def _on_scatter_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_scatter"):
            self.settings.set_scatter(val / 100.0)

    def _on_size_jitter_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_size_jitter"):
            self.settings.set_size_jitter(val / 100.0)

    def _on_angle_jitter_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_angle_jitter"):
            self.settings.set_angle_jitter(val / 100.0)
