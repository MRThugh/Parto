# parto/ui/widgets/brush_bar.py
"""
Parto v0.3.0 - Professional Interactive Brush Control Bar
Allows live configuration of brush size, opacity, hardness, color selection,
quick palette swatches, color swapping, and real-time dab preview.
Theme-aware with crisp visual hierarchy and responsive layout.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QToolButton,
    QColorDialog,
    QFrame,
    QSizePolicy,
)
from parto.themes.manager import get_theme_manager


class BrushPreviewWidget(QWidget):
    """
    Real-time interactive dab preview widget demonstrating size, hardness falloff,
    opacity, and color.
    """

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("BrushPreviewWidget")
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Real-time Brush Dab Preview (Click to choose color)")

        self._size: int = 8
        self._hardness: float = 0.8
        self._opacity: float = 1.0
        self._color: Tuple[int, int, int, int] = (0, 0, 0, 255)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def update_brush(
        self,
        size: Optional[int] = None,
        opacity: Optional[float] = None,
        hardness: Optional[float] = None,
        color: Optional[Tuple[int, int, int, int]] = None,
    ) -> None:
        if size is not None:
            self._size = max(1, int(size))
        if opacity is not None:
            self._opacity = max(0.0, min(1.0, float(opacity)))
        if hardness is not None:
            self._hardness = max(0.0, min(1.0, float(hardness)))
        if color is not None:
            self._color = color
        self.update()

    def update_preview(
        self,
        size: int,
        opacity: float,
        hardness: float,
        color: Tuple[int, int, int, int],
    ) -> None:
        self.update_brush(size=size, opacity=opacity, hardness=hardness, color=color)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        pal = get_theme_manager().get_palette()
        border_col = QColor(pal.get("border_subtle", "#3f3f46"))

        # Background container
        bg_col = QColor(pal.get("surface_sunken", "#18181b"))
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1.0))
        painter.drawRoundedRect(rect, 4, 4)

        # Scale brush size to preview bounds
        max_preview_radius = (min(rect.width(), rect.height()) - 6) / 2.0
        # Map 1-200px brush size to 2px - max_preview_radius
        preview_radius = 2.0 + (min(200, self._size) / 200.0) * (max_preview_radius - 2.0)

        cx = rect.center().x()
        cy = rect.center().y()

        # Render dab with radial gradient matching hardness & opacity
        grad = QRadialGradient(cx, cy, preview_radius)
        r, g, b, a = self._color
        effective_alpha = int(round(a * self._opacity))

        inner_ratio = max(0.0, min(1.0, self._hardness))
        inner_color = QColor(r, g, b, effective_alpha)
        edge_color = QColor(r, g, b, 0)

        if inner_ratio >= 0.98:
            grad.setColorAt(0.0, inner_color)
            grad.setColorAt(0.95, inner_color)
            grad.setColorAt(1.0, edge_color)
        else:
            grad.setColorAt(0.0, inner_color)
            grad.setColorAt(inner_ratio, inner_color)
            grad.setColorAt(1.0, edge_color)

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - preview_radius, cy - preview_radius, preview_radius * 2, preview_radius * 2))
        painter.end()


class ColorChipButton(QToolButton):
    """
    Custom tool button for displaying the active color with an optional checkerboard
    underlay to clearly indicate transparency / alpha.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        self._rgba: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self._border_color: str = "#3f3f46"

    def set_rgba(self, rgba: Tuple[int, int, int, int], border_color: str = "#3f3f46") -> None:
        self._rgba = rgba
        self._border_color = border_color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 1, -1, -1)

        # Draw subtle checkerboard underlay if color is semi-transparent
        if self._rgba[3] < 255:
            check_size = 4
            c1 = QColor(220, 220, 220)
            c2 = QColor(160, 160, 160)
            for x in range(rect.left(), rect.right(), check_size):
                for y in range(rect.top(), rect.bottom(), check_size):
                    is_even = ((x // check_size) + (y // check_size)) % 2 == 0
                    painter.fillRect(
                        x, y,
                        min(check_size, rect.right() - x + 1),
                        min(check_size, rect.bottom() - y + 1),
                        c1 if is_even else c2
                    )

        # Draw fill color with alpha
        r, g, b, a = self._rgba
        fill_color = QColor(r, g, b, a)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(QColor(self._border_color), 1.5))
        painter.drawRoundedRect(rect, 4, 4)
        painter.end()


class BrushBar(QWidget):
    """
    Floating / docked context bar for the Brush Tool.

    Logical Layout:
    [ Color & Swatches | Swap / Reset ] | [ Preview & Size ] | [ Opacity & Hardness ]
    """

    size_changed = Signal(int)
    opacity_changed = Signal(float)
    hardness_changed = Signal(float)
    color_changed = Signal(tuple)

    QUICK_COLORS = [
        ("#000000", "Black"),
        ("#ffffff", "White"),
        ("#ef4444", "Red"),
        ("#3b82f6", "Blue"),
        ("#22c55e", "Green"),
        ("#eab308", "Yellow"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("BrushBar")
        self._color: Tuple[int, int, int, int] = (0, 0, 0, 255)
        self._bg_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
        self._swatch_buttons: List[QToolButton] = []
        self._separators: List[QFrame] = []

        self._init_ui()
        self._apply_theme_styling()
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 5, 12, 5)
        main_layout.setSpacing(10)

        # Tool Header & Live Tip Preview
        self.preview = BrushPreviewWidget(self)
        self.preview.clicked.connect(self._open_color_dialog)
        main_layout.addWidget(self.preview)

        title_label = QLabel("Brush", self)
        title_label.setObjectName("BrushBarTitle")
        title_label.setStyleSheet("font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        main_layout.addWidget(title_label)

        main_layout.addWidget(self._create_separator())

        # Group 1: Color, Swatches, Swap & Reset
        self._init_color_group(main_layout)

        main_layout.addWidget(self._create_separator())

        # Group 2: Primary Control - Size & Live Preview
        self._init_size_group(main_layout)

        main_layout.addWidget(self._create_separator())

        # Group 3: Secondary Controls - Opacity & Hardness
        self._init_dynamics_group(main_layout)

        main_layout.addStretch()

    def _create_separator(self) -> QFrame:
        sep = QFrame(self)
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setFixedWidth(1)
        self._separators.append(sep)
        return sep

    def _init_color_group(self, layout: QHBoxLayout) -> None:
        color_layout = QHBoxLayout()
        color_layout.setSpacing(6)
        color_layout.setContentsMargins(0, 0, 0, 0)

        # Primary interactive color chip
        self.color_chip = ColorChipButton(self)
        self.color_chip.setToolTip("Active Brush Color (Click to change)")
        self.color_chip.clicked.connect(self._open_color_dialog)
        color_layout.addWidget(self.color_chip)

        # Micro-actions: Swap (X) & Reset (D)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(2)

        self.swap_btn = QToolButton(self)
        self.swap_btn.setText("⇄")
        self.swap_btn.setFixedSize(20, 20)
        self.swap_btn.setCursor(Qt.PointingHandCursor)
        self.swap_btn.setToolTip("Swap Foreground / Background Colors (X)")
        self.swap_btn.clicked.connect(self._on_swap_colors)
        actions_layout.addWidget(self.swap_btn)

        self.reset_btn = QToolButton(self)
        self.reset_btn.setText("D")
        self.reset_btn.setFixedSize(20, 20)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setToolTip("Reset to Default Black / White (D)")
        self.reset_btn.clicked.connect(self._on_reset_colors)
        actions_layout.addWidget(self.reset_btn)

        color_layout.addLayout(actions_layout)

        # Quick Swatches
        swatch_layout = QHBoxLayout()
        swatch_layout.setSpacing(4)
        for hex_code, name in self.QUICK_COLORS:
            btn = QToolButton(self)
            btn.setFixedSize(16, 16)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"{name} ({hex_code})")
            btn.setProperty("hex_code", hex_code)
            btn.clicked.connect(lambda _, c=hex_code: self._set_color_from_hex(c))
            self._swatch_buttons.append(btn)
            swatch_layout.addWidget(btn)

        color_layout.addLayout(swatch_layout)
        layout.addLayout(color_layout)

    def _init_size_group(self, layout: QHBoxLayout) -> None:
        size_layout = QHBoxLayout()
        size_layout.setSpacing(6)
        size_layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("Size:", self)
        lbl.setStyleSheet("font-size: 11px; font-weight: 500;")
        size_layout.addWidget(lbl)

        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setRange(1, 200)
        self.slider_size.setValue(8)
        self.slider_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_size.setMinimumWidth(60)
        self.slider_size.setMaximumWidth(110)
        self.slider_size.setToolTip("Brush Size in pixels ([ and ] shortcuts)")
        size_layout.addWidget(self.slider_size)

        self.spin_size = QSpinBox(self)
        self.spin_size.setRange(1, 200)
        self.spin_size.setValue(8)
        self.spin_size.setSuffix(" px")
        self.spin_size.setFixedWidth(70)
        self.spin_size.setAlignment(Qt.AlignRight)
        size_layout.addWidget(self.spin_size)

        self.slider_size.valueChanged.connect(self._on_size_slider_changed)
        self.spin_size.valueChanged.connect(self._on_size_spin_changed)

        layout.addLayout(size_layout)

    def _init_dynamics_group(self, layout: QHBoxLayout) -> None:
        dynamics_layout = QHBoxLayout()
        dynamics_layout.setSpacing(8)
        dynamics_layout.setContentsMargins(0, 0, 0, 0)

        # Opacity
        lbl_op = QLabel("Opacity:", self)
        lbl_op.setStyleSheet("font-size: 11px; font-weight: 500;")
        dynamics_layout.addWidget(lbl_op)

        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setRange(1, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_opacity.setMinimumWidth(50)
        self.slider_opacity.setMaximumWidth(90)
        dynamics_layout.addWidget(self.slider_opacity)

        self.spin_opacity = QSpinBox(self)
        self.spin_opacity.setRange(1, 100)
        self.spin_opacity.setValue(100)
        self.spin_opacity.setSuffix(" %")
        self.spin_opacity.setFixedWidth(70)
        self.spin_opacity.setAlignment(Qt.AlignRight)
        dynamics_layout.addWidget(self.spin_opacity)

        self.slider_opacity.valueChanged.connect(self._on_opacity_slider_changed)
        self.spin_opacity.valueChanged.connect(self._on_opacity_spin_changed)

        # Hardness
        lbl_hard = QLabel("Hardness:", self)
        lbl_hard.setStyleSheet("font-size: 11px; font-weight: 500;")
        dynamics_layout.addWidget(lbl_hard)

        self.slider_hardness = QSlider(Qt.Horizontal, self)
        self.slider_hardness.setRange(0, 100)
        self.slider_hardness.setValue(80)
        self.slider_hardness.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider_hardness.setMinimumWidth(50)
        self.slider_hardness.setMaximumWidth(90)
        dynamics_layout.addWidget(self.slider_hardness)

        self.spin_hardness = QSpinBox(self)
        self.spin_hardness.setRange(0, 100)
        self.spin_hardness.setValue(80)
        self.spin_hardness.setSuffix(" %")
        self.spin_hardness.setFixedWidth(70)
        self.spin_hardness.setAlignment(Qt.AlignRight)
        dynamics_layout.addWidget(self.spin_hardness)

        self.slider_hardness.valueChanged.connect(self._on_hardness_slider_changed)
        self.spin_hardness.valueChanged.connect(self._on_hardness_spin_changed)

        layout.addLayout(dynamics_layout)

    # --- Value Synchronization Handlers ---

    def _sync_preview(self) -> None:
        self.preview.update_preview(
            self.slider_size.value(),
            self.slider_opacity.value() / 100.0,
            self.slider_hardness.value() / 100.0,
            self._color,
        )

    def _on_size_slider_changed(self, val: int) -> None:
        self.spin_size.blockSignals(True)
        self.spin_size.setValue(val)
        self.spin_size.blockSignals(False)
        self._sync_preview()
        self.size_changed.emit(val)

    def _on_size_spin_changed(self, val: int) -> None:
        self.slider_size.blockSignals(True)
        self.slider_size.setValue(val)
        self.slider_size.blockSignals(False)
        self._sync_preview()
        self.size_changed.emit(val)

    def _on_opacity_slider_changed(self, val: int) -> None:
        self.spin_opacity.blockSignals(True)
        self.spin_opacity.setValue(val)
        self.spin_opacity.blockSignals(False)
        self._sync_preview()
        self.opacity_changed.emit(val / 100.0)

    def _on_opacity_spin_changed(self, val: int) -> None:
        self.slider_opacity.blockSignals(True)
        self.slider_opacity.setValue(val)
        self.slider_opacity.blockSignals(False)
        self._sync_preview()
        self.opacity_changed.emit(val / 100.0)

    def _on_hardness_slider_changed(self, val: int) -> None:
        self.spin_hardness.blockSignals(True)
        self.spin_hardness.setValue(val)
        self.spin_hardness.blockSignals(False)
        self._sync_preview()
        self.hardness_changed.emit(val / 100.0)

    def _on_hardness_spin_changed(self, val: int) -> None:
        self.slider_hardness.blockSignals(True)
        self.slider_hardness.setValue(val)
        self.slider_hardness.blockSignals(False)
        self._sync_preview()
        self.hardness_changed.emit(val / 100.0)

    # --- Color Interactions ---

    def _open_color_dialog(self) -> None:
        r, g, b, a = self._color
        initial = QColor(r, g, b, a)
        color = QColorDialog.getColor(
            initial, self, "Select Brush Color", QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            rgba = (color.red(), color.green(), color.blue(), color.alpha())
            self.set_color(rgba)
            self.color_changed.emit(rgba)

    def _set_color_from_hex(self, hex_str: str) -> None:
        color = QColor(hex_str)
        if color.isValid():
            rgba = (color.red(), color.green(), color.blue(), 255)
            self.set_color(rgba)
            self.color_changed.emit(rgba)

    def _on_swap_colors(self) -> None:
        self._color, self._bg_color = self._bg_color, self._color
        self._update_color_chip()
        self._sync_preview()
        self.color_changed.emit(self._color)

    def _on_reset_colors(self) -> None:
        self._color = (0, 0, 0, 255)
        self._bg_color = (255, 255, 255, 255)
        self._update_color_chip()
        self._sync_preview()
        self.color_changed.emit(self._color)

    # --- Public Value Setters ---

    def set_color(self, rgba: Tuple[int, int, int, int]) -> None:
        self._color = rgba
        self._update_color_chip()
        self._sync_preview()

    def set_size(self, size: int) -> None:
        clamped = max(1, min(200, int(size)))
        if self.slider_size.value() != clamped:
            self.slider_size.blockSignals(True)
            self.spin_size.blockSignals(True)
            self.slider_size.setValue(clamped)
            self.spin_size.setValue(clamped)
            self.slider_size.blockSignals(False)
            self.spin_size.blockSignals(False)
            self._sync_preview()

    def set_opacity(self, opacity: float) -> None:
        pct = max(1, min(100, int(round(float(opacity) * 100))))
        if self.slider_opacity.value() != pct:
            self.slider_opacity.blockSignals(True)
            self.spin_opacity.blockSignals(True)
            self.slider_opacity.setValue(pct)
            self.spin_opacity.setValue(pct)
            self.slider_opacity.blockSignals(False)
            self.spin_opacity.blockSignals(False)
            self._sync_preview()

    def set_hardness(self, hardness: float) -> None:
        pct = max(0, min(100, int(round(float(hardness) * 100))))
        if self.slider_hardness.value() != pct:
            self.slider_hardness.blockSignals(True)
            self.spin_hardness.blockSignals(True)
            self.slider_hardness.setValue(pct)
            self.spin_hardness.setValue(pct)
            self.slider_hardness.blockSignals(False)
            self.spin_hardness.blockSignals(False)
            self._sync_preview()

    # --- Theme Styling ---

    def _update_color_chip(self) -> None:
        pal = get_theme_manager().get_palette()
        border_col = pal.get("border", "#3f3f46")
        self.color_chip.set_rgba(self._color, border_color=border_col)

        # Highlight matching swatch button if any
        current_hex = f"#{self._color[0]:02x}{self._color[1]:02x}{self._color[2]:02x}".lower()
        for btn in self._swatch_buttons:
            hex_prop = btn.property("hex_code")
            if hex_prop and hex_prop.lower() == current_hex:
                btn.setStyleSheet(
                    f"background-color: {hex_prop}; border: 2px solid {pal.get('primary', '#0284c7')}; border-radius: 3px;"
                )
            elif hex_prop:
                btn.setStyleSheet(
                    f"background-color: {hex_prop}; border: 1px solid {pal.get('border', '#52525b')}; border-radius: 3px;"
                )

    def _apply_theme_styling(self) -> None:
        pal = get_theme_manager().get_palette()
        border_subtle = pal.get("border_subtle", "#2e2e33")
        surface = pal.get("surface", "#27272a")
        text = pal.get("text", "#f4f4f5")
        btn_hover = pal.get("surface_raised", "#3f3f46")

        for sep in self._separators:
            sep.setStyleSheet(f"background-color: {border_subtle};")

        action_btn_style = f"""
            QToolButton {{
                background-color: transparent;
                color: {text};
                border: 1px solid {border_subtle};
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }}
            QToolButton:hover {{
                background-color: {btn_hover};
                border-color: {pal.get('border', '#3f3f46')};
            }}
            QToolButton:pressed {{
                background-color: {pal.get('surface_sunken', '#141416')};
            }}
        """
        self.swap_btn.setStyleSheet(action_btn_style)
        self.reset_btn.setStyleSheet(action_btn_style)

        self._update_color_chip()
        self._sync_preview()

    def _on_theme_changed(self, _: str) -> None:
        self._apply_theme_styling()
        self.update()
