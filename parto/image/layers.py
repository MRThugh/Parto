# parto/image/layers.py
"""
Parto — Layers Compatibility Shim
Author: Ali Kamrani (MRThugh)

Maintains 100% backward compatibility by re-exporting authoritative Layer,
LayerStack, compose_layers, and blend modes from the parto.layers domain subsystem.
"""

from __future__ import annotations
from ..layers import (
    Layer,
    LayerStack,
    SUPPORTED_BLEND_MODES,
    compose_layers,
    blend_mode_composite,
    _blend_mode_composite,
)

__all__ = [
    "Layer",
    "LayerStack",
    "SUPPORTED_BLEND_MODES",
    "compose_layers",
    "blend_mode_composite",
    "_blend_mode_composite",
]
