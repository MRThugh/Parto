# tests/integration/test_application_startup.py
"""
Integration Tests — Application Startup, Shell & UI Bootstrap
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from parto.ui.main_window import MainWindow
from parto.themes.manager import get_theme_manager


def test_main_window_startup_state(qapp):
    """
    Verify application starts cleanly in headless mode:
    - MainWindow initializes with minimum sizes
    - Docks are closed by default for maximum workspace
    - WelcomeScreen is shown when no document is active
    """
    window = MainWindow()
    assert window is not None
    assert "Parto" in window.windowTitle()
    assert window.minimumWidth() >= 800
    assert window.minimumHeight() >= 500

    # Docks must be hidden by default per architecture design
    assert window.layers_dock.isHidden() is True
    assert window.adjustments_dock.isHidden() is True

    # Central area shows WelcomeScreen
    assert window.stack.currentWidget() == window.welcome_screen

    # Tools are initialized
    assert window.tool_move is not None
    assert window.tool_crop is not None
    assert window.tool_brush is not None
    assert window.tool_eyedropper is not None

    window.close()


def test_theme_manager_bootstrap(qapp):
    """Verify ThemeManager initializes and provides active theme palettes."""
    tm = get_theme_manager()
    assert tm is not None
    assert tm.current_theme in ("dark", "light", "graphite", "midnight", "nord")

    palette = tm.get_palette()
    assert "bg" in palette
    assert "text" in palette
    assert "accent" in palette
