# parto/ui/panels/brush/dock.py
"""
Parto Brush Studio — Authoritative Studio Dock Widget
Comprehensive dockable panel housing Header, Presets, Tip Properties,
Dynamics, Color Management, Blend Modes, and Advanced Stroke settings.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QPushButton,
)

from parto.brush.models.settings import BrushSettings
from parto.brush.presets.preset_manager import BrushPresetManager
from parto.themes.manager import get_theme_manager

from .header import BrushStudioHeader
from .presets import BrushPresetsSection
from .properties import BrushTipPropertiesSection
from .dynamics import BrushDynamicsSection
from .color import BrushColorSection
from .blend import BrushBlendSection
from .advanced import BrushAdvancedSection


class BrushStudioDock(QDockWidget):
    """
    Authoritative dockable side panel for Brush Studio.
    Provides complete, unified control over presets and brush parameters.
    """

    preset_changed = Signal(str)

    def __init__(
        self,
        settings: BrushSettings,
        preset_manager: Optional[BrushPresetManager] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__("Brush Studio", parent)
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
        container.setObjectName("BrushStudioContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Header Card with Live Dab Preview
        self.header = BrushStudioHeader(self.settings, self.preset_manager, container)
        self.header.color_clicked.connect(self._choose_fg_color)
        self.header.save_preset_clicked.connect(self._save_custom_preset)
        self.header.reset_preset_clicked.connect(self._reset_to_preset_defaults)
        self.header.duplicate_preset_clicked.connect(self._duplicate_current_preset)
        self.header.export_preset_clicked.connect(self._export_current_preset)
        self.header.import_preset_clicked.connect(self._import_preset)
        layout.addWidget(self.header)

        # 2. Presets Section
        self.presets_section = BrushPresetsSection(self.settings, self.preset_manager, container)
        self.presets_section.preset_changed.connect(self._on_preset_selected)
        layout.addWidget(self.presets_section)

        # 3. Tip Properties Section
        self.properties_section = BrushTipPropertiesSection(self.settings, container)
        layout.addWidget(self.properties_section)

        # 4. Color Section
        self.color_section = BrushColorSection(self.settings, container)
        layout.addWidget(self.color_section)

        # 5. Blend & Rendering Section
        self.blend_section = BrushBlendSection(self.settings, container)
        layout.addWidget(self.blend_section)

        # 6. Dynamics Section
        self.dynamics_section = BrushDynamicsSection(self.settings, container)
        layout.addWidget(self.dynamics_section)

        # 7. Advanced & Stroke Section
        self.advanced_section = BrushAdvancedSection(self.settings, container)
        layout.addWidget(self.advanced_section)

        # 8. Reset to Factory Defaults Button
        self.btn_reset_defaults = QPushButton("Reset Brush to Factory Defaults", container)
        self.btn_reset_defaults.setToolTip("Reset all brush parameters to default state (Shift+F9)")
        self.btn_reset_defaults.clicked.connect(self.reset_all_to_defaults)
        layout.addWidget(self.btn_reset_defaults)

        layout.addStretch()
        scroll.setWidget(container)
        self.setWidget(scroll)

    # --- Backward-Compatibility Facade Properties ---

    @property
    def preview(self):
        return self.header.preview

    @property
    def lbl_active_preset(self):
        return self.header.lbl_name

    @property
    def lbl_brush_summary(self):
        return self.header.lbl_summary

    @property
    def search_edit(self):
        return self.presets_section.search_edit

    @property
    def preset_list(self):
        return self.presets_section.grid

    @property
    def btn_save_preset(self):
        return self.presets_section.btn_save

    @property
    def btn_del_preset(self):
        return self.presets_section.btn_del

    @property
    def slider_size(self):
        return self.properties_section.row_size.slider

    @property
    def spin_size(self):
        return self.properties_section.row_size.spin

    @property
    def slider_hardness(self):
        return self.properties_section.row_hardness.slider

    @property
    def spin_hardness(self):
        return self.properties_section.row_hardness.spin

    @property
    def slider_spacing(self):
        return self.properties_section.row_spacing.slider

    @property
    def spin_spacing(self):
        return self.properties_section.row_spacing.spin

    @property
    def slider_opacity(self):
        return self.blend_section.row_opacity.slider

    @property
    def spin_opacity(self):
        return self.blend_section.row_opacity.spin

    @property
    def slider_flow(self):
        return self.blend_section.row_flow.slider

    @property
    def spin_flow(self):
        return self.blend_section.row_flow.spin

    @property
    def cb_erase_mode(self):
        return self.blend_section.cb_eraser

    @property
    def chip_fg(self):
        return self.color_section.chip_fg

    @property
    def chip_bg(self):
        return self.color_section.chip_bg

    @property
    def btn_swap_colors(self):
        return self.color_section.btn_swap

    @property
    def btn_reset_colors(self):
        return self.color_section.btn_reset

    # --- Focus Actions for Keyboard Navigation ---

    def focus_search(self) -> None:
        """Focus preset search field (Ctrl+Shift+B)."""
        self.presets_section.focus_search()

    def focus_properties(self) -> None:
        """Focus tip size control (Alt+B)."""
        self.properties_section.focus_size()

    # --- Preset Interactions ---

    def _on_preset_selected(self, name: str) -> None:
        self.header.sync_from_settings()
        self.preset_changed.emit(name)

    def _save_custom_preset(self) -> None:
        self.presets_section.save_new_preset()

    def _delete_selected_preset(self) -> None:
        item = self.presets_section.grid.currentItem()
        if item:
            name = str(item.data(Qt.UserRole))
            self.presets_section.delete_preset(name)

    def _duplicate_current_preset(self) -> None:
        current_name = self.preset_manager.active_preset_name or "Basic Round"
        self.presets_section.duplicate_preset(current_name)

    def _export_current_preset(self) -> None:
        current_name = self.preset_manager.active_preset_name or "Basic Round"
        self.presets_section.export_preset(current_name)

    def _import_preset(self) -> None:
        self.presets_section.import_preset_file()

    def _reset_to_preset_defaults(self) -> None:
        current_name = self.preset_manager.active_preset_name or "Basic Round"
        self.preset_manager.apply_preset(current_name, self.settings)

    def reset_all_to_defaults(self) -> None:
        """Reset brush parameters to factory defaults (Shift+F9)."""
        if hasattr(self.settings, "reset_to_defaults"):
            self.settings.reset_to_defaults()
        else:
            self._reset_to_preset_defaults()

    # --- Color Interactions ---

    def _choose_fg_color(self) -> None:
        self.color_section._choose_fg_color()

    def _choose_bg_color(self) -> None:
        self.color_section._choose_bg_color()

    def _on_swap_colors(self) -> None:
        self.color_section._on_swap_colors()

    def _on_reset_colors(self) -> None:
        self.color_section._on_reset_colors()

    # --- Backward-Compatible Callback Signatures ---

    def _populate_presets_list(self) -> None:
        self.presets_section.refresh()

    def _filter_presets(self, query: str) -> None:
        self.presets_section.search_edit.setText(query)

    def _on_preset_item_selected(self) -> None:
        item = self.presets_section.grid.currentItem()
        if item:
            name = str(item.data(Qt.UserRole))
            self._on_preset_selected(name)

    def _on_slider_size_changed(self, val: int) -> None:
        self.settings.set_size(val)

    def _on_spin_size_changed(self, val: int) -> None:
        self.settings.set_size(val)

    def _on_slider_opacity_changed(self, val: int) -> None:
        self.settings.set_opacity(val / 100.0)

    def _on_spin_opacity_changed(self, val: int) -> None:
        self.settings.set_opacity(val / 100.0)

    def _on_slider_flow_changed(self, val: int) -> None:
        self.settings.set_flow(val / 100.0)

    def _on_spin_flow_changed(self, val: int) -> None:
        self.settings.set_flow(val / 100.0)

    def _on_slider_hardness_changed(self, val: int) -> None:
        self.settings.set_hardness(val / 100.0)

    def _on_spin_hardness_changed(self, val: int) -> None:
        self.settings.set_hardness(val / 100.0)

    def _on_slider_spacing_changed(self, val: int) -> None:
        self.settings.set_spacing(val / 100.0)

    def _on_spin_spacing_changed(self, val: int) -> None:
        self.settings.set_spacing(val / 100.0)

    def _on_erase_mode_toggled(self, checked: bool) -> None:
        self.settings.set_is_eraser(checked)

    # --- Authoritative State Synchronization ---

    def _on_settings_changed(self) -> None:
        self._sync_from_settings()

    def _sync_from_settings(self) -> None:
        if self._updating_ui:
            return
        self._updating_ui = True
        try:
            self.header.sync_from_settings()
            self.properties_section.sync_from_settings()
            self.color_section.sync_from_settings()
            self.blend_section.sync_from_settings()
            self.dynamics_section.sync_from_settings()
            self.advanced_section.sync_from_settings()
        finally:
            self._updating_ui = False

    def _on_theme_changed(self, _: str) -> None:
        self._sync_from_settings()

    def retranslate_ui(self) -> None:
        """Update brush studio dock title, child sections, and controls with active language."""
        from parto.localization import t
        self.setWindowTitle(t("brush.studio", default="Brush Studio"))

        for section in (
            getattr(self, "presets_section", None),
            getattr(self, "properties_section", None),
            getattr(self, "color_section", None),
            getattr(self, "blend_section", None),
            getattr(self, "dynamics_section", None),
            getattr(self, "advanced_section", None),
        ):
            if section is not None and hasattr(section, "retranslate_ui"):
                section.retranslate_ui()

        if hasattr(self, "btn_reset_defaults"):
            self.btn_reset_defaults.setText(t("brush.reset_defaults", default="Reset Brush to Factory Defaults"))
            self.btn_reset_defaults.setToolTip(t("brush.reset_defaults_desc", default="Reset all brush parameters to default state (Shift+F9)"))


# Compatibility Aliases
BrushDock = BrushStudioDock
BrushPanel = BrushStudioDock
