# parto/ui/toolbar.py
"""
Parto v0.4.0 - Unified Dynamic Application Toolbar
Vector icons, dynamic theme awareness, and runtime localization support.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QToolBar,
    QWidget,
)
from ..resources.icons import get_parto_icon
from ..themes.manager import get_theme_manager
from ..localization import t


TOOLBAR_ACTION_KEYS = {
    "new": "action.file.new",
    "open": "action.file.open",
    "save": "action.file.save",
    "undo": "action.edit.undo",
    "redo": "action.edit.redo",
    "tool_move": "tool.move",
    "tool_crop": "tool.crop",
    "tool_brush": "tool.brush",
    "tool_eyedropper": "tool.eyedropper",
    "zoom_in": "action.view.zoom_in",
    "zoom_out": "action.view.zoom_out",
    "zoom_fit": "action.view.zoom_fit",
    "zoom_actual": "action.view.zoom_100",
    "rot_left": "action.image.rotate_ccw",
    "rot_right": "action.image.rotate_cw",
    "flip_h": "action.image.flip_h",
    "flip_v": "action.image.flip_v",
    "layers": "action.view.layers",
    "adjust": "action.view.adjustments",
    "brush_panel": "brush.studio",
}


class EditorToolBar(QToolBar):
    """
    Primary editor toolbar with vector icons, dynamic theme awareness,
    and runtime localization.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Main Toolbar", parent)
        self.setObjectName("MainToolBar")
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self._actions: Dict[str, QAction] = {}
        self._action_defaults: Dict[str, str] = {}
        self._tool_action_group = QActionGroup(self)
        self._tool_action_group.setExclusive(True)

        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def register_action(
        self,
        action_id: str,
        name: str,
        icon_name: str,
        checkable: bool = False,
        is_tool: bool = False,
    ) -> QAction:
        """Create and add action to toolbar with resolution-independent icon."""
        icon_color = get_theme_manager().get_icon_color()
        icon = get_parto_icon(icon_name, icon_color, 20)

        self._action_defaults[action_id] = name
        key = TOOLBAR_ACTION_KEYS.get(action_id)
        display_text = t(key, default=name) if key else name

        action = QAction(icon, display_text, self)
        action.setToolTip(display_text)
        action.setCheckable(checkable)
        action.setData(icon_name)

        if is_tool:
            self._tool_action_group.addAction(action)

        self.addAction(action)
        self._actions[action_id] = action
        return action

    def get_action(self, action_id: str) -> Optional[QAction]:
        return self._actions.get(action_id)

    def retranslate_ui(self) -> None:
        """Refresh action titles and tooltips with current locale."""
        for action_id, action in self._actions.items():
            key = TOOLBAR_ACTION_KEYS.get(action_id)
            default_name = self._action_defaults.get(action_id, "")
            display_text = t(key, default=default_name) if key else default_name
            if display_text:
                action.setText(display_text)
                action.setToolTip(display_text)

    def _on_theme_changed(self, _: str):
        """Update all action icons to contrast with the new theme palette."""
        icon_color = get_theme_manager().get_icon_color()

        for action in self._actions.values():
            icon_name = action.data()
            if icon_name:
                action.setIcon(get_parto_icon(icon_name, icon_color, 20))
