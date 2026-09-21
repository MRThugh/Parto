# parto/utils/conversions.py
"""
Parto v0.3.0 - High-performance Image & Color Conversion Utilities
Provides bidirectional conversion between PIL Image, QImage, QPixmap, and NumPy arrays.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PIL import Image
from PySide6.QtGui import QImage, QPixmap
import numpy as np


def pil_to_qimage(pil_img: Optional[Image.Image]) -> Optional[QImage]:
    """
    Convert a PIL Image to a PySide6 QImage.
    Preserves transparency, color channels, and avoids lifetime/GC crashes.
    """
    if pil_img is None:
        return None

    try:
        mode = pil_img.mode

        # Check for transparency in Palette or Alpha modes
        if mode in ("RGBA", "LA") or (mode == "P" and "transparency" in getattr(pil_img, "info", {})):
            rgba = pil_img.convert("RGBA")
            data = rgba.tobytes("raw", "RGBA")
            return QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888).copy()

        elif mode == "L":
            # Grayscale 8-bit
            data = pil_img.tobytes("raw", "L")
            return QImage(data, pil_img.width, pil_img.height, pil_img.width, QImage.Format_Grayscale8).copy()

        elif mode == "1":
            # 1-bit monochrome
            rgb = pil_img.convert("RGB")
            data = rgb.tobytes("raw", "RGB")
            return QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888).copy()

        else:
            # Standard RGB conversion
            rgb = pil_img.convert("RGB")
            data = rgb.tobytes("raw", "RGB")
            return QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format_RGB888).copy()

    except Exception as e:
        print(f"[Parto Error] pil_to_qimage failed: {e}")
        return None


def pil_to_qpixmap(pil_img: Optional[Image.Image]) -> QPixmap:
    """
    Convert a PIL Image to a PySide6 QPixmap safely using QImage.copy().
    """
    if pil_img is None:
        return QPixmap()

    qimg = pil_to_qimage(pil_img)
    if qimg is None or qimg.isNull():
        return QPixmap()

    return QPixmap.fromImage(qimg)


def qimage_to_pil(qimg: Optional[QImage]) -> Optional[Image.Image]:
    """
    Convert a PySide6 QImage to a PIL Image.
    """
    if qimg is None or qimg.isNull():
        return None

    try:
        # Convert QImage to standard RGBA8888 for consistency
        qimg_conv = qimg.convertToFormat(QImage.Format_RGBA8888)
        w, h = qimg_conv.width(), qimg_conv.height()
        ptr = qimg_conv.bits()
        # ptr is a sip/shiboken buffer; bytes() creates a safe Python byte copy
        raw_bytes = bytes(ptr)
        return Image.frombuffer("RGBA", (w, h), raw_bytes, "raw", "RGBA", 0, 1).copy()
    except Exception as e:
        print(f"[Parto Error] qimage_to_pil failed: {e}")
        return None


def pil_to_numpy(pil_img: Optional[Image.Image]) -> Optional[np.ndarray]:
    """
    Convert a PIL Image to a NumPy array (uint8).
    """
    if pil_img is None:
        return None
    try:
        return np.array(pil_img)
    except Exception as e:
        print(f"[Parto Error] pil_to_numpy failed: {e}")
        return None


def numpy_to_pil(arr: Optional[np.ndarray], mode: Optional[str] = None) -> Optional[Image.Image]:
    """
    Convert a NumPy array (uint8) back to a PIL Image.
    """
    if arr is None:
        return None
    try:
        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)
        if mode:
            return Image.fromarray(arr, mode=mode)
        return Image.fromarray(arr)
    except Exception as e:
        print(f"[Parto Error] numpy_to_pil failed: {e}")
        return None
