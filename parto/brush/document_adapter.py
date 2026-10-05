# parto/brush/document_adapter.py
"""
Parto Brush System — Document and LayerStack Integration Boundary
Isolates brush engine and stroke controllers from Document internals.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Any, Optional, Tuple
from PIL import Image


class BrushDocumentAdapter:
    """
    Standardized adapter mediating between brush raster operations and Document/LayerStack.
    Guarantees clean snapshotting, strict no-op detection, and atomic history integration.
    """

    @staticmethod
    def resolve_target(target: Any, doc: Optional[Any] = None) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Resolve (document, target_layer) from given arguments.
        Supports passing Document, Layer, or (target, doc).
        """
        if hasattr(target, "active_layer"):
            document = target
            layer = target.active_layer
        else:
            layer = target
            document = doc

        return document, layer

    @staticmethod
    def capture_pre_stroke(document: Optional[Any], layer: Optional[Any]) -> Tuple[Optional[Image.Image], Optional[Any]]:
        """
        Capture pre-stroke layer image buffer and complete document snapshot.
        """
        layer_image: Optional[Image.Image] = None
        snapshot: Optional[Any] = None

        if layer and hasattr(layer, "image") and layer.image is not None:
            layer_image = layer.image.copy()

        if document and hasattr(document, "_create_snapshot"):
            snapshot = document._create_snapshot()

        return layer_image, snapshot

    @staticmethod
    def commit_stroke(
        document: Optional[Any],
        layer: Optional[Any],
        before_layer_image: Optional[Image.Image],
        before_snapshot: Optional[Any],
        operation_name: str,
    ) -> bool:
        """
        Commit completed stroke to Document and History.
        Enforces strict no-op detection: returns True if pixels changed and history was recorded,
        or False if no actual pixel modification occurred.
        """
        if layer is None or not hasattr(layer, "image") or layer.image is None or before_layer_image is None:
            if document and hasattr(document, "invalidate_composite"):
                document.invalidate_composite()
            return False

        # Byte-level pixel difference check
        if layer.image.tobytes() == before_layer_image.tobytes():
            if document and hasattr(document, "invalidate_composite"):
                document.invalidate_composite()
            return False

        # Ensure before_snapshot exists, creating from document if needed
        if before_snapshot is None and document and hasattr(document, "_create_snapshot"):
            before_snapshot = document._create_snapshot()

        # Sync snapshot with exact pre-stroke layer image
        if before_snapshot is not None and "layer_stack" in before_snapshot:
            target_id = getattr(layer, "id", None)
            target_name = getattr(layer, "name", None)
            found = False
            for lay in before_snapshot["layer_stack"]:
                if (target_id and getattr(lay, "id", None) == target_id) or (target_name and getattr(lay, "name", None) == target_name):
                    lay.image = before_layer_image.copy()
                    found = True
                    break
            if not found and before_snapshot["layer_stack"].active_layer:
                before_snapshot["layer_stack"].active_layer.image = before_layer_image.copy()

        # Mark document dirty
        if document and hasattr(document, "set_modified"):
            document.set_modified(True)

        # Record undo/redo history operation
        if document and hasattr(document, "_record_operation") and before_snapshot is not None:
            document._record_operation(operation_name, before_snapshot)
        elif document and hasattr(document, "history") and before_snapshot is not None:
            from ..history.commands import SnapshotCommand
            after_snap = document._create_snapshot() if hasattr(document, "_create_snapshot") else None
            restore_func = getattr(document, "_restore_snapshot", lambda s: None)
            document.history.push(
                SnapshotCommand(
                    operation_name,
                    document,
                    restore_func,
                    before_snapshot,
                    after_snap,
                )
            )

        if document and hasattr(document, "invalidate_composite"):
            document.invalidate_composite()

        return True

    @staticmethod
    def rollback_stroke(
        document: Optional[Any],
        layer: Optional[Any],
        before_layer_image: Optional[Image.Image],
        before_snapshot: Optional[Any],
    ) -> None:
        """Restore document and layer to state prior to stroke start."""
        if layer and before_layer_image and hasattr(layer, "image"):
            layer.image = before_layer_image.copy()

        if document and before_snapshot is not None and hasattr(document, "_restore_snapshot"):
            document._restore_snapshot(before_snapshot)

        if document and hasattr(document, "invalidate_composite"):
            document.invalidate_composite()
