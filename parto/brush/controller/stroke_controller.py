# parto/brush/controller/stroke_controller.py
"""
Parto Brush System — Stroke Lifecycle Controller
Coordinates stroke initiation, trajectory interpolation, and commit/rollback.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Any
from PIL import Image
from ..models.settings import BrushSettings
from ..models.stroke import Stroke, StrokePoint
from ..engine.brush_engine import RasterBrushEngine, IBrushEngine
from ..engine.renderer import BrushRenderer
from ..input.normalizer import InputNormalizer
from ..document_adapter import BrushDocumentAdapter


class StrokeController:
    """
    Manages active stroke lifecycle, coordinate tracking, snapshot captures,
    and history commits with strict no-op detection.
    Decoupled from specific UI widgets.
    """

    def __init__(
        self,
        settings: BrushSettings,
        renderer_or_engine: BrushRenderer | IBrushEngine | None = None,
        adapter: Optional[BrushDocumentAdapter] = None,
    ):
        self.settings: BrushSettings = settings
        if isinstance(renderer_or_engine, BrushRenderer):
            self.engine: IBrushEngine = RasterBrushEngine(renderer_or_engine)
            self.renderer: BrushRenderer = renderer_or_engine
        elif renderer_or_engine is not None:
            self.engine = renderer_or_engine
            self.renderer = getattr(renderer_or_engine, "renderer", None) or BrushRenderer()
        else:
            self.renderer = BrushRenderer()
            self.engine = RasterBrushEngine(self.renderer)

        self.adapter: BrushDocumentAdapter = adapter or BrushDocumentAdapter()

        # Active stroke state
        self.is_drawing: bool = False
        self.last_pt: Optional[Any] = None
        self.before_snap: Optional[Any] = None
        self.before_layer_image: Optional[Image.Image] = None
        self.target_layer: Optional[Any] = None
        self.active_document: Optional[Any] = None
        self.pixels_modified: bool = False
        self.active_stroke: Optional[Stroke] = None

    def start_stroke(self, pt: Any, target: Any, doc: Optional[Any] = None) -> None:
        """
        Initiate a brush stroke on the target document / layer.
        Captures clean pre-stroke state for rollback or history commit.
        """
        self.is_drawing = True
        pointer = InputNormalizer.normalize_point(pt)
        self.last_pt = pointer

        self.active_stroke = Stroke(settings_snapshot=self.settings)
        stroke_pt = self.active_stroke.add_point(
            pointer.x, pointer.y, pointer.pressure, pointer.tilt_x, pointer.tilt_y
        )

        document, layer = self.adapter.resolve_target(target, doc)
        self.active_document = document
        self.target_layer = layer

        # Capture pre-stroke state
        layer_img, snap = self.adapter.capture_pre_stroke(document, layer)
        self.before_layer_image = layer_img
        self.before_snap = snap
        self.pixels_modified = False

        # Render initial dab
        if self.target_layer and hasattr(self.target_layer, "image") and self.target_layer.image:
            ox = getattr(self.target_layer, "offset_x", 0)
            oy = getattr(self.target_layer, "offset_y", 0)
            stamped = self.engine.render_point(
                self.target_layer.image,
                self.settings,
                stroke_pt,
                offset_x=ox,
                offset_y=oy,
            )
            if stamped:
                self.pixels_modified = True
                self.active_stroke.pixels_modified = True

    def continue_stroke(self, pt: Any, target: Any) -> None:
        """
        Interpolate and stamp stroke segment from last point to current point.
        """
        if not self.is_drawing or self.last_pt is None:
            return

        pointer = InputNormalizer.normalize_point(pt)
        if self.active_stroke is None:
            self.active_stroke = Stroke(settings_snapshot=self.settings)

        stroke_pt = self.active_stroke.add_point(
            pointer.x, pointer.y, pointer.pressure, pointer.tilt_x, pointer.tilt_y
        )

        last_stroke_pt = StrokePoint(
            x=self.last_pt.x if hasattr(self.last_pt, "x") else float(self.last_pt[0]),
            y=self.last_pt.y if hasattr(self.last_pt, "y") else float(self.last_pt[1]),
        )

        _, layer = self.adapter.resolve_target(target, self.active_document)
        t_layer = layer or self.target_layer

        if t_layer and hasattr(t_layer, "image") and t_layer.image:
            ox = getattr(t_layer, "offset_x", 0)
            oy = getattr(t_layer, "offset_y", 0)
            stamped = self.engine.render_segment(
                t_layer.image,
                self.settings,
                last_stroke_pt,
                stroke_pt,
                offset_x=ox,
                offset_y=oy,
            )
            if stamped:
                self.pixels_modified = True
                self.active_stroke.pixels_modified = True

        self.last_pt = pointer

    def end_stroke(self, doc: Any) -> bool:
        """
        Commit stroke to document history if and only if actual pixel changes occurred.
        Returns True if a history entry was created, False otherwise.
        """
        self.is_drawing = False
        self.last_pt = None

        if self.active_stroke:
            self.active_stroke.close()

        document = doc or self.active_document
        op_name = f"Brush Stroke ({self.settings.size}px)"

        committed = self.adapter.commit_stroke(
            document=document,
            layer=self.target_layer,
            before_layer_image=self.before_layer_image,
            before_snapshot=self.before_snap,
            operation_name=op_name,
        )

        # Reset stroke transient state
        self.before_snap = None
        self.before_layer_image = None
        self.target_layer = None
        self.active_document = None
        self.pixels_modified = committed
        self.active_stroke = None

        return committed

    def cancel_stroke(self, doc: Optional[Any] = None) -> None:
        """
        Cancel stroke in progress, cleanly rolling back layer and document buffers.
        """
        self.is_drawing = False
        self.last_pt = None

        if self.active_stroke:
            self.active_stroke.close()

        document = doc or self.active_document
        self.adapter.rollback_stroke(
            document=document,
            layer=self.target_layer,
            before_layer_image=self.before_layer_image,
            before_snapshot=self.before_snap,
        )

        self.before_snap = None
        self.before_layer_image = None
        self.target_layer = None
        self.active_document = None
        self.pixels_modified = False
        self.active_stroke = None
