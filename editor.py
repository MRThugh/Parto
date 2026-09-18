# editor.py
"""
Parto - Editor Engine
Core image-processing logic and history management.
Author: Ali Kamrani (MRThugh)
Version: 0.2.0
"""

import os
from PIL import Image, ImageEnhance, ImageOps


class EditorEngine:
    """
    Core image processing engine managing loaded image state,
    undo/redo history stacks, transformations, adjustments, and filters.
    """

    def __init__(self, max_history: int = 30):
        self.current_image: Image.Image | None = None
        self.original_image: Image.Image | None = None  # Snapshot of base state for Before/After
        self.filepath: str | None = None
        self.undo_stack: list[Image.Image] = []
        self.redo_stack: list[Image.Image] = []
        self.max_history = max_history
        self.is_modified = False

    def load_image(self, filepath: str):
        """
        Load an image file from disk, reset history stacks, and cache original state.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with Image.open(filepath) as img:
            self.current_image = img.copy()
            self.original_image = self.current_image.copy()

        self.filepath = filepath
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.is_modified = False

    def save_image(self, filepath: str, img_format: str | None = None, quality: int = 95):
        """
        Save the current processed image state to disk.
        Safely converts RGBA/transparency to RGB when saving to JPEG to prevent crashes.
        """
        if not self.current_image:
            raise RuntimeError("No image loaded to save.")

        ext = os.path.splitext(filepath)[1].lower()
        effective_format = img_format.upper() if img_format else None

        if not effective_format:
            format_map = {
                ".png": "PNG",
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".webp": "WEBP",
                ".bmp": "BMP",
                ".tiff": "TIFF",
                ".tif": "TIFF",
            }
            effective_format = format_map.get(ext, "PNG")

        img_to_save = self.current_image.copy()

        # Handle JPEG format conversion for images with alpha channels
        if effective_format in ("JPEG", "JPG"):
            if img_to_save.mode in ("RGBA", "LA") or (
                img_to_save.mode == "P" and "transparency" in img_to_save.info
            ):
                # Composite over a clean white background
                rgba_img = img_to_save.convert("RGBA")
                white_bg = Image.new("RGB", rgba_img.size, (255, 255, 255))
                white_bg.paste(rgba_img, mask=rgba_img.split()[3])
                img_to_save = white_bg
            elif img_to_save.mode != "RGB":
                img_to_save = img_to_save.convert("RGB")
            img_to_save.save(filepath, format="JPEG", quality=quality)
        elif effective_format == "PNG":
            img_to_save.save(filepath, format="PNG", optimize=True)
        elif effective_format == "WEBP":
            img_to_save.save(filepath, format="WEBP", quality=quality)
        else:
            img_to_save.save(filepath, format=effective_format)

        self.filepath = filepath
        self.is_modified = False

    def _commit_state(self):
        """
        Snapshot current state onto undo stack before performing a modification.
        """
        if self.current_image:
            self.undo_stack.append(self.current_image.copy())
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.is_modified = True

    @property
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def undo(self) -> bool:
        """
        Revert to previous image state.
        """
        if self.undo_stack:
            self.redo_stack.append(self.current_image.copy())
            self.current_image = self.undo_stack.pop()
            self.is_modified = True
            return True
        return False

    def redo(self) -> bool:
        """
        Re-apply previously undone state.
        """
        if self.redo_stack:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = self.redo_stack.pop()
            self.is_modified = True
            return True
        return False

    def rotate_left(self):
        """Rotate 90 degrees counter-clockwise."""
        self.rotate(90)

    def rotate_right(self):
        """Rotate 90 degrees clockwise (270 CCW)."""
        self.rotate(270)

    def rotate_180(self):
        """Rotate 180 degrees."""
        self.rotate(180)

    def rotate(self, angle: int):
        """
        Rotate image by angle (in degrees CCW), expanding canvas to fit.
        """
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.rotate(angle, expand=True)

    def flip_horizontal(self):
        """Flip horizontally (mirror left-to-right)."""
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    def flip_vertical(self):
        """Flip vertically (mirror top-to-bottom)."""
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def resize(self, width: int, height: int):
        """
        Resize image using high-quality Lanczos resampling.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)

    def crop(self, box: tuple[int, int, int, int]):
        """
        Crop image using bounding box (left, top, right, bottom).
        """
        if not self.current_image:
            return
        left, top, right, bottom = box
        w, h = self.current_image.size

        # Clamp to image boundaries
        left = max(0, min(left, w - 1))
        top = max(0, min(top, h - 1))
        right = max(left + 1, min(right, w))
        bottom = max(top + 1, min(bottom, h))

        if right - left < 1 or bottom - top < 1:
            raise ValueError("Crop region is too small.")

        self._commit_state()
        self.current_image = self.current_image.crop((left, top, right, bottom))

    def get_adjusted_preview(
        self, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0
    ) -> Image.Image | None:
        """
        Produce a real-time preview of adjustments without modifying engine state.
        Preserves alpha channels cleanly.
        """
        if not self.current_image:
            return None

        img = self.current_image.copy()

        # Handle palette images by converting to RGBA or RGB
        if img.mode == "P":
            if "transparency" in img.info:
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)

        return img

    def apply_adjustments(
        self, brightness: float = 1.0, contrast: float = 1.0, saturation: float = 1.0
    ):
        """
        Commit real-time brightness, contrast, and saturation adjustments.
        """
        if self.current_image:
            preview = self.get_adjusted_preview(brightness, contrast, saturation)
            if preview:
                self._commit_state()
                self.current_image = preview

    def get_filter_preview(self, filter_name: str) -> Image.Image | None:
        """
        Generate preview for standard photographic filters without altering current state.
        Supported filters: 'grayscale', 'sepia', 'invert'.
        Preserves alpha channel transparency.
        """
        if not self.current_image:
            return None

        img = self.current_image.copy()
        has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

        if filter_name == "grayscale":
            if has_alpha:
                rgba = img.convert("RGBA")
                r, g, b, a = rgba.split()
                gray = Image.merge("RGB", (r, g, b)).convert("L")
                return Image.merge("RGBA", (gray, gray, gray, a))
            else:
                gray = img.convert("L")
                return gray.convert("RGB")

        elif filter_name == "sepia":
            # Matrix transformation for rich photographic sepia tone
            sepia_matrix = (
                0.393, 0.769, 0.189, 0,
                0.349, 0.686, 0.168, 0,
                0.272, 0.534, 0.131, 0,
            )
            if has_alpha:
                rgba = img.convert("RGBA")
                r, g, b, a = rgba.split()
                rgb = Image.merge("RGB", (r, g, b)).convert("RGB", sepia_matrix)
                r_s, g_s, b_s = rgb.split()
                return Image.merge("RGBA", (r_s, g_s, b_s, a))
            else:
                rgb = img.convert("RGB")
                return rgb.convert("RGB", sepia_matrix)

        elif filter_name == "invert":
            if has_alpha:
                rgba = img.convert("RGBA")
                r, g, b, a = rgba.split()
                rgb = Image.merge("RGB", (r, g, b))
                inverted_rgb = ImageOps.invert(rgb)
                inv_r, inv_g, inv_b = inverted_rgb.split()
                return Image.merge("RGBA", (inv_r, inv_g, inv_b, a))
            else:
                rgb = img.convert("RGB")
                return ImageOps.invert(rgb)

        return img

    def apply_filter(self, filter_name: str):
        """
        Commit a filter to the image history.
        """
        if self.current_image:
            preview = self.get_filter_preview(filter_name)
            if preview:
                self._commit_state()
                self.current_image = preview
