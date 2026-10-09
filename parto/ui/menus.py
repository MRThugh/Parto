# parto/ui/menus.py
"""
Parto v0.4.0 - Comprehensive Application Menus
Author: Ali Kamrani (MRThugh)
Integrated with Localization Subsystem and centralized ShortcutManager.
"""

from __future__ import annotations
from typing import Optional, Any
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenuBar, QMenu

from ..themes.manager import get_theme_manager
from ..themes.palettes import THEMES
from ..shortcuts.manager import get_shortcut_manager
from ..localization import t, get_localization_manager
from .. import __version__


class EditorMenuBar:
    """
    Constructs and registers the full hierarchy of menus with centralized shortcuts
    and dynamic runtime localization support.
    """

    @classmethod
    def setup_menus(cls, menu_bar: QMenuBar, window: Any) -> None:
        sm = get_shortcut_manager()

        # ==========================================
        # 1. FILE MENU
        # ==========================================
        file_menu = menu_bar.addMenu(t("menu.file"))
        window.menu_file = file_menu

        act_new = sm.register("file_new", t("action.file.new"), "File", "Ctrl+N", t("action.file.new_desc"), file_menu.addAction(t("action.file.new")))
        act_new.action.triggered.connect(window.action_new_canvas)
        window.act_file_new = act_new.action

        act_open = sm.register("file_open", t("action.file.open"), "File", "Ctrl+O", t("action.file.open_desc"), file_menu.addAction(t("action.file.open")))
        act_open.action.triggered.connect(window.action_open_image)
        window.act_file_open = act_open.action

        file_menu.addSeparator()

        act_save = sm.register("file_save", t("action.file.save"), "File", "Ctrl+S", t("action.file.save_desc"), file_menu.addAction(t("action.file.save")))
        act_save.action.triggered.connect(window.action_save_image)
        window.act_file_save = act_save.action

        act_save_as = sm.register("file_save_as", t("action.file.save_as"), "File", "Ctrl+Shift+S", t("action.file.save_as_desc"), file_menu.addAction(t("action.file.save_as")))
        act_save_as.action.triggered.connect(window.action_save_as)
        window.act_file_save_as = act_save_as.action

        act_export = sm.register("file_export", t("action.file.export"), "File", "Ctrl+Shift+E", t("action.file.export_desc"), file_menu.addAction(t("action.file.export")))
        act_export.action.triggered.connect(window.action_export_image)
        window.act_file_export = act_export.action

        file_menu.addSeparator()

        act_info = sm.register("file_info", t("action.file.info"), "File", "Ctrl+I", t("action.file.info_desc"), file_menu.addAction(t("action.file.info")))
        act_info.action.triggered.connect(window.action_show_info)
        window.act_file_info = act_info.action

        file_menu.addSeparator()

        act_exit = sm.register("file_exit", t("action.file.exit"), "File", "Ctrl+Q", t("action.file.exit_desc"), file_menu.addAction(t("action.file.exit")))
        act_exit.action.triggered.connect(window.close)
        window.act_file_exit = act_exit.action

        # ==========================================
        # 2. EDIT MENU
        # ==========================================
        edit_menu = menu_bar.addMenu(t("menu.edit"))
        window.menu_edit = edit_menu

        act_undo = sm.register("edit_undo", t("action.edit.undo"), "Edit", "Ctrl+Z", t("action.edit.undo_desc"), edit_menu.addAction(t("action.edit.undo")))
        act_undo.action.triggered.connect(window.action_undo)
        window.act_undo = act_undo.action

        act_redo = sm.register("edit_redo", t("action.edit.redo"), "Edit", "Ctrl+Y", t("action.edit.redo_desc"), edit_menu.addAction(t("action.edit.redo")))
        act_redo.action.triggered.connect(window.action_redo)
        window.act_redo = act_redo.action

        edit_menu.addSeparator()

        act_crop = sm.register("edit_crop", t("action.edit.crop"), "Edit", "Shift+C", t("action.edit.crop_desc"), edit_menu.addAction(t("action.edit.crop")))
        act_crop.action.triggered.connect(window.action_tool_crop)
        window.act_crop = act_crop.action

        act_resize = sm.register("edit_resize", t("action.edit.resize"), "Edit", "Ctrl+Alt+I", t("action.edit.resize_desc"), edit_menu.addAction(t("action.edit.resize")))
        act_resize.action.triggered.connect(window.action_resize_image)
        window.act_resize = act_resize.action

        # ==========================================
        # 3. VIEW MENU
        # ==========================================
        view_menu = menu_bar.addMenu(t("menu.view"))
        window.menu_view = view_menu

        act_zin = sm.register("view_zoom_in", t("action.view.zoom_in"), "View", "Ctrl+=", t("action.view.zoom_in_desc"), view_menu.addAction(t("action.view.zoom_in")))
        act_zin.action.triggered.connect(window.canvas.zoom_in)
        window.act_zin = act_zin.action

        act_zout = sm.register("view_zoom_out", t("action.view.zoom_out"), "View", "Ctrl+-", t("action.view.zoom_out_desc"), view_menu.addAction(t("action.view.zoom_out")))
        act_zout.action.triggered.connect(window.canvas.zoom_out)
        window.act_zout = act_zout.action

        act_zfit = sm.register("view_zoom_fit", t("action.view.zoom_fit"), "View", "Ctrl+0", t("action.view.zoom_fit_desc"), view_menu.addAction(t("action.view.zoom_fit")))
        act_zfit.action.triggered.connect(window.canvas.zoom_fit)
        window.act_zfit = act_zfit.action

        act_z100 = sm.register("view_zoom_100", t("action.view.zoom_100"), "View", "Ctrl+1", t("action.view.zoom_100_desc"), view_menu.addAction(t("action.view.zoom_100")))
        act_z100.action.triggered.connect(window.canvas.zoom_actual)
        window.act_z100 = act_z100.action

        view_menu.addSeparator()

        act_fullscreen = sm.register("view_fullscreen", t("action.view.fullscreen"), "View", "F11", t("action.view.fullscreen_desc"), view_menu.addAction(t("action.view.fullscreen")))
        act_fullscreen.action.triggered.connect(window.action_toggle_fullscreen)
        window.act_fullscreen = act_fullscreen.action

        view_menu.addSeparator()

        if hasattr(window, "layers_dock"):
            act_tlayers = sm.register("view_layers", t("action.view.layers"), "View", "F7", t("action.view.layers_desc"), view_menu.addAction(t("action.view.layers")))
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
            window.act_tlayers = act_tlayers.action

        if hasattr(window, "adjustments_dock"):
            act_tadj = sm.register("view_adjustments", t("action.view.adjustments"), "View", "F8", t("action.view.adjustments_desc"), view_menu.addAction(t("action.view.adjustments")))
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
            window.act_tadj = act_tadj.action

        # ==========================================
        # 4. IMAGE MENU
        # ==========================================
        image_menu = menu_bar.addMenu(t("menu.image"))
        window.menu_image = image_menu

        act_rcw = sm.register("img_rot_cw", t("action.image.rotate_cw"), "Image", "Ctrl+R", t("action.image.rotate_cw_desc"), image_menu.addAction(t("action.image.rotate_cw")))
        act_rcw.action.triggered.connect(lambda: window.document.rotate_document(clockwise=True))
        window.act_rcw = act_rcw.action

        act_rccw = sm.register("img_rot_ccw", t("action.image.rotate_ccw"), "Image", "Ctrl+Shift+R", t("action.image.rotate_ccw_desc"), image_menu.addAction(t("action.image.rotate_ccw")))
        act_rccw.action.triggered.connect(lambda: window.document.rotate_document(clockwise=False))
        window.act_rccw = act_rccw.action

        act_r180 = sm.register("img_rot_180", t("action.image.rotate_180"), "Image", "Ctrl+Alt+R", t("action.image.rotate_180_desc"), image_menu.addAction(t("action.image.rotate_180")))
        act_r180.action.triggered.connect(window.document.rotate_180_document)
        window.act_r180 = act_r180.action

        image_menu.addSeparator()

        act_fliph = sm.register("img_flip_h", t("action.image.flip_h"), "Image", "Ctrl+H", t("action.image.flip_h_desc"), image_menu.addAction(t("action.image.flip_h")))
        act_fliph.action.triggered.connect(window.document.flip_horizontal_document)
        window.act_fliph = act_fliph.action

        act_flipv = sm.register("img_flip_v", t("action.image.flip_v"), "Image", "Ctrl+Shift+H", t("action.image.flip_v_desc"), image_menu.addAction(t("action.image.flip_v")))
        act_flipv.action.triggered.connect(window.document.flip_vertical_document)
        window.act_flipv = act_flipv.action

        image_menu.addSeparator()

        rb_action = image_menu.addAction(t("action.image.remove_bg"))
        rb_act = sm.register(
            "img_remove_bg",
            t("action.image.remove_bg"),
            "Image",
            "Ctrl+Alt+B",
            t("action.image.remove_bg_desc"),
            rb_action,
        )
        rb_act.action.triggered.connect(lambda: window.apply_remove_background(28, 2))
        window.act_remove_bg = rb_act.action

        # ==========================================
        # 5. LAYERS MENU
        # ==========================================
        layers_menu = menu_bar.addMenu(t("menu.layers"))
        window.menu_layers = layers_menu

        act_nl = sm.register("layer_new", t("action.layer.new"), "Layers", "Ctrl+Shift+N", t("action.layer.new_desc"), layers_menu.addAction(t("action.layer.new")))
        act_nl.action.triggered.connect(window.document.add_layer)
        window.act_nl = act_nl.action

        act_dl = sm.register("layer_dup", t("action.layer.duplicate"), "Layers", "Ctrl+J", t("action.layer.duplicate_desc"), layers_menu.addAction(t("action.layer.duplicate")))
        act_dl.action.triggered.connect(window.document.duplicate_active_layer)
        window.act_dl = act_dl.action

        act_rml = sm.register("layer_del", t("action.layer.delete"), "Layers", "Delete", t("action.layer.delete_desc"), layers_menu.addAction(t("action.layer.delete")))
        act_rml.action.triggered.connect(window.document.remove_active_layer)
        window.act_rml = act_rml.action

        layers_menu.addSeparator()

        act_mup = sm.register("layer_up", t("action.layer.move_up"), "Layers", "Ctrl+Up", t("action.layer.move_up_desc"), layers_menu.addAction(t("action.layer.move_up")))
        act_mup.action.triggered.connect(window.document.move_layer_up)
        window.act_mup = act_mup.action

        act_mdn = sm.register("layer_dn", t("action.layer.move_down"), "Layers", "Ctrl+Down", t("action.layer.move_down_desc"), layers_menu.addAction(t("action.layer.move_down")))
        act_mdn.action.triggered.connect(window.document.move_layer_down)
        window.act_mdn = act_mdn.action

        act_mrg = sm.register("layer_mrg", t("action.layer.merge_down"), "Layers", "Ctrl+E", t("action.layer.merge_down_desc"), layers_menu.addAction(t("action.layer.merge_down")))
        act_mrg.action.triggered.connect(window.document.merge_down)
        window.act_mrg = act_mrg.action

        # ==========================================
        # 6. FILTERS MENU
        # ==========================================
        filters_menu = menu_bar.addMenu(t("menu.filters"))
        window.menu_filters = filters_menu

        act_fgallery = sm.register("filter_gallery", t("action.filter.gallery"), "Filters", "Ctrl+Shift+F", t("action.filter.gallery_desc"), filters_menu.addAction(t("action.filter.gallery")))
        act_fgallery.action.triggered.connect(window.action_show_filter_gallery)
        window.act_fgallery = act_fgallery.action

        filters_menu.addSeparator()

        window.act_filter_grayscale = filters_menu.addAction(t("filter.grayscale"))
        window.act_filter_grayscale.triggered.connect(lambda: window.document.apply_filter("grayscale"))

        window.act_filter_sepia = filters_menu.addAction(t("filter.sepia"))
        window.act_filter_sepia.triggered.connect(lambda: window.document.apply_filter("sepia"))

        window.act_filter_invert = filters_menu.addAction(t("filter.invert"))
        window.act_filter_invert.triggered.connect(lambda: window.document.apply_filter("invert"))

        window.act_filter_blur = filters_menu.addAction(t("filter.blur"))
        window.act_filter_blur.triggered.connect(lambda: window.document.apply_filter("blur"))

        window.act_filter_sharpen = filters_menu.addAction(t("filter.sharpen"))
        window.act_filter_sharpen.triggered.connect(lambda: window.document.apply_filter("sharpen"))

        window.act_filter_edge = filters_menu.addAction(t("filter.edge_detect"))
        window.act_filter_edge.triggered.connect(lambda: window.document.apply_filter("edge_detect"))

        window.act_filter_emboss = filters_menu.addAction(t("filter.emboss"))
        window.act_filter_emboss.triggered.connect(lambda: window.document.apply_filter("emboss"))

        # ==========================================
        # 7. TOOLS MENU
        # ==========================================
        tools_menu = menu_bar.addMenu(t("menu.tools"))
        window.menu_tools = tools_menu

        act_tmove = sm.register("tool_move", t("tool.move"), "Tools", "V", t("tool.move_desc"), tools_menu.addAction(t("tool.move")))
        act_tmove.action.triggered.connect(window.action_tool_move)
        window.act_tool_move_menu = act_tmove.action

        act_tcrop = sm.register("tool_crop", t("tool.crop"), "Tools", "C", t("tool.crop_desc"), tools_menu.addAction(t("tool.crop")))
        act_tcrop.action.triggered.connect(window.action_tool_crop)
        window.act_tool_crop_menu = act_tcrop.action

        act_tbrush = sm.register("tool_brush", t("tool.brush"), "Tools", "B", t("tool.brush_desc"), tools_menu.addAction(t("tool.brush")))
        act_tbrush.action.triggered.connect(window.action_tool_brush)
        window.act_tool_brush_menu = act_tbrush.action

        act_teye = sm.register("tool_eyedropper", t("tool.eyedropper"), "Tools", "I", t("tool.eyedropper_desc"), tools_menu.addAction(t("tool.eyedropper")))
        act_teye.action.triggered.connect(window.action_tool_eyedropper)
        window.act_tool_eyedropper_menu = act_teye.action

        # ==========================================
        # 8. CONTEXTUAL BRUSH MENU
        # ==========================================
        brush_menu = menu_bar.addMenu(t("menu.brush"))
        window.brush_menu = brush_menu

        act_tbrush_studio = sm.register(
            "brush_studio",
            t("brush.studio"),
            "Brush",
            "F9",
            t("brush.studio_desc"),
            brush_menu.addAction(t("brush.studio")),
        )
        act_tbrush_studio.action.setCheckable(True)
        act_tbrush_studio.action.setChecked(window.brush_dock.isVisible() if hasattr(window, "brush_dock") else False)
        if hasattr(window, "set_brush_dock_visible"):
            act_tbrush_studio.action.toggled.connect(lambda checked: window.set_brush_dock_visible(checked, animate=True))
        elif hasattr(window, "brush_dock"):
            act_tbrush_studio.action.toggled.connect(window.brush_dock.setVisible)

        window.act_brush_studio = act_tbrush_studio.action

        def _sync_brush_action(vis: bool):
            try:
                action = act_tbrush_studio.action
                if action is not None and action.isChecked() != vis:
                    action.blockSignals(True)
                    action.setChecked(vis)
                    action.blockSignals(False)
            except (RuntimeError, AttributeError):
                pass

        if hasattr(window, "brush_dock"):
            window.brush_dock.visibilityChanged.connect(_sync_brush_action)

        act_bfocus_presets_action = brush_menu.addAction(t("brush.presets"))
        act_bfocus_presets_action.triggered.connect(getattr(window, "action_focus_brush_presets", lambda: None))
        sm.register("brush_focus_presets", t("brush.presets"), "Brush", "Ctrl+Shift+B", t("brush.presets_desc"), act_bfocus_presets_action)
        window.act_bfocus_presets = act_bfocus_presets_action

        act_bfocus_props_action = brush_menu.addAction(t("brush.properties"))
        act_bfocus_props_action.triggered.connect(getattr(window, "action_focus_brush_properties", lambda: None))
        sm.register("brush_focus_properties", t("brush.properties"), "Brush", "Alt+B", t("brush.properties_desc"), act_bfocus_props_action)
        window.act_bfocus_props = act_bfocus_props_action

        brush_menu.addSeparator()

        act_breset_action = brush_menu.addAction(t("brush.reset"))
        act_breset_action.triggered.connect(getattr(window, "action_reset_brush", lambda: None))
        sm.register("brush_reset_settings", t("brush.reset"), "Brush", "Shift+F9", t("brush.reset_desc"), act_breset_action)
        window.act_breset = act_breset_action

        act_bmode_action = brush_menu.addAction(t("brush.cycle_mode"))
        act_bmode_action.triggered.connect(getattr(window, "action_cycle_brush_mode", lambda: None))
        sm.register("brush_cycle_mode", t("brush.cycle_mode"), "Brush", "Shift+B", t("brush.cycle_mode_desc"), act_bmode_action)
        window.act_bmode = act_bmode_action

        brush_menu.addSeparator()

        act_bsize_dec_action = brush_menu.addAction(t("brush.decrease_size"))
        act_bsize_dec_action.triggered.connect(lambda: window.tool_brush.set_size(max(1, window.tool_brush.size - 2)) if hasattr(window, "tool_brush") else None)
        sm.register("brush_decrease_size", t("brush.decrease_size"), "Brush", "[", "Decrease brush tip diameter by 2 px", act_bsize_dec_action)
        window.act_bsize_dec = act_bsize_dec_action

        act_bsize_inc_action = brush_menu.addAction(t("brush.increase_size"))
        act_bsize_inc_action.triggered.connect(lambda: window.tool_brush.set_size(min(500, window.tool_brush.size + 2)) if hasattr(window, "tool_brush") else None)
        sm.register("brush_increase_size", t("brush.increase_size"), "Brush", "]", "Increase brush tip diameter by 2 px", act_bsize_inc_action)
        window.act_bsize_inc = act_bsize_inc_action

        act_bhard_dec_action = brush_menu.addAction(t("brush.decrease_hardness"))
        act_bhard_dec_action.triggered.connect(lambda: window.tool_brush.set_hardness(max(0.0, window.tool_brush.hardness - 0.10)) if hasattr(window, "tool_brush") else None)
        sm.register("brush_decrease_hardness", t("brush.decrease_hardness"), "Brush", "Ctrl+[", "Decrease brush tip hardness by 10%", act_bhard_dec_action)
        window.act_bhard_dec = act_bhard_dec_action

        act_bhard_inc_action = brush_menu.addAction(t("brush.increase_hardness"))
        act_bhard_inc_action.triggered.connect(lambda: window.tool_brush.set_hardness(min(1.0, window.tool_brush.hardness + 0.10)) if hasattr(window, "tool_brush") else None)
        sm.register("brush_increase_hardness", t("brush.increase_hardness"), "Brush", "Ctrl+]", "Increase brush tip hardness by 10%", act_bhard_inc_action)
        window.act_bhard_inc = act_bhard_inc_action

        # Contextual visibility: Initially hidden until Brush tool is activated
        brush_menu.menuAction().setVisible(False)

        # ==========================================
        # 9. THEME MENU
        # ==========================================
        theme_menu = menu_bar.addMenu(t("menu.theme"))
        window.menu_theme = theme_menu
        theme_group = QActionGroup(window)
        theme_group.setExclusive(True)
        window.theme_group = theme_group

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
        # 10. LANGUAGE MENU (Parto 0.4.0)
        # ==========================================
        lang_menu = menu_bar.addMenu(t("menu.language"))
        window.menu_language = lang_menu
        lang_group = QActionGroup(window)
        lang_group.setExclusive(True)
        window.lang_group = lang_group
        window.lang_actions = {}

        cls._populate_language_menu(lang_menu, lang_group, window)

        # ==========================================
        # 11. HELP MENU
        # ==========================================
        help_menu = menu_bar.addMenu(t("menu.help"))
        window.menu_help = help_menu

        act_palette = sm.register("help_palette", t("action.help.palette"), "App", "Ctrl+K", t("action.help.palette_desc"), help_menu.addAction(t("action.help.palette")))
        act_palette.action.triggered.connect(window.action_show_command_palette)
        window.act_palette = act_palette.action

        act_keys = sm.register("help_shortcuts", t("action.help.shortcuts"), "App", "F1", t("action.help.shortcuts_desc"), help_menu.addAction(t("action.help.shortcuts")))
        act_keys.action.triggered.connect(window.action_show_shortcuts)
        window.act_keys = act_keys.action

        help_menu.addSeparator()

        act_about = sm.register("help_about", t("action.help.about"), "App", "", t("action.help.about_desc", version=__version__), help_menu.addAction(t("action.help.about")))
        act_about.action.triggered.connect(window.action_show_about)
        window.act_about = act_about.action

    @classmethod
    def _populate_language_menu(cls, lang_menu: QMenu, lang_group: QActionGroup, window: Any) -> None:
        """Populate Language menu with all registered and discovered language catalogs."""
        lang_menu.clear()
        window.lang_actions.clear()

        lm = get_localization_manager()
        current_loc = lm.current_locale

        for meta in lm.get_available_languages():
            # Display format: e.g. "فارسی (Persian)" or "English (English)"
            if meta.native_name.strip() != meta.name.strip():
                display_title = f"{meta.native_name} ({meta.name})"
            else:
                display_title = meta.native_name

            lact = QAction(display_title, window)
            lact.setCheckable(True)
            lact.setData(meta.id)
            if meta.id == current_loc:
                lact.setChecked(True)

            def _make_handler(target_id: str):
                return lambda: lm.set_locale(target_id)

            lact.triggered.connect(_make_handler(meta.id))
            lang_group.addAction(lact)
            lang_menu.addAction(lact)
            window.lang_actions[meta.id] = lact

    @classmethod
    def retranslate_menus(cls, menu_bar: QMenuBar, window: Any) -> None:
        """
        Dynamically update all menu labels, action texts, tooltips, and shortcuts metadata
        without destroying widget hierarchy or disturbing document state.
        """
        sm = get_shortcut_manager()

        # Update Top Menu Bar Titles
        if hasattr(window, "menu_file"):
            window.menu_file.setTitle(t("menu.file"))
        if hasattr(window, "menu_edit"):
            window.menu_edit.setTitle(t("menu.edit"))
        if hasattr(window, "menu_view"):
            window.menu_view.setTitle(t("menu.view"))
        if hasattr(window, "menu_image"):
            window.menu_image.setTitle(t("menu.image"))
        if hasattr(window, "menu_layers"):
            window.menu_layers.setTitle(t("menu.layers"))
        if hasattr(window, "menu_filters"):
            window.menu_filters.setTitle(t("menu.filters"))
        if hasattr(window, "menu_tools"):
            window.menu_tools.setTitle(t("menu.tools"))
        if hasattr(window, "brush_menu"):
            window.brush_menu.setTitle(t("menu.brush"))
        if hasattr(window, "menu_theme"):
            window.menu_theme.setTitle(t("menu.theme"))
        if hasattr(window, "menu_language"):
            window.menu_language.setTitle(t("menu.language"))
        if hasattr(window, "menu_help"):
            window.menu_help.setTitle(t("menu.help"))

        # Helper to update both QAction and ShortcutManager
        def _update_act(act_attr: str, sid: str, key_name: str, key_desc: Optional[str] = None, **kwargs):
            action = getattr(window, act_attr, None)
            name = t(key_name, **kwargs)
            desc = t(key_desc, **kwargs) if key_desc else ""
            if action:
                action.setText(name)
                if desc:
                    action.setToolTip(desc)
            sm.update_metadata(sid, name, desc)

        # File
        _update_act("act_file_new", "file_new", "action.file.new", "action.file.new_desc")
        _update_act("act_file_open", "file_open", "action.file.open", "action.file.open_desc")
        _update_act("act_file_save", "file_save", "action.file.save", "action.file.save_desc")
        _update_act("act_file_save_as", "file_save_as", "action.file.save_as", "action.file.save_as_desc")
        _update_act("act_file_export", "file_export", "action.file.export", "action.file.export_desc")
        _update_act("act_file_info", "file_info", "action.file.info", "action.file.info_desc")
        _update_act("act_file_exit", "file_exit", "action.file.exit", "action.file.exit_desc")

        # Edit
        _update_act("act_undo", "edit_undo", "action.edit.undo", "action.edit.undo_desc")
        _update_act("act_redo", "edit_redo", "action.edit.redo", "action.edit.redo_desc")
        _update_act("act_crop", "edit_crop", "action.edit.crop", "action.edit.crop_desc")
        _update_act("act_resize", "edit_resize", "action.edit.resize", "action.edit.resize_desc")

        # View
        _update_act("act_zin", "view_zoom_in", "action.view.zoom_in", "action.view.zoom_in_desc")
        _update_act("act_zout", "view_zoom_out", "action.view.zoom_out", "action.view.zoom_out_desc")
        _update_act("act_zfit", "view_zoom_fit", "action.view.zoom_fit", "action.view.zoom_fit_desc")
        _update_act("act_z100", "view_zoom_100", "action.view.zoom_100", "action.view.zoom_100_desc")
        _update_act("act_fullscreen", "view_fullscreen", "action.view.fullscreen", "action.view.fullscreen_desc")
        _update_act("act_tlayers", "view_layers", "action.view.layers", "action.view.layers_desc")
        _update_act("act_tadj", "view_adjustments", "action.view.adjustments", "action.view.adjustments_desc")

        # Image
        _update_act("act_rcw", "img_rot_cw", "action.image.rotate_cw", "action.image.rotate_cw_desc")
        _update_act("act_rccw", "img_rot_ccw", "action.image.rotate_ccw", "action.image.rotate_ccw_desc")
        _update_act("act_r180", "img_rot_180", "action.image.rotate_180", "action.image.rotate_180_desc")
        _update_act("act_fliph", "img_flip_h", "action.image.flip_h", "action.image.flip_h_desc")
        _update_act("act_flipv", "img_flip_v", "action.image.flip_v", "action.image.flip_v_desc")
        _update_act("act_remove_bg", "img_remove_bg", "action.image.remove_bg", "action.image.remove_bg_desc")

        # Layers
        _update_act("act_nl", "layer_new", "action.layer.new", "action.layer.new_desc")
        _update_act("act_dl", "layer_dup", "action.layer.duplicate", "action.layer.duplicate_desc")
        _update_act("act_rml", "layer_del", "action.layer.delete", "action.layer.delete_desc")
        _update_act("act_mup", "layer_up", "action.layer.move_up", "action.layer.move_up_desc")
        _update_act("act_mdn", "layer_dn", "action.layer.move_down", "action.layer.move_down_desc")
        _update_act("act_mrg", "layer_mrg", "action.layer.merge_down", "action.layer.merge_down_desc")

        # Filters
        _update_act("act_fgallery", "filter_gallery", "action.filter.gallery", "action.filter.gallery_desc")
        if hasattr(window, "act_filter_grayscale"):
            window.act_filter_grayscale.setText(t("filter.grayscale"))
        if hasattr(window, "act_filter_sepia"):
            window.act_filter_sepia.setText(t("filter.sepia"))
        if hasattr(window, "act_filter_invert"):
            window.act_filter_invert.setText(t("filter.invert"))
        if hasattr(window, "act_filter_blur"):
            window.act_filter_blur.setText(t("filter.blur"))
        if hasattr(window, "act_filter_sharpen"):
            window.act_filter_sharpen.setText(t("filter.sharpen"))
        if hasattr(window, "act_filter_edge"):
            window.act_filter_edge.setText(t("filter.edge_detect"))
        if hasattr(window, "act_filter_emboss"):
            window.act_filter_emboss.setText(t("filter.emboss"))

        # Tools
        _update_act("act_tool_move_menu", "tool_move", "tool.move", "tool.move_desc")
        _update_act("act_tool_crop_menu", "tool_crop", "tool.crop", "tool.crop_desc")
        _update_act("act_tool_brush_menu", "tool_brush", "tool.brush", "tool.brush_desc")
        _update_act("act_tool_eyedropper_menu", "tool_eyedropper", "tool.eyedropper", "tool.eyedropper_desc")

        # Brush
        _update_act("act_brush_studio", "brush_studio", "brush.studio", "brush.studio_desc")
        _update_act("act_bfocus_presets", "brush_focus_presets", "brush.presets", "brush.presets_desc")
        _update_act("act_bfocus_props", "brush_focus_properties", "brush.properties", "brush.properties_desc")
        _update_act("act_breset", "brush_reset_settings", "brush.reset", "brush.reset_desc")
        _update_act("act_bmode", "brush_cycle_mode", "brush.cycle_mode", "brush.cycle_mode_desc")
        _update_act("act_bsize_dec", "brush_decrease_size", "brush.decrease_size")
        _update_act("act_bsize_inc", "brush_increase_size", "brush.increase_size")
        _update_act("act_bhard_dec", "brush_decrease_hardness", "brush.decrease_hardness")
        _update_act("act_bhard_inc", "brush_increase_hardness", "brush.increase_hardness")

        # Help
        _update_act("act_palette", "help_palette", "action.help.palette", "action.help.palette_desc")
        _update_act("act_keys", "help_shortcuts", "action.help.shortcuts", "action.help.shortcuts_desc")
        _update_act("act_about", "help_about", "action.help.about", "action.help.about_desc", version=__version__)

        # Refresh checked item in Language menu
        curr_loc = get_localization_manager().current_locale
        if hasattr(window, "lang_actions"):
            for lid, act in window.lang_actions.items():
                act.blockSignals(True)
                act.setChecked(lid == curr_loc)
                act.blockSignals(False)
