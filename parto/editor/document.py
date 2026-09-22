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

from ..image.layers import Layer, LayerStack, compose_layers
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
    Authoritatively backed by LayerStack.
    """
    document_changed = Signal()
    layer_selection_changed = Signal(int)
    modified_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None, max_history: int = 30):
        super().__init__(parent)
        self._width: int = 0
        self._height: int = 0
        self.layer_stack: LayerStack = LayerStack(1, 1)
        self._filepath: Optional[str] = None
        self._is_modified: bool = False
        self._cached_composite: Optional[Image.Image] = None
        self.history = HistoryManager(max_history=max_history, parent=self)
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
    def modified(self) -> bool:
        return self._is_modified

    @modified.setter
    def modified(self, val: bool) -> None:
        self.set_modified(val)

    @property
    def layers(self) -> List[Layer]:
        return self.layer_stack.layers

    @property
    def _layers(self) -> List[Layer]:
        """Backward-compatibility alias pointing directly to authoritative LayerStack."""
        return self.layer_stack.layers

    @_layers.setter
    def _layers(self, val: List[Layer]):
        self.layer_stack._layers = val

    @property
    def active_layer_index(self) -> int:
        return self.layer_stack.active_index

    @property
    def _active_layer_index(self) -> int:
        """Backward-compatibility alias pointing directly to authoritative LayerStack."""
        return self.layer_stack.active_index

    @_active_layer_index.setter
    def _active_layer_index(self, val: int):
        self.layer_stack.set_active_index(val)

    @property
    def active_layer(self) -> Optional[Layer]:
        return self.layer_stack.active_layer

    @property
    def has_image(self) -> bool:
        return len(self.layer_stack) > 0 and self._width > 0 and self._height > 0

    def set_modified(self, val: bool):
        if not val:
            self.history.set_clean()
        if self._is_modified != val:
            self._is_modified = val
            self.modified_changed.emit(val)

    def _on_history_changed(self):
        new_modified = not self.history.is_clean
        if self._is_modified != new_modified:
            self._is_modified = new_modified
            self.modified_changed.emit(new_modified)
        self.document_changed.emit()

    def invalidate_composite(self):
        self._cached_composite = None
        self.document_changed.emit()

    def get_composite(self) -> Optional[Image.Image]:
        """Returns the composite rendering of all visible layers."""
        if not self.has_image:
            return None
        if self._cached_composite is None:
            self._cached_composite = self.layer_stack.composite()
        return self._cached_composite

    # Document Lifetime
    def new_document(
        self,
        width: int = 1920,
        height: int = 1080,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        initial_image: Optional[Image.Image] = None,
    ) -> None:
        """Create a fresh blank document or initialize with a starting image."""
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self._filepath = None
        self.layer_stack = LayerStack(self._width, self._height)
        if initial_image is not None:
            base_img = initial_image.copy()
            if base_img.mode != "RGBA":
                base_img = base_img.convert("RGBA")
        else:
            base_img = Image.new("RGBA", (self._width, self._height), fill_color)
        self.layer_stack.add_layer(base_img, name="Background")
        self.history.clear()
        self.set_modified(False)
        self.invalidate_composite()

    def load_file(self, filepath: str, raise_on_error: bool = False) -> bool:
        """Load image file from disk into a fresh document state."""
        try:
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass

            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Image file does not exist: {filepath}")

            img = Image.open(filepath)
            img.load()

            self._width, self._height = img.size
            self._filepath = os.path.abspath(filepath)
            self.layer_stack = LayerStack(self._width, self._height)
            self.layer_stack.add_layer(img, name="Background")
            self.history.clear()
            self.set_modified(False)
            self.invalidate_composite()
            return True
        except Exception as e:
            if raise_on_error:
                raise
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
    def create_snapshot(self) -> Dict[str, Any]:
        """Capture deep clone of current state for undo/redo (public interface)."""
        return self._create_snapshot()

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot (public interface)."""
        self._restore_snapshot(snapshot)

    def record_operation(self, name: str, before_snap: Dict[str, Any]) -> None:
        """Record an operation and its pre-state to history (public interface)."""
        self._record_operation(name, before_snap)

    def _create_snapshot(self) -> Dict[str, Any]:
        """Capture deep clone of current state for undo/redo."""
        return {
            "width": self._width,
            "height": self._height,
            "layer_stack": self.layer_stack.clone(),
            "active_layer_index": self.layer_stack.active_index,
        }

    def _restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot."""
        self._width = snapshot["width"]
        self._height = snapshot["height"]
        if "layer_stack" in snapshot and isinstance(snapshot["layer_stack"], LayerStack):
            target_stack = snapshot["layer_stack"].clone()
            existing_by_id = {lay.id: lay for lay in self.layer_stack}
            new_layers = []
            for lay in target_stack:
                if lay.id in existing_by_id:
                    orig = existing_by_id[lay.id]
                    orig.name = lay.name
                    orig.image = lay.image.copy() if lay.image is not None else None
                    orig.visible = lay.visible
                    orig.opacity = lay.opacity
                    orig.blend_mode = lay.blend_mode
                    orig.offset_x = lay.offset_x
                    orig.offset_y = lay.offset_y
                    new_layers.append(orig)
                else:
                    new_layers.append(lay)
            self.layer_stack._layers = new_layers
            self.layer_stack.width = self._width
            self.layer_stack.height = self._height
            self.layer_stack.set_active_index(snapshot.get("active_layer_index", target_stack.active_index))
        elif "layers" in snapshot:
            self.layer_stack = LayerStack(self._width, self._height)
            self.layer_stack._layers = [lay.clone() for lay in snapshot["layers"]]
            self.layer_stack.set_active_index(snapshot.get("active_layer_index", 0))
        self.invalidate_composite()
        self.layer_selection_changed.emit(self.layer_stack.active_index)

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

    def undo(self) -> bool:
        """Undo last operation."""
        return self.history.undo()

    def redo(self) -> bool:
        """Redo previously undone operation."""
        return self.history.redo()

    # Layer Management
    def set_active_layer_index(self, index: int) -> None:
        if self.layer_stack.set_active_index(index):
            self.layer_selection_changed.emit(index)

    def add_layer(
        self,
        name: Optional[str] = None,
        image: Optional[Any] = None,
    ) -> Layer:
        """Add new layer above current active layer."""
        snap = self._create_snapshot()
        idx = self.layer_stack.active_index + 1
        num = len(self.layer_stack) + 1
        layer_name = name or f"Layer {num}"
        if isinstance(image, (tuple, list)):
            img = Image.new("RGBA", (self._width, self._height), tuple(image))
        elif isinstance(image, Image.Image):
            img = image
        else:
            img = Image.new("RGBA", (self._width, self._height), (0, 0, 0, 0))
        new_lay = self.layer_stack.insert_layer(idx, image_or_layer=img, name=layer_name)
        self._record_operation(f"Add {layer_name}", snap)
        self.invalidate_composite()
        self.layer_selection_changed.emit(self.layer_stack.active_index)
        return new_lay

    def duplicate_active_layer(self) -> Optional[Layer]:
        """Duplicate current active layer."""
        if not self.has_image or self.layer_stack.active_index < 0:
            return None
        snap = self._create_snapshot()
        dup = self.layer_stack.duplicate_layer(self.layer_stack.active_index)
        if dup:
            self._record_operation(f"Duplicate {dup.name}", snap)
            self.invalidate_composite()
            self.layer_selection_changed.emit(self.layer_stack.active_index)
            return dup
        return None

    def remove_active_layer(self) -> bool:
        """Remove active layer (must keep at least 1 layer)."""
        if len(self.layer_stack) <= 1:
            return False
        snap = self._create_snapshot()
        removed = self.layer_stack.remove_layer(self.layer_stack.active_index)
        if removed:
            self._record_operation(f"Delete {removed.name}", snap)
            self.invalidate_composite()
            self.layer_selection_changed.emit(self.layer_stack.active_index)
            return True
        return False

    def move_layer_up(self) -> bool:
        if self.layer_stack.active_index >= len(self.layer_stack) - 1:
            return False
        snap = self._create_snapshot()
        if self.layer_stack.move_layer_up(self.layer_stack.active_index):
            self._record_operation("Move Layer Up", snap)
            self.invalidate_composite()
            self.layer_selection_changed.emit(self.layer_stack.active_index)
            return True
        return False

    def move_layer_down(self) -> bool:
        if self.layer_stack.active_index <= 0:
            return False
        snap = self._create_snapshot()
        if self.layer_stack.move_layer_down(self.layer_stack.active_index):
            self._record_operation("Move Layer Down", snap)
            self.invalidate_composite()
            self.layer_selection_changed.emit(self.layer_stack.active_index)
            return True
        return False

    def merge_down(self) -> bool:
        """Merge active layer with the layer directly beneath it."""
        if self.layer_stack.active_index <= 0 or len(self.layer_stack) < 2:
            return False
        snap = self._create_snapshot()
        merged = self.layer_stack.merge_down(self.layer_stack.active_index)
        if merged:
            self._record_operation("Merge Down", snap)
            self.invalidate_composite()
            self.layer_selection_changed.emit(self.layer_stack.active_index)
            return True
        return False

    def set_layer_visible(self, index: int, visible: bool) -> None:
        if 0 <= index < len(self.layer_stack):
            if self.layer_stack[index].visible == visible:
                return
            snap = self._create_snapshot()
            self.layer_stack[index].visible = visible
            self._record_operation("Toggle Layer Visibility", snap)
            self.invalidate_composite()

    def set_layer_opacity(self, index: int, opacity: float, record_history: bool = True) -> None:
        if 0 <= index < len(self.layer_stack):
            clamped = max(0.0, min(1.0, float(opacity)))
            if abs(self.layer_stack[index].opacity - clamped) < 1e-4:
                return
            if record_history:
                snap = self._create_snapshot()
                self.layer_stack[index].set_opacity(clamped)
                self._record_operation("Change Layer Opacity", snap)
            else:
                self.layer_stack[index].set_opacity(clamped)
            self.invalidate_composite()

    # Transformations (Operate on all layers to maintain document size)
    def rotate_document(self, clockwise: bool = True) -> None:
        """Rotate entire document 90 degrees."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        self._width, self._height = self._height, self._width
        self.layer_stack.width = self._width
        self.layer_stack.height = self._height
        for lay in self.layer_stack:
            lay.image = rotate_90(lay.image, clockwise=clockwise)
        desc = "Rotate Right (90° CW)" if clockwise else "Rotate Left (90° CCW)"
        self._record_operation(desc, snap)
        self.invalidate_composite()

    def rotate_180_document(self) -> None:
        """Rotate entire document 180 degrees."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self.layer_stack:
            lay.image = rotate_180(lay.image)
        self._record_operation("Rotate 180°", snap)
        self.invalidate_composite()

    def flip_horizontal_document(self) -> None:
        """Flip document horizontally."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self.layer_stack:
            lay.image = flip_horizontal(lay.image)
        self._record_operation("Flip Horizontal", snap)
        self.invalidate_composite()

    def flip_vertical_document(self) -> None:
        """Flip document vertically."""
        if not self.has_image:
            return
        snap = self._create_snapshot()
        for lay in self.layer_stack:
            lay.image = flip_vertical(lay.image)
        self._record_operation("Flip Vertical", snap)
        self.invalidate_composite()

    def resize_document(self, new_width: int, new_height: int, resample: int = Image.Resampling.LANCZOS) -> None:
        """Resize entire document and all layers."""
        if not self.has_image:
            return
        nw, nh = max(1, int(new_width)), max(1, int(new_height))
        if nw == self._width and nh == self._height:
            return
        snap = self._create_snapshot()
        self._width = nw
        self._height = nh
        self.layer_stack.width = nw
        self.layer_stack.height = nh
        for lay in self.layer_stack:
            lay.image = resize_image(lay.image, nw, nh, resample=resample)
        self._record_operation(f"Resize ({nw} × {nh})", snap)
        self.invalidate_composite()

    def crop_document(self, rect: Tuple[int, int, int, int]) -> None:
        """Crop entire document to rectangle (left, top, right, bottom)."""
        if not self.has_image:
            return
        left, top, right, bottom = rect
        x1 = max(0, min(int(left), self._width))
        y1 = max(0, min(int(top), self._height))
        x2 = max(0, min(int(right), self._width))
        y2 = max(0, min(int(bottom), self._height))

        if x2 <= x1 or y2 <= y1:
            return  # Invalid crop rectangle: do nothing, no history

        new_w = x2 - x1
        new_h = y2 - y1

        if x1 == 0 and y1 == 0 and new_w == self._width and new_h == self._height:
            return  # Full canvas crop: no-op, no history

        snap = self._create_snapshot()
        self._width = new_w
        self._height = new_h
        self.layer_stack.width = new_w
        self.layer_stack.height = new_h

        clamped_rect = (x1, y1, x2, y2)
        for lay in self.layer_stack:
            lay.image = crop_image(lay.image, clamped_rect)
            lay.offset_x = max(0, lay.offset_x - x1)
            lay.offset_y = max(0, lay.offset_y - y1)

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
        if active is None or not self.has_image:
            return
        if (
            abs(brightness - 1.0) < 1e-4
            and abs(contrast - 1.0) < 1e-4
            and abs(saturation - 1.0) < 1e-4
            and abs(sharpness - 1.0) < 1e-4
        ):
            return  # 0% adjustment: no-op, no history
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
        for i, lay in enumerate(self.layer_stack):
            if i == self.layer_stack.active_index and lay.visible:
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
        if active is None or not self.has_image:
            return
        from ..image.filters import FILTER_MAP
        if filter_name.lower() not in FILTER_MAP:
            return
        snap = self._create_snapshot()
        active.image = apply_filter(active.image, filter_name)
        self._record_operation(f"Filter ({filter_name.title()})", snap)
        self.invalidate_composite()

    def get_filter_preview(self, filter_name: str) -> Optional[Image.Image]:
        """Return preview composite with filter applied to active layer."""
        if not self.has_image or not self.active_layer:
            return None
        preview_layers = []
        for i, lay in enumerate(self.layer_stack):
            if i == self.layer_stack.active_index and lay.visible:
                filt_img = apply_filter(lay.image, filter_name)
                preview_lay = lay.clone()
                preview_lay.image = filt_img
                preview_layers.append(preview_lay)
            else:
                preview_layers.append(lay)
        return compose_layers(preview_layers, (self._width, self._height))

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

