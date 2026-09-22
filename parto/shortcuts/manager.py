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

    Conflict Resolution Rules:
    --------------------------
    1. Default Policy ("track"):
       When a shortcut collision is detected during registration or remapping,
       the conflict is logged via the logging system and indexed in `find_conflicts()`.
       Both registrations are maintained for diagnostic introspection and discovery dialogs.
    2. Override Policy ("override" or `override=True`):
       The new registration takes deterministic precedence. The previous owner of
       the shortcut has its key sequence and QAction shortcut explicitly cleared,
       preventing ambiguous Qt WindowShortcut events.
    3. Strict Policy ("reject" or `reject_on_conflict=True`):
       Raises ValueError with details of the conflicting action.
    4. Explicit Resolution:
       `resolve_conflict(key_sequence, keep_action_id)` can be called to deterministically
       assign the shortcut to the chosen action and unbind all others.
    """
    _instance: Optional[ShortcutManager] = None

    def __init__(self, default_policy: str = "track"):
        self._shortcuts: Dict[str, ShortcutDefinition] = {}
        self.default_policy: str = default_policy

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
        policy: Optional[str] = None,
    ) -> ShortcutDefinition:
        """
        Register or update a shortcut in the registry.
        """
        active_policy = policy or self.default_policy

        # Detect conflicts if key_sequence already in use
        if key_sequence:
            norm_new = key_sequence.strip().lower()
            conflicting_ids = [
                existing_id for existing_id, existing_defn in self._shortcuts.items()
                if existing_id != action_id
                and existing_defn.key_sequence
                and existing_defn.key_sequence.strip().lower() == norm_new
            ]

            if conflicting_ids:
                import logging
                log = logging.getLogger("parto.shortcuts")
                log.warning(
                    f"[Parto Shortcut Conflict] Shortcut '{key_sequence}' for '{action_id}' conflicts with {conflicting_ids}"
                )

                if active_policy == "reject":
                    raise ValueError(
                        f"Shortcut conflict: '{key_sequence}' is already assigned to {conflicting_ids}"
                    )
                elif active_policy == "override":
                    for cid in conflicting_ids:
                        self.unbind_shortcut(cid)

        defn = ShortcutDefinition(
            action_id=action_id,
            name=name,
            category=category,
            key_sequence=key_sequence,
            description=description,
            action=action,
        )
        self._shortcuts[action_id] = defn

        if action is not None:
            if key_sequence:
                from PySide6.QtCore import Qt
                action.setShortcut(QKeySequence(key_sequence))
                action.setShortcutContext(Qt.WindowShortcut)
                # Format tooltip with shortcut
                base_tip = description or name
                action.setToolTip(f"{base_tip} ({key_sequence})")
            else:
                action.setShortcut(QKeySequence())
                base_tip = description or name
                action.setToolTip(base_tip)

        return defn

    def unbind_shortcut(self, action_id: str) -> bool:
        """Unbind shortcut from an action, keeping the action registered with no key sequence."""
        defn = self._shortcuts.get(action_id)
        if not defn:
            return False
        defn.key_sequence = ""
        if defn.action is not None:
            defn.action.setShortcut(QKeySequence())
            base_tip = defn.description or defn.name
            defn.action.setToolTip(base_tip)
        return True

    def resolve_conflict(self, key_sequence: str, keep_action_id: str) -> bool:
        """
        Deterministically resolve a shortcut collision: assign key_sequence exclusively
        to keep_action_id and unbind it from any other actions.
        """
        norm = key_sequence.strip().lower()
        found = False
        for aid, defn in list(self._shortcuts.items()):
            if defn.key_sequence and defn.key_sequence.strip().lower() == norm:
                if aid != keep_action_id:
                    self.unbind_shortcut(aid)
                else:
                    found = True

        if not found and keep_action_id in self._shortcuts:
            self.remap_shortcut(keep_action_id, key_sequence)
            return True
        return found

    def remap_shortcut(self, action_id: str, new_key_sequence: str, policy: Optional[str] = None) -> bool:
        """
        Dynamically update key sequence for a registered action, synchronizing with QAction.
        """
        defn = self._shortcuts.get(action_id)
        if not defn:
            return False

        active_policy = policy or self.default_policy

        if new_key_sequence:
            norm_new = new_key_sequence.strip().lower()
            conflicting_ids = [
                existing_id for existing_id, existing_defn in self._shortcuts.items()
                if existing_id != action_id
                and existing_defn.key_sequence
                and existing_defn.key_sequence.strip().lower() == norm_new
            ]
            if conflicting_ids:
                import logging
                log = logging.getLogger("parto.shortcuts")
                log.warning(
                    f"[Parto Shortcut Conflict] Shortcut '{new_key_sequence}' remapped for '{action_id}' conflicts with {conflicting_ids}"
                )
                if active_policy == "reject":
                    raise ValueError(
                        f"Shortcut conflict: '{new_key_sequence}' is already assigned to {conflicting_ids}"
                    )
                elif active_policy == "override":
                    for cid in conflicting_ids:
                        self.unbind_shortcut(cid)

        defn.key_sequence = new_key_sequence
        if defn.action is not None:
            if new_key_sequence:
                from PySide6.QtCore import Qt
                defn.action.setShortcut(QKeySequence(new_key_sequence))
                defn.action.setShortcutContext(Qt.WindowShortcut)
                base_tip = defn.description or defn.name
                defn.action.setToolTip(f"{base_tip} ({new_key_sequence})")
            else:
                defn.action.setShortcut(QKeySequence())
                defn.action.setToolTip(defn.description or defn.name)
        return True

    def find_conflicts(self) -> Dict[str, List[str]]:
        """Return any duplicated keyboard shortcuts."""
        seen: Dict[str, List[str]] = {}
        for action_id, defn in self._shortcuts.items():
            if defn.key_sequence:
                norm = defn.key_sequence.strip().lower()
                seen.setdefault(norm, []).append(action_id)
        return {k: v for k, v in seen.items() if len(v) > 1}

    def assert_no_conflicts(self) -> bool:
        """Validate that there are zero shortcut collisions in the registry."""
        conflicts = self.find_conflicts()
        if conflicts:
            raise AssertionError(f"Detected shortcut conflicts: {conflicts}")
        return True

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
