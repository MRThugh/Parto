# parto/actions/__init__.py
"""
Parto Architecture 2.0 — Action Subsystem
Author: Ali Kamrani (MRThugh)

Central entry point for Parto's Action architecture.
"""

from .action import Action, ActionCategory, ActionContext
from .registry import ActionRegistry, get_action_registry
from .context import ActionContextManager, ContextScope, get_context_manager
from .manager import ActionManager, get_action_manager
from .builtins import get_all_builtin_actions, register_all_builtins

__all__ = [
    "Action",
    "ActionCategory",
    "ActionContext",
    "ActionRegistry",
    "get_action_registry",
    "ActionContextManager",
    "ContextScope",
    "get_context_manager",
    "ActionManager",
    "get_action_manager",
    "get_all_builtin_actions",
    "register_all_builtins",
]
