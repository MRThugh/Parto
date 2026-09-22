# parto/tools/brush.py
"""
Parto v0.3.0 - Freehand Brush Tool for Active Layer
Supports size, opacity, hardness, color swapping, and keyboard shortcuts.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import math
from typing import Any, Optional, Tuple
from PIL import Image, ImageDraw
import numpy as np
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent
from .base import BaseTool


class BrushTool(BaseTool):
    """Tool allowing freehand drawing on the active layer."""

    name: str = "Brush"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def __init__(self):
        self.color: Tuple[int, int, int, int] = (0, 0, 0, 255)  # RGBA primary (Black default)
        self.background_color: Tuple[int, int, int, int] = (255, 255, 255, 255)  # Secondary
        self.size: int = 8
        self.opacity: float = 1.0
        self.hardness: float = 0.8
        self._is_drawing: bool = False
        self._last_pt: Optional[QPointF] = None
        self._before_snap: Optional[Any] = None
        self._pixels_modified: bool = False
        self._cached_dab: Optional[Image.Image] = None
        self._cached_dab_key: Optional[Tuple[int, float, float, Tuple[int, int, int, int]]] = None

    @property
    def radius(self) -> int:
        return max(1, self.size // 2)

    @radius.setter
    def radius(self, value: int):
        self.size = max(1, int(value) * 2)

    def set_color(self, color: Tuple[int, int, int, int]):
        self.color = color
        self._cached_dab_key = None

    def set_size(self, size: int):
        self.size = max(1, min(500, int(size)))
        self._cached_dab_key = None

    def set_opacity(self, opacity: float):
        self.opacity = max(0.0, min(1.0, float(opacity)))
        self._cached_dab_key = None

    def set_hardness(self, hardness: float):
        self.hardness = max(0.0, min(1.0, float(hardness)))
        self._cached_dab_key = None

    def increase_size(self, delta: int = 2):
        self.set_size(self.size + delta)

    def decrease_size(self, delta: int = 2):
        self.set_size(self.size - delta)

    def swap_colors(self):
        self.color, self.background_color = self.background_color, self.color
        self._cached_dab_key = None

    def reset_default_colors(self):
        self.color = (0, 0, 0, 255)
        self.background_color = (255, 255, 255, 255)
        self._cached_dab_key = None

    def _sync_brush_bar(self, canvas: Any):
        mw = getattr(canvas, "main_window", None)
        if mw and hasattr(mw, "brush_bar"):
            bar = mw.brush_bar
            if hasattr(bar, "set_size"):
                bar.set_size(self.size)
            if hasattr(bar, "set_color"):
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

    def _get_brush_dab(self) -> Image.Image:
        key = (self.size, round(self.hardness, 2), round(self.opacity, 3), self.color)
        if self._cached_dab is not None and self._cached_dab_key == key:
            return self._cached_dab

        D = max(1, self.size)
        R = D / 2.0
        y, x = np.ogrid[:D, :D]
        dist = np.hypot(x - (R - 0.5), y - (R - 0.5))

        inner_r = R * max(0.0, min(1.0, self.hardness))
        mask = np.zeros((D, D), dtype=np.float32)

        if R <= inner_r or R <= 0.5:
            mask[dist <= R] = 1.0
        else:
            mask[dist <= inner_r] = 1.0
            falloff = (dist > inner_r) & (dist <= R)
            mask[falloff] = 1.0 - (dist[falloff] - inner_r) / (R - inner_r)

        effective_alpha = self.color[3] * self.opacity
        alpha_channel = (mask * effective_alpha).clip(0, 255).astype(np.uint8)

        dab_arr = np.zeros((D, D, 4), dtype=np.uint8)
        dab_arr[:, :, 0] = self.color[0]
        dab_arr[:, :, 1] = self.color[1]
        dab_arr[:, :, 2] = self.color[2]
        dab_arr[:, :, 3] = alpha_channel

        self._cached_dab = Image.fromarray(dab_arr, mode="RGBA")
        self._cached_dab_key = key
        return self._cached_dab

    def _render_stroke_segment(self, target_image: Image.Image, x1: float, y1: float, x2: float, y2: float):
        if self.opacity <= 0.0 or self.size <= 0 or self.color[3] <= 0:
            return

        dab = self._get_brush_dab()
        D = dab.width
        R = D / 2.0

        dist = math.hypot(x2 - x1, y2 - y1)
        step = max(1.0, self.size * 0.25)
        img_w, img_h = target_image.width, target_image.height

        def _stamp(sx: float, sy: float):
            px = int(round(sx - R))
            py = int(round(sy - R))
            if px + D > 0 and py + D > 0 and px < img_w and py < img_h:
                self._pixels_modified = True
                target_image.alpha_composite(dab, dest=(px, py))

        if dist == 0:
            _stamp(x1, y1)
        else:
            num_steps = max(1, int(round(dist / step)))
            for i in range(1, num_steps + 1):
                t = i / num_steps
                _stamp(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

    def start_stroke(self, pt: Any, target: Any, doc: Optional[Any] = None):
        """Begin a new brush stroke."""
        self._is_drawing = True
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        self._last_pt = p
        self._pixels_modified = False

        actual_doc = doc
        if hasattr(target, "active_layer"):
            actual_doc = target
            layer = actual_doc.active_layer
        else:
            layer = target

        if actual_doc is not None and hasattr(actual_doc, "_create_snapshot"):
            if self._before_snap is None:
                self._before_snap = actual_doc._create_snapshot()

        if layer and hasattr(layer, "image") and layer.image:
            if layer.image.mode != "RGBA":
                layer.image = layer.image.convert("RGBA")
            ox = getattr(layer, "offset_x", 0)
            oy = getattr(layer, "offset_y", 0)
            self._render_stroke_segment(layer.image, p.x() - ox, p.y() - oy, p.x() - ox, p.y() - oy)

    def continue_stroke(self, pt: Any, target: Any):
        """Continue drawing an active brush stroke."""
        if not self._is_drawing or self._last_pt is None:
            return
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])

        if hasattr(target, "active_layer"):
            layer = target.active_layer
        else:
            layer = target

        if layer and hasattr(layer, "image") and layer.image:
            if layer.image.mode != "RGBA":
                layer.image = layer.image.convert("RGBA")
            ox = getattr(layer, "offset_x", 0)
            oy = getattr(layer, "offset_y", 0)
            self._render_stroke_segment(
                layer.image,
                self._last_pt.x() - ox,
                self._last_pt.y() - oy,
                p.x() - ox,
                p.y() - oy,
            )
        self._last_pt = p

    def end_stroke(self, doc: Any):
        """Commit an active brush stroke to history."""
        self._is_drawing = False
        self._last_pt = None

        if hasattr(doc, "invalidate_composite"):
            doc.invalidate_composite()

        # If stroke produced no actual pixel modifications, do not record useless history
        if not self._pixels_modified or self.opacity <= 0.0 or self.size <= 0 or self.color[3] <= 0:
            self._before_snap = None
            return

        if hasattr(doc, "set_modified"):
            doc.set_modified(True)

        if hasattr(doc, "_record_operation"):
            snap = self._before_snap if self._before_snap is not None else doc._create_snapshot()
            doc._record_operation(f"Brush Stroke ({self.size}px)", snap)
            self._before_snap = None
        elif hasattr(doc, "history"):
            from ..history.commands import SnapshotCommand
            doc.history.push(SnapshotCommand("Brush Stroke", doc, lambda s: None, None, None))
            self._before_snap = None

    def cancel_stroke(self, doc: Any) -> None:
        """Cancel stroke in progress and restore original layer snapshot."""
        self._is_drawing = False
        self._last_pt = None
        if self._before_snap is not None and hasattr(doc, "_restore_snapshot"):
            doc._restore_snapshot(self._before_snap)
            self._before_snap = None
            if hasattr(doc, "invalidate_composite"):
                doc.invalidate_composite()

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

