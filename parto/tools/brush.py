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
        if self.opacity <= 0.0 or self.size <= 0:
            return

        if self.hardness >= 0.98 and self.opacity >= 0.999:
            draw = ImageDraw.Draw(target_image)
            r = max(1, self.size // 2)
            draw.line([(x1, y1), (x2, y2)], fill=self.color, width=self.size)
            draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=self.color)
            return

        dab = self._get_brush_dab()
        D = dab.width
        R = D / 2.0

        dist = math.hypot(x2 - x1, y2 - y1)
        step = max(1.0, self.size * 0.25)
        num_steps = max(1, int(dist / step))

        for i in range(num_steps + 1):
            t = i / num_steps
            px = int(round(x1 + (x2 - x1) * t - R))
            py = int(round(y1 + (y2 - y1) * t - R))
            target_image.paste(dab, (px, py), dab)

    def start_stroke(self, pt: Any, layer: Any):
        self._is_drawing = True
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        self._last_pt = p
        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")
        self._render_stroke_segment(layer.image, p.x(), p.y(), p.x(), p.y())

    def continue_stroke(self, pt: Any, layer: Any):
        if not self._is_drawing or self._last_pt is None:
            return
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")
        self._render_stroke_segment(layer.image, self._last_pt.x(), self._last_pt.y(), p.x(), p.y())
        self._last_pt = p

    def end_stroke(self, doc: Any):
        self._is_drawing = False
        self._last_pt = None
        if hasattr(doc, "invalidate_composite"):
            doc.invalidate_composite()
        if hasattr(doc, "set_modified"):
            doc.set_modified(True)
        if hasattr(doc, "_record_operation"):
            snap = getattr(self, "_before_snap", None) or (doc._create_snapshot() if hasattr(doc, "_create_snapshot") else None)
            doc._record_operation(f"Brush Stroke ({self.size}px)", snap or doc._create_snapshot())
            self._before_snap = None
        elif hasattr(doc, "history"):
            from ..history.commands import SnapshotCommand
            doc.history.push(SnapshotCommand(f"Brush Stroke", doc, lambda s: None, None, None))

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() != Qt.LeftButton:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image or not doc.active_layer:
            return False

        self._is_drawing = True
        self._last_pt = scene_pos
        self._before_snap = doc._create_snapshot()

        # Draw initial stamp
        self._draw_stroke(doc, scene_pos, scene_pos)
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_move(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if not self._is_drawing or self._last_pt is None:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.active_layer:
            return False

        self._draw_stroke(doc, self._last_pt, scene_pos)
        self._last_pt = scene_pos
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton and self._is_drawing:
            self._is_drawing = False
            self._last_pt = None
            doc = getattr(canvas, "document", None)
            if doc:
                doc.invalidate_composite()
                doc.set_modified(True)
                if self._before_snap:
                    doc._record_operation(f"Brush Stroke ({self.size}px)", self._before_snap)
                    self._before_snap = None
                canvas.update_composite_pixmap()
            return True
        return False

    def _draw_stroke(self, doc: Any, p1: QPointF, p2: QPointF):
        layer = doc.active_layer
        if not layer or not layer.image:
            return

        if layer.image.mode != "RGBA":
            layer.image = layer.image.convert("RGBA")

        ox, oy = layer.offset_x, layer.offset_y
        x1, y1 = p1.x() - ox, p1.y() - oy
        x2, y2 = p2.x() - ox, p2.y() - oy

        self._render_stroke_segment(layer.image, x1, y1, x2, y2)

