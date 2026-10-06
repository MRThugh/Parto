# parto/actions/manager.py
"""
Parto Architecture 2.0 — Action Manager
Author: Ali Kamrani (MRThugh)

Coordinates between ActionRegistry, ShortcutManager, and Qt UI elements.
Creates bound QAction instances, manages shortcuts, and ensures bidirectional
synchronization between Actions and widgets.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QObject, Qt

from .action import Action, ActionContext
from .registry import ActionRegistry, get_action_registry
from .context import ActionContextManager, get_context_manager
from ..shortcuts.manager import ShortcutManager, get_shortcut_manager
from ..resources.icons import get_parto_icon
from ..themes.manager import get_theme_manager


class ActionManager(QObject):
    """
    Coordinates application actions with GUI widgets and shortcuts.
    """
    _instance: Optional[ActionManager] = None

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.registry: ActionRegistry = get_action_registry()
        self.context_mgr: ActionContextManager = get_context_manager()
        self.shortcut_mgr: ShortcutManager = get_shortcut_manager()
        self._qactions: Dict[str, QAction] = {}

    @classmethod
    def instance(cls) -> ActionManager:
        if cls._instance is None:
            cls._instance = ActionManager()
        return cls._instance

    def lookup(self, action_id: str) -> Optional[Action]:
        """Look up an Action by ID or alias."""
        return self.registry.get(action_id)

    def get_action(self, action_id: str) -> Optional[Action]:
        """Alias for lookup."""
        return self.registry.get(action_id)

    def create_qaction(self, action_id: str, parent: Optional[QObject] = None) -> Optional[QAction]:
        """
        Create and return a QAction bound directly to the specified Action in ActionRegistry.
        Registers the shortcut with ShortcutManager.
        """
        action = self.registry.get(action_id)
        if action is None:
            return None

        canonical_id = action.id

        # Reuse existing QAction if available
        if canonical_id in self._qactions:
            qact = self._qactions[canonical_id]
            if action_id != canonical_id:
                self._qactions[action_id] = qact
            return qact
        if action_id in self._qactions:
            return self._qactions[action_id]

        qact = QAction(action.name, parent or self)
        qact.setObjectName(action.id)

        # Set Icon if available
        if action.icon_name:
            icon_color = get_theme_manager().get_icon_color()
            qact.setIcon(get_parto_icon(action.icon_name, icon_color, 18))

        # Checkable
        if action.checkable:
            qact.setCheckable(True)
            qact.setChecked(action.checked)

        # Tooltip
        base_tip = action.description or action.name
        if action.shortcut:
            qact.setShortcut(QKeySequence(action.shortcut))
            qact.setShortcutContext(Qt.WindowShortcut)
            qact.setToolTip(f"{base_tip} ({action.shortcut})")
        else:
            qact.setToolTip(base_tip)

        # Dispatch triggered event to Action.execute
        def _on_triggered(checked: bool = False):
            ctx = self.context_mgr.create_context()
            if action.checkable:
                action.checked = checked
            action.execute(ctx)

        qact.triggered.connect(_on_triggered)

        # Register in ShortcutManager
        self.shortcut_mgr.register(
            action_id=action.id,
            name=action.name,
            category=action.category,
            key_sequence=action.shortcut,
            description=action.description,
            action=qact,
        )

        self._qactions[canonical_id] = qact
        if action_id != canonical_id:
            self._qactions[action_id] = qact
        return qact

    def get_qaction(self, action_id: str) -> Optional[QAction]:
        """Retrieve existing QAction by canonical ID or alias."""
        if action_id in self._qactions:
            return self._qactions[action_id]
        action = self.registry.get(action_id)
        if action and action.id in self._qactions:
            return self._qactions[action.id]
        return None

    def sync_shortcut(self, action_id: str, new_shortcut: str) -> bool:
        """Update shortcut on Action, QAction, and ShortcutManager."""
        action = self.registry.get(action_id)
        if action is None:
            return False
        action.shortcut = new_shortcut
        qact = self.get_qaction(action_id)
        if qact is not None:
            qact.setShortcut(QKeySequence(new_shortcut))
            base_tip = action.description or action.name
            if new_shortcut:
                qact.setToolTip(f"{base_tip} ({new_shortcut})")
            else:
                qact.setToolTip(base_tip)
        self.shortcut_mgr.set_shortcut(action.id, new_shortcut)
        return True

    def trigger(self, action_id: str) -> Any:
        """Trigger an action by ID directly using current context."""
        ctx = self.context_mgr.create_context()
        action = self.registry.get(action_id)
        if action is not None:
            return action.execute(ctx)
        return None

    def sync_action_state(self, action_id: str) -> None:
        """Update enabled and checked state of a specific QAction."""
        qact = self.get_qaction(action_id)
        action = self.registry.get(action_id)
        if qact is not None and action is not None:
            ctx = self.context_mgr.create_context()
            qact.setEnabled(action.is_enabled(ctx))
            if action.checkable:
                qact.setChecked(action.is_checked(ctx))

    def update_states(self) -> None:
        """Evaluate enabled and checked states across all registered QActions."""
        ctx = self.context_mgr.create_context()
        seen = set()
        for action_id, qact in list(self._qactions.items()):
            if id(qact) in seen:
                continue
            seen.add(id(qact))
            action = self.registry.get(action_id)
            if action is not None:
                qact.setEnabled(action.is_enabled(ctx))
                if action.checkable:
                    qact.setChecked(action.is_checked(ctx))


def get_action_manager() -> ActionManager:
    return ActionManager.instance()
