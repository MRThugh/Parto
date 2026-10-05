# parto/tools/brush.py
"""
Parto v0.3.0 - Freehand Brush Architecture
Refactored into decoupled BrushSettings, BrushRenderer, and StrokeController.
Supports size, opacity, hardness, color swapping, keyboard shortcuts,
guaranteed pixel-level undo/redo restoration, and strict no-op detection.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import math
import os
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, Tuple, List, Dict, Callable
from PIL import Image
import numpy as np
from PySide6.QtCore import Qt, QPointF, QStandardPaths
from PySide6.QtGui import QMouseEvent, QKeyEvent
from .base import BaseTool

logger = logging.getLogger("parto.tools.brush")


class BrushSettings:
    """
    Encapsulates brush configuration parameters and constraints.
    Authoritative range: 1 to 500 pixels.
    """

    def __init__(
        self,
        size: int = 8,
        opacity: float = 1.0,
        hardness: float = 0.8,
        color: Tuple[int, int, int, int] = (0, 0, 0, 255),
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        flow: float = 1.0,
        spacing: float = 0.25,
        is_eraser: bool = False,
    ):
        self.size: int = max(1, min(500, int(size)))
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.hardness: float = max(0.0, min(1.0, float(hardness)))
        self.color: Tuple[int, int, int, int] = color
        self.background_color: Tuple[int, int, int, int] = background_color
        self.flow: float = max(0.0, min(1.0, float(flow)))
        self.spacing: float = max(0.05, min(2.0, float(spacing)))
        self.is_eraser: bool = bool(is_eraser)
        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_changed(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    @property
    def radius(self) -> int:
        return max(1, self.size // 2)

    @radius.setter
    def radius(self, value: int):
        self.set_size(max(1, min(500, int(value) * 2)))

    def set_size(self, size: int) -> None:
        clamped = max(1, min(500, int(size)))
        if self.size != clamped:
            self.size = clamped
            self.notify_changed()

    def set_opacity(self, opacity: float) -> None:
        clamped = max(0.0, min(1.0, float(opacity)))
        if self.opacity != clamped:
            self.opacity = clamped
            self.notify_changed()

    def set_hardness(self, hardness: float) -> None:
        clamped = max(0.0, min(1.0, float(hardness)))
        if self.hardness != clamped:
            self.hardness = clamped
            self.notify_changed()

    def set_flow(self, flow: float) -> None:
        clamped = max(0.0, min(1.0, float(flow)))
        if self.flow != clamped:
            self.flow = clamped
            self.notify_changed()

    def set_spacing(self, spacing: float) -> None:
        clamped = max(0.05, min(2.0, float(spacing)))
        if self.spacing != clamped:
            self.spacing = clamped
            self.notify_changed()

    def set_is_eraser(self, is_eraser: bool) -> None:
        b = bool(is_eraser)
        if self.is_eraser != b:
            self.is_eraser = b
            self.notify_changed()

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        if self.color != color:
            self.color = color
            self.notify_changed()

    def set_background_color(self, color: Tuple[int, int, int, int]) -> None:
        if self.background_color != color:
            self.background_color = color
            self.notify_changed()

    def increase_size(self, delta: int = 2) -> None:
        self.set_size(self.size + delta)

    def decrease_size(self, delta: int = 2) -> None:
        self.set_size(self.size - delta)

    def swap_colors(self) -> None:
        self.color, self.background_color = self.background_color, self.color
        self.notify_changed()

    def reset_default_colors(self) -> None:
        self.color = (0, 0, 0, 255)
        self.background_color = (255, 255, 255, 255)
        self.notify_changed()


class BrushRenderer:
    """
    Handles dab rasterization and pixel compositing onto target RGBA image buffers.
    """

    def __init__(self):
        self._cached_dab: Optional[Image.Image] = None
        self._cached_dab_key: Optional[Tuple[Any, ...]] = None

    def invalidate_cache(self) -> None:
        self._cached_dab = None
        self._cached_dab_key = None

    def get_dab(self, settings: BrushSettings) -> Image.Image:
        """
        Generate or retrieve a cached circular brush dab with radial hardness falloff.
        """
        flow = getattr(settings, "flow", 1.0)
        is_eraser = getattr(settings, "is_eraser", False)
        key = (
            settings.size,
            round(settings.hardness, 2),
            round(settings.opacity, 3),
            round(flow, 3),
            settings.color,
            is_eraser,
        )
        if self._cached_dab is not None and self._cached_dab_key == key:
            return self._cached_dab

        D = max(1, settings.size)
        R = D / 2.0
        y, x = np.ogrid[:D, :D]
        dist = np.hypot(x - (R - 0.5), y - (R - 0.5))

        inner_r = R * max(0.0, min(1.0, settings.hardness))
        mask = np.zeros((D, D), dtype=np.float32)

        if R <= inner_r or R <= 0.5:
            mask[dist <= R] = 1.0
        else:
            mask[dist <= inner_r] = 1.0
            falloff = (dist > inner_r) & (dist <= R)
            mask[falloff] = 1.0 - (dist[falloff] - inner_r) / (R - inner_r)

        effective_alpha = settings.color[3] * settings.opacity * flow
        alpha_channel = (mask * effective_alpha).clip(0, 255).astype(np.uint8)

        dab_arr = np.zeros((D, D, 4), dtype=np.uint8)
        dab_arr[:, :, 0] = settings.color[0]
        dab_arr[:, :, 1] = settings.color[1]
        dab_arr[:, :, 2] = settings.color[2]
        dab_arr[:, :, 3] = alpha_channel

        self._cached_dab = Image.fromarray(dab_arr, mode="RGBA")
        self._cached_dab_key = key
        return self._cached_dab

    def render_segment(
        self,
        target_image: Image.Image,
        settings: BrushSettings,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> bool:
        """
        Interpolate and stamp dabs along the path between (x1, y1) and (x2, y2).
        Returns True if any dab was stamped within target image bounds.
        """
        if settings.opacity <= 0.0 or settings.size <= 0:
            return False
        if getattr(settings, "flow", 1.0) <= 0.0:
            return False
        is_eraser = getattr(settings, "is_eraser", False)
        if not is_eraser and settings.color[3] <= 0:
            return False

        dab = self.get_dab(settings)
        D = dab.width
        R = D / 2.0

        dist = math.hypot(x2 - x1, y2 - y1)
        spacing = getattr(settings, "spacing", 0.25)
        step = max(1.0, R * max(0.05, spacing * 2.0))
        num_steps = max(1, int(math.ceil(dist / step)))

        W, H = target_image.size
        stamped_any = False

        for i in range(num_steps + 1):
            t = float(i) / float(num_steps) if num_steps > 0 else 0.0
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t

            px = int(round(cx - R))
            py = int(round(cy - R))

            if px + D <= 0 or px >= W or py + D <= 0 or py >= H:
                continue

            sx1 = max(0, -px)
            sy1 = max(0, -py)
            sx2 = min(D, W - px)
            sy2 = min(D, H - py)

            if sx2 <= sx1 or sy2 <= sy1:
                continue

            dest_box = (px + sx1, py + sy1, px + sx2, py + sy2)
            dab_crop = dab.crop((sx1, sy1, sx2, sy2))

            if is_eraser:
                dest_crop = target_image.crop(dest_box)
                dest_arr = np.array(dest_crop)
                dab_arr = np.array(dab_crop)
                dab_alpha = dab_arr[:, :, 3].astype(np.float32) / 255.0
                dest_arr[:, :, 3] = (
                    dest_arr[:, :, 3].astype(np.float32) * (1.0 - dab_alpha)
                ).clip(0, 255).astype(np.uint8)
                erased_patch = Image.fromarray(dest_arr, mode="RGBA")
                target_image.paste(erased_patch, (px + sx1, py + sy1))
                stamped_any = True
            else:
                dest = (px + sx1, py + sy1)
                target_image.alpha_composite(dab_crop, dest=dest)
                stamped_any = True

        return stamped_any


class StrokeController:
    """
    Manages active stroke lifecycle, coordinate tracking, snapshot captures,
    and history commits with strict no-op detection.
    """

    def __init__(self, settings: BrushSettings, renderer: BrushRenderer):
        self.settings = settings
        self.renderer = renderer
        self.is_drawing: bool = False
        self.last_pt: Optional[QPointF] = None
        self.before_snap: Optional[Any] = None
        self.before_layer_image: Optional[Image.Image] = None
        self.target_layer: Optional[Any] = None
        self.pixels_modified: bool = False

    def start_stroke(self, pt: Any, target: Any, doc: Optional[Any] = None) -> None:
        """
        Initiate a brush stroke on the target document / layer.
        Captures clean pre-stroke state for rollback or undo commitment.
        """
        self.is_drawing = True
        if hasattr(pt, "x") and hasattr(pt, "y"):
            p = QPointF(float(pt.x()), float(pt.y()))
        elif isinstance(pt, QPointF):
            p = pt
        else:
            p = QPointF(float(pt[0]), float(pt[1]))
        self.last_pt = p
        self.pixels_modified = False

        # Identify target layer and document
        if hasattr(target, "active_layer"):
            self.target_layer = target.active_layer
            document = target
        else:
            self.target_layer = target
            document = doc

        if self.target_layer and hasattr(self.target_layer, "image") and self.target_layer.image:
            self.before_layer_image = self.target_layer.image.copy()

        # Capture complete pre-operation document snapshot
        if document and hasattr(document, "_create_snapshot"):
            self.before_snap = document._create_snapshot()
        else:
            self.before_snap = None

        # Stamp initial dab
        if self.target_layer and hasattr(self.target_layer, "image") and self.target_layer.image:
            ox = getattr(self.target_layer, "offset_x", 0)
            oy = getattr(self.target_layer, "offset_y", 0)
            stamped = self.renderer.render_segment(
                self.target_layer.image,
                self.settings,
                p.x() - ox,
                p.y() - oy,
                p.x() - ox,
                p.y() - oy,
            )
            if stamped:
                self.pixels_modified = True

    def continue_stroke(self, pt: Any, target: Any) -> None:
        """Interpolate and stamp stroke segment from last point to current point."""
        if not self.is_drawing or self.last_pt is None:
            return

        if hasattr(pt, "x") and hasattr(pt, "y"):
            p = QPointF(float(pt.x()), float(pt.y()))
        elif isinstance(pt, QPointF):
            p = pt
        else:
            p = QPointF(float(pt[0]), float(pt[1]))

        t_layer = target.active_layer if hasattr(target, "active_layer") else target
        if t_layer and hasattr(t_layer, "image") and t_layer.image:
            ox = getattr(t_layer, "offset_x", 0)
            oy = getattr(t_layer, "offset_y", 0)
            stamped = self.renderer.render_segment(
                t_layer.image,
                self.settings,
                self.last_pt.x() - ox,
                self.last_pt.y() - oy,
                p.x() - ox,
                p.y() - oy,
            )
            if stamped:
                self.pixels_modified = True

        self.last_pt = p

    def end_stroke(self, doc: Any) -> bool:
        """
        Commit stroke to history if and only if actual pixel changes occurred.
        Returns True if a history entry was created, False otherwise.
        """
        self.is_drawing = False
        self.last_pt = None

        has_pixel_change = False
        if (
            self.target_layer is not None
            and hasattr(self.target_layer, "image")
            and self.target_layer.image is not None
            and self.before_layer_image is not None
        ):
            has_pixel_change = (
                self.target_layer.image.tobytes() != self.before_layer_image.tobytes()
            )

        if not has_pixel_change:
            self.before_snap = None
            self.before_layer_image = None
            self.target_layer = None
            self.pixels_modified = False
            if hasattr(doc, "invalidate_composite"):
                doc.invalidate_composite()
            return False

        if self.before_snap is None and hasattr(doc, "_create_snapshot"):
            self.before_snap = doc._create_snapshot()
            target_id = getattr(self.target_layer, "id", None)
            target_name = getattr(self.target_layer, "name", None)
            found = False
            if "layer_stack" in self.before_snap:
                for lay in self.before_snap["layer_stack"]:
                    if (target_id and lay.id == target_id) or (target_name and lay.name == target_name):
                        lay.image = self.before_layer_image.copy()
                        found = True
                        break
                if not found and self.before_snap["layer_stack"].active_layer:
                    self.before_snap["layer_stack"].active_layer.image = self.before_layer_image.copy()

        if hasattr(doc, "set_modified"):
            doc.set_modified(True)

        if hasattr(doc, "_record_operation") and self.before_snap is not None:
            doc._record_operation(f"Brush Stroke ({self.settings.size}px)", self.before_snap)
        elif hasattr(doc, "history"):
            from ..history.commands import SnapshotCommand
            after_snap = doc._create_snapshot() if hasattr(doc, "_create_snapshot") else None
            restore_func = getattr(doc, "_restore_snapshot", lambda s: None)
            doc.history.push(
                SnapshotCommand(
                    f"Brush Stroke ({self.settings.size}px)",
                    doc,
                    restore_func,
                    self.before_snap,
                    after_snap,
                )
            )

        if hasattr(doc, "invalidate_composite"):
            doc.invalidate_composite()

        self.before_snap = None
        self.before_layer_image = None
        self.target_layer = None
        self.pixels_modified = True
        return True

    def cancel_stroke(self, doc: Optional[Any] = None) -> None:
        """Cancel stroke in progress, restoring layer and document state."""
        self.is_drawing = False
        self.last_pt = None

        if self.target_layer and self.before_layer_image and hasattr(self.target_layer, "image"):
            self.target_layer.image = self.before_layer_image.copy()

        if doc is not None and self.before_snap is not None and hasattr(doc, "_restore_snapshot"):
            doc._restore_snapshot(self.before_snap)

        if doc is not None and hasattr(doc, "invalidate_composite"):
            doc.invalidate_composite()

        self.before_snap = None
        self.before_layer_image = None
        self.target_layer = None
        self.pixels_modified = False


class BrushTool(BaseTool):
    """
    Authoritative Brush Tool for freehand drawing on the active layer.
    Coordinates settings, rendering, and input events through unified stroke path.
    """

    name: str = "Brush"
    cursor_shape: Qt.CursorShape = Qt.CrossCursor

    def __init__(self):
        self.settings = BrushSettings()
        self.renderer = BrushRenderer()
        self.stroke_controller = StrokeController(self.settings, self.renderer)

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

    # --- Delegated Properties ---

    @property
    def color(self) -> Tuple[int, int, int, int]:
        return self.settings.color

    @color.setter
    def color(self, value: Tuple[int, int, int, int]) -> None:
        self.settings.set_color(value)

    @property
    def background_color(self) -> Tuple[int, int, int, int]:
        return self.settings.background_color

    @background_color.setter
    def background_color(self, value: Tuple[int, int, int, int]) -> None:
        self.settings.set_background_color(value)

    @property
    def size(self) -> int:
        return self.settings.size

    @size.setter
    def size(self, value: int) -> None:
        self.settings.set_size(value)

    @property
    def opacity(self) -> float:
        return self.settings.opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.settings.set_opacity(value)

    @property
    def hardness(self) -> float:
        return self.settings.hardness

    @hardness.setter
    def hardness(self, value: float) -> None:
        self.settings.set_hardness(value)

    @property
    def flow(self) -> float:
        return self.settings.flow

    @flow.setter
    def flow(self, value: float) -> None:
        self.settings.set_flow(value)

    @property
    def spacing(self) -> float:
        return self.settings.spacing

    @spacing.setter
    def spacing(self, value: float) -> None:
        self.settings.set_spacing(value)

    @property
    def is_eraser(self) -> bool:
        return self.settings.is_eraser

    @is_eraser.setter
    def is_eraser(self, value: bool) -> None:
        self.settings.set_is_eraser(value)

    @property
    def radius(self) -> int:
        return self.settings.radius

    @radius.setter
    def radius(self, value: int) -> None:
        self.settings.radius = value

    @property
    def _is_drawing(self) -> bool:
        return self.stroke_controller.is_drawing

    @_is_drawing.setter
    def _is_drawing(self, val: bool) -> None:
        self.stroke_controller.is_drawing = val

    @property
    def _last_pt(self) -> Optional[QPointF]:
        return self.stroke_controller.last_pt

    @_last_pt.setter
    def _last_pt(self, val: Optional[QPointF]) -> None:
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
    def _cached_dab_key(self) -> Optional[Tuple[int, float, float, Tuple[int, int, int, int]]]:
        return self.renderer._cached_dab_key

    @_cached_dab_key.setter
    def _cached_dab_key(self, val: Optional[Tuple[int, float, float, Tuple[int, int, int, int]]]) -> None:
        self.renderer._cached_dab_key = val

    @property
    def _cached_dab(self) -> Optional[Image.Image]:
        return self.renderer._cached_dab

    @_cached_dab.setter
    def _cached_dab(self, val: Optional[Image.Image]) -> None:
        self.renderer._cached_dab = val

    # --- Setting Modifiers ---

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        self.settings.set_color(color)
        self.renderer.invalidate_cache()

    def set_background_color(self, color: Tuple[int, int, int, int]) -> None:
        self.settings.set_background_color(color)

    def set_size(self, size: int) -> None:
        self.settings.set_size(size)
        self.renderer.invalidate_cache()

    def set_opacity(self, opacity: float) -> None:
        self.settings.set_opacity(opacity)
        self.renderer.invalidate_cache()

    def set_hardness(self, hardness: float) -> None:
        self.settings.set_hardness(hardness)
        self.renderer.invalidate_cache()

    def set_flow(self, flow: float) -> None:
        self.settings.set_flow(flow)
        self.renderer.invalidate_cache()

    def set_spacing(self, spacing: float) -> None:
        self.settings.set_spacing(spacing)

    def set_is_eraser(self, is_eraser: bool) -> None:
        self.settings.set_is_eraser(is_eraser)
        self.renderer.invalidate_cache()

    def increase_size(self, delta: int = 2) -> None:
        self.settings.increase_size(delta)
        self.renderer.invalidate_cache()

    def decrease_size(self, delta: int = 2) -> None:
        self.settings.decrease_size(delta)
        self.renderer.invalidate_cache()

    def swap_colors(self) -> None:
        self.settings.swap_colors()
        self.renderer.invalidate_cache()

    def reset_default_colors(self) -> None:
        self.settings.reset_default_colors()
        self.renderer.invalidate_cache()

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


def get_default_presets_path() -> str:
    """Return default filesystem location for user brush presets."""
    try:
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    except Exception:
        base = ""
    if not base:
        base = os.path.expanduser("~/.parto")
    return os.path.join(base, "brush_presets.json")


@dataclass
class BrushPreset:
    """
    Data model representing a brush preset configuration.
    """
    name: str
    size: int = 12
    opacity: float = 1.0
    flow: float = 1.0
    hardness: float = 0.8
    spacing: float = 0.25
    is_eraser: bool = False
    is_builtin: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "opacity": self.opacity,
            "flow": self.flow,
            "hardness": self.hardness,
            "spacing": self.spacing,
            "is_eraser": self.is_eraser,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], is_builtin: bool = False) -> BrushPreset:
        return cls(
            name=str(data.get("name", "Custom")),
            size=int(data.get("size", 12)),
            opacity=float(data.get("opacity", 1.0)),
            flow=float(data.get("flow", 1.0)),
            hardness=float(data.get("hardness", 0.8)),
            spacing=float(data.get("spacing", 0.25)),
            is_eraser=bool(data.get("is_eraser", False)),
            is_builtin=is_builtin,
            description=str(data.get("description", "")),
        )

    def apply_to(self, settings: BrushSettings) -> None:
        """Apply preset properties to the authoritative BrushSettings."""
        settings.size = max(1, min(500, int(self.size)))
        settings.opacity = max(0.0, min(1.0, float(self.opacity)))
        settings.flow = max(0.0, min(1.0, float(self.flow)))
        settings.hardness = max(0.0, min(1.0, float(self.hardness)))
        settings.spacing = max(0.05, min(2.0, float(self.spacing)))
        settings.is_eraser = bool(self.is_eraser)
        settings.notify_changed()


class BrushPresetManager:
    """
    Coordinates built-in and user-defined brush presets.
    Guarantees built-in immutability and safe user persistence.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path: str = storage_path or get_default_presets_path()
        self._builtin_presets: List[BrushPreset] = []
        self._user_presets: List[BrushPreset] = []
        self._active_preset_name: Optional[str] = "Basic Round"
        self._init_builtins()
        self.load_user_presets()

    def _init_builtins(self) -> None:
        self._builtin_presets = [
            BrushPreset("Basic Round", size=12, opacity=1.0, flow=1.0, hardness=0.8, spacing=0.25, is_eraser=False, is_builtin=True, description="Standard general-purpose brush"),
            BrushPreset("Soft Round", size=24, opacity=0.8, flow=0.8, hardness=0.15, spacing=0.20, is_eraser=False, is_builtin=True, description="Soft feathered edges for blending"),
            BrushPreset("Hard Round", size=16, opacity=1.0, flow=1.0, hardness=1.0, spacing=0.20, is_eraser=False, is_builtin=True, description="Crisp, sharp solid round brush"),
            BrushPreset("Pencil", size=2, opacity=0.95, flow=1.0, hardness=0.95, spacing=0.15, is_eraser=False, is_builtin=True, description="Fine line sketching tool"),
            BrushPreset("Ink", size=6, opacity=1.0, flow=1.0, hardness=0.9, spacing=0.10, is_eraser=False, is_builtin=True, description="Fluid continuous inking line"),
            BrushPreset("Marker", size=22, opacity=0.55, flow=0.75, hardness=0.7, spacing=0.18, is_eraser=False, is_builtin=True, description="Semi-transparent layering marker"),
            BrushPreset("Airbrush", size=40, opacity=0.35, flow=0.45, hardness=0.02, spacing=0.15, is_eraser=False, is_builtin=True, description="Diffuse soft aerosol spray"),
            BrushPreset("Eraser", size=20, opacity=1.0, flow=1.0, hardness=0.85, spacing=0.20, is_eraser=True, is_builtin=True, description="Erases pixels from the active layer"),
        ]

    def get_all_presets(self) -> List[BrushPreset]:
        return list(self._builtin_presets) + list(self._user_presets)

    def get_builtin_presets(self) -> List[BrushPreset]:
        return list(self._builtin_presets)

    def get_user_presets(self) -> List[BrushPreset]:
        return list(self._user_presets)

    def get_preset(self, name: str) -> Optional[BrushPreset]:
        target = name.strip().lower()
        for p in self.get_all_presets():
            if p.name.strip().lower() == target:
                return p
        return None

    @property
    def active_preset_name(self) -> Optional[str]:
        return self._active_preset_name

    @active_preset_name.setter
    def active_preset_name(self, name: Optional[str]) -> None:
        self._active_preset_name = name

    def apply_preset(self, name: str, settings: BrushSettings) -> bool:
        preset = self.get_preset(name)
        if preset:
            preset.apply_to(settings)
            self._active_preset_name = preset.name
            return True
        return False

    def create_user_preset(
        self,
        name: str,
        settings: BrushSettings,
        description: str = "",
    ) -> BrushPreset:
        clean_name = name.strip()
        if not clean_name:
            clean_name = f"Custom {len(self._user_presets) + 1}"

        for b in self._builtin_presets:
            if b.name.lower() == clean_name.lower():
                clean_name = f"{clean_name} (User)"
                break

        self._user_presets = [p for p in self._user_presets if p.name.lower() != clean_name.lower()]

        preset = BrushPreset(
            name=clean_name,
            size=settings.size,
            opacity=settings.opacity,
            flow=getattr(settings, "flow", 1.0),
            hardness=settings.hardness,
            spacing=getattr(settings, "spacing", 0.25),
            is_eraser=getattr(settings, "is_eraser", False),
            is_builtin=False,
            description=description,
        )
        self._user_presets.append(preset)
        self._active_preset_name = preset.name
        self.save_user_presets()
        return preset

    def delete_user_preset(self, name: str) -> bool:
        clean_name = name.strip().lower()
        for b in self._builtin_presets:
            if b.name.strip().lower() == clean_name:
                return False

        before_len = len(self._user_presets)
        self._user_presets = [p for p in self._user_presets if p.name.strip().lower() != clean_name]
        if len(self._user_presets) < before_len:
            if self._active_preset_name and self._active_preset_name.strip().lower() == clean_name:
                self._active_preset_name = "Basic Round"
            self.save_user_presets()
            return True
        return False

    def save_user_presets(self) -> None:
        try:
            folder = os.path.dirname(self.storage_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            data = [p.to_dict() for p in self._user_presets]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist user brush presets: {e}")

    def load_user_presets(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._user_presets = [
                    BrushPreset.from_dict(item, is_builtin=False)
                    for item in data
                    if isinstance(item, dict) and "name" in item
                ]
        except Exception as e:
            logger.warning(f"Could not load user brush presets: {e}")

