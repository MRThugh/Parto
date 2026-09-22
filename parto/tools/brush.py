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
from typing import Any, Optional, Tuple
from PIL import Image
import numpy as np
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent
from .base import BaseTool


class BrushSettings:
    """
    Encapsulates brush configuration parameters and constraints.
    """

    def __init__(
        self,
        size: int = 8,
        opacity: float = 1.0,
        hardness: float = 0.8,
        color: Tuple[int, int, int, int] = (0, 0, 0, 255),
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    ):
        self.size: int = max(1, min(500, int(size)))
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.hardness: float = max(0.0, min(1.0, float(hardness)))
        self.color: Tuple[int, int, int, int] = color
        self.background_color: Tuple[int, int, int, int] = background_color

    @property
    def radius(self) -> int:
        return max(1, self.size // 2)

    @radius.setter
    def radius(self, value: int):
        self.size = max(1, min(500, int(value) * 2))

    def set_size(self, size: int) -> None:
        self.size = max(1, min(500, int(size)))

    def set_opacity(self, opacity: float) -> None:
        self.opacity = max(0.0, min(1.0, float(opacity)))

    def set_hardness(self, hardness: float) -> None:
        self.hardness = max(0.0, min(1.0, float(hardness)))

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        self.color = color

    def increase_size(self, delta: int = 2) -> None:
        self.set_size(self.size + delta)

    def decrease_size(self, delta: int = 2) -> None:
        self.set_size(self.size - delta)

    def swap_colors(self) -> None:
        self.color, self.background_color = self.background_color, self.color

    def reset_default_colors(self) -> None:
        self.color = (0, 0, 0, 255)
        self.background_color = (255, 255, 255, 255)


class BrushRenderer:
    """
    Handles dab rasterization and pixel compositing onto target RGBA image buffers.
    """

    def __init__(self):
        self._cached_dab: Optional[Image.Image] = None
        self._cached_dab_key: Optional[Tuple[int, float, float, Tuple[int, int, int, int]]] = None

    def invalidate_cache(self) -> None:
        self._cached_dab = None
        self._cached_dab_key = None

    def get_dab(self, settings: BrushSettings) -> Image.Image:
        """
        Generate or retrieve a cached circular brush dab with radial hardness falloff.
        """
        key = (settings.size, round(settings.hardness, 2), round(settings.opacity, 3), settings.color)
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

        effective_alpha = settings.color[3] * settings.opacity
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
        if settings.opacity <= 0.0 or settings.size <= 0 or settings.color[3] <= 0:
            return False

        dab = self.get_dab(settings)
        D = dab.width
        R = D / 2.0

        dist = math.hypot(x2 - x1, y2 - y1)
        step = max(1.0, settings.size * 0.25)
        img_w, img_h = target_image.width, target_image.height
        any_stamped = False

        def _stamp(sx: float, sy: float):
            nonlocal any_stamped
            px = int(round(sx - R))
            py = int(round(sy - R))
            if px + D > 0 and py + D > 0 and px < img_w and py < img_h:
                any_stamped = True
                target_image.alpha_composite(dab, dest=(px, py))

        if dist == 0:
            _stamp(x1, y1)
        else:
            num_steps = max(1, int(round(dist / step)))
            for i in range(1, num_steps + 1):
                t = i / num_steps
                _stamp(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

        return any_stamped


class StrokeController:
    """
    Manages the stroke lifecycle:
    - Pre-stroke snapshot capture before any pixel modification.
    - Interpolated segment drawing.
    - Pixel-level no-op comparison before pushing history.
    - Deterministic cancellation and cleanup.
    """

    def __init__(self, settings: BrushSettings, renderer: BrushRenderer):
        self.settings: BrushSettings = settings
        self.renderer: BrushRenderer = renderer
        self.is_drawing: bool = False
        self.last_pt: Optional[QPointF] = None
        self.before_snap: Optional[Any] = None
        self.before_layer_image: Optional[Image.Image] = None
        self.target_layer: Optional[Any] = None
        self.pixels_modified: bool = False

    def start_stroke(self, pt: Any, target: Any, doc: Optional[Any] = None) -> None:
        """Begin a new stroke, guaranteeing pre-stroke state capture before first pixel change."""
        self.is_drawing = True
        p = QPointF(pt.x(), pt.y()) if hasattr(pt, "x") else QPointF(pt[0], pt[1])
        self.last_pt = p
        self.pixels_modified = False

        actual_doc = doc
        if hasattr(target, "active_layer"):
            actual_doc = target
            layer = actual_doc.active_layer
        else:
            layer = target

        self.target_layer = layer

        # 1. Guarantee pre-stroke layer image snapshot BEFORE any pixel modification
        if layer and hasattr(layer, "image") and layer.image:
            if layer.image.mode != "RGBA":
                layer.image = layer.image.convert("RGBA")
            self.before_layer_image = layer.image.copy()

        # 2. Capture full document snapshot if document is available
        if actual_doc is not None and hasattr(actual_doc, "_create_snapshot"):
            self.before_snap = actual_doc._create_snapshot()
        else:
            self.before_snap = None

        # 3. Render initial dab at stroke start
        if layer and hasattr(layer, "image") and layer.image:
            ox = getattr(layer, "offset_x", 0)
            oy = getattr(layer, "offset_y", 0)
            stamped = self.renderer.render_segment(
                layer.image,
                self.settings,
                p.x() - ox,
                p.y() - oy,
                p.x() - ox,
                p.y() - oy,
            )
            if stamped:
                self.pixels_modified = True

    def continue_stroke(self, pt: Any, target: Any) -> None:
        """Continue drawing an active stroke with interpolated dabs."""
        if not self.is_drawing or self.last_pt is None:
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
            stamped = self.renderer.render_segment(
                layer.image,
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

        # Verify pixel-level modifications against the pre-stroke baseline
        has_pixel_change = False
        if (
            self.target_layer is not None
            and hasattr(self.target_layer, "image")
            and self.target_layer.image is not None
            and self.before_layer_image is not None
        ):
            # Fast binary byte comparison of RGBA pixel buffers
            has_pixel_change = (
                self.target_layer.image.tobytes() != self.before_layer_image.tobytes()
            )

        if not has_pixel_change:
            # NO-OP: No actual pixel changed (transparent, identical color, or out-of-bounds)
            self.before_snap = None
            self.before_layer_image = None
            self.target_layer = None
            self.pixels_modified = False
            if hasattr(doc, "invalidate_composite"):
                doc.invalidate_composite()
            return False

        # Pixels were modified: Ensure before_snap correctly contains pre-stroke image data
        if self.before_snap is None and hasattr(doc, "_create_snapshot"):
            # Construct authoritative snapshot with target layer restored to pre-stroke bytes
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

        # Push to document history
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

        # Cleanup stroke state
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
        self.settings.background_color = value

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

    # --- Delegated Setting Modifiers ---

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        self.settings.set_color(color)
        self.renderer.invalidate_cache()

    def set_size(self, size: int) -> None:
        self.settings.set_size(size)
        self.renderer.invalidate_cache()

    def set_opacity(self, opacity: float) -> None:
        self.settings.set_opacity(opacity)
        self.renderer.invalidate_cache()

    def set_hardness(self, hardness: float) -> None:
        self.settings.set_hardness(hardness)
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
        """Begin a new brush stroke."""
        self.stroke_controller.start_stroke(pt, target, doc=doc)

    def continue_stroke(self, pt: Any, target: Any) -> None:
        """Continue drawing an active brush stroke."""
        self.stroke_controller.continue_stroke(pt, target)

    def end_stroke(self, doc: Any) -> bool:
        """Commit an active brush stroke to history."""
        return self.stroke_controller.end_stroke(doc)

    def cancel_stroke(self, doc: Optional[Any] = None) -> None:
        """Cancel stroke in progress and restore original layer snapshot."""
        self.stroke_controller.cancel_stroke(doc)

    # --- UI Synchronization & Input Handling ---

    def _sync_brush_bar(self, canvas: Any) -> None:
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

    def mouse_press(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() != Qt.LeftButton:
            return False

        doc = getattr(canvas, "document", None)
        if not doc or not doc.has_image or not doc.active_layer:
            return False

        # Unified stroke entry point
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

        # Unified stroke continuation
        self.continue_stroke(scene_pos, doc)
        doc.invalidate_composite()
        canvas.update_composite_pixmap()
        return True

    def mouse_release(self, event: QMouseEvent, scene_pos: QPointF, canvas: Any) -> bool:
        if event.button() == Qt.LeftButton and self._is_drawing:
            doc = getattr(canvas, "document", None)
            if doc:
                # Unified stroke commit
                self.end_stroke(doc)
                canvas.update_composite_pixmap()
            return True
        return False
