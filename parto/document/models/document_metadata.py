# parto/document/models/document_metadata.py
"""
Parto Document Subsystem — Metadata and Snapshot Types
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate human-readable aspect ratio from width and height."""
    if width <= 0 or height <= 0:
        return "N/A"

    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    d = gcd(width, height)
    return f"{width // d}:{height // d}"


def calculate_megapixels(width: int, height: int) -> str:
    """Calculate formatted megapixels count from dimensions."""
    if width <= 0 or height <= 0:
        return "0.0 MP"
    mp = (width * height) / 1_000_000.0
    return f"{mp:.1f} MP"
