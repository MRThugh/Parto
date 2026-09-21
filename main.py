# main.py
"""
Parto - A fast, modern, and lightweight desktop image editor.
Author: Ali Kamrani (MRThugh)
Version: 0.3.0
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from parto.ui.main_window import MainWindow
from parto.resources.icons import get_parto_icon
from parto.themes.manager import get_theme_manager


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, compatible with standard Python source
    and PyInstaller frozen single-file bundles.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def main():
    # High-DPI support and modern scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_USE_PHYSICAL_DPI"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Parto")
    app.setApplicationDisplayName("Parto — پرتو")
    app.setApplicationVersion("0.3.0")
    app.setOrganizationName("Parto")

    # Initialize theme subsystem
    get_theme_manager().apply_to_application()

    # Set crisp application vector icon
    logo_path = resource_path("logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
    else:
        app.setWindowIcon(get_parto_icon("logo", "#0284c7", 64))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
