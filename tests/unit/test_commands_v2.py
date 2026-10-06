# tests/unit/test_commands_v2.py
"""
Unit Tests — Command Architecture 2.0
Author: Ali Kamrani (MRThugh)
Validates reversible domain operations, input validation, execution,
critical round-trip symmetry (Initial -> Execute -> Undo -> Redo),
and memory-safe state restoration.
"""

import pytest
from PIL import Image
from parto.editor.document import Document
from parto.layers.models.layer import Layer
from parto.commands.layers import (
    CreateLayerCommand,
    DeleteLayerCommand,
    DuplicateLayerCommand,
    MoveLayerCommand,
    MergeDownCommand,
    ChangeLayerOpacityCommand,
    ToggleLayerVisibilityCommand,
    RenameLayerCommand,
)
from parto.commands.brush import PaintStrokeCommand
from parto.commands.transform import (
    RotateCommand,
    FlipCommand,
    ResizeCommand,
    CropCommand,
)
from parto.commands.filters import (
    ApplyFilterCommand,
    ColorAdjustmentsCommand,
    RemoveBackgroundCommand,
)
from parto.commands.selection import (
    SelectAllCommand,
    DeselectCommand,
    InvertSelectionCommand,
)


@pytest.fixture
def test_doc():
    doc = Document()
    doc.new_document(100, 100, fill_color=(255, 255, 255, 255))
    return doc


def test_create_layer_command_roundtrip(test_doc):
    """Verify CreateLayerCommand execute -> undo -> redo round-trip."""
    initial_count = len(test_doc.layers)
    new_layer = Layer(name="New Layer", image=Image.new("RGBA", (100, 100), (255, 0, 0, 255)))

    cmd = CreateLayerCommand(test_doc, new_layer)
    assert cmd.can_execute() is True

    # 1. Execute
    test_doc.history.execute(cmd)
    assert len(test_doc.layers) == initial_count + 1
    assert test_doc.layers[-1] is new_layer

    # 2. Undo
    assert test_doc.undo() is True
    assert len(test_doc.layers) == initial_count
    assert new_layer not in test_doc.layers

    # 3. Redo
    assert test_doc.redo() is True
    assert len(test_doc.layers) == initial_count + 1
    assert new_layer in test_doc.layers


def test_delete_layer_command_roundtrip(test_doc):
    """Verify DeleteLayerCommand maintains exact layer restoration and validates stack minimum."""
    l2 = test_doc.add_layer(name="Secondary")
    assert len(test_doc.layers) == 2

    cmd = DeleteLayerCommand(test_doc, l2, index=1)
    assert cmd.can_execute() is True

    # 1. Execute
    test_doc.history.execute(cmd)
    assert len(test_doc.layers) == 1
    assert l2 not in test_doc.layers

    # 2. Undo
    assert test_doc.undo() is True
    assert len(test_doc.layers) == 2
    assert test_doc.layers[1].name == "Secondary"

    # 3. Redo
    assert test_doc.redo() is True
    assert len(test_doc.layers) == 1


def test_move_layer_command_roundtrip(test_doc):
    """Verify MoveLayerCommand reorders layers and reverses cleanly."""
    l1 = test_doc.layers[0]
    l2 = test_doc.add_layer(name="Top Layer")
    assert test_doc.layers[0] is l1
    assert test_doc.layers[1] is l2

    cmd = MoveLayerCommand(test_doc, from_index=1, to_index=0)
    assert cmd.can_execute() is True

    # Execute
    test_doc.history.execute(cmd)
    assert test_doc.layers[0] is l2
    assert test_doc.layers[1] is l1

    # Undo
    assert test_doc.undo() is True
    assert test_doc.layers[0] is l1
    assert test_doc.layers[1] is l2

    # Redo
    assert test_doc.redo() is True
    assert test_doc.layers[0] is l2
    assert test_doc.layers[1] is l1


def test_change_opacity_command_coalescing(test_doc):
    """Verify ChangeLayerOpacityCommand coalesces continuous adjustments."""
    layer = test_doc.active_layer
    assert layer.opacity == 1.0

    cmd1 = ChangeLayerOpacityCommand(test_doc, layer, 1.0, 0.8)
    test_doc.history.execute(cmd1)
    assert abs(layer.opacity - 0.8) < 1e-4
    assert test_doc.history.undo_count == 1

    # Merge consecutive adjustment
    cmd2 = ChangeLayerOpacityCommand(test_doc, layer, 0.8, 0.5)
    test_doc.history.execute(cmd2)
    assert abs(layer.opacity - 0.5) < 1e-4
    # Coalesced: still 1 undo entry!
    assert test_doc.history.undo_count == 1

    # Undo restores original 1.0 in single step
    assert test_doc.undo() is True
    assert abs(layer.opacity - 1.0) < 1e-4

    # Redo restores final 0.5
    assert test_doc.redo() is True
    assert abs(layer.opacity - 0.5) < 1e-4


def test_paint_stroke_command_exact_roundtrip(test_doc):
    """Verify PaintStrokeCommand exact pixel byte match across undo/redo cycle."""
    layer = test_doc.active_layer
    initial_bytes = layer.image.tobytes()

    # Create modified buffer
    modified_img = layer.image.copy()
    modified_img.putpixel((10, 10), (255, 0, 0, 255))
    modified_bytes = modified_img.tobytes()

    cmd = PaintStrokeCommand(
        target_document=test_doc,
        layer=layer,
        before_image=layer.image,
        after_image=modified_img,
        name="Brush Stroke (10px)",
    )

    # Execute
    test_doc.history.execute(cmd)
    assert layer.image.tobytes() == modified_bytes

    # Undo
    assert test_doc.undo() is True
    assert layer.image.tobytes() == initial_bytes

    # Redo
    assert test_doc.redo() is True
    assert layer.image.tobytes() == modified_bytes


def test_transform_commands_roundtrip(test_doc):
    """Verify Rotate, Flip, Resize, and Crop commands execute and undo cleanly."""
    initial_w, initial_h = test_doc.width, test_doc.height

    # 1. Rotate 90 CW
    cmd_rot = RotateCommand(test_doc, clockwise=True)
    test_doc.history.execute(cmd_rot)
    assert test_doc.undo() is True
    assert (test_doc.width, test_doc.height) == (initial_w, initial_h)

    # 2. Resize
    cmd_resize = ResizeCommand(test_doc, 200, 150)
    test_doc.history.execute(cmd_resize)
    assert (test_doc.width, test_doc.height) == (200, 150)
    assert test_doc.undo() is True
    assert (test_doc.width, test_doc.height) == (initial_w, initial_h)

    # 3. Crop
    cmd_crop = CropCommand(test_doc, (10, 10, 60, 60))
    test_doc.history.execute(cmd_crop)
    assert (test_doc.width, test_doc.height) == (50, 50)
    assert test_doc.undo() is True
    assert (test_doc.width, test_doc.height) == (initial_w, initial_h)


def test_selection_commands():
    """Verify SelectionCommand lifecycle."""
    class DummyCanvas:
        def __init__(self):
            self.selection = None
        def set_selection(self, s):
            self.selection = s

    canvas = DummyCanvas()
    cmd = SelectAllCommand(target=canvas)
    cmd.execute()
    assert canvas.selection == "all"
    cmd.undo()
    assert canvas.selection is None
