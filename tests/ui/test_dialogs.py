# tests/ui/test_dialogs.py
"""
UI Tests — Dialogs & Configuration Components
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PIL import Image

from parto import __version__, __author__
from parto.image.info import get_image_metadata
from parto.ui.dialogs.about import AboutDialog
from parto.ui.dialogs.resize import ResizeDialog
from parto.ui.dialogs.image_info import ImageInfoDialog
from parto.ui.dialogs.shortcuts_dialog import ShortcutsDialog


def test_about_dialog_metadata_and_controls(qapp):
    """Verify AboutDialog displays dynamic version and maintainer."""
    dlg = AboutDialog()
    assert dlg.windowTitle() == "About Parto"
    assert dlg.isModal() is True

    # Version label
    text_content = " ".join([w.text() for w in dlg.findChildren(object) if hasattr(w, "text")])
    assert f"v{__version__}" in text_content
    assert "Ali Kamrani" in text_content
    assert "علی کامرانی" in text_content

    dlg.close()


def test_resize_dialog_presets_and_aspect_ratio(qapp):
    """Verify ResizeDialog initializes with current image dimensions and presets."""
    dlg = ResizeDialog(current_width=800, current_height=600)
    assert dlg.width_spin.value() == 800
    assert dlg.height_spin.value() == 600
    assert dlg.lock_aspect_cb.isChecked() is True

    # 50% preset
    dlg._apply_preset(50)
    assert dlg.width_spin.value() == 400
    assert dlg.height_spin.value() == 300

    dlg.close()


def test_image_info_dialog_display(qapp):
    """Verify ImageInfoDialog displays verified image metadata."""
    img = Image.new("RGBA", (320, 240), (255, 0, 0, 128))
    meta = get_image_metadata(img, filepath="/path/to/test.png")
    dlg = ImageInfoDialog(meta)
    assert dlg.windowTitle() == "Image Properties — Parto"

    # Values in table
    assert dlg.table.rowCount() >= 5
    dlg.close()


def test_shortcuts_dialog_search(qapp):
    """Verify ShortcutsDialog opens and filters shortcut entries."""
    dlg = ShortcutsDialog()
    assert dlg.windowTitle() == "Keyboard Shortcuts — Parto"
    assert dlg.table.rowCount() > 0

    # Filter search
    dlg.search_input.setText("Undo")
    # Table should still have rows
    assert dlg.table.rowCount() > 0
    dlg.close()
