# tests/integration/test_layer_workflows.py
"""
Integration Tests — Multi-Layer Workflows
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import pytest
from PIL import Image

from parto.editor.document import Document
from parto.image.layers import LayerStack


def test_full_multilayer_creation_and_export_workflow(tmp_path):
    """
    Simulate complete user workflow:
    1. Create new document
    2. Add background color layer
    3. Add transparent graphic layer
    4. Adjust graphic opacity
    5. Reorder layers
    6. Render composite and export to PNG
    """
    doc = Document()
    doc.new_document(80, 80, fill_color=(255, 255, 255, 255))
    assert len(doc.layers) == 1

    # Add red square in center
    red_box = Image.new("RGBA", (40, 40), (255, 0, 0, 255))
    l_red = doc.add_layer(red_box, name="RedBox", offset_x=20, offset_y=20)
    assert len(doc.layers) == 2

    # Add blue overlay at 50% opacity
    blue_box = Image.new("RGBA", (40, 40), (0, 0, 255, 255))
    l_blue = doc.add_layer(blue_box, name="BlueBox", offset_x=30, offset_y=30)
    l_blue.set_opacity(0.5)
    assert len(doc.layers) == 3

    # Composite canvas
    comp = doc.get_composite()
    assert comp.size == (80, 80)
    assert comp.mode == "RGBA"

    # Export to disk
    out_file = str(tmp_path / "multilayer_export.png")
    saved, err = doc.save_file(out_file)
    assert saved is True
    assert err is None
    assert os.path.exists(out_file)

    # Inspect decoded output
    with Image.open(out_file) as loaded:
        assert loaded.size == (80, 80)
        # Background is white (0, 0)
        assert loaded.getpixel((0, 0)) == (255, 255, 255, 255)
        # Red box only at (25, 25)
        assert loaded.getpixel((25, 25)) == (255, 0, 0, 255)


def test_layer_duplicate_and_merge_workflow():
    """
    Workflow:
    1. Create document
    2. Add layer and duplicate it
    3. Modify duplicate offset
    4. Merge duplicate down
    5. Verify single merged layer preserves content
    """
    doc = Document()
    doc.new_document(40, 40, (0, 0, 0, 255))

    # Add foreground layer
    l1 = doc.add_layer(Image.new("RGBA", (20, 20), (255, 255, 0, 255)), name="YellowBox")
    assert len(doc.layers) == 2

    # Duplicate
    dup = doc.duplicate_active_layer()
    assert dup is not None
    assert len(doc.layers) == 3
    assert dup.name == "YellowBox (Copy)"

    # Shift duplicate
    dup.offset_x = 10
    dup.offset_y = 10

    # Merge down duplicate into yellow box
    assert doc.merge_down() is True
    assert len(doc.layers) == 2
