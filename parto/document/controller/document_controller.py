# parto/document/controller/document_controller.py
"""
Parto Document Subsystem — Document Controller
Author: Ali Kamrani (MRThugh)

Coordinates mutations, operations, transactions, and signal propagation
across the Document subsystem.
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, Callable, List, Union
from PIL import Image

from ..models.document_state import DocumentState
from ..engine.document_engine import DocumentEngine
from ..history.transaction import TransactionCoordinator
from ..adapters.storage_adapter import DocumentStorageAdapter
from ...layers import Layer
from ...history.manager import HistoryManager
from ...commands.layers import (
    CreateLayerCommand,
    DeleteLayerCommand,
    DuplicateLayerCommand,
    MoveLayerCommand,
    MergeDownCommand,
    ChangeLayerOpacityCommand,
    ToggleLayerVisibilityCommand,
    RenameLayerCommand,
)
from ...commands.transform import (
    RotateCommand,
    FlipCommand,
    ResizeCommand,
    CropCommand,
)
from ...commands.filters import (
    ApplyFilterCommand,
    ColorAdjustmentsCommand,
    RemoveBackgroundCommand,
)


class DocumentController:
    """
    Coordinates state mutations, domain operations, history commands,
    and storage for a DocumentState. Functions as an architectural Facade
    delegating reversible domain operations through Commands to HistoryManager.
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
        document: Optional[Any] = None,
    ):
        self.state = state
        self.engine = engine
        self.history = history
        self.storage = storage
        self.transactions = transactions
        self._on_state_changed = on_state_changed
        self._on_selection_changed = on_selection_changed
        self.document = document

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

    # --- History & Transactions Compatibility Shims ---
    def create_snapshot(self) -> Dict[str, Any]:
        """Backward-compatibility snapshot creation."""
        return self.transactions.create_snapshot(self.state)

    def restore_snapshot(self, snapshot: Dict[str, Any], target_object: Any = None) -> None:
        """Backward-compatibility snapshot restoration."""
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
        """Backward-compatibility legacy operation recorder."""
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

    # --- Layer Operations (Architecture 2.0 Commands) ---
    def add_layer(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        image_or_color: Optional[Any] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> Layer:
        idx = self.state.layer_stack.active_index + 1
        num = len(self.state.layer_stack) + 1
        layer_name = name or f"Layer {num}"

        if isinstance(image_or_color, Layer):
            new_lay = image_or_color
            for k, v in kwargs.items():
                if hasattr(new_lay, k):
                    setattr(new_lay, k, v)
        elif isinstance(image_or_color, Image.Image):
            new_lay = Layer(name=layer_name, image=image_or_color, **kwargs)
        elif isinstance(image_or_color, (tuple, list)):
            img = Image.new("RGBA", (self.state.width, self.state.height), tuple(image_or_color))
            new_lay = Layer(name=layer_name, image=img, **kwargs)
        else:
            img = Image.new("RGBA", (self.state.width, self.state.height), (0, 0, 0, 0))
            new_lay = Layer(name=layer_name, image=img, **kwargs)

        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = CreateLayerCommand(target=target, layer=new_lay, index=idx)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()
        self.notify_selection_changed(self.state.layer_stack.active_index)
        return new_lay

    def duplicate_active_layer(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Layer]:
        if not self.state.has_image or self.state.active_layer_index < 0:
            return None
        active = self.state.active_layer
        if active is None:
            return None
        idx = self.state.active_layer_index
        dup = active.duplicate()
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = DuplicateLayerCommand(target=target, original_layer=active, duplicated_layer=dup, index=idx)
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return dup
        return None

    def remove_active_layer(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        if len(self.state.layer_stack) <= 1:
            return False
        active = self.state.active_layer
        if active is None:
            return False
        idx = self.state.active_layer_index
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = DeleteLayerCommand(target=target, layer=active, index=idx)
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def remove_layer_by_id(
        self,
        layer_id: str,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        push_history: bool = True,
    ) -> bool:
        for i, lay in enumerate(self.state.layer_stack):
            if lay.id == layer_id:
                if len(self.state.layer_stack) <= 1:
                    return False
                if push_history:
                    target = target_object or getattr(self, "document", None) or self.state.layer_stack
                    cmd = DeleteLayerCommand(target=target, layer=lay, index=i)
                    if self.history.execute(cmd):
                        self.state.is_modified = True
                        self.notify_state_changed()
                        self.notify_selection_changed(self.state.layer_stack.active_index)
                        return True
                    return False
                else:
                    self.state.layer_stack.remove_layer(i)
                    self.notify_state_changed()
                    self.notify_selection_changed(self.state.layer_stack.active_index)
                    return True
        return False

    def move_layer_up(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        idx = self.state.active_layer_index
        if idx >= len(self.state.layer_stack) - 1:
            return False
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = MoveLayerCommand(target=target, from_index=idx, to_index=idx + 1)
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def move_layer_down(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        idx = self.state.active_layer_index
        if idx <= 0:
            return False
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = MoveLayerCommand(target=target, from_index=idx, to_index=idx - 1)
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def merge_down(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        idx = self.state.active_layer_index
        if idx <= 0 or len(self.state.layer_stack) < 2:
            return False
        upper = self.state.layer_stack[idx]
        lower = self.state.layer_stack[idx - 1]
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = MergeDownCommand(
            target=target,
            upper_index=idx,
            upper_layer=upper,
            lower_layer=lower,
        )
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            self.notify_selection_changed(self.state.layer_stack.active_index)
            return True
        return False

    def set_layer_visible(
        self,
        index: int,
        visible: bool,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if 0 <= index < len(self.state.layer_stack):
            layer = self.state.layer_stack[index]
            if layer.visible == visible:
                return
            target = target_object or getattr(self, "document", None) or self.state.layer_stack
            cmd = ToggleLayerVisibilityCommand(
                target=target,
                layer=layer,
                old_visible=layer.visible,
                new_visible=visible,
            )
            self.history.execute(cmd)
            self.state.is_modified = True
            self.notify_state_changed()

    def set_layer_opacity(
        self,
        index: int,
        opacity: float,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        record_history: bool = True,
    ) -> None:
        if 0 <= index < len(self.state.layer_stack):
            clamped = max(0.0, min(1.0, float(opacity)))
            layer = self.state.layer_stack[index]
            if abs(layer.opacity - clamped) < 1e-4:
                return
            if record_history:
                target = target_object or getattr(self, "document", None) or self.state.layer_stack
                cmd = ChangeLayerOpacityCommand(
                    target=target,
                    layer=layer,
                    old_opacity=layer.opacity,
                    new_opacity=clamped,
                )
                self.history.execute(cmd)
                self.state.is_modified = True
            else:
                layer.set_opacity(clamped)
            self.notify_state_changed()

    def rename_layer(
        self,
        index_or_layer: Union[int, Layer],
        new_name: str,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        if isinstance(index_or_layer, int):
            if not (0 <= index_or_layer < len(self.state.layer_stack)):
                return False
            layer = self.state.layer_stack[index_or_layer]
        else:
            layer = index_or_layer
        if layer.name == new_name:
            return False
        target = target_object or getattr(self, "document", None) or self.state.layer_stack
        cmd = RenameLayerCommand(
            target=target,
            layer=layer,
            old_name=layer.name,
            new_name=new_name,
        )
        if self.history.execute(cmd):
            self.state.is_modified = True
            self.notify_state_changed()
            return True
        return False

    # --- Geometric Transformations Domain Mutators ---
    def apply_rotate_domain(self, clockwise: bool = True, is_180: bool = False) -> None:
        if not self.state.has_image:
            return
        if is_180:
            self.engine.transforms.rotate_180(
                self.state.layer_stack, self.state.width, self.state.height
            )
        else:
            new_w, new_h = self.engine.transforms.rotate_90(
                self.state.layer_stack, self.state.width, self.state.height, clockwise=clockwise
            )
            self.state.width = new_w
            self.state.height = new_h
        self.state.is_modified = True
        self.notify_state_changed()

    def apply_flip_domain(self, horizontal: bool = True) -> None:
        if not self.state.has_image:
            return
        if horizontal:
            self.engine.transforms.flip_horizontal(self.state.layer_stack, self.state.width)
        else:
            self.engine.transforms.flip_vertical(self.state.layer_stack, self.state.height)
        self.state.is_modified = True
        self.notify_state_changed()

    def apply_resize_domain(self, new_width: int, new_height: int, resample: int = Image.Resampling.LANCZOS) -> None:
        if not self.state.has_image:
            return
        nw, nh = max(1, int(new_width)), max(1, int(new_height))
        if nw == self.state.width and nh == self.state.height:
            return
        new_w, new_h = self.engine.transforms.resize(
            self.state.layer_stack, (self.state.width, self.state.height), (nw, nh), resample=resample
        )
        self.state.width = new_w
        self.state.height = new_h
        self.state.is_modified = True
        self.notify_state_changed()

    def apply_crop_domain(self, rect: Tuple[int, int, int, int]) -> None:
        if not self.state.has_image:
            return
        crop_res = self.engine.transforms.crop(
            self.state.layer_stack, (self.state.width, self.state.height), rect
        )
        if crop_res is None:
            return
        new_w, new_h = crop_res
        self.state.width = new_w
        self.state.height = new_h
        self.state.is_modified = True
        self.notify_state_changed()

    # --- Geometric Transformations (Command Orchestration) ---
    def rotate_document(
        self,
        clockwise: bool,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = RotateCommand(document=target, clockwise=clockwise, is_180=False)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def rotate_180_document(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = RotateCommand(document=target, clockwise=True, is_180=True)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def flip_horizontal_document(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = FlipCommand(document=target, horizontal=True)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def flip_vertical_document(
        self,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = FlipCommand(document=target, horizontal=False)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def resize_document(
        self,
        new_width: int,
        new_height: int,
        resample: int,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        nw, nh = max(1, int(new_width)), max(1, int(new_height))
        if nw == self.state.width and nh == self.state.height:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = ResizeCommand(document=target, new_width=nw, new_height=nh, resample=resample)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def crop_document(
        self,
        rect: Tuple[int, int, int, int],
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = CropCommand(document=target, crop_rect=rect)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    # --- Adjustments & Filters (Command Orchestration) ---
    def apply_color_adjustments(
        self,
        brightness: float,
        contrast: float,
        saturation: float,
        sharpness: float,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = ColorAdjustmentsCommand(
            target_document=target,
            layer=active,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def apply_filter(
        self,
        filter_name: str,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = ApplyFilterCommand(target_document=target, layer=active, filter_name=filter_name)
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()

    def remove_background(
        self,
        tolerance: int,
        feather_radius: int,
        target_object: Any = None,
        restore_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        active = self.state.active_layer
        if active is None or not self.state.has_image:
            return
        target = target_object or getattr(self, "document", None) or self
        cmd = RemoveBackgroundCommand(
            target_document=target,
            layer=active,
            tolerance=tolerance,
            feather_radius=feather_radius,
        )
        self.history.execute(cmd)
        self.state.is_modified = True
        self.notify_state_changed()
