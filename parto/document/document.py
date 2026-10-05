# parto/document/document.py
"""
Parto Document Subsystem — Authoritative Document Domain Model & Facade
Author: Ali Kamrani (MRThugh)

Serves as the high-level domain boundary and facade for the Document subsystem.
Delegates state to DocumentState, operations to DocumentEngine, persistence
to DocumentStorageAdapter, history transactions to TransactionCoordinator, and
lifecycle mutations to DocumentController.
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image
from PySide6.QtCore import QObject, Signal

from .models.document_state import DocumentState
from .engine.document_engine import DocumentEngine
from .history.transaction import TransactionCoordinator, snapshots_equal
from .adapters.storage_adapter import DocumentStorageAdapter
from .controller.document_controller import DocumentController
from ..layers import Layer, LayerStack
from ..history.manager import HistoryManager


class Document(QObject):
    """
    Authoritative domain model and facade representing multi-layer image data,
    canvas dimensions, active layer selection, file persistence, and undo/redo operations.
    Backed by DocumentState and LayerStack.
    """
    document_changed = Signal()
    layer_selection_changed = Signal(int)
    modified_changed = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None, max_history: int = 30):
        super().__init__(parent)
        self._state = DocumentState(0, 0)
        self._engine = DocumentEngine()
        self._storage = DocumentStorageAdapter()
        self._transactions = TransactionCoordinator()
        self.history = HistoryManager(max_history=max_history, parent=self)
        self.history.history_changed.connect(self._on_history_changed)

        self._controller = DocumentController(
            state=self._state,
            engine=self._engine,
            history=self.history,
            storage=self._storage,
            transactions=self._transactions,
            on_state_changed=self._on_controller_state_changed,
            on_selection_changed=self._on_controller_selection_changed,
        )

    # --- Internal Signal Relays ---
    def _on_controller_state_changed(self) -> None:
        self.document_changed.emit()

    def _on_controller_selection_changed(self, index: int) -> None:
        self.layer_selection_changed.emit(index)

    def _on_history_changed(self) -> None:
        new_modified = not self.history.is_clean
        if self._state.is_modified != new_modified:
            self._state.is_modified = new_modified
            self.modified_changed.emit(new_modified)
        self.document_changed.emit()

    # --- Properties (Authoritative single-source delegation to _state) ---
    @property
    def width(self) -> int:
        return self._state.width

    @property
    def height(self) -> int:
        return self._state.height

    @property
    def dimensions(self) -> Tuple[int, int]:
        return self._state.dimensions

    @property
    def filepath(self) -> Optional[str]:
        return self._state.filepath

    @property
    def is_modified(self) -> bool:
        return self._state.is_modified

    @property
    def modified(self) -> bool:
        return self._state.is_modified

    @modified.setter
    def modified(self, val: bool) -> None:
        self.set_modified(val)

    @property
    def layer_stack(self) -> LayerStack:
        return self._state.layer_stack

    @layer_stack.setter
    def layer_stack(self, stack: LayerStack) -> None:
        self._state.layer_stack = stack

    @property
    def layers(self) -> List[Layer]:
        return self._state.layers

    @property
    def _layers(self) -> List[Layer]:
        """Backward-compatibility alias pointing directly to authoritative LayerStack."""
        return self._state.layers

    @_layers.setter
    def _layers(self, val: List[Layer]) -> None:
        self._state.layer_stack._layers = val

    @property
    def active_layer_index(self) -> int:
        return self._state.active_layer_index

    @property
    def _active_layer_index(self) -> int:
        """Backward-compatibility alias pointing directly to authoritative LayerStack."""
        return self._state.active_layer_index

    @_active_layer_index.setter
    def _active_layer_index(self, val: int) -> None:
        self.set_active_layer_index(val)

    @property
    def active_layer(self) -> Optional[Layer]:
        return self._state.active_layer

    @property
    def has_image(self) -> bool:
        return self._state.has_image

    # --- State Management & Invalidation ---
    def set_modified(self, val: bool) -> None:
        if not val:
            self.history.set_clean()
        if self._state.is_modified != val:
            self._state.is_modified = val
            self.modified_changed.emit(val)

    def invalidate_composite(self) -> None:
        self._engine.compositing.invalidate()
        self.document_changed.emit()

    def get_composite(self) -> Optional[Image.Image]:
        """Returns the composite rendering of all visible layers."""
        return self._engine.compositing.get_composite(
            self._state.layer_stack, self._state.width, self._state.height
        )

    # --- Document Lifetime ---
    def new_document(
        self,
        width: int = 1920,
        height: int = 1080,
        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        initial_image: Optional[Image.Image] = None,
    ) -> None:
        """Create a fresh blank document or initialize with a starting image."""
        self._controller.create_new(
            width=width,
            height=height,
            fill_color=fill_color,
            initial_image=initial_image,
        )
        self.set_modified(False)

    def load_file(self, filepath: str, raise_on_error: bool = False) -> bool:
        """
        Load image file from disk into a fresh document state.
        Uses safe file context handling and applies EXIF orientation normalization.
        """
        return self._controller.load_file(filepath, raise_on_error=raise_on_error)

    def save_file(
        self,
        filepath: Optional[str] = None,
        quality: int = 95,
        optimize: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Save flattened document to disk."""
        return self._controller.save_file(filepath=filepath, quality=quality, optimize=optimize)

    # --- Snapshot & History Management ---
    def create_snapshot(self) -> Dict[str, Any]:
        """Capture deep clone of current state for undo/redo (public interface)."""
        return self._controller.create_snapshot()

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore state from snapshot (public interface)."""
        self._controller.restore_snapshot(snapshot, target_object=self)

    def record_operation(self, name: str, before_snap: Dict[str, Any]) -> None:
        """Record an operation and its pre-state to history (public interface)."""
        self._controller.record_operation(
            name=name,
            before_snap=before_snap,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def _create_snapshot(self) -> Dict[str, Any]:
        """Internal/adapter snapshot capture."""
        return self._controller.create_snapshot()

    def _restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Internal/adapter snapshot restoration."""
        self._controller.restore_snapshot(snapshot, target_object=self)

    def _record_operation(self, name: str, before_snap: Dict[str, Any]) -> None:
        """Internal/adapter record operation."""
        self._controller.record_operation(
            name=name,
            before_snap=before_snap,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def undo(self) -> bool:
        """Undo last operation."""
        return self.history.undo()

    def redo(self) -> bool:
        """Redo previously undone operation."""
        return self.history.redo()

    # --- Layer Management ---
    def set_active_layer_index(self, index: int) -> None:
        if self._state.set_active_layer_index(index):
            self.layer_selection_changed.emit(index)

    def add_layer(
        self,
        arg1: Optional[Any] = None,
        arg2: Optional[Any] = None,
        name: Optional[str] = None,
        image: Optional[Any] = None,
        **kwargs,
    ) -> Layer:
        """Add new layer above current active layer."""
        actual_image = image
        actual_name = name

        for arg in (arg1, arg2):
            if isinstance(arg, (Image.Image, tuple, list)):
                actual_image = arg
            elif isinstance(arg, str):
                actual_name = arg

        return self._controller.add_layer(
            target_object=self,
            restore_callback=self._restore_snapshot,
            image_or_color=actual_image,
            name=actual_name,
            **kwargs,
        )

    def duplicate_active_layer(self) -> Optional[Layer]:
        """Duplicate current active layer."""
        return self._controller.duplicate_active_layer(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def remove_active_layer(self) -> bool:
        """Remove active layer (must keep at least 1 layer)."""
        return self._controller.remove_active_layer(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def remove_layer_by_id(self, layer_id: str, push_history: bool = True) -> bool:
        """Remove layer by its unique ID (compatibility helper)."""
        return self._controller.remove_layer_by_id(
            layer_id=layer_id,
            target_object=self,
            restore_callback=self._restore_snapshot,
            push_history=push_history,
        )

    def move_layer_up(self) -> bool:
        return self._controller.move_layer_up(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def move_layer_down(self) -> bool:
        return self._controller.move_layer_down(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def merge_down(self) -> bool:
        """Merge active layer with the layer directly beneath it."""
        return self._controller.merge_down(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def set_layer_visible(self, index: int, visible: bool) -> None:
        self._controller.set_layer_visible(
            index=index,
            visible=visible,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def set_layer_opacity(self, index: int, opacity: float, record_history: bool = True) -> None:
        self._controller.set_layer_opacity(
            index=index,
            opacity=opacity,
            target_object=self,
            restore_callback=self._restore_snapshot,
            record_history=record_history,
        )

    # --- Offset-Aware Geometric Transformations ---
    def rotate_document(self, clockwise: bool = True) -> None:
        """Rotate entire document 90 degrees with offset-aware layer transformation."""
        self._controller.rotate_document(
            clockwise=clockwise,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def rotate_180_document(self) -> None:
        """Rotate entire document 180 degrees with offset-aware layer transformation."""
        self._controller.rotate_180_document(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def flip_horizontal_document(self) -> None:
        """Flip document horizontally with offset-aware layer transformation."""
        self._controller.flip_horizontal_document(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def flip_vertical_document(self) -> None:
        """Flip document vertically with offset-aware layer transformation."""
        self._controller.flip_vertical_document(
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def resize_document(
        self,
        new_width: int,
        new_height: int,
        resample: int = Image.Resampling.LANCZOS,
    ) -> None:
        """Resize entire document and all layers with offset-aware scaling."""
        self._controller.resize_document(
            new_width=new_width,
            new_height=new_height,
            resample=resample,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def crop_document(self, rect: Tuple[int, int, int, int]) -> None:
        """
        Crop entire document to rectangle (left, top, right, bottom).
        Transforms Canvas-space crop rectangle into Layer-local coordinates for every layer.
        """
        self._controller.crop_document(
            rect=rect,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    # --- Adjustments & Filters ---
    def apply_color_adjustments(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> None:
        """Apply color adjustments to active layer."""
        self._controller.apply_color_adjustments(
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

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
        return self._engine.compositing.get_adjusted_preview(
            layer_stack=self._state.layer_stack,
            canvas_size=(self._state.width, self._state.height),
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )

    def apply_filter(self, filter_name: str) -> None:
        """Apply photographic filter to active layer."""
        self._controller.apply_filter(
            filter_name=filter_name,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def get_filter_preview(self, filter_name: str) -> Optional[Image.Image]:
        """Return preview composite with filter applied to active layer."""
        if not self.has_image or not self.active_layer:
            return None
        return self._engine.compositing.get_filter_preview(
            layer_stack=self._state.layer_stack,
            canvas_size=(self._state.width, self._state.height),
            filter_name=filter_name,
        )

    def remove_background(self, tolerance: int = 28, feather_radius: int = 2) -> None:
        """
        Remove background from the active layer with tolerance and edge feathering.
        Records history for undo/redo.
        """
        self._controller.remove_background(
            tolerance=tolerance,
            feather_radius=feather_radius,
            target_object=self,
            restore_callback=self._restore_snapshot,
        )

    def apply_remove_background(self, tolerance: int = 28, feather_radius: int = 2) -> None:
        """Consistent alias for remove_background."""
        self.remove_background(tolerance=tolerance, feather_radius=feather_radius)
