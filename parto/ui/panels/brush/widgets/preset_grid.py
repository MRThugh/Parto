# parto/ui/panels/brush/widgets/preset_grid.py
"""
Parto Brush Studio — Visual Preset Grid Widget
Responsive icon grid with custom preset stroke thumbnails, context actions,
and full keyboard navigation.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import math
from typing import Optional, List, Dict
from PySide6.QtCore import Qt, Signal, QSize, QRectF, QPointF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen,
    QPixmap,
    QRadialGradient,
    QKeyEvent,
    QContextMenuEvent,
    QAction,
)
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from parto.brush.models.preset import BrushPreset
from parto.themes.manager import get_theme_manager


class PresetGridWidget(QListWidget):
    """
    Visual grid for browsing, activating, and managing brush presets.
    """

    preset_activated = Signal(str)
    preset_duplicate_requested = Signal(str)
    preset_delete_requested = Signal(str)
    preset_rename_requested = Signal(str)
    preset_favorite_toggled = Signal(str)
    preset_export_requested = Signal(str)
    save_current_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PresetGridWidget")
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setWrapping(True)
        self.setIconSize(QSize(48, 48))
        self.setGridSize(QSize(76, 78))
        self.setSpacing(4)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.StrongFocus)

        self._thumbnail_cache: Dict[str, QPixmap] = {}
        self._presets: List[BrushPreset] = []
        self._apply_styling()
        get_theme_manager().theme_changed.connect(lambda _: self._on_theme_changed())
        self.itemActivated.connect(self._on_item_activated)
        self.itemClicked.connect(self._on_item_activated)
        self.currentItemChanged.connect(self._on_current_item_changed)

    def set_presets(self, presets: List[BrushPreset], active_name: Optional[str] = None) -> None:
        """Populate grid with preset thumbnails and labels."""
        self.blockSignals(True)
        self.clear()
        self._presets = list(presets)

        selected_item = None
        for p in presets:
            pixmap = self._get_thumbnail(p)
            star = "★ " if p.favorite else ""
            item = QListWidgetItem(f"{star}{p.name}")
            item.setIcon(pixmap)
            item.setData(Qt.UserRole, p.name)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)

            details = [
                f"{p.name} ({p.category})",
                f"Size: {p.size} px • Hardness: {int(round(p.hardness * 100))}%",
                f"Opacity: {int(round(p.opacity * 100))}% • Spacing: {int(round(p.spacing * 100))}%",
            ]
            if p.description:
                details.append(p.description)
            if p.is_builtin:
                details.append("[Built-in Preset]")
            else:
                details.append("[User Preset]")
            item.setToolTip("\n".join(details))

            self.addItem(item)
            if active_name and p.name.lower() == active_name.lower():
                selected_item = item

        if selected_item:
            self.setCurrentItem(selected_item)

        self.blockSignals(False)

    def filter_items(self, query: str = "", category: Optional[str] = None) -> None:
        """Show or hide preset items in-place using item.setHidden."""
        q = query.strip().lower()
        cat = category.strip() if category and category != "All" else None
        only_favs = (cat == "★ Favorites")

        preset_map = {p.name: p for p in self._presets}
        for i in range(self.count()):
            item = self.item(i)
            name = str(item.data(Qt.UserRole))
            p = preset_map.get(name)
            if not p:
                continue

            matches = True
            if only_favs and not p.favorite:
                matches = False
            elif cat and cat != "★ Favorites" and p.category.lower() != cat.lower():
                matches = False

            if matches and q:
                if q not in p.name.lower():
                    matches = False

            item.setHidden(not matches)

    def _get_thumbnail(self, p: BrushPreset) -> QPixmap:
        """Render or retrieve a crisp representative dab thumbnail for preset."""
        cache_key = f"{p.name}_{p.size}_{p.hardness}_{p.roundness}_{p.angle}_{p.opacity}_{p.is_eraser}_{get_theme_manager().current_theme_id}"
        if cache_key in self._thumbnail_cache:
            return self._thumbnail_cache[cache_key]

        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        pal = get_theme_manager().get_palette()
        bg_col = QColor(pal.get("surface_sunken", "#18181b"))
        border_col = QColor(pal.get("border_subtle", "#27272a"))
        accent_col = QColor(pal.get("primary", "#0284c7"))

        # Frame card
        rect = QRectF(1, 1, 46, 46)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.0))
        painter.drawRoundedRect(rect, 4, 4)

        # Scale dab to thumbnail bounds
        max_r = 18.0
        r_x = 3.0 + (min(200, p.size) / 200.0) * (max_r - 3.0)
        r_y = r_x * max(0.15, p.roundness)

        cx = 24.0
        cy = 24.0

        painter.save()
        painter.translate(cx, cy)
        if abs(p.angle) > 0.01:
            painter.rotate(p.angle)

        if p.is_eraser:
            fg_color = QColor(240, 240, 240, 220)
        else:
            fg_color = QColor(pal.get("text", "#f4f4f5"))
            fg_color.setAlpha(int(round(255 * max(0.2, p.opacity))))

        grad = QRadialGradient(0, 0, r_x)
        inner_ratio = max(0.0, min(1.0, p.hardness))
        edge_color = QColor(fg_color.red(), fg_color.green(), fg_color.blue(), 0)

        if inner_ratio >= 0.95:
            grad.setColorAt(0.0, fg_color)
            grad.setColorAt(0.95, fg_color)
            grad.setColorAt(1.0, edge_color)
        else:
            grad.setColorAt(0.0, fg_color)
            grad.setColorAt(inner_ratio, fg_color)
            grad.setColorAt(1.0, edge_color)

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-r_x, -r_y, r_x * 2, r_y * 2))
        painter.restore()

        # Stroke badge if textured or scatter
        if p.scatter > 0.1:
            painter.setPen(QPen(accent_col, 1.5))
            painter.drawPoint(38, 10)
            painter.drawPoint(40, 12)
            painter.drawPoint(36, 14)

        painter.end()
        self._thumbnail_cache[cache_key] = pixmap
        return pixmap

    def _on_theme_changed(self) -> None:
        self._thumbnail_cache.clear()
        self._apply_styling()

    def _apply_styling(self) -> None:
        pal = get_theme_manager().get_palette()
        border = pal.get("border_subtle", "#27272a")
        primary = pal.get("primary", "#0284c7")
        sunken = pal.get("surface_sunken", "#18181b")
        text = pal.get("text", "#f4f4f5")
        text_muted = pal.get("text_muted", "#a1a1aa")

        self.setStyleSheet(f"""
            QListWidget#PresetGridWidget {{
                background-color: transparent;
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget#PresetGridWidget::item {{
                background-color: {sunken};
                border: 1px solid {border};
                border-radius: 6px;
                color: {text};
                font-size: 10px;
                font-weight: 500;
                padding: 2px;
            }}
            QListWidget#PresetGridWidget::item:hover {{
                border-color: {pal.get('border', '#3f3f46')};
                background-color: {pal.get('surface_raised', '#27272a')};
            }}
            QListWidget#PresetGridWidget::item:selected {{
                border: 2px solid {primary};
                background-color: {pal.get('surface_raised', '#27272a')};
                color: {text};
            }}
        """)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        if item is not None:
            name = str(item.data(Qt.UserRole))
            if name:
                self.preset_activated.emit(name)

    def _on_current_item_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]) -> None:
        if current is not None:
            name = str(current.data(Qt.UserRole))
            if name:
                self.preset_activated.emit(name)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        item = self.itemAt(event.pos())
        if not item:
            return

        name = str(item.data(Qt.UserRole))
        p = next((x for x in self._presets if x.name == name), None)
        if not p:
            return

        menu = QMenu(self)
        act_select = menu.addAction(f"Activate '{name}' (Enter)")
        menu.addSeparator()

        fav_label = "★ Remove from Favorites" if p.favorite else "☆ Add to Favorites"
        act_fav = menu.addAction(fav_label)

        act_dup = menu.addAction("Duplicate Preset (Ctrl+D)")
        act_rename = menu.addAction("Rename Preset...")
        act_export = menu.addAction("Export Preset...")
        menu.addSeparator()

        act_delete = menu.addAction("Delete Preset (Delete)")
        if p.is_builtin:
            act_delete.setEnabled(False)
            act_delete.setText("Delete Preset (Built-in protected)")
            act_rename.setEnabled(False)

        chosen = menu.exec(event.globalPos())
        if chosen == act_select:
            self.preset_activated.emit(name)
        elif chosen == act_fav:
            self.preset_favorite_toggled.emit(name)
        elif chosen == act_dup:
            self.preset_duplicate_requested.emit(name)
        elif chosen == act_rename:
            self.preset_rename_requested.emit(name)
        elif chosen == act_export:
            self.preset_export_requested.emit(name)
        elif chosen == act_delete and not p.is_builtin:
            self.preset_delete_requested.emit(name)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()
        item = self.currentItem()
        name = str(item.data(Qt.UserRole)) if item else ""

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if name:
                self.preset_activated.emit(name)
                event.accept()
                return

        if key == Qt.Key_Delete and name:
            p = next((x for x in self._presets if x.name == name), None)
            if p and not p.is_builtin:
                self.preset_delete_requested.emit(name)
                event.accept()
                return

        if (modifiers & Qt.ControlModifier) and key == Qt.Key_D and name:
            self.preset_duplicate_requested.emit(name)
            event.accept()
            return

        if (modifiers & Qt.ControlModifier) and key == Qt.Key_S:
            self.save_current_requested.emit()
            event.accept()
            return

        super().keyPressEvent(event)
