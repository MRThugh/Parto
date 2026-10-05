# parto/editor/document.py
"""
Parto — Document Compatibility Shim
Author: Ali Kamrani (MRThugh)

Maintains 100% backward-compatible imports by re-exporting the authoritative
Document model and snapshot utilities from the parto.document domain subsystem.
"""

from __future__ import annotations
from ..document.document import Document
from ..document.history.transaction import snapshots_equal

__all__ = ["Document", "snapshots_equal"]
