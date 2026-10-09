# parto/ui/panels/brush/properties.py
"""
Parto Brush Studio — Brush Tip Properties Section
Precision controls for Size, Hardness, Spacing, Angle, and Roundness.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from parto.brush.models.settings import BrushSettings
from .widgets.slider import LabeledSliderSpinRow
from .widgets.section import CollapsibleSection


class BrushTipPropertiesSection(QWidget):
    """
    Precision controls for brush geometry and tip stamping behavior.
    """

    def __init__(self, settings: BrushSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Brush Tip", collapsed=False, parent=self)
        layout.addWidget(self.section)

        # Size: 1 to 500 px
        self.row_size = LabeledSliderSpinRow(
            label="Size:",
            min_val=1,
            max_val=500,
            suffix=" px",
            default_val=self.settings.size,
            tooltip="Brush tip diameter in pixels ([ and ] shortcuts)",
            parent=self,
        )
        self.row_size.valueChanged.connect(self._on_size_changed)
        self.section.add_widget(self.row_size)

        # Hardness: 0 to 100 %
        self.row_hardness = LabeledSliderSpinRow(
            label="Hardness:",
            min_val=0,
            max_val=100,
            suffix=" %",
            default_val=int(round(self.settings.hardness * 100)),
            tooltip="Edge sharpness vs radial feathering falloff (Ctrl+[ and Ctrl+] shortcuts)",
            parent=self,
        )
        self.row_hardness.valueChanged.connect(self._on_hardness_changed)
        self.section.add_widget(self.row_hardness)

        # Spacing: 5 to 200 %
        self.row_spacing = LabeledSliderSpinRow(
            label="Spacing:",
            min_val=5,
            max_val=200,
            suffix=" %",
            default_val=int(round(self.settings.spacing * 100)),
            tooltip="Distance between consecutive stamped dabs relative to brush radius",
            parent=self,
        )
        self.row_spacing.valueChanged.connect(self._on_spacing_changed)
        self.section.add_widget(self.row_spacing)

        # Angle: 0 to 360 °
        self.row_angle = LabeledSliderSpinRow(
            label="Angle:",
            min_val=0,
            max_val=360,
            suffix="°",
            default_val=int(round(getattr(self.settings, "angle", 0.0))),
            tooltip="Brush tip rotation in degrees",
            parent=self,
        )
        self.row_angle.valueChanged.connect(self._on_angle_changed)
        self.section.add_widget(self.row_angle)

        # Roundness: 1 to 100 %
        self.row_roundness = LabeledSliderSpinRow(
            label="Roundness:",
            min_val=1,
            max_val=100,
            suffix=" %",
            default_val=int(round(getattr(self.settings, "roundness", 1.0) * 100)),
            tooltip="Aspect ratio of brush tip ellipse (100% is circular, lower is flat/chisel)",
            parent=self,
        )
        self.row_roundness.valueChanged.connect(self._on_roundness_changed)
        self.section.add_widget(self.row_roundness)

    def focus_size(self) -> None:
        """Focus the size spinbox for keyboard entry."""
        self.section.set_collapsed(False)
        self.row_size.spin.setFocus()
        self.row_size.spin.selectAll()

    def sync_from_settings(self) -> None:
        """Reflect authoritative BrushSettings values onto UI controls."""
        if self._updating:
            return
        self._updating = True
        try:
            s = self.settings
            self.row_size.setValue(s.size)
            self.row_hardness.setValue(int(round(s.hardness * 100)))
            self.row_spacing.setValue(int(round(s.spacing * 100)))
            self.row_angle.setValue(int(round(getattr(s, "angle", 0.0))))
            self.row_roundness.setValue(int(round(getattr(s, "roundness", 1.0) * 100)))
        finally:
            self._updating = False

    def _on_size_changed(self, val: int) -> None:
        if self._updating:
            return
        self.settings.set_size(val)

    def _on_hardness_changed(self, val: int) -> None:
        if self._updating:
            return
        self.settings.set_hardness(val / 100.0)

    def _on_spacing_changed(self, val: int) -> None:
        if self._updating:
            return
        self.settings.set_spacing(val / 100.0)

    def _on_angle_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_angle"):
            self.settings.set_angle(float(val))

    def _on_roundness_changed(self, val: int) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_roundness"):
            self.settings.set_roundness(val / 100.0)

    def retranslate_ui(self) -> None:
        """Update section title and row labels with active language."""
        from parto.localization import t
        self.section.set_title(t("brush.studio.tip_title", default="Brush Tip"))
        self.row_size.label.setText(t("brush.bar.size", default="Size:"))
        self.row_hardness.label.setText(t("brush.bar.hardness", default="Hardness:"))
        self.row_spacing.label.setText(t("brush.studio.spacing", default="Spacing:"))
        self.row_angle.label.setText(t("brush.studio.angle", default="Angle:"))
        self.row_roundness.label.setText(t("brush.studio.roundness", default="Roundness:"))
