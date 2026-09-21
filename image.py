# image.py
"""
Parto v0.3.0 - Image Conversion & Metadata Compatibility Layer
Author: Ali Kamrani (MRThugh)
"""

import os
from PIL import Image
from PySide6.QtGui import QPixmap
from parto.utils.conversions import pil_to_qpixmap

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def get_image_info(filepath: str | None = None, pil_img: Image.Image | None = None) -> dict:
    """
    Extract verified, accurate technical information about the image file and in-memory object.
    """
    info = {
        "filename": "Untitled",
        "filepath": filepath or "In-memory",
        "width": 0,
        "height": 0,
        "dimensions_str": "0 × 0 px",
        "aspect_ratio": "N/A",
        "megapixels": "0.00 MP",
        "format": "Unknown",
        "mode": "Unknown",
        "has_transparency": False,
        "size_bytes": 0,
        "size_str": "N/A",
    }

    if filepath and os.path.exists(filepath):
        info["filename"] = os.path.basename(filepath)
        info["filepath"] = os.path.abspath(filepath)
        size_bytes = os.path.getsize(filepath)
        info["size_bytes"] = size_bytes
        if size_bytes >= 1024 * 1024:
            info["size_str"] = f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            info["size_str"] = f"{size_bytes / 1024:.1f} KB"

    img = pil_img
    opened_here = False
    if img is None and filepath and os.path.exists(filepath):
        try:
            img = Image.open(filepath)
            opened_here = True
        except Exception:
            return info

    if img is not None:
        w, h = img.width, img.height
        info["width"] = w
        info["height"] = h
        info["dimensions_str"] = f"{w} × {h} px"
        info["format"] = img.format if img.format else "RAW"
        info["mode"] = img.mode

        has_alpha = img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in getattr(img, "info", {})
        )
        info["has_transparency"] = has_alpha

        if h > 0:
            ratio = w / h
            common_ratios = [
                (1.0, "1:1"),
                (4 / 3, "4:3"),
                (16 / 9, "16:9"),
                (3 / 2, "3:2"),
                (5 / 4, "5:4"),
                (21 / 9, "21:9"),
            ]
            matched = False
            for target_val, label in common_ratios:
                if abs(ratio - target_val) < 0.02:
                    info["aspect_ratio"] = label
                    matched = True
                    break
            if not matched:
                info["aspect_ratio"] = f"{ratio:.2f}:1"

        mp = (w * h) / 1_000_000.0
        info["megapixels"] = f"{mp:.2f} MP"

        if opened_here:
            img.close()

    return info


__all__ = ["get_image_info", "pil_to_qpixmap"]
