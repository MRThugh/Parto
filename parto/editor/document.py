# parto/editor/document.py
"""
Parto v0.3.0 - Image Document Model with Layer and History Management
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image
from PySide6.QtCore import QObject, Signal

from ..image.layers import Layer, compose_layers
from ..image.transforms import (
    rotate_90,
    rotate_180,
    flip_horizontal,
    flip_vertical,
    resize_image,
    crop_image,
)
from ..image.processing import apply_color_adjustments, remove_background
from ..image.filters import apply_filter
from ..image.export import save_image_file
from ..history.manager import HistoryManager
from ..history.commands import SnapshotCommand


class Document(QObject):
    """
    Central document state representing multi-layer image data, canvas dimensions,
    active layer selection, file persistence, and undo/redo operations.
    """
    document_changed = Signal()
    layer_selection_changed = Signal(int)
    modified_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._layers: List[Layer] = []
        self._active_layer_index: int = 0
        self._width: int = 0
        self._height: int = 0
        self._filepath: Optional[str] = None
        self._is_modified: bool = False
        self._cached_composite: Optional[Image.Image] = None
        self.history = HistoryManager(max_history=30, parent=self)
        self.history.history_changed.connect(self._on_history_changed)

    # Properties
    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def filepath(self) -> Optional[str]:
        return self._filepath

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    @property
    def layers(self) -> List[Layer]:
        return self._layers

    @property
    def active_layer_index(self) -> int:
        return self._active_layer_index

    @property
    def active_layer(self) -> Optional[Layer]:
        if 0 <= self._active_layer_index < len(self._layers):
            return self._layers[self._active_layer_index]
        return None

    @property
    def has_image(self) -> bool:
        return len(self._layers) > 0 and self._width > 0 and self._height > 0

    def set_modified(self, val: bool):
        if self._is_modified != val:
            self._is_modified = val
            self.modified_changed.emit(val)

    def _on_history_changed(self):
        self.document_changed.emit()

    def invalidate_composite(self):
        self._cached_composite = None
        self.document_changed.emit()

    def get_composite(self) -> Optional[Image.Image]:
        """Returns the composite rendering of all visible layers."""
        if not self.has_image:
            return None
        if self._cached_composite is None:
            self._cached_composite = compose_layers(self._layers, (self._width, self._height))
        return self._cached_composite

    # Document Lifetime
    def new_document(
        self,
        width: int = 1920,
        height: int = 1080,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:
        """Create a fresh blank document."""
        self._width = max(1, width)
        self._height = max(1, height)
        self._filepath = None
        base_img = Image.new("RGBA", (self._width, self._height), fill_color)
        bg_layer = Layer(name="Background", image=base_img)
        self._layers = [bg_layer]
        self._active_layer_index = 0
        self.history.clear()
        self.set_modified(False)
        self.invalidate_composite()

    def load_file(self, filepath: str) -> bool:
        """Load image file from disk into a fresh document state."""
        try:
            # pillow-heif registration handles heic if available
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass

            img = Image.open(filepath)
            # Ensure loaded fully into memory
            img.load()

            self._width, self._height = img.size
            self._filepath = os.path.abspath(filepath)
            bg_layer = Layer(name="Background", image=img)
            self._layers = [bg_layer]
            self._active_layer_index = 0
            self.history.clear()
            self.set_modified(False)
            self.invalidate_composite()
            return True
        except Exception as e:
            print(f"[Parto Document Error] Failed to load {filepath}: {e}")
            return False

    def save_file(
        self,
        filepath: Optional[str] = None,
        quality: int = 95,
        optimize: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Save flattened document to disk."""
        target_path = filepath or self._filepath
        if not target_path:
            return False, "No filepath specified"

        comp = self.get_composite()
        if comp is None:
            return False, "No active image to save"

        success, err = save_image_file(comp, target_path, quality=quality, optimize=optimize)
        if success:
            self._filepath = os.path.abspath(target_path)
            self.set_modified(False)
        return success, err

    # Snapshot & History Management
    def _create_snapshot(self) -> Dict[str, Any]:
        """Capture deep clone of current state for undo/redo."""
        return {
            "width": self._width,
            "height": self._height,
            "active_layer_index": self._active_layer_index,
            "layers": [lay.clone() for lay in self._layers],
        }

    def _restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot."""
        self._width = snapshot["width"]
        self._height = snapshot["height"]
        self._active_layer_index = min(snapshot["active_layer_index"], len(snapshot["layers"]) - 1)
        self._layers = [lay.clone() for lay in snapshot["layers"]]
        self.set_modified(True)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)

    def _record_operation(self, name: str, before_snap: Dict[str, Any]):
        after_snap = self._create_snapshot()
        cmd = SnapshotCommand(
            name=name,
            target_object=self,
            restore_fn=self._restore_snapshot,
            before_state=before_snap,
            after_state=after_snap,
        )
        self.history.push(cmd)
        self.set_modified(True)

    # Layer Management
    def set_active_layer_index(self, index: int) -> None:
        if 0 <= index < len(self._layers):
            self._active_layer_index = index
            self.layer_selection_changed.emit(index)

    def add_layer(
        self,
        name: Optional[str] = None,
        image: Optional[Image.Image] = None,
    ) -> Layer:
        """Add new layer above current active layer."""
        snap = self._create_snapshot()
        idx = self._active_layer_index + 1
        num = len(self._layers) + 1
        layer_name = name or f"Layer {num}"
        img = image if image is not None else Image.new("RGBA", (self._width, self._height), (0, 0, 0, 0))
        new_lay = Layer(name=layer_name, image=img)
        self._layers.insert(idx, new_lay)
        self._active_layer_index = idx
        self._record_operation(f"Add {layer_name}", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return new_lay

    def duplicate_active_layer(self) -> Optional[Layer]:
        """Duplicate current active layer."""
        active = self.active_layer
        if active is None:
            return None
        snap = self._create_snapshot()
        idx = self._active_layer_index + 1
        new_lay = active.clone()
        self._layers.insert(idx, new_lay)
        self._active_layer_index = idx
        self._record_operation(f"Duplicate {active.name}", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return new_lay

    def remove_active_layer(self) -> bool:
        """Remove active layer (must keep at least 1 layer)."""
        if len(self._layers) <= 1:
            return False
        snap = self._create_snapshot()
        removed = self._layers.pop(self._active_layer_index)
        self._active_layer_index = max(0, min(self._active_layer_index, len(self._layers) - 1))
        self._record_operation(f"Delete {removed.name}", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return True

    def move_layer_up(self) -> bool:
        if self._active_layer_index >= len(self._layers) - 1:
            return False
        snap = self._create_snapshot()
        i = self._active_layer_index
        self._layers[i], self._layers[i + 1] = self._layers[i + 1], self._layers[i]
        self._active_layer_index = i + 1
        self._record_operation("Move Layer Up", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return True

    def move_layer_down(self) -> bool:
        if self._active_layer_index <= 0:
            return False
        snap = self._create_snapshot()
        i = self._active_layer_index
        self._layers[i], self._layers[i - 1] = self._layers[i - 1], self._layers[i]
        self._active_layer_index = i - 1
        self._record_operation("Move Layer Down", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return True

    def merge_down(self) -> bool:
        """Merge active layer with the layer directly beneath it."""
        if self._active_layer_index <= 0 or len(self._layers) < 2:
            return False
        snap = self._create_snapshot()
        top_idx = self._active_layer_index
        bottom_idx = top_idx - 1

        top_layer = self._layers[top_idx]
        bottom_layer = self._layers[bottom_idx]

        # Composite top onto bottom
        merged = compose_layers([bottom_layer, top_layer], (self._width, self._height))
        bottom_layer.image = merged
        self._layers.pop(top_idx)
        self._active_layer_index = bottom_idx

        self._record_operation("Merge Down", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self._active_layer_index)
        return True

    def set_layer_visible(self, index: int, visible: bool) -> None:
        if 0 <= index < len(self._layers):
            snap = self._create_snapshot()
            self._layers[index].visible = visible
            self._record_operation("Toggle Layer Visibility", snap)
            self.invalidate_composite()

    def set_layer_opacity(self, index: int, opacity: float, record_history: bool = True) -> None:
        if 0 <= index < len(self._layers):
            if record_history:
                snap = self._create_snapshot()
                self._layers[index].set_opacity(opacity)
                self._record_operation("Change Layer Opacity", snap)
            else:
                self._layers[index].set_opacity(opacity)
            self.invalidate_composite()

    # Transformations (Operate on active layer or entire document)
    def rotate_document(self, clockwise: bool = True) -> None:
        """Rotate entire document 90 degrees."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        self._width, self._height = self._height, self._width
        for lay in self._layers:
            lay.image = rotate_90(lay.image, clockwise=clockwise)
        desc = "Rotate Right (90° CW)" if clockwise else "Rotate Left (90° CCW)"
        self._record_operation(desc, snap)
        self.invalidate_composite()

    def rotate_180_document(self) -> None:
        """Rotate entire document 180 degrees."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self._layers:
            lay.image = rotate_180(lay.image)
        self._record_operation("Rotate 180°", snap)
        self.invalidate_composite()

    def flip_horizontal_document(self) -> None:
        """Flip document horizontally."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self._layers:
            lay.image = flip_horizontal(lay.image)
        self._record_operation("Flip Horizontal", snap)
        self.invalidate_composite()

    def flip_vertical_document(self) -> None:
        """Flip document vertically."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self._layers:
            lay.image = flip_vertical(lay.image)
        self._record_operation("Flip Vertical", snap)
        self.invalidate_composite()

    def resize_document(self, new_width: int, new_height: int) -> None:
        """Resize entire document and all layers."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        nw, nh = max(1, int(new_width)), max(1, int(new_height))
        self._width = nw
        self._height = nh
        for lay in self._layers:
            lay.image = resize_image(lay.image, nw, nh)
        self._record_operation(f"Resize ({nw} × {nh})", snap)
        self.invalidate_composite()

    def crop_document(self, rect: Tuple[int, int, int, int]) -> None:
        """Crop entire document to rectangle (left, top, right, bottom)."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        left, top, right, bottom = rect
        new_w = max(1, right - left)
        new_h = max(1, bottom - top)

        self._width = new_w
        self._height = new_h

        for lay in self._layers:
            lay.image = crop_image(lay.image, rect)
            lay.offset_x = max(0, lay.offset_x - left)
            lay.offset_y = max(0, lay.offset_y - top)

        self._record_operation(f"Crop ({new_w} × {new_h})", snap)
        self.invalidate_composite()

    def apply_color_adjustments(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> None:
        """Apply color adjustments to active layer."""
        active = self.active_layer
        if active is None:
            return
        snap = self._create_snapshot()
        active.image = apply_color_adjustments(
            active.image,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )
        self._record_operation("Color Adjustments", snap)
        self.invalidate_composite()

    def get_adjusted_preview(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Optional[Image.Image]:
        """Return preview composite of active layer adjusted without modifying document state."""
        if not self.has_image or not self.active_layer:
            return None
        preview_layers = []
        for i, lay in enumerate(self._layers):
            if i == self._active_layer_index and lay.visible:
                adj_img = apply_color_adjustments(
                    lay.image,
                    brightness=brightness,
                    contrast=contrast,
                    saturation=saturation,
                    sharpness=sharpness,
                )
                preview_lay = lay.clone()
                preview_lay.image = adj_img
                preview_layers.append(preview_lay)
            else:
                preview_layers.append(lay)
        return compose_layers(preview_layers, (self._width, self._height))

    def apply_filter(self, filter_name: str) -> None:
        """Apply photographic filter to active layer."""
        active = self.active_layer
        if active is None:
            return
        snap = self._create_snapshot()
        active.image = apply_filter(active.image, filter_name)
        self._record_operation(f"Filter ({filter_name.title()})", snap)
        self.invalidate_composite()

    def remove_background(self, tolerance: int = 28, feather_radius: int = 2) -> None:
        """
        Remove background from the active layer with tolerance and edge feathering.
        Records history for undo/redo.
        """
        active = self.active_layer
        if active is None or not self.has_image:
            return
        snap = self._create_snapshot()
        active.image = remove_background(
            active.image,
            tolerance=tolerance,
            feather_radius=feather_radius,
        )
        self._record_operation("Remove Background", snap)
        self.invalidate_composite()
        self.set_modified(True)

    def apply_remove_background(self, tolerance: int = 28, feather_radius: int = 2) -> None:
        """Consistent alias for remove_background."""
        self.remove_background(tolerance=tolerance, feather_radius=feather_radius)

