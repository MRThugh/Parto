# parto/layers/engine/compositor.py
"""
Parto Layers Subsystem — Compositor Engine
Author: Ali Kamrani (MRThugh)

Responsible for compositing an ordered sequence of Layer models into a single RGBA image.
Respects stacking order (index 0 bottom to index N-1 top), visibility flags, opacity scaling,
positional offsets, and blend mode calculations.
"""

from __future__ import annotations
from typing import Sequence, Tuple
from PIL import Image

from ..models.layer import Layer
from .blender import blend_mode_composite


def compose_layers(
    layers: Sequence[Layer],
    canvas_size: Tuple[int, int],
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    """
    Composite an ordered stack of layers into a single output image.
    Layers are processed from index 0 (bottom/background) to index N-1 (top/foreground).
    Respects visibility, opacity, offset, and blend modes without mutating layer images.
    """
    cw, ch = canvas_size
    if cw <= 0 or ch <= 0:
        return Image.new("RGBA", (1, 1), bg_color)

    composite = Image.new("RGBA", (cw, ch), bg_color)

    visible_layers = [lay for lay in layers if lay.visible and lay.opacity > 0.0]
    if not visible_layers:
        return composite

    for lay in visible_layers:
        layer_img = lay.image
        if layer_img is None or layer_img.width <= 0 or layer_img.height <= 0:
            continue

        # Adjust alpha by layer opacity if opacity < 1.0 (without modifying original)
        if lay.opacity < 0.999:
            r, g, b, a = layer_img.split()
            alpha_lut = [int(v * lay.opacity) for v in range(256)]
            a = a.point(alpha_lut)
            adjusted_layer = Image.merge("RGBA", (r, g, b, a))
        else:
            adjusted_layer = layer_img

        pos = (lay.offset_x, lay.offset_y)
        b_mode = (lay.blend_mode or "normal").lower()

        if b_mode in ("multiply", "screen", "overlay", "darken", "lighten"):
            blend_mode_composite(composite, adjusted_layer, pos, b_mode)
        else:
            composite.alpha_composite(adjusted_layer, dest=pos)

    return composite


class LayerCompositor:
    """
    Stateful or reusable compositor providing high-level layer composition services.
    """

    def __init__(self, bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)):
        self.bg_color = bg_color

    def composite(
        self, layers: Sequence[Layer], canvas_size: Tuple[int, int]
    ) -> Image.Image:
        """Composite layers using configured background color."""
        return compose_layers(layers, canvas_size, bg_color=self.bg_color)
