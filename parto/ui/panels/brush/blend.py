# parto/ui/panels/brush/blend.py
"""
Parto Brush Studio — Blending & Rendering Section
Controls Blend Mode, Opacity, Flow, and Alpha Eraser Mode.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
)
from parto.brush.models.settings import BrushSettings
from parto.brush.models.enums import BlendMode
from .widgets.slider import LabeledSliderSpinRow
from .widgets.section import CollapsibleSection


BLEND_MODES: List[str] = [
    "Normal",
    "Multiply",
    "Screen",
    "Overlay",
    "Darken",
    "Lighten",
]


class BrushBlendSection(QWidget):
    """
    Controls layer blending, opacity, flow transfer, and eraser mode.
    """

    def __init__(self, settings: BrushSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Blend & Rendering", collapsed=False, parent=self)
        layout.addWidget(self.section)

        # 1. Blend Mode Dropdown
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)

        lbl_mode = QLabel("Blend Mode:", self)
        lbl_mode.setFixedWidth(70)
        lbl_mode.setStyleSheet("font-size: 11px; font-weight: 500;")
        mode_row.addWidget(lbl_mode)

        self.combo_mode = QComboBox(self)
        self.combo_mode.addItems(BLEND_MODES)
        self.combo_mode.setToolTip("Photometric blending calculation for brush dabs on the active layer")
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.combo_mode)
        self.section.add_layout(mode_row)

        # 2. Opacity Slider & Spin (1 to 100 %)
        self.row_opacity = LabeledSliderSpinRow(
            label="Opacity:",
            min_val=1,
            max_val=100,
            suffix=" %",
            default_val=int(round(self.settings.opacity * 100)),
            tooltip="Maximum opacity limit for the stroke (Keys 1-9, 0)",
            parent=self,
        )
        self.row_opacity.valueChanged.connect(self._on_opacity_changed)
        self.section.add_widget(self.row_opacity)

        # 3. Flow Slider & Spin (1 to 100 %)
        self.row_flow = LabeledSliderSpinRow(
            label="Flow:",
            min_val=1,
            max_val=100,
            suffix=" %",
            default_val=int(round(self.settings.flow * 100)),
            tooltip="Rate at which paint deposits per stamped dab",
            parent=self,
        )
        self.row_flow.valueChanged.connect(self._on_flow_changed)
        self.section.add_widget(self.row_flow)

        # 4. Erase Mode Checkbox
        self.cb_eraser = QCheckBox("Erase Mode (Alpha Eraser)", self)
        self.cb_eraser.setToolTip("When checked, stroke removes layer opacity instead of depositing pigment (Shift+B)")
        self.cb_eraser.setChecked(self.settings.is_eraser)
        self.cb_eraser.toggled.connect(self._on_eraser_toggled)
        self.section.add_widget(self.cb_eraser)

        self.sync_from_settings()

    def sync_from_settings(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            s = self.settings
            self.row_opacity.setValue(int(round(s.opacity * 100)))
            self.row_flow.setValue(int(round(s.flow * 100)))

            mode_str = s.blend_mode.value if hasattr(s.blend_mode, "value") else str(s.blend_mode)
            idx = self.combo_mode.findText(mode_str.capitalize(), Qt.MatchFixedString)
            if idx >= 0 and self.combo_mode.currentIndex() != idx:
                self.combo_mode.setCurrentIndex(idx)

            if self.cb_eraser.isChecked() != s.is_eraser:
                self.cb_eraser.setChecked(s.is_eraser)
        finally:
            self._updating = False

    def _on_mode_changed(self, text: str) -> None:
        if self._updating:
            return
        self.settings.blend_mode = text.lower()

    def _on_opacity_changed(self, val: int) -> None:
        if self._updating:
            return
        self.settings.set_opacity(val / 100.0)

    def _on_flow_changed(self, val: int) -> None:
        if self._updating:
            return
        self.settings.set_flow(val / 100.0)

    def _on_eraser_toggled(self, checked: bool) -> None:
        if self._updating:
            return
        self.settings.set_is_eraser(checked)

    def retranslate_ui(self) -> None:
        """Update blend section header and labels with active language."""
        from parto.localization import t
        self.section.set_title(t("brush.studio.blend_title", default="Blend & Rendering"))
        self.row_opacity.label.setText(t("brush.bar.opacity", default="Opacity:"))
        self.row_flow.label.setText(t("brush.studio.flow", default="Flow:"))
        self.cb_eraser.setText(t("brush.studio.erase_mode", default="Erase Mode (Alpha Eraser)"))
