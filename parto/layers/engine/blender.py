# parto/layers/engine/blender.py
"""
Parto Layers Subsystem — Blend Modes Engine
Author: Ali Kamrani (MRThugh)

Provides mathematically rigorous, offset-aware pixel blending algorithms for RGBA image buffers:
- Normal (Source-Over)
- Multiply: B(Cb, Cs) = Cb * Cs
- Screen: B(Cb, Cs) = 1 - (1 - Cb) * (1 - Cs)
- Overlay: B(Cb, Cs) = 2 * Cb * Cs if Cb < 0.5 else 1 - 2 * (1 - Cb) * (1 - Cs)
- Darken: B(Cb, Cs) = min(Cb, Cs)
- Lighten: B(Cb, Cs) = max(Cb, Cs)
"""

from __future__ import annotations
from typing import Tuple
from PIL import Image
import numpy as np


def blend_mode_composite(
    base_img: Image.Image,
    top_img: Image.Image,
    pos: Tuple[int, int],
    mode: str,
) -> None:
    """
    Apply non-normal blend modes over the overlapping rectangular region of base_img and top_img.
    Mutates base_img in-place within the overlapping region, respecting alpha compositing.
    """
    bx, by = pos
    bw, bh = base_img.size
    tw, th = top_img.size

    # Overlap rectangle in base image coordinates
    ix1 = max(0, bx)
    iy1 = max(0, by)
    ix2 = min(bw, bx + tw)
    iy2 = min(bh, by + th)

    if ix2 <= ix1 or iy2 <= iy1:
        return

    # Corresponding rectangle in top image coordinates
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

    mode_lower = mode.lower() if mode else "normal"

    if mode_lower == "multiply":
        rr = br * tr
        rg = bg * tg
        rb = bb * tb
    elif mode_lower == "screen":
        rr = 1.0 - (1.0 - br) * (1.0 - tr)
        rg = 1.0 - (1.0 - bg) * (1.0 - tg)
        rb = 1.0 - (1.0 - bb) * (1.0 - tb)
    elif mode_lower == "overlay":
        rr = np.where(br < 0.5, 2.0 * br * tr, 1.0 - 2.0 * (1.0 - br) * (1.0 - tr))
        rg = np.where(bg < 0.5, 2.0 * bg * tg, 1.0 - 2.0 * (1.0 - bg) * (1.0 - tg))
        rb = np.where(bb < 0.5, 2.0 * bb * tb, 1.0 - 2.0 * (1.0 - bb) * (1.0 - tb))
    elif mode_lower == "darken":
        rr = np.minimum(br, tr)
        rg = np.minimum(bg, tg)
        rb = np.minimum(bb, tb)
    elif mode_lower == "lighten":
        rr = np.maximum(br, tr)
        rg = np.maximum(bg, tg)
        rb = np.maximum(bb, tb)
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


# Backward compatibility alias
_blend_mode_composite = blend_mode_composite
