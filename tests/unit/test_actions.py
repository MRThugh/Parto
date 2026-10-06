# tests/unit/test_actions.py
"""
Unit Tests — Action Architecture 2.0
Author: Ali Kamrani (MRThugh)
Validates Action creation, ActionRegistry, ActionContext, contexts,
and ActionManager synchronization.
"""

import pytest
from PySide6.QtGui import QAction
from parto.actions.action import Action, ActionCategory, ActionContext
from parto.actions.registry import ActionRegistry
from parto.actions.context import ActionContextManager, ContextScope
from parto.actions.manager import ActionManager
from parto.actions.builtins import register_all_builtins


def test_action_creation_and_execution():
    """Verify Action contract: properties, enabled evaluation, execution."""
    executed = []

    act = Action(
        id="test.demo",
        name="Demo Action",
        description="A test demo action",
        category=ActionCategory.EDIT,
        default_shortcut="Ctrl+D",
        handler=lambda ctx: executed.append(ctx.context_name),
    )

    assert act.id == "test.demo"
    assert act.name == "Demo Action"
    assert act.category == ActionCategory.EDIT
    assert act.shortcut == "Ctrl+D"
    assert act.is_enabled() is True

    # Execute with default context
    act.execute(ActionContext(context_name="GLOBAL"))
    assert executed == ["GLOBAL"]


def test_action_enabled_and_checked_predicates():
    """Verify conditional enablement and checkable state."""
    act = Action(
        id="test.doc_op",
        name="Doc Op",
        is_enabled_fn=lambda ctx: ctx.has_document,
        checkable=True,
        checked=False,
    )

    ctx_empty = ActionContext(document=None)
    assert act.is_enabled(ctx_empty) is False

    class DummyDoc:
        has_image = True

    ctx_with_doc = ActionContext(document=DummyDoc())
    assert act.is_enabled(ctx_with_doc) is True

    # Checkable toggle on execute
    assert act.checked is False
    act.execute(ctx_with_doc)
    assert act.checked is True


def test_action_context_scoping():
    """Verify context-aware action restrictions."""
    act_brush = Action(
        id="test.brush_only",
        name="Brush Only Action",
        contexts=["BRUSH"],
        handler=lambda ctx: "brush_executed",
    )

    assert act_brush.is_enabled(ActionContext(context_name="CANVAS")) is False
    assert act_brush.is_enabled(ActionContext(context_name="BRUSH")) is True


def test_action_registry_crud_and_aliases():
    """Verify ActionRegistry registration, alias mapping, search, and categorization."""
    reg = ActionRegistry()
    act = Action(
        id="layer.create",
        name="New Layer",
        description="Add a new blank layer",
        category=ActionCategory.LAYER,
        default_shortcut="Ctrl+Shift+N",
    )

    reg.register(act)
    reg.register_alias("legacy_add_layer", "layer.create")

    # Direct retrieval
    assert reg.get("layer.create") is act
    # Alias retrieval
    assert reg.get("legacy_add_layer") is act
    assert "legacy_add_layer" in reg

    # Categories
    assert ActionCategory.LAYER in reg.categories()
    assert act in reg.by_category(ActionCategory.LAYER)

    # Search
    search_results = reg.search("blank layer")
    assert act in search_results

    # Unregister
    reg.unregister("layer.create")
    assert reg.get("layer.create") is None
    assert reg.get("legacy_add_layer") is None


def test_action_manager_qaction_binding(qapp):
    """Verify ActionManager generates synchronized QAction objects."""
    reg = ActionRegistry()
    register_all_builtins(reg)

    mgr = ActionManager()
    mgr.registry = reg

    qact = mgr.create_qaction("document.new")
    assert qact is not None
    assert isinstance(qact, QAction)
    assert qact.text() == "New Canvas..."
    assert qact.shortcut().toString() == "Ctrl+N"
