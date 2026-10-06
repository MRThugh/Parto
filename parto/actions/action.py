# parto/actions/action.py
"""
Parto Architecture 2.0 — Action Contract & Context Model
Author: Ali Kamrani (MRThugh)

Defines what the user wants to do, decoupled from widgets and domain state.
Actions are identifiable, searchable, executable, enable/disable aware,
context-aware, and bindable to menus, toolbars, shortcuts, and command palettes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional, Any, List, Dict


class ActionCategory:
    """Standardized action categories."""
    APPLICATION = "Application"
    FILE = "File"
    EDIT = "Edit"
    VIEW = "View"
    IMAGE = "Image"
    LAYER = "Layer"
    BRUSH = "Brush"
    SELECTION = "Selection"
    TRANSFORM = "Transform"
    FILTER = "Filter"
    HELP = "Help"


@dataclass
class ActionContext:
    """
    Evaluation context providing state introspection to Actions.
    Prevents Actions from directly querying GUI widgets.
    """
    context_name: str = "GLOBAL"
    document: Optional[Any] = None
    window: Optional[Any] = None
    canvas: Optional[Any] = None
    active_tool: Optional[Any] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_document(self) -> bool:
        return self.document is not None and getattr(self.document, "has_image", False)

    @property
    def active_layer(self) -> Optional[Any]:
        return getattr(self.document, "active_layer", None) if self.document else None

    @property
    def can_undo(self) -> bool:
        if self.document and hasattr(self.document, "history"):
            return self.document.history.can_undo
        return False

    @property
    def can_redo(self) -> bool:
        if self.document and hasattr(self.document, "history"):
            return self.document.history.can_redo
        return False


class Action:
    """
    Authoritative representation of a user intent in Parto.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        category: str = ActionCategory.APPLICATION,
        default_shortcut: str = "",
        icon_name: Optional[str] = None,
        checkable: bool = False,
        checked: bool = False,
        contexts: Optional[List[str]] = None,
        handler: Optional[Callable[[ActionContext], Any]] = None,
        is_enabled_fn: Optional[Callable[[ActionContext], bool]] = None,
        is_checked_fn: Optional[Callable[[ActionContext], bool]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description or name
        self.category = category
        self.default_shortcut = default_shortcut
        self.shortcut = default_shortcut
        self.icon_name = icon_name
        self.checkable = checkable
        self._checked = checked
        self.contexts = contexts or ["GLOBAL"]
        self.handler = handler
        self.is_enabled_fn = is_enabled_fn
        self.is_checked_fn = is_checked_fn

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, val: bool) -> None:
        self._checked = bool(val)

    def is_enabled(self, context: Optional[ActionContext] = None) -> bool:
        """Evaluate whether this action is currently available."""
        ctx = context or ActionContext()
        # Context scope check
        if "GLOBAL" not in self.contexts and ctx.context_name not in self.contexts:
            return False

        if self.is_enabled_fn is not None:
            try:
                return bool(self.is_enabled_fn(ctx))
            except Exception:
                return False
        return True

    def is_checked(self, context: Optional[ActionContext] = None) -> bool:
        """Evaluate checked state for checkable actions."""
        if not self.checkable:
            return False
        if self.is_checked_fn is not None:
            ctx = context or ActionContext()
            try:
                return bool(self.is_checked_fn(ctx))
            except Exception:
                pass
        return self._checked

    def execute(self, context: Optional[ActionContext] = None) -> Any:
        """Execute action intent."""
        ctx = context or ActionContext()
        if not self.is_enabled(ctx):
            return None

        if self.checkable:
            self._checked = not self._checked

        if self.handler is not None:
            return self.handler(ctx)
        return None

    def matches(self, query: str) -> bool:
        """Return True if query matches action name, description, shortcut, or id."""
        if not query:
            return True
        q = query.lower().strip()
        return (
            q in self.name.lower()
            or q in self.description.lower()
            or q in self.id.lower()
            or q in self.category.lower()
            or (self.shortcut and q in self.shortcut.lower())
        )

    def __repr__(self) -> str:
        return f"<Action id={self.id!r} name={self.name!r} shortcut={self.shortcut!r}>"
