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
        assert "border_color" in pal


def test_theme_semantic_colors():
    tm = ThemeManager()
    for semantic_name in ("primary", "bg", "text", "border_color", "accent", "danger"):
        color = tm.get_semantic_color(semantic_name)
        assert isinstance(color, str)
        assert color.startswith("#") or color.startswith("rgba")


def test_shortcut_manager_no_conflicts():
    sm = ShortcutManager()
    # Register core menu shortcuts
    sm.register("file_new", "New Canvas...", "File", "Ctrl+N", "Create canvas")
    sm.register("file_open", "Open Image...", "File", "Ctrl+O", "Open image")
    sm.register("file_save", "Save", "File", "Ctrl+S", "Save image")
    sm.register("file_save_as", "Save As...", "File", "Ctrl+Shift+S", "Save as")
    sm.register("file_export", "Export As...", "File", "Ctrl+Shift+E", "Export image")
    sm.register("edit_undo", "Undo", "Edit", "Ctrl+Z", "Undo")
    sm.register("edit_redo", "Redo", "Edit", "Ctrl+Y", "Redo")
    sm.register("edit_resize", "Resize Image...", "Edit", "Ctrl+Alt+I", "Resize image")
    sm.register("tool_move", "Pan / Move Tool", "Tools", "V", "Pan canvas")
    sm.register("tool_crop", "Crop Tool", "Tools", "C", "Crop canvas")
    sm.register("tool_brush", "Brush Tool", "Tools", "B", "Brush tool")
    sm.register("tool_eyedropper", "Eyedropper", "Tools", "I", "Sample color")
    sm.register("view_layers", "Layers Panel", "View", "F7", "Toggle layers")
    sm.register("view_adjustments", "Adjustments Panel", "View", "F8", "Toggle adjustments")
    sm.register("img_rot_cw", "Rotate 90° Clockwise", "Image", "Ctrl+R", "Rotate CW")
    sm.register("img_rot_ccw", "Rotate 90° Counter-Clockwise", "Image", "Ctrl+Shift+R", "Rotate CCW")
    sm.register("img_rot_180", "Rotate 180°", "Image", "Ctrl+Alt+R", "Rotate 180")
    sm.register("img_fliph", "Flip Horizontal", "Image", "Ctrl+H", "Flip horizontal")
    sm.register("img_flipv", "Flip Vertical", "Image", "Ctrl+Shift+H", "Flip vertical")
    sm.register("layer_mrg", "Merge Down", "Layers", "Ctrl+E", "Merge down")
    sm.register("help_palette", "Command Palette...", "App", "Ctrl+K", "Command palette")
    sm.register("edit_crop", "Crop Canvas...", "Edit", "Shift+C", "Crop canvas")
    sm.register("img_remove_bg", "Remove Background", "Image", "Ctrl+Shift+B", "Remove background")

    conflicts = sm.find_conflicts()
    assert len(conflicts) == 0, f"Detected shortcut conflicts: {conflicts}"


def test_brush_tool_properties_and_shortcuts():
    brush = BrushTool()
    # Initial defaults
    assert brush.size == 8
    assert brush.opacity == 1.0
    assert brush.hardness == 0.8
    assert brush.color == (0, 0, 0, 255)

    # Size adjustment and clamping
    brush.increase_size(4)
    assert brush.size == 12
    brush.decrease_size(2)
    assert brush.size == 10

    # Color swapping (X key)
    brush.color = (255, 0, 0, 255)
    brush.background_color = (0, 255, 0, 255)
    brush.swap_colors()
    assert brush.color == (0, 255, 0, 255)
    assert brush.background_color == (255, 0, 0, 255)

    # Reset to default black & white (D key)
    brush.reset_default_colors()
    assert brush.color == (0, 0, 0, 255)
    assert brush.background_color == (255, 255, 255, 255)


def test_vector_icon_canonical_aliases():
    from parto.resources.icons import ICON_ALIASES
    assert ICON_ALIASES.get("rotate_cw") == "rotate-cw"
    assert ICON_ALIASES.get("rotate_ccw") == "rotate-ccw"
    assert ICON_ALIASES.get("flip_h") == "flip-horizontal"
    assert ICON_ALIASES.get("flip_v") == "flip-vertical"
    assert ICON_ALIASES.get("zoom_in") == "zoom-in"
    assert ICON_ALIASES.get("zoom_out") == "zoom-out"
    assert ICON_ALIASES.get("zoom_fit") == "zoom-fit"


def test_layer_opacity_history_coalescing(base_image):
    doc = Document()
    doc.new_document(300, 200)
    assert doc.active_layer is not None

    # Simulate slider drag: multiple continuous updates with record_history=False
    start_snap = doc._create_snapshot()
    doc.set_layer_opacity(0, 0.8, record_history=False)
    doc.set_layer_opacity(0, 0.6, record_history=False)
    doc.set_layer_opacity(0, 0.4, record_history=False)

    # Opacity updated on layer without filling history stack
    assert doc.active_layer.opacity == 0.4
    assert doc.history.can_undo is False

    # Slider released: commit single history entry
    doc._record_operation("Change Layer Opacity", start_snap)
    assert doc.history.can_undo is True

    # Undo restores original 1.0 opacity
    doc.history.undo()
    assert doc.active_layer.opacity == 1.0


def test_adjustment_factor_math():
    # Slider values: -100 to +100 mapped to factors 0.0 to 2.0
    def get_factors(b_val, c_val, s_val, sh_val):
        b = max(0.0, 1.0 + (b_val / 100.0))
        c = max(0.0, 1.0 + (c_val / 100.0))
        s = max(0.0, 1.0 + (s_val / 100.0))
        sh = max(0.0, 1.0 + (sh_val / 100.0))
        return b, c, s, sh

    # Neutral values
    b, c, s, sh = get_factors(0, 0, 0, 0)
    assert b == 1.0 and c == 1.0 and s == 1.0 and sh == 1.0

    # Max increase
    b, c, s, sh = get_factors(100, 50, -50, -100)
    assert b == 2.0
    assert c == 1.5
    assert s == 0.5
    assert sh == 0.0


def test_brush_bar_and_icon_aliases():
    from parto.ui.widgets.brush_bar import BrushBar
    from parto.resources.icons import ICON_ALIASES

    # Verify brush bar can be imported
    assert BrushBar is not None

    # Verify zoom icon aliases exist
    assert "zoom_in" in ICON_ALIASES
    assert "zoom_out" in ICON_ALIASES
    assert "zoom_fit" in ICON_ALIASES


def test_background_removal_api_consistency():
    import inspect
    from parto.editor.engine import EditorEngine
    from parto.editor.document import Document
    from parto.image.processing import remove_background
    from parto.ui.main_window import MainWindow

    # Check function signature in image processing
    proc_sig = inspect.signature(remove_background)
    assert "tolerance" in proc_sig.parameters
    assert "feather_radius" in proc_sig.parameters

    # Check EditorEngine methods
    ee_rm = inspect.signature(EditorEngine.remove_background)
    assert "tolerance" in ee_rm.parameters
    assert "feather_radius" in ee_rm.parameters
    ee_apply = inspect.signature(EditorEngine.apply_remove_background)
    assert "tolerance" in ee_apply.parameters
    assert "feather_radius" in ee_apply.parameters

    # Check Document methods
    doc_rm = inspect.signature(Document.remove_background)
    assert "tolerance" in doc_rm.parameters
    assert "feather_radius" in doc_rm.parameters
    doc_apply = inspect.signature(Document.apply_remove_background)
    assert "tolerance" in doc_apply.parameters
    assert "feather_radius" in doc_apply.parameters

    # Check MainWindow methods
    mw_rm = inspect.signature(MainWindow.remove_background)
    assert "tolerance" in mw_rm.parameters
    assert "feather_radius" in mw_rm.parameters
    mw_apply = inspect.signature(MainWindow.apply_remove_background)
    assert "tolerance" in mw_apply.parameters
    assert "feather_radius" in mw_apply.parameters

    # Safe None handling
    assert remove_background(None, tolerance=28, feather_radius=2) is None


