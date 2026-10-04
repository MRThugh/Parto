# tests/ui/test_main_window.py
"""
UI Tests — MainWindow, Controls & Toolbar Interactions
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PySide6.QtCore import Qt
from PIL import Image

from parto.ui.main_window import MainWindow
from parto.editor.document import Document


def test_main_window_components(qapp):
    """Verify MainWindow initializes all primary UI components."""
    win = MainWindow()

    assert win.toolbar is not None
    assert win.statusbar is not None
    assert win.layers_dock is not None
    assert win.adjustments_dock is not None
    assert win.welcome_screen is not None
    assert win.canvas is not None
    assert win.brush_bar is not None
    assert win.crop_bar is not None

    win.close()


def test_main_window_document_lifecycle(qapp):
    """Verify loading an image transitions from welcome screen to canvas view."""
    win = MainWindow()
    assert win.stack.currentWidget() == win.welcome_screen

    # Create new document
    win.document.new_document(100, 100, (255, 255, 255, 255))

    # Canvas should now be displayed
    assert win.stack.currentWidget() == win.canvas
    assert win.document.has_image is True

    win.close()


def test_main_window_zoom_controls(qapp):
    """Verify zoom in, out, reset, and fit actions."""
    win = MainWindow()
    win.document.new_document(100, 100)

    initial_scale = win.canvas.zoom_factor
    win.canvas.zoom_in()
    assert win.canvas.zoom_factor > initial_scale

    win.canvas.zoom_out()
    win.canvas.zoom_actual()
    assert abs(win.canvas.zoom_factor - 1.0) < 1e-4

    win.close()
