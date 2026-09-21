# parto/shortcuts/manager.py
"""
Parto v0.3.0 - Centralized Shortcut Manager
Coordinates action shortcuts, categories, conflicts, and discovery dialogs.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from PySide6.QtGui import QKeySequence, QAction


@dataclass
class ShortcutDefinition:
    action_id: str
    name: str
    category: str
    key_sequence: str
    description: str
    action: Optional[QAction] = None


class ShortcutManager:
    """
    Centralized registry of application keyboard shortcuts.
    """
    _instance: Optional[ShortcutManager] = None

    def __init__(self):
        self._shortcuts: Dict[str, ShortcutDefinition] = {}

    @classmethod
    def instance(cls) -> ShortcutManager:
        if cls._instance is None:
            cls._instance = ShortcutManager()
        return cls._instance

    def register(
        self,
        action_id: str,
        name: str,
        category: str,
        key_sequence: str,
        description: str,
        action: Optional[QAction] = None,
    ) -> ShortcutDefinition:
        """
        Register or update a shortcut in the registry.
        """
        # Detect conflicts if key_sequence already in use
        if key_sequence:
            for existing_id, existing_defn in self._shortcuts.items():
                if existing_id != action_id and existing_defn.key_sequence.lower() == key_sequence.lower():
                    import logging
                    logging.getLogger("parto.shortcuts").warning(
                        f"[Parto Shortcut Conflict] Shortcut '{key_sequence}' registered for '{action_id}' conflicts with '{existing_id}'"
                    )

        defn = ShortcutDefinition(
            action_id=action_id,
            name=name,
            category=category,
            key_sequence=key_sequence,
            description=description,
            action=action,
        )
        self._shortcuts[action_id] = defn

        if action is not None and key_sequence:
            action.setShortcut(QKeySequence(key_sequence))
            # Format tooltip with shortcut
            base_tip = description or name
            action.setToolTip(f"{base_tip} ({key_sequence})")

        return defn

    def find_conflicts(self) -> Dict[str, List[str]]:
        """Return any duplicated keyboard shortcuts."""
        seen: Dict[str, List[str]] = {}
        for action_id, defn in self._shortcuts.items():
            if defn.key_sequence:
                norm = defn.key_sequence.lower()
                seen.setdefault(norm, []).append(action_id)
        return {k: v for k, v in seen.items() if len(v) > 1}

    def __contains__(self, action_id: str) -> bool:
        return action_id in self._shortcuts

    def get(self, action_id: str) -> Optional[ShortcutDefinition]:
        return self._shortcuts.get(action_id)

    def get_all(self) -> List[ShortcutDefinition]:
        return list(self._shortcuts.values())

    def get_by_category(self) -> Dict[str, List[ShortcutDefinition]]:
        categories: Dict[str, List[ShortcutDefinition]] = {}
        for defn in self._shortcuts.values():
            categories.setdefault(defn.category, []).append(defn)
        return categories

    def get_action(self, action_id: str) -> Optional[QAction]:
        defn = self._shortcuts.get(action_id)
        return defn.action if defn else None

    def get_shortcut_string(self, action_id: str) -> str:
        defn = self._shortcuts.get(action_id)
        return defn.key_sequence if defn else ""


def get_shortcut_manager() -> ShortcutManager:
    return ShortcutManager.instance()
