# parto/ui/main_window.py
"""
Parto v0.3.0 - Production Application Shell & Main Window
Coordinates document, canvas, tools, panels, menus, and file I/O.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
from typing import Optional, List, Tuple, Callable
from PIL import Image
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedWidget,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QApplication,
)

from ..editor.document import Document
from ..editor.canvas import Canvas
from ..editor.engine import EditorEngine
from ..tools.move import MoveTool
from ..tools.crop import CropTool
from ..tools.brush import BrushTool
from ..tools.eyedropper import EyedropperTool
from ..image.info import get_image_metadata
from ..themes.manager import get_theme_manager
from ..resources.icons import get_parto_icon
from ..shortcuts.manager import get_shortcut_manager
from ..workers.image_worker import AsyncOperationRunner

from .widgets.welcome import WelcomeScreen
from .widgets.crop_bar import CropBar
from .widgets.toast import Toast
from .panels.adjustments import AdjustmentDock
from .panels.layers_panel import LayersDock
from .statusbar import EditorStatusBar
from .toolbar import EditorToolBar
from .menus import EditorMenuBar
from .dialogs.resize import ResizeDialog
from .dialogs.filter_gallery import FilterDialog
from .dialogs.image_info import ImageInfoDialog
from .dialogs.command_palette import CommandPalette
from .dialogs.shortcuts_dialog import ShortcutsDialog
from .dialogs.about import AboutDialog


class MainWindow(QMainWindow):
    """
    Primary desktop window for Parto v0.3.0 image editor.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parto — Lightweight Image Editor")
        self.resize(1280, 800)
        self.setMinimumSize(800, 500)
        self.setAcceptDrops(True)

        # Set Window Icon
        app_icon = get_parto_icon("logo", "#0284c7", size=64)
        self.setWindowIcon(app_icon)

        # Document Model & Processing Engine
        self.document = Document(parent=self)
        self.engine = EditorEngine()
        self.async_runner = AsyncOperationRunner(parent=self)

        # Interactive Tools
        self.tool_move = MoveTool()
        self.tool_crop = CropTool()
        self.tool_brush = BrushTool()
        self.tool_eyedropper = EyedropperTool()

        # UI Initialization
        self._init_central_area()
        self._init_docks()
        self._init_toolbar()
        self._init_statusbar()
        self._init_menus()

        # Toast notification
        self.toast = Toast(self)

        # Connect Document & Canvas Signals
        self.document.document_changed.connect(self._on_document_changed)
        self.document.modified_changed.connect(self._update_window_title)
        self.document.history.history_changed.connect(self._update_history_actions)
        self.canvas.zoom_changed.connect(self.statusbar.set_zoom)
        self.canvas.pixel_inspected.connect(self._on_pixel_inspected)

        # Apply active theme
        get_theme_manager().apply_to_application()
        self._update_window_title()
        self._update_history_actions()

    def _init_central_area(self):
        """Construct central stack hosting Welcome Screen and Editor Canvas."""
        self.central_container = QWidget(self)
        self.central_layout = QVBoxLayout(self.central_container)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # Crop Bar (Hidden by default until Crop tool is active)
        self.crop_bar = CropBar(self)
        self.crop_bar.hide()
        self.crop_bar.aspect_ratio_changed.connect(lambda r: self.tool_crop.set_aspect_ratio(r, self.canvas))
        self.crop_bar.apply_clicked.connect(self.apply_crop)
        self.crop_bar.cancel_clicked.connect(self.cancel_crop)
        self.central_layout.addWidget(self.crop_bar)

        # Stack: 0 -> Welcome Screen, 1 -> Canvas
        self.stack = QStackedWidget(self)

        self.welcome_screen = WelcomeScreen(self)
        self.welcome_screen.open_requested.connect(self.action_open_image)
        self.welcome_screen.new_requested.connect(self.action_new_canvas)
        self.welcome_screen.file_dropped.connect(self.open_image_file)
        self.stack.addWidget(self.welcome_screen)

        self.canvas = Canvas(self.document, parent=self)
        self.stack.addWidget(self.canvas)

        self.central_layout.addWidget(self.stack)
        self.setCentralWidget(self.central_container)

    def _init_docks(self):
        """Create side panels for Adjustments and Layers."""
        # Layers Dock (Right)
        self.layers_dock = LayersDock(self.document, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layers_dock)

        # Adjustments Dock (Right, tabified with Layers)
        self.adjustments_dock = AdjustmentDock(self)
        self.adjustments_dock.adjustments_applied.connect(self._on_apply_adjustments)
        self.adjustments_dock.preview_requested.connect(self._on_preview_adjustments)
        self.adjustments_dock.reset_preview_requested.connect(self._on_reset_preview_adjustments)
        self.addDockWidget(Qt.RightDockWidgetArea, self.adjustments_dock)

        self.tabifyDockWidget(self.layers_dock, self.adjustments_dock)
        self.layers_dock.raise_()

    def _init_toolbar(self):
        """Construct the top tool bar."""
        self.toolbar = EditorToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # File actions
        act_new = self.toolbar.register_action("new", "New Canvas", "new")
        act_new.triggered.connect(self.action_new_canvas)

        act_open = self.toolbar.register_action("open", "Open Image", "open")
        act_open.triggered.connect(self.action_open_image)

        act_save = self.toolbar.register_action("save", "Save", "save")
        act_save.triggered.connect(self.action_save_image)

        self.toolbar.addSeparator()

        # History actions
        self.tb_act_undo = self.toolbar.register_action("undo", "Undo", "undo")
        self.tb_act_undo.triggered.connect(self.action_undo)

        self.tb_act_redo = self.toolbar.register_action("redo", "Redo", "redo")
        self.tb_act_redo.triggered.connect(self.action_redo)

        self.toolbar.addSeparator()

        # Tools group
        self.tb_tool_move = self.toolbar.register_action("move", "Pan / Hand Tool (H)", "move", checkable=True, is_tool=True)
        self.tb_tool_move.setChecked(True)
        self.tb_tool_move.triggered.connect(self.action_tool_move)

        self.tb_tool_crop = self.toolbar.register_action("crop", "Crop Tool (C)", "crop", checkable=True, is_tool=True)
        self.tb_tool_crop.triggered.connect(self.action_tool_crop)

        self.tb_tool_brush = self.toolbar.register_action("brush", "Brush Tool (B)", "brush", checkable=True, is_tool=True)
        self.tb_tool_brush.triggered.connect(self.action_tool_brush)

        self.tb_tool_eyedropper = self.toolbar.register_action("eyedropper", "Eyedropper (I)", "eyedropper", checkable=True, is_tool=True)
        self.tb_tool_eyedropper.triggered.connect(self.action_tool_eyedropper)

        self.toolbar.addSeparator()

        # Quick transforms
        act_rcw = self.toolbar.register_action("rot_cw", "Rotate Right", "rotate_cw")
        act_rcw.triggered.connect(lambda: self.document.rotate_document(True))

        act_fliph = self.toolbar.register_action("flip_h", "Flip Horizontal", "flip_h")
        act_fliph.triggered.connect(self.document.flip_horizontal_document)

        act_resize = self.toolbar.register_action("resize", "Resize Image", "resize")
        act_resize.triggered.connect(self.action_resize_image)

        self.toolbar.addSeparator()

        # Zoom buttons
        act_zin = self.toolbar.register_action("zoom_in", "Zoom In", "zoom_in")
        act_zin.triggered.connect(self.canvas.zoom_in)

        act_zout = self.toolbar.register_action("zoom_out", "Zoom Out", "zoom_out")
        act_zout.triggered.connect(self.canvas.zoom_out)

        act_zfit = self.toolbar.register_action("zoom_fit", "Fit Window", "zoom_fit")
        act_zfit.triggered.connect(self.canvas.zoom_fit)

    def _init_statusbar(self):
        """Construct the bottom telemetry status bar."""
        self.statusbar = EditorStatusBar(self)
        self.setStatusBar(self.statusbar)

    def _init_menus(self):
        """Construct application menus and bind shortcuts."""
        EditorMenuBar.setup_menus(self.menuBar(), self)

    # Document & State Handlers
    def _on_document_changed(self):
        if self.document.has_image:
            self.stack.setCurrentIndex(1)
            meta = get_image_metadata(self.document.get_composite(), self.document.filepath)
            self.statusbar.set_image_info(
                self.document.width,
                self.document.height,
                meta.get("aspect_ratio", "N/A"),
                meta.get("megapixels", "N/A"),
            )
        else:
            self.stack.setCurrentIndex(0)
            self.statusbar.set_image_info(0, 0, "", "")

        self._update_window_title()

    def _update_window_title(self, *_: Any):
        fp = self.document.filepath
        fname = os.path.basename(fp) if fp else ("Untitled" if self.document.has_image else "")
        mod_mark = " *" if self.document.is_modified else ""

        if fname:
            self.setWindowTitle(f"Parto — {fname}{mod_mark}")
        else:
            self.setWindowTitle("Parto — Lightweight Image Editor")

    def _update_history_actions(self):
        can_u = self.document.history.can_undo
        can_r = self.document.history.can_redo

        if hasattr(self, "act_undo"):
            self.act_undo.setEnabled(can_u)
            self.act_undo.setText(self.document.history.undo_description())
        if hasattr(self, "act_redo"):
            self.act_redo.setEnabled(can_r)
            self.act_redo.setText(self.document.history.redo_description())

        if hasattr(self, "tb_act_undo"):
            self.tb_act_undo.setEnabled(can_u)
            self.tb_act_undo.setToolTip(self.document.history.undo_description())
        if hasattr(self, "tb_act_redo"):
            self.tb_act_redo.setEnabled(can_r)
            self.tb_act_redo.setToolTip(self.document.history.redo_description())

    def _on_pixel_inspected(self, x: int, y: int, r: int, g: int, b: int, a: int):
        self.statusbar.set_coordinates(x, y)
        self.statusbar.set_pixel_color(r, g, b, a)

    # File Operations
    def action_new_canvas(self):
        self.document.new_document(1920, 1080)
        self.canvas.zoom_fit()
        self.toast.show_message("Created new 1920 × 1080 canvas")

    def action_open_image(self):
        file_filter = (
            "Supported Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.heic);;"
            "PNG Files (*.png);;"
            "JPEG Files (*.jpg *.jpeg);;"
            "WebP Files (*.webp);;"
            "All Files (*.*)"
        )
        path, _ = QFileDialog.getOpenFileName(self, "Open Image — Parto", "", file_filter)
        if path:
            self.open_image_file(path)

    def open_image_file(self, path: str):
        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"File not found: {path}")
            return

        success = self.document.load_file(path)
        if success:
            try:
                self.engine.load_image(path)
            except Exception:
                pass
            self.canvas.zoom_fit()
            self.toast.show_message(f"Opened {os.path.basename(path)}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to open image: {path}")

    def open_image_by_path(self, path: str):
        """Compatibility method for opening image by path."""
        self.open_image_file(path)

    @property
    def theme_mode(self) -> str:
        """Compatibility property returning 'dark' or 'light'."""
        tid = get_theme_manager().current_theme_id
        return "light" if "light" in tid else "dark"

    def toggle_theme(self):
        """Compatibility method to toggle between dark and light themes."""
        cur = self.theme_mode
        new_theme = "light" if cur == "dark" else "dark"
        get_theme_manager().set_theme(new_theme)

    def cancel_crop_mode(self):
        """Compatibility method to cancel crop mode."""
        self.cancel_crop()

    def action_save_image(self):
        if not self.document.filepath:
            self.action_save_as()
            return

        success, err = self.document.save_file()
        if success:
            self.toast.show_message(f"Saved {os.path.basename(self.document.filepath)}")
        else:
            QMessageBox.critical(self, "Save Error", f"Could not save file: {err}")

    def action_save_as(self):
        file_filter = (
            "PNG Image (*.png);;"
            "JPEG Image (*.jpg *.jpeg);;"
            "WebP Image (*.webp);;"
            "BMP Image (*.bmp);;"
            "TIFF Image (*.tiff)"
        )
        default_name = self.document.filepath or "Untitled.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save Image As — Parto", default_name, file_filter)
        if path:
            success, err = self.document.save_file(path)
            if success:
                self.toast.show_message(f"Saved as {os.path.basename(path)}")
            else:
                QMessageBox.critical(self, "Save Error", f"Could not save file: {err}")

    def action_export_image(self):
        self.action_save_as()

    def action_show_info(self):
        if not self.document.has_image:
            QMessageBox.information(self, "Properties", "No image is currently open.")
            return

        meta = get_image_metadata(self.document.get_composite(), self.document.filepath)
        dlg = ImageInfoDialog(meta, self)
        dlg.exec()

    # Edit & History Actions
    def action_undo(self):
        if self.document.history.undo():
            self.toast.show_message("Undone")

    def action_redo(self):
        if self.document.history.redo():
            self.toast.show_message("Redone")

    def action_resize_image(self):
        if not self.document.has_image:
            return

        dlg = ResizeDialog(self.document.width, self.document.height, self)
        if dlg.exec():
            nw, nh = dlg.get_dimensions()
            self.document.resize_document(nw, nh)
            self.canvas.zoom_fit()
            self.toast.show_message(f"Resized image to {nw} × {nh} px")

    # Tool Switching
    def action_tool_move(self):
        self.crop_bar.hide()
        self.canvas.set_tool(self.tool_move)
        self.tb_tool_move.setChecked(True)

    def action_tool_crop(self):
        if not self.document.has_image:
            return
        self.crop_bar.show()
        self.crop_bar.set_dimension_text(f"{self.document.width} × {self.document.height} px")
        self.canvas.set_tool(self.tool_crop)
        self.tb_tool_crop.setChecked(True)
        self.toast.show_message("Crop Tool active — Drag handles, Enter to apply, Esc to cancel")

    def apply_crop(self):
        if not self.document.has_image:
            return
        rect = self.tool_crop.get_crop_rect()
        self.action_tool_move()
        self.document.crop_document(rect)
        self.canvas.zoom_fit()
        self.toast.show_message(f"Cropped to {self.document.width} × {self.document.height} px")

    def cancel_crop(self):
        self.action_tool_move()
        self.toast.show_message("Crop cancelled")

    def action_tool_brush(self):
        self.crop_bar.hide()
        self.canvas.set_tool(self.tool_brush)
        self.tb_tool_brush.setChecked(True)
        self.toast.show_message("Brush Tool active")

    def action_tool_eyedropper(self):
        self.crop_bar.hide()
        self.canvas.set_tool(self.tool_eyedropper)
        self.tb_tool_eyedropper.setChecked(True)
        self.toast.show_message("Eyedropper active — Click pixel to sample color")

    def set_brush_color(self, rgba: Tuple[int, int, int, int]):
        self.tool_brush.color = rgba
        r, g, b, _ = rgba
        self.toast.show_message(f"Sampled #{r:02X}{g:02X}{b:02X}")

    # Adjustments
    def _on_apply_adjustments(self, b: float, c: float, s: float, sh: float):
        self.document.apply_color_adjustments(b, c, s, sh)
        self.toast.show_message("Color adjustments applied to active layer")

    def _on_preview_adjustments(self, b: float, c: float, s: float, sh: float):
        # Temporary live view can be displayed on canvas if desired
        pass

    def _on_reset_preview_adjustments(self):
        self.canvas.update_composite_pixmap()

    # Filters
    def action_show_filter_gallery(self):
        if not self.document.has_image or not self.document.active_layer:
            return

        dlg = FilterDialog(self.document.active_layer.image, self)
        if dlg.exec():
            fname = dlg.get_filter_name()
            self.document.apply_filter(fname)
            self.toast.show_message(f"Applied {fname.title()} filter")

    # Command Palette & Cheat Sheet
    def action_show_command_palette(self):
        commands: List[Tuple[str, str, str, Callable[[], None]]] = [
            ("file_new", "New Canvas...", "Ctrl+N", self.action_new_canvas),
            ("file_open", "Open Image...", "Ctrl+O", self.action_open_image),
            ("file_save", "Save", "Ctrl+S", self.action_save_image),
            ("file_save_as", "Save As...", "Ctrl+Shift+S", self.action_save_as),
            ("file_info", "Properties & Metadata...", "Ctrl+I", self.action_show_info),
            ("edit_undo", "Undo", "Ctrl+Z", self.action_undo),
            ("edit_redo", "Redo", "Ctrl+Y", self.action_redo),
            ("edit_crop", "Crop Tool", "C", self.action_tool_crop),
            ("edit_resize", "Resize Image...", "Ctrl+R", self.action_resize_image),
            ("tool_move", "Pan / Hand Tool", "H", self.action_tool_move),
            ("tool_brush", "Brush Tool", "B", self.action_tool_brush),
            ("tool_eyedropper", "Eyedropper", "I", self.action_tool_eyedropper),
            ("view_zin", "Zoom In", "Ctrl+=", self.canvas.zoom_in),
            ("view_zout", "Zoom Out", "Ctrl+-", self.canvas.zoom_out),
            ("view_zfit", "Fit on Screen", "Ctrl+0", self.canvas.zoom_fit),
            ("view_z100", "Actual Pixels (100%)", "Ctrl+1", self.canvas.zoom_actual),
            ("view_fullscreen", "Toggle Fullscreen", "F11", self.action_toggle_fullscreen),
            ("img_rcw", "Rotate 90° Clockwise", "Ctrl+]", lambda: self.document.rotate_document(True)),
            ("img_rccw", "Rotate 90° Counter-Clockwise", "Ctrl+[", lambda: self.document.rotate_document(False)),
            ("img_r180", "Rotate 180°", "Ctrl+Shift+R", self.document.rotate_180_document),
            ("img_fliph", "Flip Horizontal", "Ctrl+H", self.document.flip_horizontal_document),
            ("img_flipv", "Flip Vertical", "Ctrl+J", self.document.flip_vertical_document),
            ("filter_gallery", "Filter Gallery...", "Ctrl+Shift+F", self.action_show_filter_gallery),
            ("help_shortcuts", "Keyboard Shortcuts...", "F1", self.action_show_shortcuts),
            ("help_about", "About Parto", "", self.action_show_about),
        ]

        dlg = CommandPalette(commands, self)
        dlg.exec()

    def action_show_shortcuts(self):
        dlg = ShortcutsDialog(self)
        dlg.exec()

    def action_show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def action_toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # Drag & Drop Support
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = urls[0].toLocalFile()
            self.open_image_file(path)
            event.acceptProposedAction()

    # Window Closing Safeguard
    def closeEvent(self, event: QCloseEvent) -> None:
        if self.document.is_modified:
            ans = QMessageBox.question(
                self,
                "Unsaved Changes",
                "Do you want to save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if ans == QMessageBox.Save:
                self.action_save_image()
                event.accept()
            elif ans == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
