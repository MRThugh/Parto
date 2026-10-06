# parto/actions/context.py
"""
Parto Architecture 2.0 — Action Context Management
Author: Ali Kamrani (MRThugh)

Manages contextual scopes (GLOBAL, CANVAS, BRUSH, LAYERS, TEXT_INPUT, DIALOG)
to ensure actions and keyboard shortcuts respond accurately to active focus.
"""

from __future__ import annotations
from typing import List, Optional, Any
from .action import ActionContext


class ContextScope:
    GLOBAL = "GLOBAL"
    CANVAS = "CANVAS"
    BRUSH = "BRUSH"
    LAYERS = "LAYERS"
    PANEL = "PANEL"
    DIALOG = "DIALOG"
    TEXT_INPUT = "TEXT_INPUT"


class ActionContextManager:
    """
    Manages active context hierarchy and provides populated ActionContext instances.
    """
    _instance: Optional[ActionContextManager] = None

    def __init__(self):
        self._context_stack: List[str] = [ContextScope.GLOBAL]
        self._active_window: Optional[Any] = None
        self._active_document: Optional[Any] = None

    @classmethod
    def instance(cls) -> ActionContextManager:
        if cls._instance is None:
            cls._instance = ActionContextManager()
        return cls._instance

    def set_environment(self, window: Optional[Any] = None, document: Optional[Any] = None) -> None:
        self._active_window = window
        self._active_document = document

    def push_context(self, scope: str) -> None:
        """Push a new contextual scope to the top of stack."""
        self._context_stack.append(scope)

    def pop_context(self) -> str:
        """Pop top contextual scope from stack."""
        if len(self._context_stack) > 1:
            return self._context_stack.pop()
        return self._context_stack[0]

    def current_scope(self) -> str:
        """Return the current active scope name."""
        return self._context_stack[-1] if self._context_stack else ContextScope.GLOBAL

    def create_context(
        self,
        scope: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> ActionContext:
        """Create a fully populated ActionContext for evaluating actions."""
        win = self._active_window
        doc = getattr(win, "document", None) or self._active_document
        canvas = getattr(win, "canvas", None)
        active_tool = getattr(canvas, "active_tool", None) if canvas else None

        return ActionContext(
            context_name=scope or self.current_scope(),
            document=doc,
            window=win,
            canvas=canvas,
            active_tool=active_tool,
            extra=extra or {},
        )


def get_context_manager() -> ActionContextManager:
    return ActionContextManager.instance()
