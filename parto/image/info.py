# parto/image/info.py
"""
Parto v0.3.0 - Image Metadata & Technical Properties Inspector
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
import math
from typing import Dict, Any, Optional
from PIL import Image


def get_image_metadata(image: Optional[Image.Image], filepath: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract comprehensive technical properties and metadata from an image.
    """
    if image is None:
        return {
            "valid": False,
            "width": 0,
            "height": 0,
            "dimensions": "0 × 0",
            "aspect_ratio": "N/A",
            "megapixels": "0 MP",
            "color_mode": "N/A",
            "has_alpha": False,
            "file_format": "N/A",
            "file_size": "N/A",
            "file_path": filepath or "None",
        }

    w, h = image.size
    mp = (w * h) / 1_000_000.0

    # Aspect ratio reduction
    gcd = math.gcd(w, h)
    if gcd > 0 and (w // gcd < 50 and h // gcd < 50):
        aspect_ratio = f"{w // gcd}:{h // gcd}"
    else:
        ratio_float = w / h if h > 0 else 0
        aspect_ratio = f"{ratio_float:.2f}:1"

    # Alpha detection
    has_alpha = image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in getattr(image, "info", {}))

    # Color mode description
    mode_desc = {
        "RGB": "RGB (24-bit True Color)",
        "RGBA": "RGBA (32-bit True Color with Alpha)",
        "L": "Grayscale (8-bit)",
        "LA": "Grayscale with Alpha (16-bit)",
        "1": "Monochrome (1-bit)",
        "P": "Palette Indexed (8-bit)",
        "CMYK": "CMYK (Color Printing)",
    }.get(image.mode, f"{image.mode} Mode")

    # File size formatting
    file_size_str = "Unsaved / In Memory"
    if filepath and os.path.exists(filepath):
        try:
            bytes_size = os.path.getsize(filepath)
            if bytes_size < 1024:
                file_size_str = f"{bytes_size} B"
            elif bytes_size < 1024 * 1024:
                file_size_str = f"{bytes_size / 1024:.1f} KB"
            else:
                file_size_str = f"{bytes_size / (1024 * 1024):.2f} MB"
        except Exception:
            pass

    fmt = image.format or (os.path.splitext(filepath)[1][1:].upper() if filepath else "RAW")

    return {
        "valid": True,
        "width": w,
        "height": h,
        "dimensions": f"{w} × {h} px",
        "aspect_ratio": aspect_ratio,
        "megapixels": f"{mp:.2f} MP" if mp >= 0.1 else f"{mp:.3f} MP",
        "color_mode": mode_desc,
        "has_alpha": has_alpha,
        "file_format": fmt,
        "file_size": file_size_str,
        "file_path": filepath or "Unsaved Image",
    }
