# parto/document/adapters/storage_adapter.py
"""
Parto Document Subsystem — Persistence & Storage Adapter
Author: Ali Kamrani (MRThugh)

Responsible for safe image file I/O, EXIF orientation correction,
memory decoupling, and export formatting.
"""

from __future__ import annotations
import os
from typing import Optional, Tuple
from PIL import Image, ImageOps

from ...image.export import save_image_file


class DocumentStorageAdapter:
    """
    Handles file loading and saving for Document images.
    Encapsulates Pillow format management and EXIF orientation normalization.
    """

    @staticmethod
    def load_file(
        filepath: str,
        raise_on_error: bool = False,
    ) -> Tuple[bool, Optional[Image.Image], Optional[str], Optional[str]]:
        """
        Load an image file safely from disk into an RGBA Pillow Image.
        Returns (success, image, resolved_path, error_message).
        """
        try:
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass

            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Image file does not exist: {filepath}")

            with Image.open(filepath) as raw_img:
                oriented = ImageOps.exif_transpose(raw_img)
                if oriented is None:
                    oriented = raw_img
                # Load fully into memory as RGBA and copy so file handle is released
                if oriented.mode != "RGBA":
                    img = oriented.convert("RGBA")
                else:
                    img = oriented.copy()

            resolved_path = os.path.abspath(filepath)
            return True, img, resolved_path, None

        except Exception as e:
            if raise_on_error:
                raise
            err_msg = f"[Parto Document Error] Failed to load {filepath}: {e}"
            print(err_msg)
            return False, None, None, str(e)

    @staticmethod
    def save_file(
        composite: Optional[Image.Image],
        target_path: Optional[str],
        quality: int = 95,
        optimize: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Save flattened composite image to disk.
        Returns (success, error_message).
        """
        if not target_path:
            return False, "No filepath specified"

        if composite is None:
            return False, "No active image to save"

        return save_image_file(composite, target_path, quality=quality, optimize=optimize)
