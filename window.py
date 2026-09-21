# window.py
"""
Parto v0.3.0 - Window & UI Compatibility Layer
Decoupled in v0.3.0: Re-exports modular UI components from the parto.ui package.
Author: Ali Kamrani (MRThugh)
"""

from parto.ui.main_window import MainWindow
from parto.ui.dialogs.resize import ResizeDialog
from parto.ui.dialogs.filter_gallery import FilterDialog
from parto.ui.dialogs.image_info import ImageInfoDialog
from parto.ui.dialogs.command_palette import CommandPalette
from parto.ui.dialogs.shortcuts_dialog import ShortcutsDialog
from parto.ui.dialogs.about import AboutDialog
from parto.ui.widgets.crop_bar import CropBar
from parto.ui.widgets.welcome import WelcomeScreen
from parto.ui.widgets.toast import Toast

__all__ = [
    "MainWindow",
    "ResizeDialog",
    "FilterDialog",
    "ImageInfoDialog",
    "CommandPalette",
    "ShortcutsDialog",
    "AboutDialog",
    "CropBar",
    "WelcomeScreen",
    "Toast",
]
