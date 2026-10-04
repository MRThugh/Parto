# tests/integration/test_editing_workflows.py
"""
Integration Tests — Image Editing Workflows
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import pytest
from PIL import Image

from parto.editor.document import Document
from parto.editor.engine import EditorEngine


def test_editing_workflow_adjust_transform_undo_export(tmp_path):
    """
    End-to-end editing workflow:
    1. Initialize document with image
    2. Adjust brightness
    3. Rotate 90 CW
    4. Crop region
    5. Undo crop
    6. Redo crop
    7. Save output
    """
    doc = Document()
    doc.new_document(100, 100, fill_color=(128, 128, 128, 255))
    engine = EditorEngine(document=doc)

    # 1. Adjust Brightness
    engine.apply_adjustments(brightness=1.3)
    comp1 = doc.get_composite()
    assert comp1.getpixel((0, 0))[0] > 128

    # 2. Rotate
    engine.rotate_right()
    assert doc.width == 100
    assert doc.height == 100

    # 3. Crop to (10, 10, 60, 60) -> 50x50
    engine.crop((10, 10, 60, 60))
    assert doc.width == 50
    assert doc.height == 50

    # 4. Undo Crop
    assert doc.undo() is True
    assert doc.width == 100
    assert doc.height == 100

    # 5. Redo Crop
    assert doc.redo() is True
    assert doc.width == 50
    assert doc.height == 50

    # 6. Export
    out_file = str(tmp_path / "edited_output.webp")
    saved, err = doc.save_file(out_file)
    assert saved is True
    assert os.path.exists(out_file)

    with Image.open(out_file) as loaded:
        assert loaded.size == (50, 50)
