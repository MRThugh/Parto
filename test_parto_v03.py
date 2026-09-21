# test_parto_v03.py
"""
Parto v0.3.0 - Comprehensive Architectural & Subsystem Test Suite
Tests multi-layer architecture, command-based undo/redo, interactive tools,
threading workers, theme management, shortcut registry, and export pipeline.
Author: Ali Kamrani (MRThugh)
Version: 0.3.0
"""

import os
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QRectF

from parto.editor.document import Document
from parto.editor.canvas import Canvas
from parto.editor.selection import CropSelection
from parto.image.layers import Layer, LayerStack
from parto.image.export import save_image_file
from parto.image.transforms import rotate_90, rotate_180, flip_horizontal, flip_vertical, crop_image, resize_image
from parto.image.processing import apply_color_adjustments
from parto.image.filters import apply_filter, SUPPORTED_FILTERS
from parto.history.manager import HistoryManager
from parto.history.commands import (
    AddLayerCommand,
    RemoveLayerCommand,
    DuplicateLayerCommand,
    MoveLayerCommand,
    MergeDownCommand,
    ApplyAdjustmentCommand,
    ApplyFilterCommand,
)
from parto.shortcuts.manager import ShortcutManager
from parto.tools.crop import CropTool
from parto.tools.brush import BrushTool
from parto.tools.eyedropper import EyedropperTool
from parto.tools.move import MoveTool
from parto.themes.manager import ThemeManager
from parto.themes.palettes import THEME_PALETTES


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def base_image():
    """Create a 300x200 RGBA test image."""
    return Image.new("RGBA", (300, 200), color=(100, 150, 200, 255))


# ============================================================================
# 1. LAYER STACK & DOCUMENT MODEL TESTS
# ============================================================================

def test_layer_creation(base_image):
    layer = Layer(base_image, name="Background", opacity=0.8, visible=True)
    assert layer.name == "Background"
    assert layer.opacity == 0.8
    assert layer.visible is True
    assert layer.width == 300
    assert layer.height == 200

    dup = layer.duplicate()
    assert dup.name == "Background (Copy)"
    assert dup.opacity == 0.8
    assert dup.width == 300


def test_layer_stack_operations(base_image):
    stack = LayerStack(300, 200)
    bg = stack.add_layer(base_image, "Background")
    assert len(stack) == 1
    assert stack.active_layer == bg

    # Add second layer
    overlay_img = Image.new("RGBA", (300, 200), color=(255, 0, 0, 128))
    top = stack.add_layer(overlay_img, "Overlay")
    assert len(stack) == 2
    assert stack.active_layer == top
    assert stack.active_index == 1

    # Move down
    assert stack.move_layer_down(1) is True
    assert stack.active_index == 0
    assert stack.layers[0] == top

    # Move up
    assert stack.move_layer_up(0) is True
    assert stack.active_index == 1
    assert stack.layers[1] == top

    # Composite generation
    comp = stack.composite()
    assert comp.size == (300, 200)
    assert comp.mode == "RGBA"

    # Merge down
    merged = stack.merge_down(1)
    assert merged is not None
    assert len(stack) == 1
    assert stack.active_index == 0


def test_document_signals_and_history(qapp, base_image):
    doc = Document()
    doc.new_document(300, 200)
    assert doc.has_image is True
    assert doc.width == 300
    assert doc.height == 200

    # Add layer
    l2 = doc.add_layer()
    assert len(doc.layers) == 2
    assert doc.history.can_undo is True

    # Undo add layer
    doc.history.undo()
    assert len(doc.layers) == 1

    # Redo add layer
    doc.history.redo()
    assert len(doc.layers) == 2


# ============================================================================
# 2. COMMAND PATTERN & UNDO/REDO ARCHITECTURE TESTS
# ============================================================================

def test_command_manager_bounds():
    manager = HistoryManager(max_history=5)
    stack = LayerStack(100, 100)
    stack.add_layer(Image.new("RGBA", (100, 100), (0, 0, 0, 255)), "Base")

    for i in range(10):
        layer = Layer(Image.new("RGBA", (100, 100)), f"L{i}")
        cmd = AddLayerCommand(stack, layer)
        manager.execute(cmd)

    assert len(manager.undo_stack) == 5
    assert manager.can_undo is True


def test_transform_command_undo_redo(base_image):
    manager = HistoryManager()
    stack = LayerStack(300, 200)
    stack.add_layer(base_image, "Main")

    # Apply adjustments
    cmd = ApplyAdjustmentCommand(stack, brightness=1.4, contrast=1.2)
    manager.execute(cmd)
    assert manager.can_undo is True

    manager.undo()
    assert manager.can_redo is True

    manager.redo()
    assert manager.can_undo is True


def test_filter_command_undo_redo(base_image):
    manager = HistoryManager()
    stack = LayerStack(300, 200)
    layer = stack.add_layer(base_image, "Main")

    cmd = ApplyFilterCommand(stack, "grayscale")
    manager.execute(cmd)
    assert manager.can_undo is True

    manager.undo()
    assert manager.can_redo is True


# ============================================================================
# 3. INTERACTIVE TOOLS TESTS
# ============================================================================

def test_crop_selection_math():
    sel = CropSelection()
    sel.init_rect(1000, 500)
    assert sel.rect.width() == 1000
    assert sel.rect.height() == 500

    # Test aspect ratio 1:1 constraint
    sel.set_aspect_ratio(1.0, 1000, 500)
    assert sel.rect.width() == 500
    assert sel.rect.height() == 500

    # Test aspect ratio 16:9
    sel.set_aspect_ratio(16.0 / 9.0, 1920, 1080)
    r = sel.get_pixel_rect(1920, 1080)
    assert r[2] > 0
    assert r[3] > 0


def test_brush_tool_drawing(qapp):
    doc = Document()
    doc.new_document(100, 100)
    brush = BrushTool()
    brush.color = (255, 0, 0, 255)
    brush.radius = 5

    layer = doc.active_layer
    assert layer is not None

    # Simulate stroke
    brush.start_stroke(QPoint(10, 10), layer)
    brush.continue_stroke(QPoint(20, 20), layer)
    brush.end_stroke(doc)

    # Document history recorded brush stroke
    assert doc.history.can_undo is True


def test_eyedropper_tool(qapp, base_image):
    doc = Document()
    doc.new_document(300, 200)
    # Fill active layer with known color
    doc.active_layer.image = base_image

    eyedropper = EyedropperTool()
    color = eyedropper.sample_color(150, 100, doc)
    assert color == (100, 150, 200, 255)


# ============================================================================
# 4. EXPORT & FORMAT CONVERSION TESTS
# ============================================================================

def test_export_all_formats(tmp_path, base_image):
    formats = [
        ("test.png", {"format": "PNG"}),
        ("test.jpg", {"format": "JPEG", "quality": 85}),
        ("test.webp", {"format": "WEBP", "lossless": True}),
        ("test.bmp", {"format": "BMP"}),
        ("test.tiff", {"format": "TIFF"}),
    ]

    for filename, kwargs in formats:
        path = str(tmp_path / filename)
        success, err = save_image_file(base_image, path, **kwargs)
        assert success is True, f"Failed to save {filename}: {err}"
        assert os.path.exists(path)

        with Image.open(path) as loaded:
            assert loaded.size == (300, 200)


# ============================================================================
# 5. SHORTCUT REGISTRY TESTS
# ============================================================================

def test_shortcut_manager_registration():
    sm = ShortcutManager()
    entry = sm.register("test_act", "Test Action", "Testing", "Ctrl+T", "A test shortcut")
    assert entry.action_id == "test_act"
    assert entry.key_sequence == "Ctrl+T"

    found = sm.get("test_act")
    assert found == entry

    all_sc = sm.get_all()
    assert any(sc.action_id == "test_act" for sc in all_sc)
    assert "test_act" in sm


# ============================================================================
# 6. THEME SUBSYSTEM TESTS
# ============================================================================

def test_theme_manager_palettes():
    tm = ThemeManager()
    themes = tm.get_available_themes()
    assert "dark" in themes
    assert "light" in themes
    assert "graphite" in themes
    assert "midnight" in themes
    assert "nord" in themes

    for t in themes:
        pal = tm.get_palette(t)
        assert "bg" in pal
        assert "text" in pal
        assert "primary" in pal
        assert "canvas_bg" in pal
