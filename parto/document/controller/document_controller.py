# parto/document/controller/document_controller.py
"""
Parto Document Subsystem — Document Controller
Author: Ali Kamrani (MRThugh)

Coordinates mutations, operations, transactions, and signal propagation
across the Document subsystem.
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, Callable, List
from PIL import Image

from ..models.document_state import DocumentState
from ..engine.document_engine import DocumentEngine
from ..history.transaction import TransactionCoordinator
from ..adapters.storage_adapter import DocumentStorageAdapter
from ...image.layers import Layer
from ...history.manager import HistoryManager


class DocumentController:
    """
    Coordinates state mutations, domain operations, history transactions,
    and storage for a DocumentState.
    """

    def __init__(
        self,
        state: DocumentState,
        engine: DocumentEngine,
        history: HistoryManager,
        storage: DocumentStorageAdapter,
        transactions: TransactionCoordinator,
        on_state_changed: Optional[Callable[[], None]] = None,
        on_selection_changed: Optional[Callable[[int], None]] = None,
    ):
        self.state = state
        self.engine = engine
        self.history = history
        self.storage = storage
        self.transactions = transactions
        self._on_state_changed = on_state_changed
        self._on_selection_changed = on_selection_changed

    def notify_state_changed(self) -> None:
        self.engine.compositing.invalidate()
        if self._on_state_changed:
            self._on_state_changed()

    def notify_selection_changed(self, index: int) -> None:
        if self._on_selection_changed:
            self._on_selection_changed(index)

    # --- Lifecycle ---
    def create_new(
        self,
        width: int = 1920,
        height: int = 1080,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        initial_image: Optional[Image.Image] = None,
    ) -> None:
        self.state.reset(
            width=width,
            height=height,
            fill_color=fill_color,
            initial_image=initial_image,
        )
        self.history.clear()
        self.state.is_modified = False
        self.notify_state_changed()

    def load_file(self, filepath: str, raise_on_error: bool = False) -> bool:
        success, img, abspath, err = self.storage.load_file(filepath, raise_on_error=raise_on_error)
        if not success or img is None:
            return False

        w, h = img.size
        self.state.reset(width=w, height=h, initial_image=img, filepath=abspath)
        self.history.clear()
        self.state.is_modified = False
        self.notify_state_changed()
        return True

    def save_file(
        self,
        filepath: Optional[str] = None,
        quality: int = 95,
        optimize: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        target_path = filepath or self.state.filepath
        comp = self.engine.compositing.get_composite(
            self.state.layer_stack, self.state.width, self.state.height
        )
        success, err = self.storage.save_file(
            comp, target_path, quality=quality, optimize=optimize
        )
        if success and target_path:
            self.state.filepath = target_path
            self.state.is_modified = False
            self.history.set_clean()
        return success, err

    # --- History & Transactions ---
    def create_snapshot(self) -> Dict[str, Any]:
        return self.transactions.create_snapshot(self.state)

    def restore_snapshot(self, snapshot: Dict[str, Any], target_object: Any = None) -> None:
        self.transactions.restore_snapshot(self.state, snapshot)
        self.notify_state_changed()
        self.notify_selection_changed(self.state.active_layer_index)

    def record_operation(
        self,
        name: str,
        before_snap: Dict[str, Any],
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        recorded = self.transactions.record_operation(
            state=self.state,
            history=self.history,
            target_object=target_object,
            name=name,
            before_snap=before_snap,
            restore_callback=restore_callback,
        )
        if recorded:
            self.state.is_modified = True
            self.notify_state_changed()
        return recorded

    # --- Layer Operations ---
    def add_layer(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
        image_or_color: Optional[Any] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> Layer:
        before_snap = self.create_snapshot()
        idx = self.state.layer_stack.active_index + 1
        num = len(self.state.layer_stack) + 1
        layer_name = name or f"Layer {num}"

        if isinstance(image_or_color, Image.Image):
            img = image_or_color
        elif isinstance(image_or_color, (tuple, list)):
            img = Image.new("RGBA", (self.state.width, self.state.height), tuple(image_or_color))
        else:
            img = Image.new("RGBA", (self.state.width, self.state.height), (0, 0, 0, 0))

        new_lay = self.state.layer_stack.insert_layer(idx, image_or_layer=img, name=layer_name, **kwargs)
        self.record_operation(f"Add {layer_name}", before_snap, target_object, restore_callback)
        self.notify_selection_changed(self.state.layer_stack.active_index)
        return new_lay

    def duplicate_active_layer(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> Optional[Layer]:
        if not self.state.has_image or self.state.active_layer_index < 0:
            return None
        before_snap = self.create_snapshot()
        dup = self.state.layer_stack.duplicate_layer(self.state.active_layer_index)
        if dup:
            self.record_operation(f"Duplicate {dup.name}", before_snap, target_object, restore_callback)
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return dup
        return None

    def remove_active_layer(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        if len(self.state.layer_stack) <= 1:
            return False
        before_snap = self.create_snapshot()
        removed = self.state.layer_stack.remove_layer(self.state.active_layer_index)
        if removed:
            self.record_operation(f"Delete {removed.name}", before_snap, target_object, restore_callback)
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def remove_layer_by_id(
        self,
        layer_id: str,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
        push_history: bool = True,
    ) -> bool:
        for i, lay in enumerate(self.state.layer_stack):
            if lay.id == layer_id:
                if push_history:
                    before_snap = self.create_snapshot()
                    removed = self.state.layer_stack.remove_layer(i)
                    if removed:
                        self.record_operation(f"Delete {removed.name}", before_snap, target_object, restore_callback)
                        self.notify_selection_changed(self.state.layer_stack.active_index)
                        return True
                else:
                    self.state.layer_stack.remove_layer(i)
                    self.notify_state_changed()
                    self.notify_selection_changed(self.state.layer_stack.active_index)
                    return True
        return False

    def move_layer_up(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        if self.state.active_layer_index >= len(self.state.layer_stack) - 1:
            return False
        before_snap = self.create_snapshot()
        if self.state.layer_stack.move_layer_up(self.state.active_layer_index):
            self.record_operation("Move Layer Up", before_snap, target_object, restore_callback)
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def move_layer_down(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        if self.state.active_layer_index <= 0:
            return False
        before_snap = self.create_snapshot()
        if self.state.layer_stack.move_layer_down(self.state.active_layer_index):
            self.record_operation("Move Layer Down", before_snap, target_object, restore_callback)
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def merge_down(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        if self.state.active_layer_index <= 0 or len(self.state.layer_stack) < 2:
            return False
        before_snap = self.create_snapshot()
        merged = self.state.layer_stack.merge_down(self.state.active_layer_index)
        if merged:
            self.record_operation("Merge Down", before_snap, target_object, restore_callback)
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def set_layer_visible(
        self,
        index: int,
        visible: bool,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if 0 <= index < len(self.state.layer_stack):
            if self.state.layer_stack[index].visible == visible:
                return
            before_snap = self.create_snapshot()
            self.state.layer_stack[index].visible = visible
            self.record_operation("Toggle Layer Visibility", before_snap, target_object, restore_callback)
            self.notify_state_changed()

    def set_layer_opacity(
        self,
        index: int,
        opacity: float,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
        record_history: bool = True,
    ) -> None:
        if 0 <= index < len(self.state.layer_stack):
            clamped = max(0.0, min(1.0, float(opacity)))
            if abs(self.state.layer_stack[index].opacity - clamped) < 1e-4:
                return
            if record_history:
                before_snap = self.create_snapshot()
                self.state.layer_stack[index].set_opacity(clamped)
                self.record_operation("Change Layer Opacity", before_snap, target_object, restore_callback)
            else:
                self.state.layer_stack[index].set_opacity(clamped)
            self.notify_state_changed()

    # --- Geometric Transformations ---
    def rotate_document(
        self,
        clockwise: bool,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        new_w, new_h = self.engine.transforms.rotate_90(
            self.state.layer_stack, self.state.width, self.state.height, clockwise=clockwise
        )
        self.state.width = new_w
        self.state.height = new_h
        desc = "Rotate Right (90° CW)" if clockwise else "Rotate Left (90° CCW)"
        self.record_operation(desc, before_snap, target_object, restore_callback)
        self.notify_state_changed()

    def rotate_180_document(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        self.engine.transforms.rotate_180(
            self.state.layer_stack, self.state.width, self.state.height
        )
        self.record_operation("Rotate 180°", before_snap, target_object, restore_callback)
        self.notify_state_changed()

    def flip_horizontal_document(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        self.engine.transforms.flip_horizontal(self.state.layer_stack, self.state.width)
        self.record_operation("Flip Horizontal", before_snap, target_object, restore_callback)
        self.notify_state_changed()

    def flip_vertical_document(
        self,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        self.engine.transforms.flip_vertical(self.state.layer_stack, self.state.height)
        self.record_operation("Flip Vertical", before_snap, target_object, restore_callback)
        self.notify_state_changed()

    def resize_document(
        self,
        new_width: int,
        new_height: int,
        resample: int,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        nw, nh = max(1, int(new_width)), max(1, int(new_height))
        if nw == self.state.width and nh == self.state.height:
            return
        before_snap = self.create_snapshot()
        new_w, new_h = self.engine.transforms.resize(
            self.state.layer_stack, (self.state.width, self.state.height), (nw, nh), resample=resample
        )
        self.state.width = new_w
        self.state.height = new_h
        self.record_operation(f"Resize ({nw} × {nh})", before_snap, target_object, restore_callback)
        self.notify_state_changed()

    def crop_document(
        self,
        rect: Tuple[int, int, int, int],
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        if not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        crop_res = self.engine.transforms.crop(
            self.state.layer_stack, (self.state.width, self.state.height), rect
        )
        if crop_res is None:
            return
        new_w, new_h = crop_res
        self.state.width = new_w
        self.state.height = new_h
        self.record_operation(f"Crop ({new_w} × {new_h})", before_snap, target_object, restore_callback)
        self.notify_state_changed()

    # --- Adjustments & Filters ---
    def apply_color_adjustments(
        self,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        if self.engine.apply_color_adjustments(
            active,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        ):
            self.record_operation("Color Adjustments", before_snap, target_object, restore_callback)
            self.notify_state_changed()

    def apply_filter(
        self,
        filter_name: str,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        if self.engine.apply_filter(active, filter_name):
            self.record_operation(f"Filter ({filter_name.title()})", before_snap, target_object, restore_callback)
            self.notify_state_changed()

    def remove_background(
        self,
        tolerance: int,
        feather_radius: int,
        target_object: Any,
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        before_snap = self.create_snapshot()
        if self.engine.remove_background(active, tolerance=tolerance, feather_radius=feather_radius):
            self.record_operation("Remove Background", before_snap, target_object, restore_callback)
            self.notify_state_changed()
