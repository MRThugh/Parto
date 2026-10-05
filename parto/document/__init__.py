# parto/document/__init__.py
"""
Parto Document Domain Subsystem
Author: Ali Kamrani (MRThugh)

Provides the authoritative Document model, state container, engines,
and transactions for image editing.
"""

from .document import Document
from .models.document_state import DocumentState
from .engine.document_engine import DocumentEngine
from .engine.transform_engine import TransformEngine
from .engine.compositing_engine import CompositingEngine
from .adapters.storage_adapter import DocumentStorageAdapter
from .history.transaction import TransactionCoordinator, snapshots_equal
from .controller.document_controller import DocumentController

__all__ = [
    "Document",
    "DocumentState",
    "DocumentEngine",
    "TransformEngine",
    "CompositingEngine",
    "DocumentStorageAdapter",
    "TransactionCoordinator",
    "snapshots_equal",
    "DocumentController",
]
