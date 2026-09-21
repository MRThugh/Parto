# parto/editor/canvas.py
"""
Parto v0.3.0 - High-Performance Interactive Graphics View Canvas
Smooth zoom/pan, tool routing, pixel color inspection, and transparency checkerboard.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import math
from typing import Optional, Any
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter,
    QPixmap,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
    QBrush,
    QColor,
    QBitmap,
)
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
)

from .document import Document
from ..tools.base import BaseTool
from ..tools.move import MoveTool
from ..tools.crop import CropTool
from ..utils.conversions import pil_to_qpixmap
from ..themes.manager import get_theme_manager


class Canvas(QGraphicsView):
    """
    Primary editor viewport supporting multi-layer rendering, interactive tools,
    pixel inspection, and zoom/pan navigation.
    """
    zoom_changed = Signal(float)
    pixel_inspected = Signal(int, int, int, int, int, int)  # x, y, r, g, b, a

    ZOOM_MIN = 0.05
    ZOOM_MAX = 32.0
    ZOOM_STEP = 1.25

    def __init__(self, document: Document, parent: Optional[Any] = None):
        super().__init__(parent)
        self.document = document
        self.main_window = parent

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Rendering options for silky smooth interaction
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Graphic items
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._bg_rect_item: Optional[QGraphicsRectItem] = None

        # Tools & State
        self.default_tool = MoveTool()
        self.active_tool: BaseTool = self.default_tool
        self._zoom_factor: float = 1.0
        self._is_space_pressed: bool = False

        # Connect document and theme
        self.document.document_changed.connect(self.update_composite_pixmap)
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

        self._setup_checkerboard()

    def _setup_checkerboard(self):
        """Create dynamic checkerboard pattern matching current theme."""
        pal = get_theme_manager().get_palette()
        c1 = QColor(pal.get("canvas_checker_1", "#1a1a1c"))
        c2 = QColor(pal.get("canvas_checker_2", "#222226"))

        # 16x16 tile pattern
        pix = QPixmap(16, 16)
        p = QPainter(pix)
        p.fillRect(0, 0, 8, 8, c1)
        p.fillRect(8, 8, 8, 8, c1)
        p.fillRect(8, 0, 8, 8, c2)
        p.fillRect(0, 8, 8, 8, c2)
        p.end()

        self.setBackgroundBrush(QBrush(pix))

    def _on_theme_changed(self, _: str):
        self._setup_checkerboard()
        self.viewport().update()

    @property
    def crop_mode(self) -> bool:
        return isinstance(self.active_tool, CropTool)

    @property
    def crop_aspect_ratio(self) -> Optional[float]:
        if isinstance(self.active_tool, CropTool):
            return self.active_tool.selection.aspect_ratio
        return None

    def set_crop_mode(self, enabled: bool, aspect_ratio: Optional[float] = None) -> None:
        """Compatibility method to enable or disable crop mode."""
        if enabled:
            if not isinstance(self.active_tool, CropTool):
                crop_tool = CropTool()
                if aspect_ratio is not None:
                    crop_tool.selection.aspect_ratio = aspect_ratio
                self.set_tool(crop_tool)
            else:
                if aspect_ratio is not None:
                    self.active_tool.selection.aspect_ratio = aspect_ratio
                    self.viewport().update()
        else:
            self.set_tool(self.default_tool)

    def set_tool(self, tool: BaseTool) -> None:
        """Switch current interactive tool."""
        if self.active_tool:
            self.active_tool.deactivate(self)
        self.active_tool = tool
        self.active_tool.activate(self)
        self.viewport().update()

    def update_composite_pixmap(self) -> None:
        """Refresh rendered scene from document composite."""
        comp = self.document.get_composite()
        if comp is None:
            self._scene.clear()
            self._pixmap_item = None
            return

        pix = pil_to_qpixmap(comp)
        if self._pixmap_item is None:
            self._scene.clear()
            self._pixmap_item = self._scene.addPixmap(pix)
            self._pixmap_item.setZValue(1)
        else:
            self._pixmap_item.setPixmap(pix)

        self._scene.setSceneRect(0, 0, self.document.width, self.document.height)
        self.viewport().update()

    def show_preview_image(self, image: Optional[Any]) -> None:
        """Display a live temporary adjustment preview without modifying document."""
        if image is None:
            self.update_composite_pixmap()
            return

        pix = pil_to_qpixmap(image)
        if self._pixmap_item is None:
            self._scene.clear()
            self._pixmap_item = self._scene.addPixmap(pix)
            self._pixmap_item.setZValue(1)
        else:
            self._pixmap_item.setPixmap(pix)

        self._scene.setSceneRect(0, 0, self.document.width, self.document.height)
        self.viewport().update()

    # Zoom & View Operations
    @property
    def zoom_factor(self) -> float:
        return self._zoom_factor

    def set_zoom(self, factor: float) -> None:
        factor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, factor))
        scale_change = factor / self._zoom_factor
        self._zoom_factor = factor
        self.scale(scale_change, scale_change)
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom_factor * self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom_factor / self.ZOOM_STEP)

    def zoom_actual(self) -> None:
        """Reset zoom to 100% (1:1 pixel scale)."""
        scale_change = 1.0 / self._zoom_factor
        self._zoom_factor = 1.0
        self.scale(scale_change, scale_change)
        self.zoom_changed.emit(1.0)

    def zoom_fit(self) -> None:
        """Fit entire image neatly into current viewport window."""
        if not self.document.has_image:
            return

        vw = max(10, self.viewport().width() - 32)
        vh = max(10, self.viewport().height() - 32)
        iw = self.document.width
        ih = self.document.height

        scale = min(vw / iw, vh / ih)
        # Apply transformation
        self.resetTransform()
        self._zoom_factor = scale
        self.scale(scale, scale)
        self.centerOn(iw / 2.0, ih / 2.0)
        self.zoom_changed.emit(self._zoom_factor)

    # Event Handling & Tool Dispatching
    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = self.ZOOM_STEP if delta > 0 else (1.0 / self.ZOOM_STEP)
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, self._zoom_factor * factor))
        actual_change = new_zoom / self._zoom_factor
        self._zoom_factor = new_zoom
        self.scale(actual_change, actual_change)
        self.zoom_changed.emit(self._zoom_factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        scene_pos = self.mapToScene(event.pos())

        # Middle click pans view
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and self._is_space_pressed):
            self.default_tool.mouse_press(event, scene_pos, self)
            return

        if self.active_tool and self.active_tool.mouse_press(event, scene_pos, self):
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        scene_pos = self.mapToScene(event.pos())

        # Pixel inspection
        if self.document.has_image:
            x, y = int(scene_pos.x()), int(scene_pos.y())
            if 0 <= x < self.document.width and 0 <= y < self.document.height:
                comp = self.document.get_composite()
                if comp:
                    try:
                        px = comp.getpixel((x, y))
                        if isinstance(px, (tuple, list)):
                            r = px[0]
                            g = px[1] if len(px) > 1 else r
                            b = px[2] if len(px) > 2 else r
                            a = px[3] if len(px) > 3 else 255
                            self.pixel_inspected.emit(x, y, r, g, b, a)
                    except Exception:
                        pass

        if self.active_tool and self.active_tool.mouse_move(event, scene_pos, self):
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        scene_pos = self.mapToScene(event.pos())
        if self.active_tool and self.active_tool.mouse_release(event, scene_pos, self):
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Space and not self._is_space_pressed and not event.isAutoRepeat():
            self._is_space_pressed = True
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return

        if self.active_tool and self.active_tool.key_press(event, self):
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._is_space_pressed = False
            if self.active_tool:
                self.setCursor(self.active_tool.cursor_shape)
            event.accept()
            return

        super().keyReleaseEvent(event)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """Let active tool render custom overlays (e.g. crop lines/handles) in scene coordinates."""
        super().drawForeground(painter, rect)
        if self.active_tool:
            self.active_tool.paint_overlay(painter, self)
