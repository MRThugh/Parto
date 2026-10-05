# parto/document/history/__init__.py
"""
Parto Document Subsystem History
Author: Ali Kamrani (MRThugh)
"""

from .transaction import TransactionCoordinator, snapshots_equal

__all__ = ["TransactionCoordinator", "snapshots_equal"]
