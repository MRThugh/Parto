# parto/ui/menus.py
"""
Parto v0.3.0 - Comprehensive Application Menus
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, Any
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenuBar, QMenu
from ..themes.manager import get_theme_manager
from ..themes.palettes import THEMES
from ..shortcuts.manager import get_shortcut_manager


class EditorMenuBar:
    """
    Constructs and registers the full hierarchy of menus with centralized shortcuts.
    """

    @classmethod
    def setup_menus(cls, menu_bar: QMenuBar, window: Any) -> None:
        sm = get_shortcut_manager()

        # ==========================================
        # 1. FILE MENU
        # ==========================================
        file_menu = menu_bar.addMenu("&File")

        act_new = sm.register("file_new", "New Canvas...", "File", "Ctrl+N", "Create new empty image canvas", file_menu.addAction("New Canvas..."))
        act_new.action.triggered.connect(window.action_new_canvas)

        act_open = sm.register("file_open", "Open Image...", "File", "Ctrl+O", "Open existing image file", file_menu.addAction("Open Image..."))
        act_open.action.triggered.connect(window.action_open_image)

        file_menu.addSeparator()

        act_save = sm.register("file_save", "Save", "File", "Ctrl+S", "Save image changes to disk", file_menu.addAction("Save"))
        act_save.action.triggered.connect(window.action_save_image)

        act_save_as = sm.register("file_save_as", "Save As...", "File", "Ctrl+Shift+S", "Save image to a new file", file_menu.addAction("Save As..."))
        act_save_as.action.triggered.connect(window.action_save_as)

        act_export = sm.register("file_export", "Export As...", "File", "Ctrl+Shift+E", "Export image to WebP, JPEG, PNG, TIFF", file_menu.addAction("Export As..."))
        act_export.action.triggered.connect(window.action_export_image)

        file_menu.addSeparator()

        act_info = sm.register("file_info", "Properties & Metadata...", "File", "Ctrl+I", "View image technical specifications", file_menu.addAction("Properties & Metadata..."))
        act_info.action.triggered.connect(window.action_show_info)

        file_menu.addSeparator()

        act_exit = sm.register("file_exit", "Exit", "File", "Ctrl+Q", "Exit Parto", file_menu.addAction("Exit"))
        act_exit.action.triggered.connect(window.close)

        # ==========================================
        # 2. EDIT MENU
        # ==========================================
        edit_menu = menu_bar.addMenu("&Edit")

        act_undo = sm.register("edit_undo", "Undo", "Edit", "Ctrl+Z", "Undo last operation", edit_menu.addAction("Undo"))
        act_undo.action.triggered.connect(window.action_undo)
        window.act_undo = act_undo.action

        act_redo = sm.register("edit_redo", "Redo", "Edit", "Ctrl+Y", "Redo previously undone operation", edit_menu.addAction("Redo"))
        act_redo.action.triggered.connect(window.action_redo)
        window.act_redo = act_redo.action

        edit_menu.addSeparator()

        act_crop = sm.register("edit_crop", "Crop Canvas...", "Edit", "Shift+C", "Crop image canvas", edit_menu.addAction("Crop Canvas..."))
        act_crop.action.triggered.connect(window.action_tool_crop)

        act_resize = sm.register("edit_resize", "Resize Image...", "Edit", "Ctrl+Alt+I", "Resize image dimensions", edit_menu.addAction("Resize Image..."))
        act_resize.action.triggered.connect(window.action_resize_image)

        # ==========================================
        # 3. VIEW MENU
        # ==========================================
        view_menu = menu_bar.addMenu("&View")

        act_zin = sm.register("view_zoom_in", "Zoom In", "View", "Ctrl+=", "Increase canvas zoom", view_menu.addAction("Zoom In"))
        act_zin.action.triggered.connect(window.canvas.zoom_in)

        act_zout = sm.register("view_zoom_out", "Zoom Out", "View", "Ctrl+-", "Decrease canvas zoom", view_menu.addAction("Zoom Out"))
        act_zout.action.triggered.connect(window.canvas.zoom_out)

        act_zfit = sm.register("view_zoom_fit", "Fit on Screen", "View", "Ctrl+0", "Fit entire image inside view", view_menu.addAction("Fit on Screen"))
        act_zfit.action.triggered.connect(window.canvas.zoom_fit)

        act_z100 = sm.register("view_zoom_100", "Actual Pixels (100%)", "View", "Ctrl+1", "View image at 1:1 scale", view_menu.addAction("Actual Pixels (100%)"))
        act_z100.action.triggered.connect(window.canvas.zoom_actual)

        view_menu.addSeparator()

        act_fullscreen = sm.register("view_fullscreen", "Toggle Fullscreen", "View", "F11", "Toggle fullscreen mode", view_menu.addAction("Toggle Fullscreen"))
        act_fullscreen.action.triggered.connect(window.action_toggle_fullscreen)

        view_menu.addSeparator()

        if hasattr(window, "layers_dock"):
            act_tlayers = sm.register("view_layers", "Layers Panel", "View", "F7", "Toggle Layers Panel", view_menu.addAction("Layers Panel"))
            act_tlayers.action.setCheckable(True)
            act_tlayers.action.setChecked(window.layers_dock.isVisible())
            if hasattr(window, "set_layers_dock_visible"):
                act_tlayers.action.toggled.connect(lambda checked: window.set_layers_dock_visible(checked, animate=True))
            else:
                act_tlayers.action.toggled.connect(window.layers_dock.setVisible)

            def _sync_layers_action(vis: bool):
                try:
                    action = act_tlayers.action
                    if action is not None and action.isChecked() != vis:
                        action.blockSignals(True)
                        action.setChecked(vis)
                        action.blockSignals(False)
                except (RuntimeError, AttributeError):
                    pass

            window.layers_dock.visibilityChanged.connect(_sync_layers_action)

        if hasattr(window, "adjustments_dock"):
            act_tadj = sm.register("view_adjustments", "Adjustments Panel", "View", "F8", "Toggle Live Adjustments Panel", view_menu.addAction("Adjustments Panel"))
            act_tadj.action.setCheckable(True)
            act_tadj.action.setChecked(window.adjustments_dock.isVisible())
            if hasattr(window, "set_adjustments_dock_visible"):
                act_tadj.action.toggled.connect(lambda checked: window.set_adjustments_dock_visible(checked, animate=True))
            else:
                act_tadj.action.toggled.connect(window.adjustments_dock.setVisible)

            def _sync_adj_action(vis: bool):
                try:
                    action = act_tadj.action
                    if action is not None and action.isChecked() != vis:
                        action.blockSignals(True)
                        action.setChecked(vis)
                        action.blockSignals(False)
                except (RuntimeError, AttributeError):
                    pass

            window.adjustments_dock.visibilityChanged.connect(_sync_adj_action)

        # ==========================================
        # 4. IMAGE MENU
        # ==========================================
        image_menu = menu_bar.addMenu("&Image")

        act_rcw = sm.register("img_rot_cw", "Rotate 90° Clockwise", "Image", "Ctrl+R", "Rotate 90 degrees right", image_menu.addAction("Rotate 90° Clockwise"))
        act_rcw.action.triggered.connect(lambda: window.document.rotate_document(clockwise=True))

        act_rccw = sm.register("img_rot_ccw", "Rotate 90° Counter-Clockwise", "Image", "Ctrl+Shift+R", "Rotate 90 degrees left", image_menu.addAction("Rotate 90° Counter-Clockwise"))
        act_rccw.action.triggered.connect(lambda: window.document.rotate_document(clockwise=False))

        act_r180 = sm.register("img_rot_180", "Rotate 180°", "Image", "Ctrl+Alt+R", "Rotate upside down", image_menu.addAction("Rotate 180°"))
        act_r180.action.triggered.connect(window.document.rotate_180_document)

        image_menu.addSeparator()

        act_fliph = sm.register("img_flip_h", "Flip Horizontal", "Image", "Ctrl+H", "Flip canvas left to right", image_menu.addAction("Flip Horizontal"))
        act_fliph.action.triggered.connect(window.document.flip_horizontal_document)

        act_flipv = sm.register("img_flip_v", "Flip Vertical", "Image", "Ctrl+Shift+H", "Flip canvas top to bottom", image_menu.addAction("Flip Vertical"))
        act_flipv.action.triggered.connect(window.document.flip_vertical_document)

        image_menu.addSeparator()

        rb_action = image_menu.addAction("Remove Background")
        rb_act = sm.register(
            "img_remove_bg",
            "Remove Background",
            "Image",
            "Ctrl+Shift+B",
            "Automatically remove image background with edge feathering",
            rb_action,
        )
        rb_act.action.triggered.connect(lambda: window.apply_remove_background(28, 2))


        # ==========================================
        # 5. LAYERS MENU
        # ==========================================
        layers_menu = menu_bar.addMenu("&Layers")

        act_nl = sm.register("layer_new", "New Layer", "Layers", "Ctrl+Shift+N", "Add empty layer", layers_menu.addAction("New Layer"))
        act_nl.action.triggered.connect(window.document.add_layer)

        act_dl = sm.register("layer_dup", "Duplicate Layer", "Layers", "Ctrl+J", "Duplicate selected layer", layers_menu.addAction("Duplicate Layer"))
        act_dl.action.triggered.connect(window.document.duplicate_active_layer)

        act_rml = sm.register("layer_del", "Delete Layer", "Layers", "Delete", "Delete active layer", layers_menu.addAction("Delete Layer"))
        act_rml.action.triggered.connect(window.document.remove_active_layer)

        layers_menu.addSeparator()

        act_mup = sm.register("layer_up", "Move Layer Up", "Layers", "Ctrl+Up", "Move layer higher in stack", layers_menu.addAction("Move Layer Up"))
        act_mup.action.triggered.connect(window.document.move_layer_up)

        act_mdn = sm.register("layer_dn", "Move Layer Down", "Layers", "Ctrl+Down", "Move layer lower in stack", layers_menu.addAction("Move Layer Down"))
        act_mdn.action.triggered.connect(window.document.move_layer_down)

        act_mrg = sm.register("layer_mrg", "Merge Down", "Layers", "Ctrl+E", "Merge active layer into layer below", layers_menu.addAction("Merge Down"))
        act_mrg.action.triggered.connect(window.document.merge_down)

        # ==========================================
        # 6. FILTERS MENU
        # ==========================================
        filters_menu = menu_bar.addMenu("&Filters")

        act_fgallery = sm.register("filter_gallery", "Filter Gallery...", "Filters", "Ctrl+Shift+F", "Open interactive filter gallery", filters_menu.addAction("Filter Gallery..."))
        act_fgallery.action.triggered.connect(window.action_show_filter_gallery)

        filters_menu.addSeparator()
        filters_menu.addAction("Grayscale").triggered.connect(lambda: window.document.apply_filter("grayscale"))
        filters_menu.addAction("Sepia").triggered.connect(lambda: window.document.apply_filter("sepia"))
        filters_menu.addAction("Invert Colors").triggered.connect(lambda: window.document.apply_filter("invert"))
        filters_menu.addAction("Gaussian Blur").triggered.connect(lambda: window.document.apply_filter("blur"))
        filters_menu.addAction("Sharpen").triggered.connect(lambda: window.document.apply_filter("sharpen"))
        filters_menu.addAction("Find Edges").triggered.connect(lambda: window.document.apply_filter("edge_detect"))
        filters_menu.addAction("Emboss").triggered.connect(lambda: window.document.apply_filter("emboss"))

        # ==========================================
        # 7. TOOLS MENU
        # ==========================================
        tools_menu = menu_bar.addMenu("&Tools")

        act_tmove = sm.register("tool_move", "Pan / Move Tool", "Tools", "V", "Pan canvas view", tools_menu.addAction("Pan / Move Tool"))
        act_tmove.action.triggered.connect(window.action_tool_move)

        act_tcrop = sm.register("tool_crop", "Crop Tool", "Tools", "C", "Crop canvas geometry", tools_menu.addAction("Crop Tool"))
        act_tcrop.action.triggered.connect(window.action_tool_crop)

        act_tbrush = sm.register("tool_brush", "Brush Tool", "Tools", "B", "Freehand drawing tool", tools_menu.addAction("Brush Tool"))
        act_tbrush.action.triggered.connect(window.action_tool_brush)

        act_teye = sm.register("tool_eyedropper", "Eyedropper", "Tools", "I", "Sample pixel color", tools_menu.addAction("Eyedropper"))
        act_teye.action.triggered.connect(window.action_tool_eyedropper)

        # ==========================================
        # 8. THEME MENU
        # ==========================================
        theme_menu = menu_bar.addMenu("&Theme")
        theme_group = QActionGroup(window)
        theme_group.setExclusive(True)

        current_theme = get_theme_manager().current_theme_id
        for tid, tmeta in THEMES.items():
            tact = QAction(tmeta["name"], window)
            tact.setCheckable(True)
            if tid == current_theme:
                tact.setChecked(True)
            tact.triggered.connect(lambda _, t=tid: get_theme_manager().transition_theme(t, window=window, duration_ms=200))
            theme_group.addAction(tact)
            theme_menu.addAction(tact)

        # ==========================================
        # 9. HELP MENU
        # ==========================================
        help_menu = menu_bar.addMenu("&Help")

        act_palette = sm.register("help_palette", "Command Palette...", "App", "Ctrl+K", "Search and run any command", help_menu.addAction("Command Palette..."))
        act_palette.action.triggered.connect(window.action_show_command_palette)

        act_keys = sm.register("help_shortcuts", "Keyboard Shortcuts...", "App", "F1", "View shortcuts cheat sheet", help_menu.addAction("Keyboard Shortcuts..."))
        act_keys.action.triggered.connect(window.action_show_shortcuts)

        help_menu.addSeparator()

        act_about = sm.register("help_about", "About Parto", "App", "", "About Parto v0.3.0", help_menu.addAction("About Parto"))
        act_about.action.triggered.connect(window.action_show_about)
