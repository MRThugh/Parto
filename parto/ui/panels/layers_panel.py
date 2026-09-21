# parto/ui/panels/layers_panel.py
"""
Parto v0.3.0 - Multi-Layer Stack Management Dock Panel
Vector-only icons, custom interactive layer rows, theme-aware controls, and opacity slider.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QSlider,
    QToolButton,
)
from parto.editor.document import Document
from parto.resources.icons import get_parto_icon
from parto.themes.manager import get_theme_manager


class LayerItemWidget(QWidget):
    """Custom row widget for layer items in the list with vector eye toggle button."""

    def __init__(
        self,
        doc_idx: int,
        name: str,
        visible: bool,
        opacity: float,
        on_toggle_vis,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.doc_idx = doc_idx
        self.visible_state = visible
        self.on_toggle_vis = on_toggle_vis

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 6, 2)
        layout.setSpacing(8)

        # Visibility Toggle Button (Vector Eye / Eye-off)
        self.vis_btn = QToolButton(self)
        self.vis_btn.setFixedSize(22, 22)
        self.vis_btn.setAutoRaise(True)
        self.vis_btn.setCursor(Qt.PointingHandCursor)
        self.vis_btn.setToolTip("Toggle Layer Visibility")
        self._update_eye_icon()
        self.vis_btn.clicked.connect(self._on_vis_clicked)
        layout.addWidget(self.vis_btn)

        # Layer Name Label
        self.name_label = QLabel(name, self)
        self.name_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        layout.addWidget(self.name_label)

        layout.addStretch()

        # Opacity indicator if < 100%
        if opacity < 0.999:
            pct_lbl = QLabel(f"{int(opacity * 100)}%", self)
            pct_lbl.setStyleSheet("font-size: 11px; opacity: 0.6;")
            layout.addWidget(pct_lbl)

    def _update_eye_icon(self):
        icon_color = get_theme_manager().get_icon_color()
        icon_name = "eye" if self.visible_state else "eye-off"
        # If hidden, make icon slightly dimmed
        if not self.visible_state:
            self.vis_btn.setIcon(get_parto_icon(icon_name, "#71717a", 16))
        else:
            self.vis_btn.setIcon(get_parto_icon(icon_name, icon_color, 16))

    def _on_vis_clicked(self):
        self.on_toggle_vis(self.doc_idx, not self.visible_state)


class LayersDock(QDockWidget):
    """
    Dockable panel showing document layer stack, opacity, and stack manipulation tools.
    """

    def __init__(self, document: Document, parent: Optional[QWidget] = None):
        super().__init__("Layers", parent)
        self.setObjectName("LayersDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.document = document

        self._updating = False
        self._init_ui()

        self.document.document_changed.connect(self.refresh_layers)
        self.document.layer_selection_changed.connect(self._on_layer_selection_changed)
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _init_ui(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Opacity Control Row
        op_layout = QHBoxLayout()
        op_lbl = QLabel("Opacity:", self)
        op_lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
        op_layout.addWidget(op_lbl)

        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.sliderPressed.connect(self._on_opacity_slider_pressed)
        self.opacity_slider.valueChanged.connect(self._on_opacity_slider_changed)
        self.opacity_slider.sliderReleased.connect(self._on_opacity_slider_released)
        op_layout.addWidget(self.opacity_slider)

        self.opacity_label = QLabel("100%", self)
        self.opacity_label.setFixedWidth(40)
        self.opacity_label.setStyleSheet("font-size: 11px;")
        op_layout.addWidget(self.opacity_label)
        layout.addLayout(op_layout)

        # Layers List (Displayed top-to-bottom: index N-1 down to 0)
        self.layer_list = QListWidget(self)
        self.layer_list.setObjectName("LayersList")
        self.layer_list.currentRowChanged.connect(self._on_list_row_changed)
        layout.addWidget(self.layer_list)

        # Bottom Action Bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        icon_color = get_theme_manager().get_icon_color()

        self.add_btn = QToolButton(self)
        self.add_btn.setIcon(get_parto_icon("layer-add", icon_color, 18))
        self.add_btn.setToolTip("Add New Layer")
        self.add_btn.clicked.connect(self._on_add_layer)
        btn_layout.addWidget(self.add_btn)

        self.dup_btn = QToolButton(self)
        self.dup_btn.setIcon(get_parto_icon("layer-duplicate", icon_color, 18))
        self.dup_btn.setToolTip("Duplicate Active Layer")
        self.dup_btn.clicked.connect(self._on_duplicate_layer)
        btn_layout.addWidget(self.dup_btn)

        self.del_btn = QToolButton(self)
        self.del_btn.setIcon(get_parto_icon("layer-delete", "#ef4444", 18))
        self.del_btn.setToolTip("Delete Active Layer")
        self.del_btn.clicked.connect(self._on_delete_layer)
        btn_layout.addWidget(self.del_btn)

        btn_layout.addSpacing(8)

        self.up_btn = QToolButton(self)
        self.up_btn.setIcon(get_parto_icon("layer-up", icon_color, 18))
        self.up_btn.setToolTip("Move Layer Up")
        self.up_btn.clicked.connect(self.document.move_layer_up)
        btn_layout.addWidget(self.up_btn)

        self.down_btn = QToolButton(self)
        self.down_btn.setIcon(get_parto_icon("layer-down", icon_color, 18))
        self.down_btn.setToolTip("Move Layer Down")
        self.down_btn.clicked.connect(self.document.move_layer_down)
        btn_layout.addWidget(self.down_btn)

        self.merge_btn = QToolButton(self)
        self.merge_btn.setIcon(get_parto_icon("layer-merge", icon_color, 18))
        self.merge_btn.setToolTip("Merge Down")
        self.merge_btn.clicked.connect(self.document.merge_down)
        btn_layout.addWidget(self.merge_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setWidget(container)

    def _on_theme_changed(self, _: str):
        icon_color = get_theme_manager().get_icon_color()
        self.add_btn.setIcon(get_parto_icon("layer-add", icon_color, 18))
        self.dup_btn.setIcon(get_parto_icon("layer-duplicate", icon_color, 18))
        self.del_btn.setIcon(get_parto_icon("layer-delete", "#ef4444", 18))
        self.up_btn.setIcon(get_parto_icon("layer-up", icon_color, 18))
        self.down_btn.setIcon(get_parto_icon("layer-down", icon_color, 18))
        self.merge_btn.setIcon(get_parto_icon("layer-merge", icon_color, 18))
        self.refresh_layers()

    def _on_toggle_visibility(self, doc_idx: int, new_visible: bool):
        self.document.set_layer_visible(doc_idx, new_visible)

    def refresh_layers(self):
        """Rebuild list items from document layers with vector eye row widgets."""
        self._updating = True
        self.layer_list.clear()

        layers = self.document.layers
        for doc_idx in reversed(range(len(layers))):
            layer = layers[doc_idx]
            item = QListWidgetItem(self.layer_list)
            item.setSizeHint(QSize(180, 32))
            item.setData(Qt.UserRole, doc_idx)

            row_widget = LayerItemWidget(
                doc_idx=doc_idx,
                name=layer.name,
                visible=layer.visible,
                opacity=layer.opacity,
                on_toggle_vis=self._on_toggle_visibility,
                parent=self.layer_list,
            )
            self.layer_list.setItemWidget(item, row_widget)

        # Select corresponding visual row for active layer index
        num_layers = len(layers)
        active_idx = self.document.active_layer_index
        visual_row = (num_layers - 1) - active_idx
        if 0 <= visual_row < self.layer_list.count():
            self.layer_list.setCurrentRow(visual_row)

        # Update opacity slider
        active_layer = self.document.active_layer
        if active_layer:
            pct = int(active_layer.opacity * 100)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(pct)
            self.opacity_slider.blockSignals(False)
            self.opacity_label.setText(f"{pct}%")

        self._updating = False

    def _on_list_row_changed(self, row: int):
        if self._updating or row < 0:
            return
        item = self.layer_list.item(row)
        if item:
            doc_idx = item.data(Qt.UserRole)
            self.document.set_active_layer_index(doc_idx)

    def _on_layer_selection_changed(self, doc_idx: int):
        if self._updating:
            return
        num_layers = len(self.document.layers)
        visual_row = (num_layers - 1) - doc_idx
        if 0 <= visual_row < self.layer_list.count():
            self._updating = True
            self.layer_list.setCurrentRow(visual_row)
            active_layer = self.document.active_layer
            if active_layer:
                pct = int(active_layer.opacity * 100)
                self.opacity_slider.blockSignals(True)
                self.opacity_slider.setValue(pct)
                self.opacity_slider.blockSignals(False)
                self.opacity_label.setText(f"{pct}%")
            self._updating = False

    def _on_opacity_slider_pressed(self):
        self._opacity_snap = self.document._create_snapshot()

    def _on_opacity_slider_changed(self, val: int):
        self.opacity_label.setText(f"{val}%")
        active = self.document.active_layer
        if active:
            self.document.set_layer_opacity(self.document.active_layer_index, val / 100.0, record_history=False)

    def _on_opacity_slider_released(self):
        if hasattr(self, "_opacity_snap") and self._opacity_snap is not None:
            self.document._record_operation("Change Layer Opacity", self._opacity_snap)
            self._opacity_snap = None

    def _on_add_layer(self):
        self.document.add_layer()

    def _on_duplicate_layer(self):
        self.document.duplicate_active_layer()

    def _on_delete_layer(self):
        self.document.remove_active_layer()
