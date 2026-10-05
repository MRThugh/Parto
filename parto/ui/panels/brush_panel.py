# parto/ui/panels/brush_panel.py
"""
Parto v0.3.0 - Professional Brush Settings & Presets Dock Panel
Coordinates authoritative BrushSettings, BrushPresetManager, live dab preview,
dynamic brush properties, and preset authoring/management.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, List, Any, Tuple
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QPushButton,
    QGroupBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QInputDialog,
    QToolButton,
    QCheckBox,
    QColorDialog,
    QSizePolicy,
    QScrollArea,
)

from ...brush import BrushSettings, BrushPreset, BrushPresetManager
from ..widgets.brush_bar import BrushPreviewWidget, ColorChipButton
from ...themes.manager import get_theme_manager


class BrushDock(QDockWidget):
    """
    Authoritative dockable side panel for Brush Presets and Live Brush Parameters.
    Directly inspects and controls the authoritative BrushSettings.
    """

    preset_changed = Signal(str)

    def __init__(
        self,
        settings: BrushSettings,
        preset_manager: Optional[BrushPresetManager] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__("Brush Settings", parent)
        self.setObjectName("BrushDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.settings: BrushSettings = settings
        self.preset_manager: BrushPresetManager = preset_manager or BrushPresetManager()
        self._updating_ui: bool = False

        self._init_ui()
        self.settings.add_listener(self._on_settings_changed)
        get_theme_manager().theme_changed.connect(self._on_theme_changed)
        self._sync_from_settings()

    def _init_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget(scroll)
        container.setObjectName("BrushDockContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 1. Header with Live Preview
        header_card = QWidget(container)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.preview = BrushPreviewWidget(header_card)
        self.preview.setFixedSize(38, 38)
        self.preview.clicked.connect(self._choose_fg_color)
        header_layout.addWidget(self.preview)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        self.lbl_active_preset = QLabel("Basic Round", header_card)
        self.lbl_active_preset.setStyleSheet("font-weight: 700; font-size: 13px;")
        header_text_layout.addWidget(self.lbl_active_preset)

        self.lbl_brush_summary = QLabel("12 px • 100% Opacity", header_card)
        self.lbl_brush_summary.setStyleSheet("font-size: 11px; opacity: 0.8;")
        header_text_layout.addWidget(self.lbl_brush_summary)

        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        layout.addWidget(header_card)

        # 2. Presets Group
        self._init_presets_group(layout, container)

        # 3. Brush Dynamics Group
        self._init_dynamics_group(layout, container)

        # 4. Color & Mode Group
        self._init_color_mode_group(layout, container)

        # 5. Quick Reset Button
        self.btn_reset_defaults = QPushButton("Reset Brush to Defaults", container)
        self.btn_reset_defaults.setToolTip("Reset brush parameters to preset defaults")
        self.btn_reset_defaults.clicked.connect(self._reset_to_preset_defaults)
        layout.addWidget(self.btn_reset_defaults)

        layout.addStretch()
        scroll.setWidget(container)
        self.setWidget(scroll)

    def _init_presets_group(self, parent_layout: QVBoxLayout, container: QWidget) -> None:
        group = QGroupBox("Brush Presets", container)
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(8)

        # Search filter
        self.search_edit = QLineEdit(group)
        self.search_edit.setPlaceholderText("Filter presets...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._filter_presets)
        g_layout.addWidget(self.search_edit)

        # Presets List
        self.preset_list = QListWidget(group)
        self.preset_list.setFixedHeight(130)
        self.preset_list.itemSelectionChanged.connect(self._on_preset_item_selected)
        g_layout.addWidget(self.preset_list)

        # Preset Management Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_save_preset = QPushButton("+ Save Preset...", group)
        self.btn_save_preset.setToolTip("Save current settings as a new custom preset")
        self.btn_save_preset.clicked.connect(self._save_custom_preset)
        btn_row.addWidget(self.btn_save_preset)

        self.btn_del_preset = QPushButton("Delete", group)
        self.btn_del_preset.setToolTip("Delete selected user preset")
        self.btn_del_preset.setEnabled(False)
        self.btn_del_preset.clicked.connect(self._delete_selected_preset)
        btn_row.addWidget(self.btn_del_preset)

        g_layout.addLayout(btn_row)
        parent_layout.addWidget(group)
        self._populate_presets_list()

    def _init_dynamics_group(self, parent_layout: QVBoxLayout, container: QWidget) -> None:
        group = QGroupBox("Brush Dynamics", container)
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        # Size (1..500 px)
        self.slider_size, self.spin_size = self._create_slider_spin_row(
            "Size:", 1, 500, " px", g_layout, group
        )
        self.slider_size.valueChanged.connect(self._on_slider_size_changed)
        self.spin_size.valueChanged.connect(self._on_spin_size_changed)

        # Opacity (1..100 %)
        self.slider_opacity, self.spin_opacity = self._create_slider_spin_row(
            "Opacity:", 1, 100, " %", g_layout, group
        )
        self.slider_opacity.valueChanged.connect(self._on_slider_opacity_changed)
        self.spin_opacity.valueChanged.connect(self._on_spin_opacity_changed)

        # Flow (1..100 %)
        self.slider_flow, self.spin_flow = self._create_slider_spin_row(
            "Flow:", 1, 100, " %", g_layout, group
        )
        self.slider_flow.valueChanged.connect(self._on_slider_flow_changed)
        self.spin_flow.valueChanged.connect(self._on_spin_flow_changed)

        # Hardness (0..100 %)
        self.slider_hardness, self.spin_hardness = self._create_slider_spin_row(
            "Hardness:", 0, 100, " %", g_layout, group
        )
        self.slider_hardness.valueChanged.connect(self._on_slider_hardness_changed)
        self.spin_hardness.valueChanged.connect(self._on_spin_hardness_changed)

        # Spacing (5..200 %)
        self.slider_spacing, self.spin_spacing = self._create_slider_spin_row(
            "Spacing:", 5, 200, " %", g_layout, group
        )
        self.slider_spacing.valueChanged.connect(self._on_slider_spacing_changed)
        self.spin_spacing.valueChanged.connect(self._on_spin_spacing_changed)

        parent_layout.addWidget(group)

    def _create_slider_spin_row(
        self,
        label_text: str,
        min_val: int,
        max_val: int,
        suffix: str,
        parent_layout: QVBoxLayout,
        parent_widget: QWidget,
    ) -> Tuple[QSlider, QSpinBox]:
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        lbl = QLabel(label_text, parent_widget)
        lbl.setFixedWidth(56)
        lbl.setStyleSheet("font-size: 11px; font-weight: 500;")
        row_layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal, parent_widget)
        slider.setRange(min_val, max_val)
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_layout.addWidget(slider)

        spin = QSpinBox(parent_widget)
        spin.setRange(min_val, max_val)
        spin.setSuffix(suffix)
        spin.setFixedWidth(76)
        spin.setAlignment(Qt.AlignRight)
        row_layout.addWidget(spin)

        parent_layout.addLayout(row_layout)
        return slider, spin

    def _init_color_mode_group(self, parent_layout: QVBoxLayout, container: QWidget) -> None:
        group = QGroupBox("Color & Mode", container)
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(8)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)

        lbl_fg = QLabel("FG:", group)
        lbl_fg.setStyleSheet("font-size: 11px; font-weight: 500;")
        color_row.addWidget(lbl_fg)

        self.chip_fg = ColorChipButton(group)
        self.chip_fg.setToolTip("Foreground Color (Click to change)")
        self.chip_fg.clicked.connect(self._choose_fg_color)
        color_row.addWidget(self.chip_fg)

        lbl_bg = QLabel("BG:", group)
        lbl_bg.setStyleSheet("font-size: 11px; font-weight: 500;")
        color_row.addWidget(lbl_bg)

        self.chip_bg = ColorChipButton(group)
        self.chip_bg.setToolTip("Background Color (Click to change)")
        self.chip_bg.clicked.connect(self._choose_bg_color)
        color_row.addWidget(self.chip_bg)

        self.btn_swap_colors = QToolButton(group)
        self.btn_swap_colors.setText("⇄")
        self.btn_swap_colors.setFixedSize(22, 22)
        self.btn_swap_colors.setToolTip("Swap Foreground and Background Colors (X)")
        self.btn_swap_colors.clicked.connect(self._on_swap_colors)
        color_row.addWidget(self.btn_swap_colors)

        self.btn_reset_colors = QToolButton(group)
        self.btn_reset_colors.setText("D")
        self.btn_reset_colors.setFixedSize(22, 22)
        self.btn_reset_colors.setToolTip("Reset to Default Black / White (D)")
        self.btn_reset_colors.clicked.connect(self._on_reset_colors)
        color_row.addWidget(self.btn_reset_colors)

        color_row.addStretch()
        g_layout.addLayout(color_row)

        # Mode: Paint vs Erase
        self.cb_erase_mode = QCheckBox("Erase Mode (Alpha Eraser)", group)
        self.cb_erase_mode.setToolTip("When checked, stroke removes layer opacity instead of depositing color")
        self.cb_erase_mode.toggled.connect(self._on_erase_mode_toggled)
        g_layout.addWidget(self.cb_erase_mode)

        parent_layout.addWidget(group)

    # --- Preset Management & Selection ---

    def _populate_presets_list(self) -> None:
        self.preset_list.blockSignals(True)
        self.preset_list.clear()

        all_presets = self.preset_manager.get_all_presets()
        active_name = self.preset_manager.active_preset_name or "Basic Round"

        selected_item = None
        for p in all_presets:
            tag = "  " if p.is_builtin else "  ★ "
            item = QListWidgetItem(f"{p.name}{tag}")
            item.setData(Qt.UserRole, p.name)
            item.setToolTip(p.description or f"{p.name} ({p.size}px)")
            self.preset_list.addItem(item)
            if p.name.lower() == active_name.lower():
                selected_item = item

        if selected_item:
            self.preset_list.setCurrentItem(selected_item)
            self._update_delete_button_state(selected_item)

        self.preset_list.blockSignals(False)

    def _filter_presets(self, query: str) -> None:
        q = query.strip().lower()
        for i in range(self.preset_list.count()):
            item = self.preset_list.item(i)
            preset_name = str(item.data(Qt.UserRole) or "")
            item.setHidden(bool(q and q not in preset_name.lower()))

    def _on_preset_item_selected(self) -> None:
        if self._updating_ui:
            return
        item = self.preset_list.currentItem()
        if not item:
            return
        name = str(item.data(Qt.UserRole))
        self._update_delete_button_state(item)
        success = self.preset_manager.apply_preset(name, self.settings)
        if success:
            self.lbl_active_preset.setText(name)
            self.preset_changed.emit(name)

    def _update_delete_button_state(self, item: Optional[QListWidgetItem]) -> None:
        if not item:
            self.btn_del_preset.setEnabled(False)
            return
        name = str(item.data(Qt.UserRole))
        preset = self.preset_manager.get_preset(name)
        # Built-in presets are protected from deletion
        self.btn_del_preset.setEnabled(bool(preset and not preset.is_builtin))

    def _save_custom_preset(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            "Save Brush Preset",
            "Preset Name:",
            text=f"Custom {len(self.preset_manager.get_user_presets()) + 1}",
        )
        if ok and name.strip():
            preset = self.preset_manager.create_user_preset(
                name.strip(),
                self.settings,
                description=f"User preset ({self.settings.size}px)",
            )
            self._populate_presets_list()
            self.lbl_active_preset.setText(preset.name)

    def _delete_selected_preset(self) -> None:
        item = self.preset_list.currentItem()
        if not item:
            return
        name = str(item.data(Qt.UserRole))
        preset = self.preset_manager.get_preset(name)
        if not preset or preset.is_builtin:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete preset '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.preset_manager.delete_user_preset(name)
            self._populate_presets_list()

    def _reset_to_preset_defaults(self) -> None:
        current_name = self.preset_manager.active_preset_name or "Basic Round"
        self.preset_manager.apply_preset(current_name, self.settings)

    # --- Parameter Modifiers ---

    def _on_slider_size_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.spin_size.blockSignals(True)
        self.spin_size.setValue(val)
        self.spin_size.blockSignals(False)
        self.settings.set_size(val)

    def _on_spin_size_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.slider_size.blockSignals(True)
        self.slider_size.setValue(val)
        self.slider_size.blockSignals(False)
        self.settings.set_size(val)

    def _on_slider_opacity_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.spin_opacity.blockSignals(True)
        self.spin_opacity.setValue(val)
        self.spin_opacity.blockSignals(False)
        self.settings.set_opacity(val / 100.0)

    def _on_spin_opacity_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.slider_opacity.blockSignals(True)
        self.slider_opacity.setValue(val)
        self.slider_opacity.blockSignals(False)
        self.settings.set_opacity(val / 100.0)

    def _on_slider_flow_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.spin_flow.blockSignals(True)
        self.spin_flow.setValue(val)
        self.spin_flow.blockSignals(False)
        self.settings.set_flow(val / 100.0)

    def _on_spin_flow_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.slider_flow.blockSignals(True)
        self.slider_flow.setValue(val)
        self.slider_flow.blockSignals(False)
        self.settings.set_flow(val / 100.0)

    def _on_slider_hardness_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.spin_hardness.blockSignals(True)
        self.spin_hardness.setValue(val)
        self.spin_hardness.blockSignals(False)
        self.settings.set_hardness(val / 100.0)

    def _on_spin_hardness_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.slider_hardness.blockSignals(True)
        self.slider_hardness.setValue(val)
        self.slider_hardness.blockSignals(False)
        self.settings.set_hardness(val / 100.0)

    def _on_slider_spacing_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.spin_spacing.blockSignals(True)
        self.spin_spacing.setValue(val)
        self.spin_spacing.blockSignals(False)
        self.settings.set_spacing(val / 100.0)

    def _on_spin_spacing_changed(self, val: int) -> None:
        if self._updating_ui:
            return
        self.slider_spacing.blockSignals(True)
        self.slider_spacing.setValue(val)
        self.slider_spacing.blockSignals(False)
        self.settings.set_spacing(val / 100.0)

    def _on_erase_mode_toggled(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self.settings.set_is_eraser(checked)

    # --- Color Interactions ---

    def _choose_fg_color(self) -> None:
        r, g, b, a = self.settings.color
        col = QColorDialog.getColor(QColor(r, g, b, a), self, "Select Foreground Color", QColorDialog.ShowAlphaChannel)
        if col.isValid():
            self.settings.set_color((col.red(), col.green(), col.blue(), col.alpha()))

    def _choose_bg_color(self) -> None:
        r, g, b, a = self.settings.background_color
        col = QColorDialog.getColor(QColor(r, g, b, a), self, "Select Background Color", QColorDialog.ShowAlphaChannel)
        if col.isValid():
            self.settings.set_background_color((col.red(), col.green(), col.blue(), col.alpha()))

    def _on_swap_colors(self) -> None:
        self.settings.swap_colors()

    def _on_reset_colors(self) -> None:
        self.settings.reset_default_colors()

    # --- State Synchronization ---

    def _on_settings_changed(self) -> None:
        self._sync_from_settings()

    def _sync_from_settings(self) -> None:
        self._updating_ui = True
        try:
            s = self.settings

            # Dynamics
            self._set_slider_and_spin(self.slider_size, self.spin_size, s.size)
            self._set_slider_and_spin(self.slider_opacity, self.spin_opacity, int(round(s.opacity * 100)))
            flow_val = int(round(getattr(s, "flow", 1.0) * 100))
            self._set_slider_and_spin(self.slider_flow, self.spin_flow, flow_val)
            self._set_slider_and_spin(self.slider_hardness, self.spin_hardness, int(round(s.hardness * 100)))
            spacing_val = int(round(getattr(s, "spacing", 0.25) * 100))
            self._set_slider_and_spin(self.slider_spacing, self.spin_spacing, spacing_val)

            # Colors & Mode
            pal = get_theme_manager().get_palette()
            border = pal.get("border", "#3f3f46")
            self.chip_fg.set_rgba(s.color, border_color=border)
            self.chip_bg.set_rgba(s.background_color, border_color=border)

            is_eraser = getattr(s, "is_eraser", False)
            if self.cb_erase_mode.isChecked() != is_eraser:
                self.cb_erase_mode.blockSignals(True)
                self.cb_erase_mode.setChecked(is_eraser)
                self.cb_erase_mode.blockSignals(False)

            # Header info
            active_name = self.preset_manager.active_preset_name or "Custom"
            mode_tag = " (Eraser)" if is_eraser else ""
            self.lbl_active_preset.setText(f"{active_name}{mode_tag}")
            self.lbl_brush_summary.setText(f"{s.size} px • {int(round(s.opacity * 100))}% Opacity")

            # Preview
            self.preview.update_preview(
                s.size,
                s.opacity * (1.0 if not is_eraser else 0.5),
                s.hardness,
                s.color if not is_eraser else (255, 255, 255, 180),
            )
        finally:
            self._updating_ui = False

    def _set_slider_and_spin(self, slider: QSlider, spin: QSpinBox, val: int) -> None:
        if slider.value() != val:
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)
        if spin.value() != val:
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)

    def _on_theme_changed(self, _: str) -> None:
        self._sync_from_settings()


# Compatibility alias
BrushPanel = BrushDock
