# test_parto.py
"""
Parto 0.2.0 - 30-Point Comprehensive Test Suite
Author: Ali Kamrani (MRThugh)
Version: 0.2.0
"""

import os
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from editor import EditorEngine
from image import get_image_info, pil_to_qpixmap
from window import MainWindow, ResizeDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_images(tmp_path):
    """Generate various test image fixtures."""
    # 1. RGB PNG
    rgb_png = tmp_path / "test_rgb.png"
    img_rgb = Image.new("RGB", (200, 100), color=(255, 0, 0))
    img_rgb.save(rgb_png, "PNG")

    # 2. RGBA PNG (with transparency)
    rgba_png = tmp_path / "test_rgba.png"
    img_rgba = Image.new("RGBA", (150, 150), color=(0, 255, 0, 128))
    img_rgba.save(rgba_png, "PNG")

    # 3. JPEG
    jpg_file = tmp_path / "test.jpg"
    img_jpg = Image.new("RGB", (100, 100), color=(0, 0, 255))
    img_jpg.save(jpg_file, "JPEG")

    # 4. WebP
    webp_file = tmp_path / "test.webp"
    img_rgb.save(webp_file, "WEBP")

    # 5. Corrupt file
    corrupt_file = tmp_path / "corrupt.png"
    with open(corrupt_file, "w") as f:
        f.write("Not an image")

    return {
        "rgb_png": str(rgb_png),
        "rgba_png": str(rgba_png),
        "jpg": str(jpg_file),
        "webp": str(webp_file),
        "corrupt": str(corrupt_file),
        "tmp_dir": str(tmp_path),
    }


# Test 1: Application launch with no arguments (displays welcome screen)
def test_app_launch_welcome_screen(qapp):
    win = MainWindow()
    assert win.stack.currentIndex() == 0  # Welcome screen active
    assert win.windowTitle().startswith("Parto")
    win.close()


# Test 2: Application launch and open valid image (shows canvas)
def test_open_valid_image_shows_canvas(qapp, sample_images):
    win = MainWindow()
    win.open_image_by_path(sample_images["rgb_png"])
    assert win.stack.currentIndex() == 1  # Canvas active
    assert win.engine.current_image is not None
    assert win.engine.current_image.size == (200, 100)
    win.close()


# Test 3: Open PNG image
def test_open_png(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    assert engine.current_image.size == (200, 100)
    assert engine.filepath == sample_images["rgb_png"]


# Test 4: Open JPG image
def test_open_jpg(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["jpg"])
    assert engine.current_image.size == (100, 100)


# Test 5: Open WebP image
def test_open_webp(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["webp"])
    assert engine.current_image.size == (200, 100)


# Test 6: Open invalid / corrupt file (graceful error handling)
def test_open_corrupt_file(sample_images):
    engine = EditorEngine()
    with pytest.raises(Exception):
        engine.load_image(sample_images["corrupt"])


# Test 7: Save image
def test_save_image(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_left()
    save_path = os.path.join(sample_images["tmp_dir"], "saved.png")
    engine.save_image(save_path)
    assert os.path.exists(save_path)
    with Image.open(save_path) as saved_img:
        assert saved_img.size == (100, 200)


# Test 8: Save RGBA with transparency to JPEG (converts without crash)
def test_save_rgba_to_jpeg(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgba_png"])
    save_path = os.path.join(sample_images["tmp_dir"], "saved_from_rgba.jpg")
    engine.save_image(save_path, img_format="JPEG")
    assert os.path.exists(save_path)
    with Image.open(save_path) as saved_img:
        assert saved_img.mode == "RGB"


# Test 9: Undo single action
def test_undo_single_action(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    orig_size = engine.current_image.size
    engine.rotate_left()
    assert engine.current_image.size != orig_size
    assert engine.can_undo
    engine.undo()
    assert engine.current_image.size == orig_size


# Test 10: Undo multiple actions up to history limit
def test_undo_multiple_actions(sample_images):
    engine = EditorEngine(max_history=5)
    engine.load_image(sample_images["rgb_png"])
    for _ in range(7):
        engine.rotate_left()
    assert len(engine.undo_stack) <= 5


# Test 11: Redo single action
def test_redo_single_action(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_left()
    rot_size = engine.current_image.size
    engine.undo()
    assert engine.can_redo
    engine.redo()
    assert engine.current_image.size == rot_size


# Test 12: Redo multiple actions
def test_redo_multiple_actions(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_left()
    engine.flip_horizontal()
    engine.undo()
    engine.undo()
    assert len(engine.redo_stack) == 2
    engine.redo()
    engine.redo()
    assert len(engine.redo_stack) == 0


# Test 13: Crop image (valid region)
def test_crop_image(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.crop((10, 10, 60, 50))
    assert engine.current_image.size == (50, 40)


# Test 14: Crop image aspect ratios
def test_crop_aspect_ratios(qapp, sample_images):
    win = MainWindow()
    win.open_image_by_path(sample_images["rgb_png"])
    win.canvas.set_crop_mode(True, aspect_ratio=1.0)
    assert win.canvas.crop_mode is True
    assert win.canvas.crop_aspect_ratio == 1.0
    win.cancel_crop_mode()
    assert win.canvas.crop_mode is False
    win.close()


# Test 15: Resize image with preserved aspect ratio
def test_resize_image_aspect(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.resize(100, 50)
    assert engine.current_image.size == (100, 50)


# Test 16: Resize image dialog calculations
def test_resize_dialog_presets(qapp):
    dlg = ResizeDialog(200, 100)
    dlg.apply_preset(50)
    w, h = dlg.get_dimensions()
    assert w == 100
    assert h == 50
    dlg.close()


# Test 17: Rotate 90 degrees left
def test_rotate_left(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_left()
    assert engine.current_image.size == (100, 200)


# Test 18: Rotate 90 degrees right
def test_rotate_right(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_right()
    assert engine.current_image.size == (100, 200)


# Test 19: Rotate 180 degrees
def test_rotate_180(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_180()
    assert engine.current_image.size == (200, 100)


# Test 20: Flip horizontal
def test_flip_horizontal(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.flip_horizontal()
    assert engine.current_image.size == (200, 100)


# Test 21: Flip vertical
def test_flip_vertical(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.flip_vertical()
    assert engine.current_image.size == (200, 100)


# Test 22: Brightness adjustment preview and apply
def test_brightness_adjustment(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    preview = engine.get_adjusted_preview(brightness=1.5)
    assert preview is not None
    engine.apply_adjustments(brightness=1.5)
    assert engine.can_undo


# Test 23: Contrast adjustment preview and apply
def test_contrast_adjustment(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    preview = engine.get_adjusted_preview(contrast=1.2)
    assert preview is not None
    engine.apply_adjustments(contrast=1.2)
    assert engine.can_undo


# Test 24: Saturation adjustment preview and apply
def test_saturation_adjustment(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    preview = engine.get_adjusted_preview(saturation=0.5)
    assert preview is not None
    engine.apply_adjustments(saturation=0.5)
    assert engine.can_undo


# Test 25: Grayscale filter with alpha preservation
def test_grayscale_filter_alpha(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgba_png"])
    gray = engine.get_filter_preview("grayscale")
    assert gray.mode == "RGBA"
    # Check alpha channel preserved
    assert gray.split()[3].getextrema() == (128, 128)
    engine.apply_filter("grayscale")
    assert engine.can_undo


# Test 26: Sepia filter with alpha preservation
def test_sepia_filter_alpha(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgba_png"])
    sepia = engine.get_filter_preview("sepia")
    assert sepia.mode == "RGBA"
    assert sepia.split()[3].getextrema() == (128, 128)


# Test 27: Invert filter with alpha preservation
def test_invert_filter_alpha(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgba_png"])
    inv = engine.get_filter_preview("invert")
    assert inv.mode == "RGBA"
    assert inv.split()[3].getextrema() == (128, 128)


# Test 28: Before / After preview
def test_before_after_preview(sample_images):
    engine = EditorEngine()
    engine.load_image(sample_images["rgb_png"])
    engine.rotate_left()
    assert engine.original_image.size == (200, 100)
    assert engine.current_image.size == (100, 200)


# Test 29: Image information metadata accuracy
def test_image_info_accuracy(sample_images):
    info = get_image_info(sample_images["rgb_png"])
    assert info["width"] == 200
    assert info["height"] == 100
    assert info["format"] == "PNG"
    assert info["mode"] == "RGB"
    assert info["has_transparency"] is False
    assert "200 × 100 px" in info["dimensions_str"]


# Test 30: Theme toggle
def test_theme_toggle(qapp):
    win = MainWindow()
    assert win.theme_mode == "dark"
    win.toggle_theme()
    assert win.theme_mode == "light"
    win.toggle_theme()
    assert win.theme_mode == "dark"
    win.close()
