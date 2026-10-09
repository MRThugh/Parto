# parto/ui/panels/brush/presets.py
"""
Parto Brush Studio — Presets Section
Provides category filtering, responsive search, visual grid of presets,
and preset management workflows.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import os
from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from parto.brush.models.settings import BrushSettings
from parto.brush.presets.preset_manager import BrushPresetManager
from .widgets.preset_grid import PresetGridWidget
from .widgets.section import CollapsibleSection


CATEGORIES: List[str] = [
    "All",
    "Basic",
    "Pencil",
    "Ink",
    "Paint",
    "Airbrush",
    "Marker",
    "Texture",
    "Eraser",
    "Custom",
    "★ Favorites",
]


class BrushPresetsSection(QWidget):
    """
    Modular preset browser section featuring search, category filter, and visual preset grid.
    """

    preset_changed = Signal(str)

    def __init__(
        self,
        settings: BrushSettings,
        preset_manager: BrushPresetManager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.preset_manager = preset_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.section = CollapsibleSection("Brush Presets", collapsed=False, parent=self)
        layout.addWidget(self.section)

        # Content of Section
        # Row 1: Search & Category Filter
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("🔍 Search presets... (Ctrl+Shift+B)")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.search_edit, stretch=3)

        self.category_combo = QComboBox(self)
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.setFixedWidth(105)
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.category_combo, stretch=2)

        self.section.add_layout(filter_row)

        # Row 2: Visual Preset Grid
        self.grid = PresetGridWidget(self)
        self.grid.setFixedHeight(170)
        self.grid.preset_activated.connect(self._on_preset_activated)
        self.grid.preset_duplicate_requested.connect(self.duplicate_preset)
        self.grid.preset_delete_requested.connect(self.delete_preset)
        self.grid.preset_rename_requested.connect(self.rename_preset)
        self.grid.preset_favorite_toggled.connect(self.toggle_favorite)
        self.grid.preset_export_requested.connect(self.export_preset)
        self.grid.save_current_requested.connect(self.save_new_preset)
        self.section.add_widget(self.grid)

        # Row 3: Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_save = QPushButton("+ Save Preset...", self)
        self.btn_save.setToolTip("Save current brush settings as a new custom preset")
        self.btn_save.clicked.connect(self.save_new_preset)
        btn_row.addWidget(self.btn_save)

        self.btn_dup = QPushButton("Duplicate", self)
        self.btn_dup.setToolTip("Duplicate selected preset (Ctrl+D)")
        self.btn_dup.clicked.connect(self._on_duplicate_clicked)
        btn_row.addWidget(self.btn_dup)

        self.btn_del = QPushButton("Delete", self)
        self.btn_del.setToolTip("Delete selected user preset (Delete)")
        self.btn_del.clicked.connect(self._on_delete_clicked)
        btn_row.addWidget(self.btn_del)

        self.section.add_layout(btn_row)
        self.refresh()

    def focus_search(self) -> None:
        """Focus the search input for rapid keyboard search."""
        self.section.set_collapsed(False)
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def focus_grid(self) -> None:
        """Focus the preset grid for keyboard arrow navigation."""
        self.section.set_collapsed(False)
        self.grid.setFocus()

    def refresh(self) -> None:
        """Refresh presets in the grid according to search and category filters."""
        all_presets = self.preset_manager.get_all_presets()
        active_name = self.preset_manager.active_preset_name
        self.grid.set_presets(all_presets, active_name=active_name)
        self.apply_filter()

    def apply_filter(self) -> None:
        """Apply query and category filters to the grid in-place."""
        query = self.search_edit.text()
        cat = self.category_combo.currentText()
        self.grid.filter_items(query=query, category=cat)
        self._update_btn_states()

    def _on_filter_changed(self, *_) -> None:
        self.apply_filter()

    def _on_preset_activated(self, name: str) -> None:
        success = self.preset_manager.apply_preset(name, self.settings)
        if success:
            self._update_btn_states()
            self.preset_changed.emit(name)

    def _update_btn_states(self) -> None:
        item = self.grid.currentItem()
        name = str(item.data(Qt.UserRole)) if item else ""
        preset = self.preset_manager.get_preset(name) if name else None

        has_user_preset = bool(preset and not preset.is_builtin)
        self.btn_del.setEnabled(has_user_preset)
        self.btn_dup.setEnabled(bool(preset))

    def _on_duplicate_clicked(self) -> None:
        item = self.grid.currentItem()
        if item:
            name = str(item.data(Qt.UserRole))
            self.duplicate_preset(name)

    def _on_delete_clicked(self) -> None:
        item = self.grid.currentItem()
        if item:
            name = str(item.data(Qt.UserRole))
            self.delete_preset(name)

    def duplicate_preset(self, name: str) -> None:
        dup = self.preset_manager.duplicate_user_preset(name)
        if dup:
            self.refresh()
            self.preset_changed.emit(dup.name)

    def delete_preset(self, name: str) -> None:
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
            self.refresh()
            if self.preset_manager.active_preset_name:
                self.preset_changed.emit(self.preset_manager.active_preset_name)

    def rename_preset(self, old_name: str) -> None:
        preset = self.preset_manager.get_preset(old_name)
        if not preset or preset.is_builtin:
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Preset",
            "New Preset Name:",
            text=old_name,
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            if self.preset_manager.rename_user_preset(old_name, new_name.strip()):
                self.refresh()
                self.preset_changed.emit(new_name.strip())

    def toggle_favorite(self, name: str) -> None:
        self.preset_manager.toggle_favorite(name)
        self.refresh()

    def save_new_preset(self) -> None:
        default_name = f"Custom {len(self.preset_manager.get_user_presets()) + 1}"
        name, ok = QInputDialog.getText(
            self,
            "Save Brush Preset",
            "Preset Name:",
            text=default_name,
        )
        if ok and name.strip():
            preset = self.preset_manager.create_user_preset(
                name.strip(),
                self.settings,
                description=f"User preset ({self.settings.size}px)",
                category="Custom",
            )
            self.refresh()
            self.preset_changed.emit(preset.name)

    def export_preset(self, name: str) -> None:
        preset = self.preset_manager.get_preset(name)
        if not preset:
            return

        clean_file_name = "".join(c for c in preset.name if c.isalnum() or c in (" ", "_", "-")).rstrip()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Brush Preset",
            f"{clean_file_name}.json",
            "Parto Brush Presets (*.json)",
        )
        if path:
            self.preset_manager.export_preset(name, path)

    def import_preset_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Brush Preset",
            "",
            "Parto Brush Presets (*.json);;All Files (*.*)",
        )
        if path and os.path.exists(path):
            imported = self.preset_manager.import_preset(path)
            if imported:
                self.refresh()
                self.preset_changed.emit(imported.name)
            else:
                QMessageBox.warning(self, "Import Failed", f"Could not read brush preset from {os.path.basename(path)}")

    def retranslate_ui(self) -> None:
        """Update presets section header and search placeholder with active language."""
        from parto.localization import t
        self.section.set_title(t("brush.studio.presets_title", default="Brush Presets"))
        self.search_edit.setPlaceholderText(t("brush.studio.search_placeholder", default="🔍 Search presets... (Ctrl+Shift+B)"))
