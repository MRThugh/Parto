# parto/ui/toolbar.py
"""
Parto v0.3.0 - Unified Dynamic Application Toolbar
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QToolBar,
    QWidget,
    QComboBox,
    QLabel,
)
from ..resources.icons import get_parto_icon
from ..themes.manager import get_theme_manager
from ..themes.palettes import THEMES


class EditorToolBar(QToolBar):
    """
    Primary editor toolbar with vector icons and dynamic theme awareness.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Main Toolbar", parent)
        self.setObjectName("MainToolBar")
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)

        self._actions: Dict[str, QAction] = {}
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

        action = QAction(icon, name, self)
        action.setCheckable(checkable)
        action.setData(icon_name)

        if is_tool:
            self._tool_action_group.addAction(action)

        self.addAction(action)
        self._actions[action_id] = action
        return action

    def get_action(self, action_id: str) -> Optional[QAction]:
        return self._actions.get(action_id)

    def _on_theme_changed(self, _: str):
        """Update all action icons to contrast with the new theme palette."""
        icon_color = get_theme_manager().get_icon_color()

        for action in self._actions.values():
            icon_name = action.data()
            if icon_name:
                action.setIcon(get_parto_icon(icon_name, icon_color, 20))
