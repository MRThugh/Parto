# tests/integration/test_save_reload.py
"""
Integration Tests — Image Save & Reload Roundtrip Integrity
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import pytest
from PIL import Image

from parto.editor.document import Document


@pytest.mark.parametrize(
    "filename, fmt, original_mode, tolerance",
    [
        ("roundtrip.png", "PNG", "RGBA", 0),
        ("roundtrip.webp", "WEBP", "RGBA", 5),
        ("roundtrip.bmp", "BMP", "RGB", 0),
        ("roundtrip.tiff", "TIFF", "RGBA", 0),
    ],
)
def test_document_save_and_reload_roundtrip(tmp_path, filename, fmt, original_mode, tolerance):
    """
    Verify complete save and reload roundtrip preserves pixel integrity
    and correctly resets modified state.
    """
    doc1 = Document()
    doc1.new_document(30, 20, fill_color=(40, 80, 160, 255))
    assert doc1.modified is False

    # Draw distinguishing block
    doc1.active_layer.image.paste(Image.new("RGBA", (8, 8), (255, 200, 100, 255)), (4, 4))
    doc1.set_modified(True)
    assert doc1.modified is True

    # Save to disk
    target_path = str(tmp_path / filename)
    success, err = doc1.save_file(target_path)
    assert success is True
    assert err is None
    assert doc1.modified is False

    # Reload into a completely separate document instance
    doc2 = Document()
    loaded = doc2.load_file(target_path)
    assert loaded is True
    assert doc2.width == 30
    assert doc2.height == 20
    assert doc2.modified is False

    # Verify central pixel inside block at (8, 8)
    px = doc2.get_composite().getpixel((8, 8))
    assert abs(px[0] - 255) <= tolerance
    assert abs(px[1] - 200) <= tolerance
    assert abs(px[2] - 100) <= tolerance
