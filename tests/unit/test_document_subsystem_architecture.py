# tests/unit/test_document_subsystem_architecture.py
"""
Unit Tests — Document Subsystem Domain Architecture & Boundary Separation
Author: Ali Kamrani (MRThugh)

Verifies:
1. DocumentState encapsulates canvas dimensions, layers, filepath, and dirty tracking.
2. LayerStack remains the authoritative layer state within DocumentState.
3. TransformEngine performs offset-aware transformations without duplicating image algorithms.
4. CompositingEngine provides non-destructive preview rendering and composite caching.
5. DocumentStorageAdapter handles file I/O, EXIF orientation, and format saving.
6. TransactionCoordinator executes deep snapshotting, restoration, and history integration.
7. Document facade coordinates thin delegations across subsystems without god-object logic.
8. Full undo/redo lifecycle across all document mutations.
"""

import os
import pytest
from PIL import Image

from parto.document import (
    Document,
    DocumentState,
    DocumentEngine,
    TransformEngine,
    CompositingEngine,
    DocumentStorageAdapter,
    TransactionCoordinator,
    snapshots_equal,
    DocumentController,
)
from parto.image.layers import Layer, LayerStack
from parto.history.manager import HistoryManager


def test_document_state_isolation():
    """Verify DocumentState owns canvas dimensions and authoritative LayerStack."""
    state = DocumentState(200, 100)
    assert state.width == 200
    assert state.height == 100
    assert state.dimensions == (200, 100)
    assert state.is_modified is False
    assert state.filepath is None
    assert isinstance(state.layer_stack, LayerStack)

    # Dimension synchronization
    state.set_dimensions(400, 300)
    assert state.width == 400
    assert state.height == 300
    assert state.layer_stack.width == 400
    assert state.layer_stack.height == 300

    # Reset with initial image
    test_img = Image.new("RGBA", (150, 150), (255, 0, 0, 255))
    state.reset(150, 150, initial_image=test_img, filepath="/tmp/test.png")
    assert state.width == 150
    assert state.height == 150
    assert state.filepath == "/tmp/test.png"
    assert len(state.layers) == 1
    assert state.active_layer is not None
    assert state.active_layer.name == "Background"


def test_transform_engine_delegation():
    """Verify TransformEngine coordinates offset-aware transforms on LayerStack."""
    stack = LayerStack(100, 50)
    img = Image.new("RGBA", (100, 50), (0, 128, 255, 255))
    stack.add_layer(img, name="Base")

    # Rotate 90 CW: (100, 50) -> (50, 100)
    w, h = TransformEngine.rotate_90(stack, 100, 50, clockwise=True)
    assert (w, h) == (50, 100)
    assert (stack.width, stack.height) == (50, 100)

    # Rotate 180
    w2, h2 = TransformEngine.rotate_180(stack, 50, 100)
    assert (w2, h2) == (50, 100)

    # Resize: (50, 100) -> (25, 50)
    w3, h3 = TransformEngine.resize(stack, (50, 100), (25, 50))
    assert (w3, h3) == (25, 50)
    assert (stack.width, stack.height) == (25, 50)

    # Crop
    crop_res = TransformEngine.crop(stack, (25, 50), (5, 5, 20, 30))
    assert crop_res == (15, 25)
    assert (stack.width, stack.height) == (15, 25)

    # Full canvas crop is no-op
    noop_crop = TransformEngine.crop(stack, (15, 25), (0, 0, 15, 25))
    assert noop_crop is None


def test_compositing_engine_and_preview():
    """Verify CompositingEngine caches composite and provides non-destructive previews."""
    comp_engine = CompositingEngine()
    stack = LayerStack(60, 60)
    l1 = stack.add_layer(Image.new("RGBA", (60, 60), (255, 0, 0, 255)), name="Red")
    l2 = stack.add_layer(Image.new("RGBA", (60, 60), (0, 255, 0, 128)), name="GreenSemi")

    # Generate composite
    composite = comp_engine.get_composite(stack, 60, 60)
    assert composite is not None
    assert composite.size == (60, 60)

    # Cache hit returns same object
    assert comp_engine.get_composite(stack, 60, 60) is composite

    # Invalidate clears cache
    comp_engine.invalidate()
    new_comp = comp_engine.get_composite(stack, 60, 60)
    assert new_comp is not None

    # Adjusted preview is non-destructive
    preview = comp_engine.get_adjusted_preview(stack, (60, 60), brightness=1.5)
    assert preview is not None
    # Layer 2 original image must NOT have mutated
    assert l2.image.getpixel((0, 0)) == (0, 255, 0, 128)


def test_transaction_coordinator_snapshots():
    """Verify TransactionCoordinator snapshot capture, equality, and restoration."""
    state = DocumentState(80, 80)
    state.reset(80, 80, fill_color=(50, 50, 50, 255))
    l2 = state.layer_stack.add_layer(Image.new("RGBA", (80, 80), (100, 100, 100, 255)), name="L2")

    snap1 = TransactionCoordinator.create_snapshot(state)
    assert snap1["width"] == 80
    assert snap1["height"] == 80
    assert len(snap1["layer_stack"]) == 2

    # Snapshots of unchanged state are equal
    snap2 = TransactionCoordinator.create_snapshot(state)
    assert snapshots_equal(snap1, snap2) is True

    # Mutate state
    TransformEngine.resize(state.layer_stack, (80, 80), (160, 160))
    state.width = 160
    state.height = 160

    snap3 = TransactionCoordinator.create_snapshot(state)
    assert snapshots_equal(snap1, snap3) is False

    # Restore snapshot
    TransactionCoordinator.restore_snapshot(state, snap1)
    assert state.width == 80
    assert state.height == 80
    assert len(state.layers) == 2


def test_storage_adapter_save_and_load(tmp_path):
    """Verify DocumentStorageAdapter loads and saves image files cleanly."""
    adapter = DocumentStorageAdapter()
    test_file = str(tmp_path / "adapter_test.png")

    # Create and save image
    img = Image.new("RGBA", (75, 45), (12, 34, 56, 255))
    success, err = adapter.save_file(img, test_file)
    assert success is True
    assert err is None
    assert os.path.exists(test_file)

    # Load file
    load_success, loaded_img, resolved_path, load_err = adapter.load_file(test_file)
    assert load_success is True
    assert loaded_img is not None
    assert loaded_img.size == (75, 45)
    assert resolved_path == os.path.abspath(test_file)

    # Missing file handling
    missing_success, _, _, _ = adapter.load_file(str(tmp_path / "nonexistent.png"))
    assert missing_success is False


def test_document_facade_complete_operations_and_history():
    """Verify Document facade coordinates all operations with complete undo/redo support."""
    doc = Document()
    doc.new_document(100, 100, fill_color=(20, 20, 20, 255))

    assert doc.width == 100
    assert doc.height == 100
    assert doc.modified is False
    assert doc.history.can_undo is False

    # 1. Add layer
    l2 = doc.add_layer(name="Overlay")
    assert len(doc.layers) == 2
    assert doc.active_layer_index == 1
    assert doc.modified is True
    assert doc.history.can_undo is True

    # 2. Rotate
    doc.rotate_document(clockwise=True)
    assert doc.history.undo_count == 2

    # 3. Flip
    doc.flip_horizontal_document()
    assert doc.history.undo_count == 3

    # 4. Resize
    doc.resize_document(200, 200)
    assert (doc.width, doc.height) == (200, 200)
    assert doc.history.undo_count == 4

    # 5. Crop
    doc.crop_document((10, 10, 110, 110))
    assert (doc.width, doc.height) == (100, 100)
    assert doc.history.undo_count == 5

    # 6. Filters
    doc.apply_filter("grayscale")
    assert doc.history.undo_count == 6

    # 7. Adjustments
    doc.apply_color_adjustments(brightness=1.2, contrast=1.1)
    assert doc.history.undo_count == 7

    # 8. Undo sequence back to clean state
    for _ in range(7):
        assert doc.undo() is True

    assert doc.modified is False
    assert (doc.width, doc.height) == (100, 100)
    assert len(doc.layers) == 1

    # 9. Redo sequence
    for _ in range(7):
        assert doc.redo() is True

    assert doc.modified is True
    assert len(doc.layers) == 2
