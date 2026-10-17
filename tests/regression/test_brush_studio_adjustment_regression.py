# tests/regression/test_brush_studio_adjustment_regression.py
"""
Parto — Comprehensive Regression Suite for:
Bug A: Brush Studio Integration with Brush Tool Workflow (no standalone toggle)
Bug B: Adjustment Processing & Canvas Integrity (no blank canvas / preserved pixels)

Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import pytest
from PIL import Image
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QApplication

from parto.ui.main_window import MainWindow
from parto.ui.panels.adjustments import AdjustmentDock
from parto.actions.registry import get_action_registry
from parto.shortcuts.manager import get_shortcut_manager
from parto.commands.filters import ColorAdjustmentsCommand
from parto.commands.brush import PaintStrokeCommand


# ============================================================================
# BUG A REGRESSION TESTS: Brush Studio as Integral Part of Brush Tool Workflow
# ============================================================================

def test_bug_a_no_standalone_brush_studio_toolbar_button(qapp):
    """
    Verify that there is NO dedicated Brush Studio toggle or button on the main toolbar.
    The toolbar must only contain tools, file ops, undo/redo, zoom, transforms,
    and side docks for Layers (F7) and Adjustments (F8).
    """
    win = MainWindow()
    win.show()
    qapp.processEvents()

    # Toolbar must not possess act_brush_panel attribute
    assert not hasattr(win.toolbar, "act_brush_panel")

    # Toolbar action texts and data must not contain brush_panel or standalone brush studio toggle
    for action in win.toolbar.actions():
        act_text = action.text().lower()
        act_data = action.data()
        assert act_data != "brush_panel", f"Found standalone brush_panel action in toolbar: {act_text}"
        # If text mentions Brush, it must be the Brush Tool, NOT Brush Studio panel toggle
        if "brush" in act_text and not action.isSeparator():
            assert "tool" in act_text, f"Unexpected standalone brush action on toolbar: {act_text}"

    win.close()


def test_bug_a_no_standalone_brush_studio_menu_toggle(qapp):
    """
    Verify that neither the global View menu nor the contextual Brush menu
    exposes a standalone Brush Studio toggle action (act_brush_studio or F9 toggle).
    """
    win = MainWindow()
    win.show()
    qapp.processEvents()

    # 1. Window must not have act_brush_studio
    assert not hasattr(win, "act_brush_studio")

    # 2. View menu must not contain Brush Studio toggle
    view_menu = None
    for action in win.menuBar().actions():
        menu = action.menu()
        if menu and "View" in menu.title().replace("&", ""):
            view_menu = menu
            break
    assert view_menu is not None
    view_texts = [a.text().replace("&", "").strip() for a in view_menu.actions()]
    assert "Brush Studio" not in view_texts

    # 3. Contextual Brush menu must not contain a standalone Brush Studio toggle action
    brush_menu = win.brush_menu
    assert brush_menu is not None
    brush_texts = [a.text().replace("&", "").strip() for a in brush_menu.actions()]
    assert "Brush Studio" not in brush_texts

    win.close()


def test_bug_a_no_stale_action_registry_or_shortcut_entries(qapp):
    """
    Verify ActionRegistry and ShortcutManager do not expose removed standalone toggles:
    - 'brush.toggle_studio' is NOT registered
    - 'view.toggle_brush' is NOT registered
    - 'brush.activate' remains registered as the single authoritative Brush entry point
    """
    reg = get_action_registry()
    assert "brush.toggle_studio" not in reg
    assert "view.toggle_brush" not in reg
    assert "brush.activate" in reg

    act_brush = reg.get("brush.activate")
    assert act_brush is not None
    assert act_brush.default_shortcut == "B"

    # Presets, properties, reset settings, cycle mode remain registered
    assert "brush.focus_presets" in reg
    assert "brush.focus_properties" in reg
    assert "brush.reset_settings" in reg
    assert "brush.cycle_mode" in reg


def test_bug_a_brush_tool_auto_reveals_and_hides_dock(qapp):
    """
    Verify:
    1. Initial default state (Move tool): Brush dock and brush bar are hidden.
    2. Activating Brush tool automatically reveals and raises Brush dock and brush bar.
    3. Switching to Move, Crop, or Eyedropper automatically hides Brush dock.
    4. Switching back to Brush tool restores Brush dock and brush bar.
    """
    win = MainWindow()
    win.document.new_document(300, 300)
    win.show()
    qapp.processEvents()

    # 1. Default (Move tool active)
    assert win.tb_tool_move.isChecked() is True
    assert win.brush_dock.isVisible() is False
    assert win.brush_bar.isVisible() is False

    # 2. Activate Brush tool (B)
    win.action_tool_brush()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_dock.isVisible() is True
    assert win.brush_bar.isVisible() is True

    # 3. Switch to Move (V)
    win.action_tool_move()
    qapp.processEvents()
    assert win.tb_tool_move.isChecked() is True
    assert win.brush_dock.isVisible() is False
    assert win.brush_bar.isVisible() is False

    # 4. Switch to Crop (C)
    win.action_tool_crop()
    qapp.processEvents()
    assert win.tb_tool_crop.isChecked() is True
    assert win.brush_dock.isVisible() is False
    assert win.brush_bar.isVisible() is False
    assert win.crop_bar.isVisible() is True

    # 5. Switch to Eyedropper (I)
    win.action_tool_eyedropper()
    qapp.processEvents()
    assert win.tb_tool_eyedropper.isChecked() is True
    assert win.brush_dock.isVisible() is False
    assert win.brush_bar.isVisible() is False

    # 6. Return to Brush (B)
    win.action_tool_brush()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_dock.isVisible() is True
    assert win.brush_bar.isVisible() is True

    win.close()


def test_bug_a_brush_settings_preserved_across_tool_switches(qapp):
    """
    Verify brush settings (size, opacity, hardness, colors, eraser mode)
    are strictly preserved across arbitrary tool switches.
    """
    win = MainWindow()
    win.document.new_document(200, 200)
    win.show()
    qapp.processEvents()

    # Configure custom brush parameters
    win.action_tool_brush()
    qapp.processEvents()
    win.tool_brush.set_size(64)
    win.tool_brush.set_opacity(0.72)
    win.tool_brush.set_hardness(0.35)
    win.tool_brush.set_color((210, 45, 90, 255))
    win.tool_brush.set_background_color((10, 20, 30, 255))
    win.tool_brush.set_is_eraser(True)

    # Switch away to other tools
    win.action_tool_move()
    qapp.processEvents()
    win.action_tool_crop()
    qapp.processEvents()
    win.action_tool_eyedropper()
    qapp.processEvents()

    # Return to brush
    win.action_tool_brush()
    qapp.processEvents()

    assert win.tool_brush.size == 64
    assert abs(win.tool_brush.opacity - 0.72) < 1e-3
    assert abs(win.tool_brush.hardness - 0.35) < 1e-3
    assert win.tool_brush.color == (210, 45, 90, 255)
    assert win.tool_brush.background_color == (10, 20, 30, 255)
    assert win.tool_brush.is_eraser is True

    win.close()


def test_bug_a_brush_focus_shortcuts_activate_brush_workflow(qapp):
    """
    Verify presets and property focus shortcuts activate the Brush tool
    and focus the respective controls when triggered from non-brush tools.
    """
    win = MainWindow()
    win.document.new_document(200, 200)
    win.show()
    qapp.processEvents()

    # Start on Move tool
    win.action_tool_move()
    qapp.processEvents()
    assert win.brush_dock.isVisible() is False

    # Focus Presets (Ctrl+Shift+B)
    win.action_focus_brush_presets()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_dock.isVisible() is True

    # Switch away to Move
    win.action_tool_move()
    qapp.processEvents()
    assert win.brush_dock.isVisible() is False

    # Focus Properties (Alt+B)
    win.action_focus_brush_properties()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_dock.isVisible() is True

    win.close()


# ============================================================================
# BUG B REGRESSION TESTS: Adjustments Never Turn Document Into Blank Canvas
# ============================================================================

def test_bug_b_adjustment_dock_factor_mapping():
    """
    Verify AdjustmentDock.slider_to_factor mapping:
    - Neutral slider (0) -> factor 1.0 (no distortion)
    - Negative slider (-100) -> factor 0.0
    - Positive slider (+100) -> factor 2.0
    - Intermediate values map linearly around 1.0
    """
    assert AdjustmentDock.slider_to_factor(0) == 1.0
    assert AdjustmentDock.slider_to_factor(100) == 2.0
    assert AdjustmentDock.slider_to_factor(-100) == 0.0
    assert AdjustmentDock.slider_to_factor(50) == 1.5
    assert AdjustmentDock.slider_to_factor(-50) == 0.5

    # Inverse mapping
    assert AdjustmentDock.factor_to_slider(1.0) == 0
    assert AdjustmentDock.factor_to_slider(2.0) == 100
    assert AdjustmentDock.factor_to_slider(0.0) == -100
    assert AdjustmentDock.factor_to_slider(1.5) == 50
    assert AdjustmentDock.factor_to_slider(0.5) == -50


def test_bug_b_painting_then_adjusting_does_not_blank_canvas(qapp):
    """
    CRITICAL WORKFLOW TEST FOR BUG B:
    1. Create a non-empty image (vibrant image with known pixel values).
    2. Paint visible brush strokes using BrushTool.
    3. Verify layer count, active layer, and stroke pixels are intact.
    4. Open Adjustments dock while Brush tool was used.
    5. Change brightness slider; verify preview is a valid adjusted image, NOT blank/black/grey.
    6. Change contrast, saturation, and sharpness; verify preview validity.
    7. Test neutral settings (slider at 0 preserves exact composite pixels).
    8. Test 'Hold to Compare Original' and release.
    9. Apply adjustments; verify ColorAdjustmentsCommand on history stack and modified pixels.
    10. Undo restores exact pre-adjustment pixels (including brush strokes!).
    11. Redo restores adjusted pixels.
    12. Paint another brush stroke after adjustment; canvas continues to function perfectly.
    """
    win = MainWindow()
    win.maybe_save_unsaved_changes = lambda: True

    # 1. Non-empty canvas with vibrant background: Sky Blue (100, 180, 255, 255)
    bg_color = (100, 180, 255, 255)
    img = Image.new("RGBA", (200, 200), bg_color)
    win.document.new_document(200, 200, initial_image=img)
    win.show()
    qapp.processEvents()

    assert win.document.has_image is True
    assert win.document.width == 200
    assert win.document.height == 200
    initial_comp = win.document.get_composite()
    assert initial_comp.getpixel((50, 50)) == bg_color

    # 2. Paint visible red brush strokes using actual BrushTool
    win.action_tool_brush()
    qapp.processEvents()
    brush = win.tool_brush
    brush.set_size(20)
    brush.set_hardness(1.0)
    brush.set_opacity(1.0)
    brush.set_color((255, 0, 0, 255))  # Bright red stroke

    # Paint stroke from (40, 100) to (160, 100)
    brush.start_stroke(QPointF(40, 100), win.document)
    brush.continue_stroke(QPointF(160, 100), win.document)
    committed = brush.end_stroke(win.document)
    assert committed is True
    qapp.processEvents()

    # Verify stroke is present in composite
    post_stroke_comp = win.document.get_composite()
    assert post_stroke_comp is not None
    # Center of stroke must be red
    stroke_pixel = post_stroke_comp.getpixel((100, 100))
    assert stroke_pixel[0] == 255  # Red channel
    assert stroke_pixel[1] < 50   # Green channel low
    assert stroke_pixel[2] < 50   # Blue channel low

    # Background area away from stroke must still be sky blue
    unpainted_pixel = post_stroke_comp.getpixel((20, 20))
    assert unpainted_pixel == bg_color

    # 3. Open Adjustments panel
    win.toggle_adjustments_dock(animate=False)
    qapp.processEvents()
    assert win.adjustments_dock.isVisible() is True
    dock = win.adjustments_dock

    # 4. Neutral settings: emit preview with sliders at 0
    # Must NOT turn image black or grey!
    dock._emit_preview()
    qapp.processEvents()
    assert win.canvas.is_previewing is True
    preview_img = win.document.get_adjusted_preview(1.0, 1.0, 1.0, 1.0)
    assert preview_img is not None
    assert preview_img.getpixel((20, 20)) == bg_color
    assert preview_img.getpixel((100, 100))[0] == 255

    # 5. Brightness adjustment: +30%
    dock.b_slider.setValue(30)
    qapp.processEvents()
    b, c, s, sh = dock._get_factors()
    assert abs(b - 1.3) < 1e-3
    assert abs(c - 1.0) < 1e-3
    assert abs(s - 1.0) < 1e-3
    assert abs(sh - 1.0) < 1e-3

    preview_b = win.document.get_adjusted_preview(b, c, s, sh)
    assert preview_b is not None
    # Sky blue background pixel must be BRIGHTER than original, NOT pitch black or empty
    bright_bg = preview_b.getpixel((20, 20))
    assert bright_bg[0] >= bg_color[0]
    assert bright_bg[1] >= bg_color[1]
    assert bright_bg[2] >= bg_color[2]
    assert bright_bg != (0, 0, 0, 255)
    assert bright_bg != (128, 128, 128, 255)

    # 6. Contrast adjustment: +40%
    dock.b_slider.setValue(0)
    dock.c_slider.setValue(40)
    qapp.processEvents()
    b, c, s, sh = dock._get_factors()
    assert abs(c - 1.4) < 1e-3
    preview_c = win.document.get_adjusted_preview(b, c, s, sh)
    assert preview_c is not None
    assert preview_c.getpixel((20, 20)) != (0, 0, 0, 255)
    assert preview_c.getpixel((100, 100))[0] == 255

    # 7. Saturation adjustment: -50%
    dock.c_slider.setValue(0)
    dock.s_slider.setValue(-50)
    qapp.processEvents()
    b, c, s, sh = dock._get_factors()
    assert abs(s - 0.5) < 1e-3
    preview_s = win.document.get_adjusted_preview(b, c, s, sh)
    assert preview_s is not None
    assert preview_s.getpixel((20, 20)) != (0, 0, 0, 255)

    # 8. Sharpness adjustment: +50%
    dock.s_slider.setValue(0)
    dock.sh_slider.setValue(50)
    qapp.processEvents()
    b, c, s, sh = dock._get_factors()
    assert abs(sh - 1.5) < 1e-3
    preview_sh = win.document.get_adjusted_preview(b, c, s, sh)
    assert preview_sh is not None

    # 9. Multi-slider combination
    dock.b_slider.setValue(20)
    dock.c_slider.setValue(15)
    dock.s_slider.setValue(10)
    dock.sh_slider.setValue(5)
    qapp.processEvents()
    combo_preview = win.document.get_adjusted_preview(*dock._get_factors())
    assert combo_preview is not None
    # Both background and stroke must be visible and valid
    assert combo_preview.getpixel((20, 20)) != (0, 0, 0, 255)
    assert combo_preview.getpixel((100, 100))[0] > 200

    # 10. Compare Original
    dock._on_compare_pressed()
    qapp.processEvents()
    # While comparing, canvas must show unadjusted composite
    assert win.canvas.is_previewing is False

    dock._on_compare_released()
    qapp.processEvents()
    # Releasing restores preview
    assert win.canvas.is_previewing is True

    # 11. Reset All
    dock.reset_all()
    qapp.processEvents()
    assert dock.b_slider.value() == 0
    assert dock.c_slider.value() == 0
    assert dock.s_slider.value() == 0
    assert dock.sh_slider.value() == 0
    assert win.canvas.is_previewing is False

    # 12. Apply adjustment (+25% brightness)
    pre_apply_bytes = win.document.active_layer.image.tobytes()
    dock.b_slider.setValue(25)
    qapp.processEvents()
    dock._on_apply()
    qapp.processEvents()

    # Applied: canvas must no longer be in preview mode
    assert win.canvas.is_previewing is False
    # Sliders must have reset to 0%
    assert dock.b_slider.value() == 0
    assert dock.c_slider.value() == 0
    # Active layer bytes must have changed
    post_apply_bytes = win.document.active_layer.image.tobytes()
    assert post_apply_bytes != pre_apply_bytes

    # History entry must be ColorAdjustmentsCommand
    assert win.document.history.can_undo is True
    top_cmd = win.document.history.undo_stack[-1]
    assert isinstance(top_cmd, ColorAdjustmentsCommand)

    # 13. Undo: exact pixel restoration of pre-adjustment state
    assert win.document.undo() is True
    assert win.document.active_layer.image.tobytes() == pre_apply_bytes
    # Stroke is still present!
    assert win.document.get_composite().getpixel((100, 100))[0] == 255

    # 14. Redo: exact restoration of applied adjustment
    assert win.document.redo() is True
    assert win.document.active_layer.image.tobytes() == post_apply_bytes

    # 15. Paint again after adjustment: verify canvas and brush pipeline continue working
    win.action_tool_brush()
    qapp.processEvents()
    brush.set_color((0, 255, 0, 255))  # Green stroke
    brush.start_stroke(QPointF(100, 40), win.document)
    brush.continue_stroke(QPointF(100, 160), win.document)
    brush.end_stroke(win.document)
    qapp.processEvents()

    # Both red and green strokes must exist in the final composite
    final_comp = win.document.get_composite()
    green_pixel = final_comp.getpixel((100, 50))
    assert green_pixel[1] == 255  # Green channel active

    win.document.set_modified(False)
    win.close()


def test_bug_b_multilayer_adjustment_preserves_underlying_layers(qapp):
    """
    Verify adjustments targeting a transparent upper layer with brush strokes
    do NOT cause the opaque background layer beneath it to disappear or blank out.
    """
    win = MainWindow()
    win.maybe_save_unsaved_changes = lambda: True

    # Layer 0: Solid blue background (0, 100, 200, 255)
    bg_img = Image.new("RGBA", (150, 150), (0, 100, 200, 255))
    win.document.new_document(150, 150, initial_image=bg_img)
    win.show()
    qapp.processEvents()

    # Layer 1: Transparent layer with a yellow brush stroke
    paint_layer = win.document.add_layer(name="Paint Layer")
    assert win.document.active_layer is paint_layer
    assert len(win.document.layers) == 2

    # Draw yellow stroke on active Layer 1
    for x in range(40, 80):
        for y in range(40, 80):
            paint_layer.image.putpixel((x, y), (255, 255, 0, 255))
    win.document.invalidate_composite()

    composite_before = win.document.get_composite()
    assert composite_before.getpixel((10, 10)) == (0, 100, 200, 255)  # Bg intact
    assert composite_before.getpixel((50, 50)) == (255, 255, 0, 255)  # Stroke intact

    # Preview adjustment on Layer 1: +50% brightness
    preview = win.document.get_adjusted_preview(brightness=1.5, contrast=1.0, saturation=1.0, sharpness=1.0)
    assert preview is not None

    # CRITICAL INVARIANT: The non-target background layer (0, 100, 200) MUST NOT DISAPPEAR!
    assert preview.getpixel((10, 10)) == (0, 100, 200, 255)
    # The yellow stroke on Layer 1 is brightened
    assert preview.getpixel((50, 50))[0] == 255
    assert preview.getpixel((50, 50))[1] == 255

    # Switch active layer to Background (Layer 0) and adjust it
    win.document.set_active_layer_index(0)
    preview_bg = win.document.get_adjusted_preview(brightness=1.3, contrast=1.0, saturation=1.0, sharpness=1.0)
    assert preview_bg is not None

    # Background must be brightened
    bg_adj_pixel = preview_bg.getpixel((10, 10))
    assert bg_adj_pixel[2] > 200  # Blue channel increased from 200
    # Yellow stroke on Layer 1 must still be visible on top!
    stroke_top_pixel = preview_bg.getpixel((50, 50))
    assert stroke_top_pixel == (255, 255, 0, 255)

    win.document.set_modified(False)
    win.close()
