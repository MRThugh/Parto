# parto/ui/panels/brush/color.py
"""
Parto Brush Studio — Color Section
Foreground, Background, Quick Swatches, Recent Swatches, Swap & Default Actions.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Tuple, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QColorDialog,
    QFrame,
)
from parto.brush.models.settings import BrushSettings
from .widgets.color_chip import ColorChipButton
from .widgets.section import CollapsibleSection
from parto.themes.manager import get_theme_manager


PALETTE_SWATCHES = [
    ("#000000", "Black"),
    ("#ffffff", "White"),
    ("#71717a", "Gray"),
    ("#ef4444", "Red"),
    ("#f97316", "Orange"),
    ("#eab308", "Yellow"),
    ("#22c55e", "Green"),
    ("#06b6d4", "Cyan"),
    ("#3b82f6", "Blue"),
    ("#a855f7", "Purple"),
]


class BrushColorSection(QWidget):
    """
    Dedicated color controls with FG/BG dual chips, recent colors tracking,
    and fast palette swatches.
    """

    color_changed = Signal(tuple)

    def __init__(self, settings: BrushSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self._updating = False
        self._recent_colors: List[Tuple[int, int, int, int]] = [
            (0, 0, 0, 255),
            (255, 255, 255, 255),
            (239, 68, 68, 255),
            (59, 130, 246, 255),
            (34, 197, 94, 255),
            (234, 179, 8, 255),
        ]
        self._recent_buttons: List[QToolButton] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Color", collapsed=False, parent=self)
        layout.addWidget(self.section)

        # 1. Dual chips row: FG, BG, Swap (X), Default (D)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)

        lbl_fg = QLabel("FG:", self)
        lbl_fg.setStyleSheet("font-size: 11px; font-weight: 500;")
        chips_row.addWidget(lbl_fg)

        self.chip_fg = ColorChipButton(self)
        self.chip_fg.setToolTip("Foreground Color (Click to select)")
        self.chip_fg.clicked.connect(self._choose_fg_color)
        chips_row.addWidget(self.chip_fg)

        lbl_bg = QLabel("BG:", self)
        lbl_bg.setStyleSheet("font-size: 11px; font-weight: 500;")
        chips_row.addWidget(lbl_bg)

        self.chip_bg = ColorChipButton(self)
        self.chip_bg.setToolTip("Background Color (Click to select)")
        self.chip_bg.clicked.connect(self._choose_bg_color)
        chips_row.addWidget(self.chip_bg)

        self.btn_swap = QToolButton(self)
        self.btn_swap.setText("⇄")
        self.btn_swap.setFixedSize(24, 24)
        self.btn_swap.setToolTip("Swap Foreground and Background (X)")
        self.btn_swap.clicked.connect(self._on_swap_colors)
        chips_row.addWidget(self.btn_swap)

        self.btn_reset = QToolButton(self)
        self.btn_reset.setText("D")
        self.btn_reset.setFixedSize(24, 24)
        self.btn_reset.setToolTip("Reset to Default Black & White (D)")
        self.btn_reset.clicked.connect(self._on_reset_colors)
        chips_row.addWidget(self.btn_reset)

        chips_row.addStretch()
        self.section.add_layout(chips_row)

        # 2. Standard Palette Swatches
        pal_row = QHBoxLayout()
        pal_row.setSpacing(4)
        for hex_code, name in PALETTE_SWATCHES:
            btn = QToolButton(self)
            btn.setFixedSize(18, 18)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_code})")
            btn.setStyleSheet(f"background-color: {hex_code}; border: 1px solid #3f3f46; border-radius: 3px;")
            btn.clicked.connect(lambda _, c=hex_code: self._set_color_from_hex(c))
            pal_row.addWidget(btn)
        pal_row.addStretch()
        self.section.add_layout(pal_row)

        # 3. Recent Colors Row
        recent_label_row = QHBoxLayout()
        lbl_recent = QLabel("Recent Colors:", self)
        lbl_recent.setStyleSheet("font-size: 10px; opacity: 0.75;")
        recent_label_row.addWidget(lbl_recent)
        recent_label_row.addStretch()
        self.section.add_layout(recent_label_row)

        self.recent_swatches_layout = QHBoxLayout()
        self.recent_swatches_layout.setSpacing(4)
        self.section.add_layout(self.recent_swatches_layout)
        self._rebuild_recent_swatches()

        self.sync_from_settings()

    def sync_from_settings(self) -> None:
        pal = get_theme_manager().get_palette()
        border = pal.get("border", "#3f3f46")
        self.chip_fg.set_rgba(self.settings.color, border_color=border)
        self.chip_bg.set_rgba(self.settings.background_color, border_color=border)

    def _choose_fg_color(self) -> None:
        r, g, b, a = self.settings.color
        col = QColorDialog.getColor(
            QColor(r, g, b, a), self, "Select Foreground Color", QColorDialog.ShowAlphaChannel
        )
        if col.isValid():
            rgba = (col.red(), col.green(), col.blue(), col.alpha())
            self.settings.set_color(rgba)
            self._add_recent_color(rgba)
            self.sync_from_settings()
            self.color_changed.emit(rgba)

    def _choose_bg_color(self) -> None:
        r, g, b, a = self.settings.background_color
        col = QColorDialog.getColor(
            QColor(r, g, b, a), self, "Select Background Color", QColorDialog.ShowAlphaChannel
        )
        if col.isValid():
            rgba = (col.red(), col.green(), col.blue(), col.alpha())
            self.settings.set_background_color(rgba)
            self._add_recent_color(rgba)
            self.sync_from_settings()

    def _on_swap_colors(self) -> None:
        self.settings.swap_colors()
        self.sync_from_settings()
        self.color_changed.emit(self.settings.color)

    def _on_reset_colors(self) -> None:
        self.settings.reset_default_colors()
        self.sync_from_settings()
        self.color_changed.emit(self.settings.color)

    def _set_color_from_hex(self, hex_code: str) -> None:
        c = QColor(hex_code)
        if c.isValid():
            rgba = (c.red(), c.green(), c.blue(), 255)
            self.settings.set_color(rgba)
            self._add_recent_color(rgba)
            self.sync_from_settings()
            self.color_changed.emit(rgba)

    def _add_recent_color(self, rgba: Tuple[int, int, int, int]) -> None:
        if rgba in self._recent_colors:
            self._recent_colors.remove(rgba)
        self._recent_colors.insert(0, rgba)
        if len(self._recent_colors) > 8:
            self._recent_colors = self._recent_colors[:8]
        self._rebuild_recent_swatches()

    def _rebuild_recent_swatches(self) -> None:
        # Clear layout items
        while self.recent_swatches_layout.count():
            item = self.recent_swatches_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for rgba in self._recent_colors:
            btn = ColorChipButton(self)
            btn.setFixedSize(18, 18)
            btn.set_rgba(rgba, border_color="#3f3f46")
            btn.setToolTip(f"#{rgba[0]:02X}{rgba[1]:02X}{rgba[2]:02X}")
            btn.clicked.connect(lambda _, col=rgba: self._set_color_from_rgba(col))
            self.recent_swatches_layout.addWidget(btn)

        self.recent_swatches_layout.addStretch()

    def _set_color_from_rgba(self, rgba: Tuple[int, int, int, int]) -> None:
        self.settings.set_color(rgba)
        self.sync_from_settings()
        self.color_changed.emit(rgba)

    def retranslate_ui(self) -> None:
        """Update color section header and button tooltips with active language."""
        from parto.localization import t
        self.section.set_title(t("brush.studio.color_title", default="Color"))
        self.btn_swap.setToolTip(t("brush.bar.swap_colors", default="Swap Foreground and Background (X)"))
        self.btn_reset.setToolTip(t("brush.bar.reset_colors", default="Reset to Default Black / White (D)"))
