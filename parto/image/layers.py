# parto/image/layers.py
"""
Parto v0.3.0 - Multi-Layer Image Architecture
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import uuid
from typing import Any, List, Tuple, Optional
from PIL import Image
import numpy as np


class Layer:
    """
    A single image layer in a document.
    Maintains image data (RGBA), visibility, opacity, blend mode, and offset.
    """

    def __init__(
        self,
        arg1: Any = None,
        arg2: Any = None,
        name: Optional[str] = None,
        image: Optional[Image.Image] = None,
        visible: bool = True,
        opacity: float = 1.0,
        blend_mode: str = "normal",
        offset_x: int = 0,
        offset_y: int = 0,
        layer_id: Optional[str] = None,
    ):
        self.id: str = layer_id or str(uuid.uuid4())[:8]

        actual_image = image
        actual_name = name

        for arg in (arg1, arg2):
            if isinstance(arg, Image.Image):
                actual_image = arg
            elif isinstance(arg, str):
                actual_name = arg

        if actual_name is None:
            actual_name = "Layer"

        self.name: str = actual_name
        self.visible: bool = visible
        self.opacity: float = max(0.0, min(1.0, float(opacity)))
        self.blend_mode: str = blend_mode
        self.offset_x: int = int(offset_x)
        self.offset_y: int = int(offset_y)

        if actual_image is not None:
            if isinstance(actual_image, (tuple, list)):
                self.image: Image.Image = Image.new("RGBA", (100, 100), tuple(actual_image))
            elif actual_image.mode != "RGBA":
                self.image = actual_image.convert("RGBA")
            else:
                self.image = actual_image.copy()
        else:
            self.image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    def clone(self, preserve_id: bool = True, preserve_name: bool = True) -> Layer:
        """Create a deep copy of this layer, preserving name and id by default for snapshots."""
        return Layer(
            name=self.name if preserve_name else f"{self.name} (Copy)",
            image=self.image.copy(),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            layer_id=self.id if preserve_id else None,
        )

    def duplicate(self) -> Layer:
        """Create an intentional user-facing duplicate with a new ID and (Copy) name suffix."""
        return self.clone(preserve_id=False, preserve_name=False)

    def set_opacity(self, value: float):
        self.opacity = max(0.0, min(1.0, float(value)))


def _blend_mode_composite(
    base_img: Image.Image,
    top_img: Image.Image,
    pos: Tuple[int, int],
    mode: str,
) -> None:
    """Apply non-normal blend modes (multiply, screen, overlay) over the overlapping region."""
    bx, by = pos
    bw, bh = base_img.size
    tw, th = top_img.size

    # Overlap rectangle in base coordinates
    ix1 = max(0, bx)
    iy1 = max(0, by)
    ix2 = min(bw, bx + tw)
    iy2 = min(bh, by + th)

    if ix2 <= ix1 or iy2 <= iy1:
        return

    # Corresponding rectangle in top coordinates
    tx1 = ix1 - bx
    ty1 = iy1 - by
    tx2 = ix2 - bx
    ty2 = iy2 - by

    base_crop = base_img.crop((ix1, iy1, ix2, iy2))
    top_crop = top_img.crop((tx1, ty1, tx2, ty2))

    base_arr = np.array(base_crop, dtype=np.float32) / 255.0
    top_arr = np.array(top_crop, dtype=np.float32) / 255.0

    br, bg, bb, ba = base_arr[:, :, 0], base_arr[:, :, 1], base_arr[:, :, 2], base_arr[:, :, 3]
    tr, tg, tb, ta = top_arr[:, :, 0], top_arr[:, :, 1], top_arr[:, :, 2], top_arr[:, :, 3]

    if mode == "multiply":
        rr = br * tr
        rg = bg * tg
        rb = bb * tb
    elif mode == "screen":
        rr = 1.0 - (1.0 - br) * (1.0 - tr)
        rg = 1.0 - (1.0 - bg) * (1.0 - tg)
        rb = 1.0 - (1.0 - bb) * (1.0 - tb)
    elif mode == "overlay":
        rr = np.where(br < 0.5, 2.0 * br * tr, 1.0 - 2.0 * (1.0 - br) * (1.0 - tr))
        rg = np.where(bg < 0.5, 2.0 * bg * tg, 1.0 - 2.0 * (1.0 - bg) * (1.0 - tg))
        rb = np.where(bb < 0.5, 2.0 * bb * tb, 1.0 - 2.0 * (1.0 - bb) * (1.0 - tb))
    else:
        rr, rg, rb = tr, tg, tb

    out_a = ta + ba * (1.0 - ta)
    mask = out_a > 1e-5
    out_r = np.zeros_like(rr)
    out_g = np.zeros_like(rg)
    out_b = np.zeros_like(rb)

    term_blend_r = ta * ba * rr
    term_blend_g = ta * ba * rg
    term_blend_b = ta * ba * rb

    term_src_r = ta * (1.0 - ba) * tr
    term_src_g = ta * (1.0 - ba) * tg
    term_src_b = ta * (1.0 - ba) * tb

    term_back_r = ba * (1.0 - ta) * br
    term_back_g = ba * (1.0 - ta) * bg
    term_back_b = ba * (1.0 - ta) * bb

    out_r[mask] = (term_blend_r[mask] + term_src_r[mask] + term_back_r[mask]) / out_a[mask]
    out_g[mask] = (term_blend_g[mask] + term_src_g[mask] + term_back_g[mask]) / out_a[mask]
    out_b[mask] = (term_blend_b[mask] + term_src_b[mask] + term_back_b[mask]) / out_a[mask]

    out_arr = np.dstack([out_r, out_g, out_b, out_a])
    blended_crop = Image.fromarray((np.clip(out_arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), mode="RGBA")
    base_img.paste(blended_crop, (ix1, iy1))


def compose_layers(
    layers: List[Layer],
    canvas_size: Tuple[int, int],
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    """
    Composite an ordered stack of layers into a single output image.
    Layers are processed from index 0 (bottom) to index N-1 (top).
    Respects visibility, opacity, offset, and blend modes.
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

        # Adjust alpha by layer opacity if opacity < 1.0
        if lay.opacity < 0.999:
            r, g, b, a = layer_img.split()
            alpha_lut = [int(v * lay.opacity) for v in range(256)]
            a = a.point(alpha_lut)
            adjusted_layer = Image.merge("RGBA", (r, g, b, a))
        else:
            adjusted_layer = layer_img

        pos = (lay.offset_x, lay.offset_y)
        b_mode = (lay.blend_mode or "normal").lower()

        if b_mode in ("multiply", "screen", "overlay"):
            _blend_mode_composite(composite, adjusted_layer, pos, b_mode)
        else:
            composite.alpha_composite(adjusted_layer, dest=pos)

    return composite


class LayerStack:
    """
    Self-contained layer collection managing stacking order, active layer,
    and composite generation. Serves as the single authoritative layer state.
    """

    def __init__(self, width: int, height: int):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self._layers: List[Layer] = []
        self._active_index: int = -1

    def __len__(self) -> int:
        return len(self._layers)

    def __iter__(self):
        return iter(self._layers)

    def __getitem__(self, index: int) -> Layer:
        return self._layers[index]

    @property
    def layers(self) -> List[Layer]:
        return self._layers

    @property
    def active_index(self) -> int:
        return self._active_index

    @property
    def active_layer(self) -> Optional[Layer]:
        if 0 <= self._active_index < len(self._layers):
            return self._layers[self._active_index]
        return None

    def set_active_index(self, index: int) -> bool:
        """Update active layer index within valid bounds."""
        if 0 <= index < len(self._layers):
            self._active_index = index
            return True
        elif not self._layers:
            self._active_index = -1
            return True
        return False

    def add_layer(self, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
        """Append a new or existing layer to the top of the stack and activate it."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
            for k, v in kwargs.items():
                if hasattr(layer, k):
                    setattr(layer, k, v)
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            layer = Layer(name=name, image=img, **kwargs)
        self._layers.append(layer)
        self._active_index = len(self._layers) - 1
        return layer

    def insert_layer(self, index: int, image_or_layer: Any = None, name: str = "Layer", **kwargs) -> Layer:
        """Insert a layer at the specified index and activate it."""
        if isinstance(image_or_layer, Layer):
            layer = image_or_layer
            for k, v in kwargs.items():
                if hasattr(layer, k):
                    setattr(layer, k, v)
        else:
            img = image_or_layer
            if img is None:
                img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            elif isinstance(img, (tuple, list)):
                img = Image.new("RGBA", (self.width, self.height), tuple(img))
            layer = Layer(name=name, image=img, **kwargs)
        target_idx = max(0, min(index, len(self._layers)))
        self._layers.insert(target_idx, layer)
        self._active_index = target_idx
        return layer

    def duplicate_layer(self, index: int) -> Optional[Layer]:
        """Duplicate layer at index and insert it directly above."""
        if 0 <= index < len(self._layers):
            src = self._layers[index]
            dup = src.duplicate()
            self._layers.insert(index + 1, dup)
            self._active_index = index + 1
            return dup
        return None

    def remove_layer(self, index: int) -> Optional[Layer]:
        """Remove layer at index and maintain correct active layer selection."""
        if 0 <= index < len(self._layers):
            removed = self._layers.pop(index)
            if not self._layers:
                self._active_index = -1
            elif self._active_index > index:
                self._active_index -= 1
            elif self._active_index == index:
                self._active_index = min(index, len(self._layers) - 1)
            return removed
        return None

    def move_layer(self, from_idx: int, to_idx: int) -> bool:
        """Move layer from from_idx to to_idx and update active index."""
        if from_idx == to_idx and 0 <= from_idx < len(self._layers):
            return True
        if 0 <= from_idx < len(self._layers) and 0 <= to_idx < len(self._layers):
            layer = self._layers.pop(from_idx)
            self._layers.insert(to_idx, layer)
            if self._active_index == from_idx:
                self._active_index = to_idx
            elif from_idx < self._active_index <= to_idx:
                self._active_index -= 1
            elif to_idx <= self._active_index < from_idx:
                self._active_index += 1
            return True
        return False

    def move_layer_down(self, index: int) -> bool:
        """Move layer downward (towards bottom/background)."""
        if 0 < index < len(self._layers):
            return self.move_layer(index, index - 1)
        return False

    def move_layer_up(self, index: int) -> bool:
        """Move layer upward (towards top of stack)."""
        if 0 <= index < len(self._layers) - 1:
            return self.move_layer(index, index + 1)
        return False

    def merge_down(self, index: int) -> Optional[Layer]:
        """
        Merge layer at index into the layer beneath it preserving visibility semantics.
        If the upper layer is hidden, it does NOT contribute pixels to the visible result.
        If both layers are hidden, the merged layer remains hidden.
        """
        if index <= 0 or index >= len(self._layers):
            return None
        lower = self._layers[index - 1]
        upper = self._layers[index]

        if lower.visible and upper.visible:
            comp = compose_layers([lower, upper], (self.width, self.height))
            lower.image = comp
            lower.offset_x = 0
            lower.offset_y = 0
            lower.opacity = 1.0
            lower.blend_mode = "normal"
            lower.visible = True
        elif lower.visible and not upper.visible:
            # Upper hidden: contributes nothing to visible pixels
            comp = compose_layers([lower], (self.width, self.height))
            lower.image = comp
            lower.offset_x = 0
            lower.offset_y = 0
            lower.opacity = 1.0
            lower.visible = True
        elif not lower.visible and upper.visible:
            # Lower hidden: contributes nothing to visible pixels
            comp = compose_layers([upper], (self.width, self.height))
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
            comp = compose_layers([temp_lower, temp_upper], (self.width, self.height))
            lower.image = comp
            lower.offset_x = 0
            lower.offset_y = 0
            lower.opacity = 1.0
            lower.blend_mode = "normal"
            lower.visible = False

        self._layers.pop(index)
        self._active_index = index - 1
        return lower

    def clear(self) -> None:
        """Clear all layers."""
        self._layers.clear()
        self._active_index = -1

    def clone(self, preserve_ids: bool = True) -> LayerStack:
        """Create a deep snapshot clone of the entire layer stack."""
        new_stack = LayerStack(self.width, self.height)
        new_stack._layers = [lay.clone(preserve_id=preserve_ids) for lay in self._layers]
        new_stack._active_index = self._active_index
        return new_stack

    def composite(self) -> Image.Image:
        """Render composite image of all visible layers."""
        return compose_layers(self._layers, (self.width, self.height))
