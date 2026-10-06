# parto/actions/registry.py
"""
Parto Architecture 2.0 — Central Action Registry
Author: Ali Kamrani (MRThugh)

Central catalog of all identifiable actions. Enables action discovery,
command palette lookups, category indexing, and legacy alias resolution.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from .action import Action, ActionContext


class ActionRegistry:
    """
    Central repository of actions in the application.
    """
    _instance: Optional[ActionRegistry] = None

    def __init__(self):
        self._actions: Dict[str, Action] = {}
        self._aliases: Dict[str, str] = {}

    @classmethod
    def instance(cls) -> ActionRegistry:
        if cls._instance is None:
            cls._instance = ActionRegistry()
        return cls._instance

    def register(self, action: Action) -> Action:
        """Register or update an action in the registry."""
        self._actions[action.id] = action
        return action

    def register_alias(self, alias_id: str, canonical_id: str) -> None:
        """Register a backward-compatible alias pointing to a canonical action ID."""
        self._aliases[alias_id] = canonical_id

    def unregister(self, action_id: str) -> Optional[Action]:
        """Remove action from registry."""
        resolved = self._aliases.get(action_id, action_id)
        action = self._actions.pop(resolved, None)
        self._aliases.pop(action_id, None)
        return action

    def get(self, action_id: str) -> Optional[Action]:
        """Look up action by ID or alias."""
        resolved = self._aliases.get(action_id, action_id)
        return self._actions.get(resolved)

    def __contains__(self, action_id: str) -> bool:
        resolved = self._aliases.get(action_id, action_id)
        return resolved in self._actions

    def get_all(self) -> List[Action]:
        """Return all registered unique actions."""
        return list(self._actions.values())

    def by_category(self, category: str) -> List[Action]:
        """Return all actions within a category."""
        return [act for act in self._actions.values() if act.category == category]

    def categories(self) -> List[str]:
        """Return unique sorted list of categories."""
        return sorted(list({act.category for act in self._actions.values()}))

    def search(self, query: str, context: Optional[ActionContext] = None) -> List[Action]:
        """
        Search registered actions matching the query string.
        Optionally filters out actions that are disabled in the given context.
        """
        results = [act for act in self._actions.values() if act.matches(query)]
        if context is not None:
            results = [act for act in results if act.is_enabled(context)]
        return results

    def execute(self, action_id: str, context: Optional[ActionContext] = None) -> Any:
        """Execute an action by ID or alias."""
        action = self.get(action_id)
        if action is None:
            raise KeyError(f"Action not found: {action_id}")
        return action.execute(context)

    def clear(self) -> None:
        """Clear registry."""
        self._actions.clear()
        self._aliases.clear()


def get_action_registry() -> ActionRegistry:
    return ActionRegistry.instance()
