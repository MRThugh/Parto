# parto/ui/panels/brush/dynamics.py
"""
Parto Brush Studio — Dynamics Section
Configures sensor and trajectory modulation for Size, Opacity, Flow, and Angle.
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
)
from parto.brush.models.settings import BrushSettings
from .widgets.section import CollapsibleSection


DYNAMICS_OPTIONS: List[str] = [
    "Off",
    "Pressure",
    "Tilt",
    "Velocity",
    "Random",
]

ANGLE_DYNAMICS_OPTIONS: List[str] = [
    "Off",
    "Direction",
    "Tilt",
    "Random",
]


class BrushDynamicsSection(QWidget):
    """
    Brush dynamics panel for mapping input tablet pressure, velocity, tilt,
    and randomization to brush properties.
    """

    def __init__(self, settings: BrushSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Dynamics", collapsed=True, parent=self)
        layout.addWidget(self.section)

        # 1. Size Dynamics
        self.combo_size = self._create_row("Size:", DYNAMICS_OPTIONS, "Modulate brush tip diameter based on stylus pressure or velocity")
        self.combo_size.currentTextChanged.connect(self._on_size_dyn_changed)

        # 2. Opacity Dynamics
        self.combo_opacity = self._create_row("Opacity:", DYNAMICS_OPTIONS, "Modulate opacity based on stylus pressure or velocity")
        self.combo_opacity.currentTextChanged.connect(self._on_opacity_dyn_changed)

        # 3. Flow Dynamics
        self.combo_flow = self._create_row("Flow:", DYNAMICS_OPTIONS, "Modulate ink flow rate based on pressure or velocity")
        self.combo_flow.currentTextChanged.connect(self._on_flow_dyn_changed)

        # 4. Angle Dynamics
        self.combo_angle = self._create_row("Angle:", ANGLE_DYNAMICS_OPTIONS, "Modulate tip angle based on stroke direction, tilt, or random rotation")
        self.combo_angle.currentTextChanged.connect(self._on_angle_dyn_changed)

        self.sync_from_settings()

    def _create_row(self, label: str, options: List[str], tooltip: str) -> QComboBox:
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel(label, self)
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("font-size: 11px; font-weight: 500;")
        lbl.setToolTip(tooltip)
        row.addWidget(lbl)

        combo = QComboBox(self)
        combo.addItems(options)
        combo.setToolTip(tooltip)
        row.addWidget(combo)

        self.section.add_layout(row)
        return combo

    def sync_from_settings(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            s = self.settings
            self._set_combo_text(self.combo_size, getattr(s, "dynamics_size", "off").capitalize())
            self._set_combo_text(self.combo_opacity, getattr(s, "dynamics_opacity", "off").capitalize())
            self._set_combo_text(self.combo_flow, getattr(s, "dynamics_flow", "off").capitalize())
            self._set_combo_text(self.combo_angle, getattr(s, "dynamics_angle", "off").capitalize())
        finally:
            self._updating = False

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        idx = combo.findText(text, Qt.MatchFixedString)
        if idx >= 0 and combo.currentIndex() != idx:
            combo.setCurrentIndex(idx)

    def _on_size_dyn_changed(self, text: str) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_dynamics_size"):
            self.settings.set_dynamics_size(text.lower())

    def _on_opacity_dyn_changed(self, text: str) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_dynamics_opacity"):
            self.settings.set_dynamics_opacity(text.lower())

    def _on_flow_dyn_changed(self, text: str) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_dynamics_flow"):
            self.settings.set_dynamics_flow(text.lower())

    def _on_angle_dyn_changed(self, text: str) -> None:
        if self._updating:
            return
        if hasattr(self.settings, "set_dynamics_angle"):
            self.settings.set_dynamics_angle(text.lower())
