# image.py
"""
Parto - Image Conversion & Metadata Utilities
Author: Ali Kamrani (MRThugh)
Version: 0.2.0
"""

import os
from PIL import Image
from PySide6.QtGui import QImage, QPixmap

# Optional HEIF format support for Apple device images
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def get_image_info(filepath: str | None = None, pil_img: Image.Image | None = None) -> dict:
    """
    Extract verified, accurate information about the image file and in-memory object.
    Does not invent fake or estimated data.
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

    # If PIL Image instance provided, extract properties directly
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

        # Calculate exact aspect ratio
        if h > 0:
            ratio = w / h
            # Match common standard aspect ratios
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


def pil_to_qpixmap(pil_img: Image.Image | None) -> QPixmap:
    """
    Convert a PIL Image to PySide6 QPixmap safely using copy()
    to prevent memory collection issues during rapid zoom/transformations.
    Preserves alpha channels and handles diverse PIL modes (RGBA, LA, P, L, RGB, CMYK).
    """
    if pil_img is None:
        return QPixmap()

    try:
        mode = pil_img.mode

        # Check for transparency in Palette or Alpha modes
        if mode in ("RGBA", "LA") or (mode == "P" and "transparency" in getattr(pil_img, "info", {})):
            rgba = pil_img.convert("RGBA")
            data = rgba.tobytes("raw", "RGBA")
            qimg = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888).copy()
        elif mode == "L":
            # Grayscale 8-bit
            data = pil_img.tobytes("raw", "L")
            qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width, QImage.Format_Grayscale8).copy()
        else:
            # Standard RGB conversion
            rgb = pil_img.convert("RGB")
            data = rgb.tobytes("raw", "RGB")
            qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888).copy()

        return QPixmap.fromImage(qimg)
    except Exception as e:
        print(f"Error converting PIL Image to QPixmap: {e}")
        return QPixmap()
