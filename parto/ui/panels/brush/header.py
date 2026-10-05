# parto/ui/panels/brush/header.py
"""
Parto Brush Studio — Header Card
Displays real-time brush preview, preset badge, size/opacity summary,
and quick preset management options.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Tuple
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QToolButton,
    QMenu,
    QFrame,
)
from parto.brush.models.settings import BrushSettings
from parto.brush.presets.preset_manager import BrushPresetManager
from .widgets.brush_preview import StudioBrushPreviewWidget
from parto.themes.manager import get_theme_manager


class BrushStudioHeader(QFrame):
    """
    Header card showing active brush preview, name, summary, and quick management triggers.
    """

    color_clicked = Signal()
    save_preset_clicked = Signal()
    reset_preset_clicked = Signal()
    duplicate_preset_clicked = Signal()
    export_preset_clicked = Signal()
    import_preset_clicked = Signal()

    def __init__(
        self,
        settings: BrushSettings,
        preset_manager: BrushPresetManager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("BrushStudioHeader")
        self.settings = settings
        self.preset_manager = preset_manager

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # 1. Real-time tip preview
        self.preview = StudioBrushPreviewWidget(self)
        self.preview.clicked.connect(self.color_clicked.emit)
        layout.addWidget(self.preview)

        # 2. Text layout
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_name = QLabel("Basic Round", self)
        self.lbl_name.setStyleSheet("font-weight: 700; font-size: 13px;")
        text_layout.addWidget(self.lbl_name)

        self.lbl_summary = QLabel("12 px • 100% Opacity • 80% Hardness", self)
        self.lbl_summary.setStyleSheet("font-size: 11px; opacity: 0.85;")
        text_layout.addWidget(self.lbl_summary)

        layout.addLayout(text_layout)
        layout.addStretch()

        # 3. Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        # Reset button
        self.btn_reset = QToolButton(self)
        self.btn_reset.setText("↺")
        self.btn_reset.setToolTip("Reset Brush to Preset Defaults (Shift+F9)")
        self.btn_reset.setFixedSize(26, 26)
        self.btn_reset.clicked.connect(self.reset_preset_clicked.emit)
        btn_layout.addWidget(self.btn_reset)

        # Save Preset (+) button
        self.btn_save = QToolButton(self)
        self.btn_save.setText("+")
        self.btn_save.setToolTip("Save Current Settings as New Preset")
        self.btn_save.setFixedSize(26, 26)
        self.btn_save.clicked.connect(self.save_preset_clicked.emit)
        btn_layout.addWidget(self.btn_save)

        # More menu (⋮)
        self.btn_more = QToolButton(self)
        self.btn_more.setText("⋮")
        self.btn_more.setToolTip("Preset & Brush Options")
        self.btn_more.setFixedSize(26, 26)
        self.btn_more.setPopupMode(QToolButton.InstantPopup)
        self._init_more_menu()
        btn_layout.addWidget(self.btn_more)

        layout.addLayout(btn_layout)
        self._apply_styling()
        get_theme_manager().theme_changed.connect(lambda _: self._apply_styling())

    def _init_more_menu(self) -> None:
        menu = QMenu(self)
        act_save = menu.addAction("+ Save as New Preset...")
        act_save.triggered.connect(self.save_preset_clicked.emit)

        act_dup = menu.addAction("Duplicate Current Preset (Ctrl+D)")
        act_dup.triggered.connect(self.duplicate_preset_clicked.emit)

        menu.addSeparator()
        act_reset = menu.addAction("Reset Brush to Defaults (Shift+F9)")
        act_reset.triggered.connect(self.reset_preset_clicked.emit)

        menu.addSeparator()
        act_export = menu.addAction("Export Active Preset...")
        act_export.triggered.connect(self.export_preset_clicked.emit)

        act_import = menu.addAction("Import Preset from File...")
        act_import.triggered.connect(self.import_preset_clicked.emit)

        self.btn_more.setMenu(menu)

    def sync_from_settings(self) -> None:
        s = self.settings
        p_name = self.preset_manager.active_preset_name or "Custom"
        mode_tag = " [Eraser]" if s.is_eraser else ""
        self.lbl_name.setText(f"{p_name}{mode_tag}")

        op_pct = int(round(s.opacity * 100))
        hd_pct = int(round(s.hardness * 100))
        angle_str = f" • {int(round(s.angle))}°" if abs(s.angle) > 0.01 else ""
        self.lbl_summary.setText(f"{s.size} px • {op_pct}% Opacity • {hd_pct}% Hardness{angle_str}")

        self.preview.update_preview(
            size=s.size,
            opacity=s.opacity if not s.is_eraser else 0.5,
            hardness=s.hardness,
            color=s.color if not s.is_eraser else (255, 255, 255, 200),
            angle=s.angle,
            roundness=s.roundness,
        )

    def _apply_styling(self) -> None:
        pal = get_theme_manager().get_palette()
        border = pal.get("border_subtle", "#27272a")
        sunken = pal.get("surface_sunken", "#18181b")
        text = pal.get("text", "#f4f4f5")
        primary = pal.get("primary", "#0284c7")

        self.setStyleSheet(f"""
            QFrame#BrushStudioHeader {{
                background-color: {sunken};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text};
            }}
            QToolButton {{
                background-color: transparent;
                border: 1px solid {border};
                border-radius: 4px;
                color: {text};
                font-size: 13px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                border-color: {primary};
                background-color: {pal.get('surface_raised', '#27272a')};
            }}
        """)
