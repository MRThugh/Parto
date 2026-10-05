# parto/layers/operations/merger.py
"""
Parto Layers Subsystem — Layer Merging Operations
Author: Ali Kamrani (MRThugh)

Implements domain rules for layer merging:
- Preserves canvas dimensions and offset-aware placement
- Strict visibility semantics (hidden upper contributes no visible pixels)
- When both are hidden, internal composite is updated and visibility remains False
- Blending mode and opacity normalization
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from ..engine.compositor import compose_layers

if TYPE_CHECKING:
    from ..models.layer import Layer
    from ..models.layer_stack import LayerStack


def merge_down_layers(stack: LayerStack, index: int) -> Optional[Layer]:
    """
    Merge the layer at `index` into the layer beneath it (`index - 1`).
    
    Visibility and blending semantics:
    - Both visible: composited together, lower layer takes result, opacity=1.0, blend_mode='normal', visible=True.
    - Lower visible, upper hidden: upper contributes nothing to visible pixels.
    - Lower hidden, upper visible: lower takes upper's composite, adopts upper's blend_mode, visible=True.
    - Both hidden: composited internally, lower remains hidden (visible=False), blend_mode='normal'.
    
    Upon success, upper layer is removed from stack and active_index becomes `index - 1`.
    """
    if index <= 0 or index >= len(stack):
        return None

    lower = stack.layers[index - 1]
    upper = stack.layers[index]
    canvas_size = (stack.width, stack.height)

    if lower.visible and upper.visible:
        comp = compose_layers([lower, upper], canvas_size)
        lower.image = comp
        lower.offset_x = 0
        lower.offset_y = 0
        lower.opacity = 1.0
        lower.blend_mode = "normal"
        lower.visible = True
    elif lower.visible and not upper.visible:
        # Upper hidden: contributes nothing to visible pixels
        comp = compose_layers([lower], canvas_size)
        lower.image = comp
        lower.offset_x = 0
        lower.offset_y = 0
        lower.opacity = 1.0
        lower.visible = True
    elif not lower.visible and upper.visible:
        # Lower hidden: contributes nothing to visible pixels
        comp = compose_layers([upper], canvas_size)
        lower.image = comp
        lower.offset_x = 0
        lower.offset_y = 0
        lower.opacity = 1.0
        lower.blend_mode = upper.blend_mode or "normal"
        lower.visible = True
    else:
        # Both hidden: composite them for internal buffer, remain hidden
        temp_lower = lower.clone()
        temp_lower.visible = True
        temp_upper = upper.clone()
        temp_upper.visible = True
        comp = compose_layers([temp_lower, temp_upper], canvas_size)
        lower.image = comp
        lower.offset_x = 0
        lower.offset_y = 0
        lower.opacity = 1.0
        lower.blend_mode = "normal"
        lower.visible = False

    # Remove upper layer from stack and adjust active index
    stack._layers.pop(index)
    stack._active_index = index - 1
    return lower
