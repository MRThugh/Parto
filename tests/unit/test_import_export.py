# tests/unit/test_import_export.py
"""
Unit Tests — Image Import, Export & File Format Pipeline
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import pytest
from PIL import Image
from parto.image.export import save_image_file
from parto.editor.document import Document


def test_export_formats_png_jpeg_webp_bmp_tiff(tmp_path):
    """Verify exporting an RGBA image across all claimed supported formats."""
    img = Image.new("RGBA", (32, 32), (255, 128, 64, 255))

    formats = [
        ("test.png", "PNG"),
        ("test.jpg", "JPEG"),
        ("test.webp", "WEBP"),
        ("test.bmp", "BMP"),
        ("test.tiff", "TIFF"),
    ]

    for fname, fmt in formats:
        target = str(tmp_path / fname)
        success, err = save_image_file(img, target)
        assert success is True, f"Failed saving {fmt}: {err}"
        assert os.path.exists(target)
        assert os.path.getsize(target) > 0

        # Verify Pillow decodes the saved file
        with Image.open(target) as loaded:
            assert loaded.size == (32, 32)


def test_export_jpeg_safe_matte_compositing(tmp_path):
    """
    Verify transparent RGBA pixels are composited onto white matte when saving to JPEG,
    avoiding black artifacts or unhandled exceptions.
    """
    # 50% semi-transparent Red over empty canvas
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    target = str(tmp_path / "matte.jpg")

    success, err = save_image_file(img, target, matte_color=(255, 255, 255))
    assert success is True
    assert os.path.exists(target)

    with Image.open(target) as loaded:
        assert loaded.mode == "RGB"
        # Over white matte, 50% Red yields Pink: (255, ~127, ~127)
        px = loaded.getpixel((0, 0))
        assert px[0] > 200
        assert abs(px[1] - 128) < 10
        assert abs(px[2] - 128) < 10


def test_export_invalid_directory_handling():
    """Verify export fails gracefully when given an invalid filesystem path or None image."""
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 255))
    invalid_path = "/dev/null/cannot_write.png"
    success, err = save_image_file(img, invalid_path)
    assert success is False
    assert err is not None

    # None image
    none_success, none_err = save_image_file(None, "dummy.png")
    assert none_success is False
    assert none_err == "No image to save"


def test_document_load_missing_file_handling():
    """Verify Document.load_file handles missing files cleanly without crashing."""
    doc = Document()
    result = doc.load_file("this_file_definitely_does_not_exist_404.png")
    assert result is False
    assert doc.has_image is False

    with pytest.raises(FileNotFoundError):
        doc.load_file("this_file_definitely_does_not_exist_404.png", raise_on_error=True)


def test_document_load_corrupt_file_handling(tmp_path):
    """Verify Document.load_file handles corrupt headers cleanly."""
    corrupt = tmp_path / "broken.png"
    with open(corrupt, "w") as f:
        f.write("Not a real image file content")

    doc = Document()
    result = doc.load_file(str(corrupt))
    assert result is False
    assert doc.has_image is False
