# tests/unit/test_icons.py
"""
Unit Tests — Vector Icon System & Canonical Alias Resolution
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PySide6.QtGui import QIcon

from parto.resources.icons import (
    get_parto_icon,
    clear_icon_cache,
    ICON_ALIASES,
    _WARNED_MISSING_ICONS,
)


@pytest.mark.parametrize(
    "alias_name, expected_canonical",
    [
        ("tool_move", "move"),
        ("tool-move", "move"),
        ("tool_crop", "crop"),
        ("tool-crop", "crop"),
        ("tool_brush", "brush"),
        ("tool-brush", "brush"),
        ("tool_eyedropper", "eyedropper"),
        ("tool-eyedropper", "eyedropper"),
        ("rot_left", "rotate-ccw"),
        ("rot-left", "rotate-ccw"),
        ("rot_right", "rotate-cw"),
        ("rot-right", "rotate-cw"),
    ],
)
def test_icon_alias_resolution(qapp, alias_name, expected_canonical):
    """Verify toolbar and menu action aliases resolve to canonical vector renderers."""
    clear_icon_cache()
    _WARNED_MISSING_ICONS.clear()

    icon = get_parto_icon(alias_name, "#ffffff", 24)
    assert isinstance(icon, QIcon)
    assert not icon.isNull()
    # Alias must not trigger missing-icon warning
    assert alias_name not in _WARNED_MISSING_ICONS


def test_icon_cache_mechanism(qapp):
    """Verify identical icon requests retrieve cached QIcon instances."""
    clear_icon_cache()
    icon1 = get_parto_icon("save", "#0284c7", 20)
    icon2 = get_parto_icon("save", "#0284c7", 20)

    assert not icon1.isNull()
    # Should resolve to identical cached QIcon instance
    assert icon1 is icon2


def test_core_vector_icon_renderers(qapp):
    """Verify all primary navigation and tool icon primitives render valid pixmaps."""
    core_icons = [
        "new", "open", "save", "save-as", "export",
        "undo", "redo", "crop", "resize", "rotate-cw", "rotate-ccw",
        "flip-h", "flip-v", "adjust", "filters", "compare",
        "zoom-in", "zoom-out", "zoom-fit", "zoom-reset",
        "theme", "info", "move", "brush", "eyedropper",
        "layers", "layer-add", "layer-delete", "layer-duplicate",
        "layer-up", "layer-down", "layer-merge", "eye-open", "eye-closed",
        "check", "close", "logo",
    ]

    for icon_name in core_icons:
        icon = get_parto_icon(icon_name, "#ffffff", 20)
        assert isinstance(icon, QIcon), f"Icon '{icon_name}' is not a QIcon"
        assert not icon.isNull(), f"Icon '{icon_name}' produced a null QIcon"
