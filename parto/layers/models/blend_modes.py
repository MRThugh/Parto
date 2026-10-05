# parto/layers/models/blend_modes.py
"""
Parto Layers Subsystem — Blend Modes
Author: Ali Kamrani (MRThugh)

Defines supported blend modes and canonical identifiers.
"""

from typing import Tuple

SUPPORTED_BLEND_MODES: Tuple[str, ...] = (
    "normal",
    "multiply",
    "screen",
    "overlay",
    "darken",
    "lighten",
)
