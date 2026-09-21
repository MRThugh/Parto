# parto/image/export.py
"""
Parto v0.3.0 - Safe File Export & Save Pipeline
Handles alpha compositing for JPEG, compression, and modern formats.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import os
from typing import Tuple, Optional
from PIL import Image


def save_image_file(
    image: Image.Image,
    filepath: str,
    quality: int = 95,
    optimize: bool = True,
    matte_color: Tuple[int, int, int] = (255, 255, 255),
    format: Optional[str] = None,
    **kwargs,
) -> Tuple[bool, Optional[str]]:
    """
    Save image safely to disk.
    Automatically composite RGBA images onto matte_color when saving to JPEG.
    """
    if image is None:
        return False, "No image to save"

    try:
        # Ensure parent directory exists
        dirname = os.path.dirname(os.path.abspath(filepath))
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        ext = os.path.splitext(filepath)[1].lower()
        target_format = format.upper() if format else None

        if target_format == "JPEG" or ext in (".jpg", ".jpeg"):
            # Safe JPEG alpha compositing
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in getattr(image, "info", {})):
                rgba = image.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, matte_color + (255,))
                composite = Image.alpha_composite(bg, rgba)
                img_to_save = composite.convert("RGB")
            else:
                img_to_save = image.convert("RGB")

            img_to_save.save(filepath, "JPEG", quality=quality, optimize=optimize)

        elif target_format == "PNG" or ext == ".png":
            img_to_save = image
            img_to_save.save(filepath, "PNG", optimize=optimize)

        elif target_format == "WEBP" or ext == ".webp":
            img_to_save = image
            webp_args = {"quality": quality}
            if "lossless" in kwargs:
                webp_args["lossless"] = kwargs["lossless"]
            img_to_save.save(filepath, "WEBP", **webp_args)

        elif target_format == "BMP" or ext == ".bmp":
            img_to_save = image.convert("RGB") if image.mode in ("RGBA", "LA") else image
            img_to_save.save(filepath, "BMP")

        elif target_format == "TIFF" or ext in (".tif", ".tiff"):
            img_to_save = image
            img_to_save.save(filepath, "TIFF")

        else:
            # Default save
            save_args = {}
            if target_format:
                save_args["format"] = target_format
            image.save(filepath, **save_args)

        return True, None

    except Exception as e:
        err = f"Failed to save image to {filepath}: {e}"
        print(f"[Parto Error] {err}")
        return False, str(e)
