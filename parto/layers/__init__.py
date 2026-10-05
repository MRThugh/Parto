# parto/layers/__init__.py
"""
Parto Layers Domain Subsystem
Author: Ali Kamrani (MRThugh)

First-class domain subsystem providing authoritative multi-layer models,
collection invariants, mathematical blend modes, and compositing services.
"""

from .models.layer import Layer
from .models.layer_stack import LayerStack
from .models.blend_modes import SUPPORTED_BLEND_MODES
from .engine.compositor import compose_layers, LayerCompositor
from .engine.blender import blend_mode_composite, _blend_mode_composite
from .operations.merger import merge_down_layers

__all__ = [
    "Layer",
    "LayerStack",
    "SUPPORTED_BLEND_MODES",
    "compose_layers",
    "LayerCompositor",
    "blend_mode_composite",
    "_blend_mode_composite",
    "merge_down_layers",
]
