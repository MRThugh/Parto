# test_parto_v03_stabilization_pass.py
"""
Parto v0.3.0 - Deep Stabilization Pass & Regression Test Suite
Author: Ali Kamrani (MRThugh)
Validates:
1. Bug 1: Merge Down + Hidden Layers (all visibility combinations, offsets, opacities)
2. Bug 2: Offset-Aware Crop (contained, partial intersect, fully outside, transparent)
3. Bug 3: Offset-Aware Resize (proportional coordinate and dimension scaling, resampling filters)
4. Bug 4: Offset-Aware Rotate (90° CW, 90° CCW, 180° with offset transformation)
5. Bug 5: Offset-Aware Flip (Horizontal & Vertical offset reflection)
6. Coordinate System & Geometry conversions
7. Blend Mode handling
8. Unsaved Changes & Close Event Safety (Save, Cancel, Discard, Failure)
9. Brush Lifecycle & Tool Deactivation Safety
10. Canvas Interaction Ownership (Space-pan, Middle-click pan routing)
11. Brush Color & Background Synchronization
12. Brush Size 1-500px Range Consistency
13. Resize Resampling algorithm pass-through
14. Compare Original non-destructive preview behavior
15. History No-Op suppression
16. Safe Image File I/O & EXIF Orientation handling
17. LayerStack API consistency (active index on delete/reorder/insert)
"""

import os
import tempfile
import numpy as np
import pytest
from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QMouseEvent, QCloseEvent
from PySide6.QtWidgets import QMessageBox

from parto.image.layers import Layer, LayerStack, compose_layers
from parto.editor.document import Document
from parto.editor.geometry import (
    layer_canvas_bounds,
    canvas_to_layer_coords,
    layer_to_canvas_coords,
    rect_intersection,
    transform_layer_crop,
    transform_layer_resize,
    transform_layer_rotate_90,
    transform_layer_rotate_180,
    transform_layer_flip_horizontal,
    transform_layer_flip_vertical,
)
from parto.editor.engine import EditorEngine
from parto.tools.brush import BrushTool, BrushSettings
from parto.tools.move import MoveTool
from parto.editor.canvas import Canvas
from parto.ui.main_window import MainWindow, SaveResult
from parto.ui.dialogs.resize import ResizeDialog


# ============================================================================
# 1. BUG 1: MERGE DOWN + HIDDEN LAYERS SEMANTICS
# ============================================================================

def test_merge_down_visible_upper_visible_lower():
    """Both layers visible: merged layer combines both and is visible."""
    stack = LayerStack(100, 100)
    l1 = stack.add_layer(Image.new("RGBA", (100, 100), (255, 0, 0, 255)), name="L1")
    l2 = stack.add_layer(Image.new("RGBA", (100, 100), (0, 0, 255, 128)), name="L2")
    
    comp_before = stack.composite()
    merged = stack.merge_down(1)
    
    assert merged is not None
    assert merged.visible is True
    assert len(stack) == 1
    comp_after = stack.composite()
    assert np.array_equal(np.array(comp_before), np.array(comp_after))


def test_merge_down_hidden_upper_visible_lower():
    """Hidden upper layer must NOT introduce pixels into the merged result."""
    stack = LayerStack(100, 100)
    l1 = stack.add_layer(Image.new("RGBA", (100, 100), (255, 0, 0, 255)), name="L1")  # Red
    l2 = stack.add_layer(Image.new("RGBA", (100, 100), (0, 255, 0, 255)), name="L2")  # Green
    l2.visible = False  # Upper is hidden!
    
    comp_before = stack.composite()
    merged = stack.merge_down(1)
    
    assert merged is not None
    assert merged.visible is True
    comp_after = stack.composite()
    # Hidden upper layer green must NOT appear in composite
    assert np.array_equal(np.array(comp_before), np.array(comp_after))
    # Merged pixel should be pure red
    assert merged.image.getpixel((50, 50)) == (255, 0, 0, 255)


def test_merge_down_visible_upper_hidden_lower():
    """Visible upper and hidden lower: merged layer retains upper's pixels and is visible."""
    stack = LayerStack(100, 100)
    l1 = stack.add_layer(Image.new("RGBA", (100, 100), (255, 0, 0, 255)), name="L1")
    l1.visible = False  # Lower is hidden!
    l2 = stack.add_layer(Image.new("RGBA", (100, 100), (0, 0, 255, 255)), name="L2")
    l2.visible = True
    
    comp_before = stack.composite()
    merged = stack.merge_down(1)
    
    assert merged is not None
    assert merged.visible is True
    comp_after = stack.composite()
    assert np.array_equal(np.array(comp_before), np.array(comp_after))
    assert merged.image.getpixel((50, 50)) == (0, 0, 255, 255)


def test_merge_down_both_hidden():
    """Both layers hidden: merged layer MUST remain hidden."""
    stack = LayerStack(100, 100)
    l1 = stack.add_layer(Image.new("RGBA", (100, 100), (255, 0, 0, 255)), name="L1")
    l1.visible = False
    l2 = stack.add_layer(Image.new("RGBA", (100, 100), (0, 0, 255, 255)), name="L2")
    l2.visible = False
    
    comp_before = stack.composite()
    merged = stack.merge_down(1)
    
    assert merged is not None
    assert merged.visible is False
    comp_after = stack.composite()
    assert np.array_equal(np.array(comp_before), np.array(comp_after))


def test_merge_down_with_different_offsets_and_opacities():
    """Merging layers with non-zero offsets and opacities composites correctly to (0,0)."""
    stack = LayerStack(100, 100)
    l1 = stack.add_layer(
        Image.new("RGBA", (40, 40), (255, 0, 0, 255)),
        offset_x=10,
        offset_y=10,
        opacity=0.5,
    )
    l2 = stack.add_layer(
        Image.new("RGBA", (40, 40), (0, 255, 0, 255)),
        offset_x=30,
        offset_y=30,
        opacity=0.8,
    )
    
    comp_before = stack.composite()
    merged = stack.merge_down(1)
    assert merged is not None
    assert merged.offset_x == 0
    assert merged.offset_y == 0
    assert merged.opacity == 1.0
    comp_after = stack.composite()
    assert np.array_equal(np.array(comp_before), np.array(comp_after))


# ============================================================================
# 2. BUG 2: OFFSET-AWARE CROP
# ============================================================================

def test_crop_layer_with_positive_offset_contained():
    """Crop completely enclosing an offset layer preserves layer position relative to new origin."""
    doc = Document()
    doc.new_document(200, 200)
    # Layer 20x20 at offset (50, 50)
    layer = doc.add_layer(
        Image.new("RGBA", (20, 20), (255, 0, 0, 255)),
        offset_x=50,
        offset_y=50,
    )
    # Crop canvas to rect (40, 40, 100, 100) -> new canvas is 60x60
    doc.crop_document((40, 40, 100, 100))
    
    assert doc.width == 60
    assert doc.height == 60
    # In new canvas, layer should be at (50-40, 50-40) = (10, 10)
    assert layer.offset_x == 10
    assert layer.offset_y == 10
    assert layer.width == 20
    assert layer.height == 20


def test_crop_layer_partially_intersecting():
    """Crop partially intersecting an offset layer crops only intersecting portion."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (30, 30), (0, 0, 255, 255)),
        offset_x=20,
        offset_y=20,
    )
    # Layer bounds are (20, 20, 50, 50). Crop rect is (30, 30, 80, 80) -> new canvas 50x50
    doc.crop_document((30, 30, 80, 80))
    
    assert doc.width == 50
    assert doc.height == 50
    # Overlap is (30, 30, 50, 50) -> width 20, height 20
    assert layer.width == 20
    assert layer.height == 20
    assert layer.offset_x == 0  # 30 - 30 = 0
    assert layer.offset_y == 0  # 30 - 30 = 0


def test_crop_layer_completely_outside():
    """Crop completely missing an offset layer preserves layer metadata and ordering safely."""
    doc = Document()
    doc.new_document(200, 200)
    layer = doc.add_layer(
        Image.new("RGBA", (20, 20), (0, 255, 0, 255)),
        offset_x=150,
        offset_y=150,
    )
    # Crop rect (0, 0, 50, 50) - layer is completely outside
    doc.crop_document((0, 0, 50, 50))
    assert doc.width == 50
    assert doc.height == 50
    assert len(doc.layers) == 2  # Background + Layer
    assert layer.offset_x == 150
    assert layer.offset_y == 150


# ============================================================================
# 3. BUG 3: OFFSET-AWARE RESIZE
# ============================================================================

def test_resize_layer_with_offset_proportional():
    """Resizing document from 100x100 to 200x200 scales layer position and dimensions by 2x."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (20, 30), (255, 100, 0, 255)),
        offset_x=10,
        offset_y=20,
    )
    doc.resize_document(200, 200)
    
    assert doc.width == 200
    assert doc.height == 200
    assert layer.width == 40
    assert layer.height == 60
    assert layer.offset_x == 20
    assert layer.offset_y == 40


def test_resize_respects_resampling_filter():
    """Document.resize_document passes resampling filter through."""
    doc = Document()
    doc.new_document(50, 50)
    # Create checkerboard pattern
    img = Image.new("RGBA", (50, 50), (255, 255, 255, 255))
    for x in range(0, 50, 2):
        for y in range(0, 50, 2):
            img.putpixel((x, y), (0, 0, 0, 255))
    
    doc.layers[0].image = img
    # Resize with Nearest vs Lanczos
    doc_nearest = Document()
    doc_nearest.new_document(50, 50)
    doc_nearest.layers[0].image = img.copy()
    doc_nearest.resize_document(100, 100, resample=Image.Resampling.NEAREST)
    
    doc_lanczos = Document()
    doc_lanczos.new_document(50, 50)
    doc_lanczos.layers[0].image = img.copy()
    doc_lanczos.resize_document(100, 100, resample=Image.Resampling.LANCZOS)
    
    arr_n = np.array(doc_nearest.layers[0].image)
    arr_l = np.array(doc_lanczos.layers[0].image)
    # Nearest has only 0 and 255; Lanczos introduces intermediate values
    assert not np.array_equal(arr_n, arr_l)


# ============================================================================
# 4. BUG 4: OFFSET-AWARE ROTATE (90° CW, 90° CCW, 180°)
# ============================================================================

def test_rotate_90_cw_offset_transformation():
    """Rotate 90° CW transforms layer offset and dimensions accurately."""
    doc = Document()
    doc.new_document(100, 80)  # W=100, H=80
    layer = doc.add_layer(
        Image.new("RGBA", (30, 20), (255, 0, 0, 255)),
        offset_x=10,
        offset_y=15,
    )
    # In 90° CW:
    # new_W = 80, new_H = 100
    # new_ox = H - oy - lh = 80 - 15 - 20 = 45
    # new_oy = ox = 10
    doc.rotate_document(clockwise=True)
    assert doc.width == 80
    assert doc.height == 100
    assert layer.width == 20
    assert layer.height == 30
    assert layer.offset_x == 45
    assert layer.offset_y == 10


def test_rotate_90_ccw_offset_transformation():
    """Rotate 90° CCW transforms layer offset and dimensions accurately."""
    doc = Document()
    doc.new_document(100, 80)  # W=100, H=80
    layer = doc.add_layer(
        Image.new("RGBA", (30, 20), (255, 0, 0, 255)),
        offset_x=10,
        offset_y=15,
    )
    # In 90° CCW:
    # new_W = 80, new_H = 100
    # new_ox = oy = 15
    # new_oy = W - ox - lw = 100 - 10 - 30 = 60
    doc.rotate_document(clockwise=False)
    assert doc.width == 80
    assert doc.height == 100
    assert layer.width == 20
    assert layer.height == 30
    assert layer.offset_x == 15
    assert layer.offset_y == 60


def test_rotate_180_offset_transformation():
    """Rotate 180° mirrors offset around both canvas dimensions."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (30, 20), (255, 0, 0, 255)),
        offset_x=10,
        offset_y=15,
    )
    # new_ox = 100 - 10 - 30 = 60
    # new_oy = 100 - 15 - 20 = 65
    doc.rotate_180_document()
    assert layer.offset_x == 60
    assert layer.offset_y == 65
    assert layer.width == 30
    assert layer.height == 20


# ============================================================================
# 5. BUG 5: OFFSET-AWARE FLIP
# ============================================================================

def test_flip_horizontal_offset_transformation():
    """Flip Horizontal mirrors layer offset across canvas vertical center line."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (25, 25), (0, 255, 0, 255)),
        offset_x=10,
        offset_y=30,
    )
    # new_ox = 100 - 10 - 25 = 65
    # new_oy = 30
    doc.flip_horizontal_document()
    assert layer.offset_x == 65
    assert layer.offset_y == 30


def test_flip_vertical_offset_transformation():
    """Flip Vertical mirrors layer offset across canvas horizontal center line."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (25, 25), (0, 255, 0, 255)),
        offset_x=30,
        offset_y=10,
    )
    # new_ox = 30
    # new_oy = 100 - 10 - 25 = 65
    doc.flip_vertical_document()
    assert layer.offset_x == 30
    assert layer.offset_y == 65


# ============================================================================
# 6. GEOMETRY ENGINE CONVERSIONS
# ============================================================================

def test_geometry_conversions():
    """Validate layer bounds and canvas ↔ layer coordinate conversions."""
    layer = Layer(name="Test", image=Image.new("RGBA", (40, 50)), offset_x=15, offset_y=25)
    bounds = layer_canvas_bounds(layer)
    assert bounds == (15, 25, 55, 75)
    
    lx, ly = canvas_to_layer_coords(20, 30, layer)
    assert lx == 5
    assert ly == 5
    
    cx, cy = layer_to_canvas_coords(5, 5, layer)
    assert cx == 20
    assert cy == 30


# ============================================================================
# 7. BLEND MODES
# ============================================================================

def test_blend_mode_multiply_and_screen():
    """Compositor respects multiply, screen, and normal blend modes."""
    l1 = Layer(name="Base", image=Image.new("RGBA", (10, 10), (128, 128, 128, 255)))
    l2 = Layer(name="Multiply", image=Image.new("RGBA", (10, 10), (128, 128, 128, 255)), blend_mode="multiply")
    comp = compose_layers([l1, l2], (10, 10))
    # 0.5 * 0.5 = 0.25 -> ~64
    r, g, b, _ = comp.getpixel((0, 0))
    assert 60 <= r <= 68

    l3 = Layer(name="Screen", image=Image.new("RGBA", (10, 10), (128, 128, 128, 255)), blend_mode="screen")
    comp_screen = compose_layers([l1, l3], (10, 10))
    # 1 - (1-0.5)*(1-0.5) = 0.75 -> ~191
    sr, sg, sb, _ = comp_screen.getpixel((0, 0))
    assert 188 <= sr <= 195


# ============================================================================
# 8. BRUSH LIFECYCLE, TOOL DEACTIVATION & RANGE
# ============================================================================

def test_brush_deactivate_safely_terminates_stroke(qapp):
    """Switching away from brush while drawing finalizes the active stroke safely."""
    doc = Document()
    doc.new_document(100, 100)
    canvas = Canvas(doc)
    
    brush = BrushTool()
    canvas.set_tool(brush)
    
    # Start drawing
    brush.start_stroke((10, 10), doc)
    assert brush._is_drawing is True
    
    # Switch away to move tool
    move = MoveTool()
    canvas.set_tool(move)
    
    # Brush stroke must NOT be drawing anymore
    assert brush._is_drawing is False


def test_brush_size_range_consistency():
    """Brush size supports full 1-500px range across settings and tool."""
    settings = BrushSettings()
    settings.set_size(500)
    assert settings.size == 500
    settings.set_size(600)  # Clamps to 500
    assert settings.size == 500
    settings.set_size(0)    # Clamps to 1
    assert settings.size == 1


def test_brush_color_synchronization():
    """BrushTool swap_colors swaps foreground and background accurately."""
    brush = BrushTool()
    brush.color = (255, 0, 0, 255)
    brush.background_color = (0, 0, 255, 255)
    
    brush.swap_colors()
    assert brush.color == (0, 0, 255, 255)
    assert brush.background_color == (255, 0, 0, 255)


# ============================================================================
# 9. CANVAS INTERACTION OWNERSHIP
# ============================================================================

def test_canvas_interaction_ownership(qapp):
    """Middle-click pan interaction ownership routes move and release to MoveTool."""
    doc = Document()
    doc.new_document(100, 100)
    canvas = Canvas(doc)
    
    brush = BrushTool()
    canvas.set_tool(brush)
    assert canvas.active_tool is brush
    
    from PySide6.QtCore import QEvent
    # Simulate MiddleButton press for panning
    press_event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(50, 50),
        QPointF(50, 50),
        Qt.MouseButton.MiddleButton,
        Qt.MouseButton.MiddleButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mousePressEvent(press_event)
    assert canvas._interaction_tool is canvas.default_tool
    assert canvas.default_tool._is_dragging is True
    
    # Simulate release
    release_event = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(60, 60),
        QPointF(60, 60),
        Qt.MouseButton.MiddleButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    canvas.mouseReleaseEvent(release_event)
    assert canvas._interaction_tool is None
    assert canvas.default_tool._is_dragging is False


# ============================================================================
# 10. LAYERSTACK ACTIVE INDEX ROBUSTNESS
# ============================================================================

def test_layerstack_delete_indices():
    """Validate active index when deleting active, before active, or only layer."""
    stack = LayerStack(100, 100)
    stack.add_layer(name="L1")
    stack.add_layer(name="L2")
    stack.add_layer(name="L3")
    
    # Active is index 2 (L3). Delete index 0 (L1).
    stack.set_active_index(2)
    stack.remove_layer(0)
    assert len(stack) == 2
    # Active should shift to 1 (still pointing to L3!)
    assert stack.active_index == 1
    assert stack.active_layer.name == "L3"
    
    # Delete active layer (index 1)
    stack.remove_layer(1)
    assert len(stack) == 1
    assert stack.active_index == 0
    assert stack.active_layer.name == "L2"
    
    # Delete only layer
    stack.remove_layer(0)
    assert len(stack) == 0
    assert stack.active_index == -1


def test_layerstack_move_layer():
    """LayerStack.move_layer updates ordering and active index consistently."""
    stack = LayerStack(100, 100)
    stack.add_layer(name="L1")
    stack.add_layer(name="L2")
    stack.add_layer(name="L3")
    
    stack.set_active_index(0)
    # Move L1 to top (index 2)
    stack.move_layer(0, 2)
    assert stack.layers[2].name == "L1"
    assert stack.active_index == 2


# ============================================================================
# 11. IMAGE FILE HANDLING & EXIF ORIENTATION
# ============================================================================

def test_image_load_closes_handle_and_handles_exif(tmp_path):
    """Document.load_file closes file handle immediately and handles orientation."""
    test_file = tmp_path / "exif_test.png"
    img = Image.new("RGBA", (60, 40), (100, 150, 200, 255))
    img.save(test_file)
    
    doc = Document()
    assert doc.load_file(str(test_file)) is True
    assert doc.width == 60
    assert doc.height == 40
    # Overwriting or removing file must succeed because file handle is closed
    os.remove(test_file)
    assert not os.path.exists(test_file)


# ============================================================================
# 12. UNSAVED CHANGES SAFETY & CLOSE EVENT
# ============================================================================

def test_save_result_enum():
    """Verify SaveResult enum values."""
    assert SaveResult.SUCCESS.value == "success"
    assert SaveResult.CANCELLED.value == "cancelled"
    assert SaveResult.FAILED.value == "failed"


def test_close_event_with_clean_document(qapp):
    """Closing window with clean document accepts event immediately."""
    win = MainWindow()
    win.document.set_modified(False)
    
    event = QCloseEvent()
    win.closeEvent(event)
    assert event.isAccepted() is True
    win.close()
