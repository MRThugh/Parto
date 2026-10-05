# parto/document/history/transaction.py
"""
Parto Document Subsystem — Transaction & Snapshot Coordinator
Author: Ali Kamrani (MRThugh)

Responsible for capturing deep snapshots of document state, verifying no-op boundaries,
restoring states atomically, and integrating with HistoryManager.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Callable
from PIL import Image

from ..models.document_state import DocumentState
from ...image.layers import LayerStack
from ...history.manager import HistoryManager
from ...history.commands import SnapshotCommand


def snapshots_equal(snap1: Dict[str, Any], snap2: Dict[str, Any]) -> bool:
    """Compare two document snapshots to determine if any actual change occurred."""
    if snap1["width"] != snap2["width"] or snap1["height"] != snap2["height"]:
        return False
    if snap1.get("active_layer_index") != snap2.get("active_layer_index"):
        return False
    stack1 = snap1.get("layer_stack")
    stack2 = snap2.get("layer_stack")
    if stack1 is None or stack2 is None:
        return False
    if len(stack1) != len(stack2):
        return False
    for l1, l2 in zip(stack1, stack2):
        if l1.id != l2.id or l1.name != l2.name:
            return False
        if l1.visible != l2.visible:
            return False
        if abs(l1.opacity - l2.opacity) > 1e-4:
            return False
        if l1.blend_mode != l2.blend_mode:
            return False
        if l1.offset_x != l2.offset_x or l1.offset_y != l2.offset_y:
            return False
        if l1.image.size != l2.image.size:
            return False
        if l1.image.tobytes() != l2.image.tobytes():
            return False
    return True


class TransactionCoordinator:
    """
    Coordinates snapshot capture, equality detection, atomic restoration,
    and history command creation for a DocumentState.
    """

    @staticmethod
    def create_snapshot(state: DocumentState) -> Dict[str, Any]:
        """Capture deep clone of current state for undo/redo."""
        return {
            "width": state.width,
            "height": state.height,
            "layer_stack": state.layer_stack.clone(),
            "active_layer_index": state.layer_stack.active_index,
        }

    @staticmethod
    def restore_snapshot(state: DocumentState, snapshot: Dict[str, Any]) -> None:
        """
        Restore state from snapshot.
        Preserves existing Layer object identities when IDs match to protect external references.
        """
        state.width = snapshot["width"]
        state.height = snapshot["height"]

        if "layer_stack" in snapshot and isinstance(snapshot["layer_stack"], LayerStack):
            target_stack = snapshot["layer_stack"].clone()
            existing_by_id = {lay.id: lay for lay in state.layer_stack}
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
            state.layer_stack._layers = new_layers
            state.layer_stack.width = state.width
            state.layer_stack.height = state.height
            state.layer_stack.set_active_index(snapshot.get("active_layer_index", target_stack.active_index))
        elif "layers" in snapshot:
            state.layer_stack = LayerStack(state.width, state.height)
            state.layer_stack._layers = [lay.clone() for lay in snapshot["layers"]]
            state.layer_stack.set_active_index(snapshot.get("active_layer_index", 0))

    @classmethod
    def record_operation(
        cls,
        state: DocumentState,
        history: HistoryManager,
        target_object: Any,
        name: str,
        before_snap: Dict[str, Any],
        restore_callback: Callable[[Dict[str, Any]], None],
    ) -> bool:
        """
        Captures after-state and pushes a SnapshotCommand to history.
        """
        after_snap = cls.create_snapshot(state)
        cmd = SnapshotCommand(
            name=name,
            target_object=target_object,
            restore_fn=restore_callback,
            before_state=before_snap,
            after_state=after_snap,
        )
        history.push(cmd)
        state.is_modified = True
        return True
