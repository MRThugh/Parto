# parto/brush/tools/brush_tool.py
"""
Parto Brush System — Canvas Tool Integration Adapter
Subclasses BaseTool and connects Canvas event dispatch to BrushController.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Any, Optional, Tuple
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent
from PIL import Image

from ..models.settings import BrushSettings
from ..engine.renderer import BrushRenderer
from ..controller.stroke_controller import StrokeController
from ..controller.brush_controller import BrushController


class BrushTool:
    """
    Authoritative Brush Tool for freehand drawing on the active layer.
    Coordinates settings, rendering, and input events through the brush subsystem.
    """

    name: str = "Brush"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def activate(self, canvas: Any) -> None:
        """Called when this tool is selected on the canvas."""
        if hasattr(canvas, "setCursor"):
            canvas.setCursor(self.cursor_shape)

    def paint_overlay(self, painter: Any, canvas: Any) -> None:
        """Paint interactive visual overlays if needed."""
        pass

    def __init__(
        self,
        settings: Optional[BrushSettings] = None,
        controller: Optional[BrushController] = None,
    ):
        if controller is not None:
            self.controller = controller
        else:
            self.controller = BrushController(settings=settings)

        self.settings: BrushSettings = self.controller.settings
        self.renderer: BrushRenderer = self.controller.renderer
        self.stroke_controller: StrokeController = self.controller.stroke_controller

    def deactivate(self, canvas: Any) -> None:
        """Safely terminate active stroke when switching tools or deactivating."""
        if self._is_drawing:
            doc = getattr(canvas, "document", None)
            if doc:
                self.end_stroke(doc)
            else:
                self.cancel_stroke()
            if hasattr(canvas, "update_composite_pixmap"):
                canvas.update_composite_pixmap()

    # --- Delegated Configuration Properties ---

    @property
    def color(self) -> Tuple[int, int, int, int]:
        return self.settings.color

    @color.setter
    def color(self, value: Tuple[int, int, int, int]) -> None:
        self.set_color(value)

    @property
    def background_color(self) -> Tuple[int, int, int, int]:
        return self.settings.background_color

    @background_color.setter
    def background_color(self, value: Tuple[int, int, int, int]) -> None:
        self.set_background_color(value)

    @property
    def size(self) -> int:
        return self.settings.size

    @size.setter
    def size(self, value: int) -> None:
        self.set_size(value)

    @property
    def opacity(self) -> float:
        return self.settings.opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.set_opacity(value)

    @property
    def hardness(self) -> float:
        return self.settings.hardness

    @hardness.setter
    def hardness(self, value: float) -> None:
        self.set_hardness(value)

    @property
    def flow(self) -> float:
        return self.settings.flow

    @flow.setter
    def flow(self, value: float) -> None:
        self.set_flow(value)

    @property
    def spacing(self) -> float:
        return self.settings.spacing

    @spacing.setter
    def spacing(self, value: float) -> None:
        self.set_spacing(value)

    @property
    def is_eraser(self) -> bool:
        return self.settings.is_eraser

    @is_eraser.setter
    def is_eraser(self, value: bool) -> None:
        self.set_is_eraser(value)

    @property
    def radius(self) -> int:
        return self.settings.radius

    @radius.setter
    def radius(self, value: int) -> None:
        self.settings.radius = value

    # --- Delegated Controller & Stroke Lifecycle Properties ---

    @property
    def _is_drawing(self) -> bool:
        return self.stroke_controller.is_drawing

    @_is_drawing.setter
    def _is_drawing(self, val: bool) -> None:
        self.stroke_controller.is_drawing = val

    @property
    def _last_pt(self) -> Optional[Any]:
        return self.stroke_controller.last_pt

    @_last_pt.setter
    def _last_pt(self, val: Optional[Any]) -> None:
        self.stroke_controller.last_pt = val

    @property
    def _before_snap(self) -> Optional[Any]:
        return self.stroke_controller.before_snap

    @_before_snap.setter
    def _before_snap(self, val: Optional[Any]) -> None:
        self.stroke_controller.before_snap = val

    @property
    def _pixels_modified(self) -> bool:
        return self.stroke_controller.pixels_modified

    @_pixels_modified.setter
    def _pixels_modified(self, val: bool) -> None:
        self.stroke_controller.pixels_modified = val

    @property
    def _cached_dab_key(self) -> Optional[Tuple[Any, ...]]:
        return self.renderer._cached_dab_key

    @_cached_dab_key.setter
    def _cached_dab_key(self, val: Optional[Tuple[Any, ...]]) -> None:
        self.renderer._cached_dab_key = val

    @property
    def _cached_dab(self) -> Optional[Image.Image]:
        return self.renderer._cached_dab

    @_cached_dab.setter
    def _cached_dab(self, val: Optional[Image.Image]) -> None:
        self.renderer._cached_dab = val

    # --- Setting Modifiers ---

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        self.controller.set_color(color)

    def set_background_color(self, color: Tuple[int, int, int, int]) -> None:
        self.controller.set_background_color(color)

    def set_size(self, size: int) -> None:
        self.controller.set_size(size)

    def set_opacity(self, opacity: float) -> None:
        self.controller.set_opacity(opacity)

    def set_hardness(self, hardness: float) -> None:
        self.controller.set_hardness(hardness)

    def set_flow(self, flow: float) -> None:
        self.controller.set_flow(flow)

    def set_spacing(self, spacing: float) -> None:
        self.controller.set_spacing(spacing)

    def set_is_eraser(self, is_eraser: bool) -> None:
        self.controller.set_is_eraser(is_eraser)

    def increase_size(self, delta: int = 2) -> None:
        self.settings.increase_size(delta)
        self.renderer.invalidate_cache()

    def decrease_size(self, delta: int = 2) -> None:
        self.settings.decrease_size(delta)
        self.renderer.invalidate_cache()

    def swap_colors(self) -> None:
        self.controller.swap_colors()

    def reset_default_colors(self) -> None:
        self.controller.reset_default_colors()

    # --- Backward-Compatible Internal API ---

    def _get_brush_dab(self) -> Image.Image:
        return self.renderer.get_dab(self.settings)

    def _render_stroke_segment(
        self,
        target_image: Image.Image,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> None:
        stamped = self.renderer.render_segment(target_image, self.settings, x1, y1, x2, y2)
        if stamped:
            self.stroke_controller.pixels_modified = True

    # --- Authoritative Stroke Lifecycle ---

    def start_stroke(self, pt: Any, target: Any, doc: Optional[Any] = None) -> None:
        self.stroke_controller.start_stroke(pt, target, doc=doc)

    def continue_stroke(self, pt: Any, target: Any) -> None:
        self.stroke_controller.continue_stroke(pt, target)

    def end_stroke(self, doc: Any) -> bool:
        return self.stroke_controller.end_stroke(doc)

    def cancel_stroke(self, doc: Optional[Any] = None) -> None:
        self.stroke_controller.cancel_stroke(doc)

    # --- UI Synchronization & Input Handling ---

    def _sync_brush_bar(self, canvas: Any) -> None:
        mw = getattr(canvas, "main_window", None)
        if mw and hasattr(mw, "brush_bar"):
            bar = mw.brush_bar
            if hasattr(bar, "set_size"):
                bar.set_size(self.size)
            if hasattr(bar, "set_colors"):
                bar.set_colors(self.color, self.background_color)
            elif hasattr(bar, "set_color"):
                bar.set_color(self.color)
            if hasattr(bar, "set_opacity"):
                bar.set_opacity(self.opacity)
            if hasattr(bar, "set_hardness"):
                bar.set_hardness(self.hardness)

    def key_press(self, event: QKeyEvent, canvas: Any) -> bool:
        key = event.key()
        if key == Qt.Key_BracketRight:
            self.increase_size(2)
            self._sync_brush_bar(canvas)
            return True
        elif key == Qt.Key_BracketLeft:
            self.decrease_size(2)
            self._sync_brush_bar(canvas)
            return True
        elif key == Qt.Key_X:
            self.swap_colors()
            self._sync_brush_bar(canvas)
            return True
        elif key == Qt.Key_D:
            self.reset_default_colors()
            self._sync_brush_bar(canvas)
            return True
        return False

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() != Qt.LeftButton:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image or not doc.active_layer:
            return False

        self.start_stroke(scene_pos, doc)
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if not self._is_drawing or self._last_pt is None:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.active_layer:
            return False

        self.continue_stroke(scene_pos, doc)
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton and self._is_drawing:
            doc = getattr(canvas, "document", None)
            if doc:
                self.end_stroke(doc)
                canvas.update_composite_pixmap()
            return True
        return False
