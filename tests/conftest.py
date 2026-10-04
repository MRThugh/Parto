# tests/conftest.py
"""
Parto Central Test Fixtures and Environment Configuration
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import sys
import tempfile
import pytest
import numpy as np
from PIL import Image

# Enforce offscreen headless platform for PySide6 in CI and headless containers
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """
    Session-wide headless QApplication instance.
    Safe for offscreen rendering, icon rasterization, and dialog inspection.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    return app


@pytest.fixture
def sample_images(tmp_path):
    """Generate various test image fixtures across standard formats."""
    # 1. RGB PNG
    rgb_png = tmp_path / "test_rgb.png"
    img_rgb = Image.new("RGB", (200, 100), color=(255, 0, 0))
    img_rgb.save(rgb_png, "PNG")

    # 2. RGBA PNG (with semi-transparency)
    rgba_png = tmp_path / "test_rgba.png"
    img_rgba = Image.new("RGBA", (150, 150), color=(0, 255, 0, 128))
    img_rgba.save(rgba_png, "PNG")

    # 3. JPEG
    jpg_file = tmp_path / "test.jpg"
    img_jpg = Image.new("RGB", (100, 100), color=(0, 0, 255))
    img_jpg.save(jpg_file, "JPEG")

    # 4. WebP
    webp_file = tmp_path / "test.webp"
    img_rgb.save(webp_file, "WEBP")

    # 5. Corrupt file
    corrupt_file = tmp_path / "corrupt.png"
    with open(corrupt_file, "w") as f:
        f.write("This is not a valid image format payload.")

    return {
        "rgb_png": str(rgb_png),
        "rgba_png": str(rgba_png),
        "jpg": str(jpg_file),
        "webp": str(webp_file),
        "corrupt": str(corrupt_file),
        "tmp_dir": str(tmp_path),
    }


@pytest.fixture
def transparent_test_image():
    """Create a 100x100 4-quadrant test image with varying alpha values."""
    arr = np.zeros((100, 100, 4), dtype=np.uint8)
    # Red quadrant with 255 alpha (opaque)
    arr[0:50, 0:50] = [255, 0, 0, 255]
    # Green quadrant with 128 alpha (semi-transparent)
    arr[0:50, 50:100] = [0, 255, 0, 128]
    # Blue quadrant with 64 alpha (translucent)
    arr[50:100, 0:50] = [0, 0, 255, 64]
    # Transparent quadrant with 0 alpha
    arr[50:100, 50:100] = [0, 0, 0, 0]
    return Image.fromarray(arr, mode="RGBA")


@pytest.fixture
def deterministic_swatches():
    """
    Deterministic 2x2 and 4x4 RGBA swatches for pixel-perfect mathematical verification.
    """
    def _create(color, size=(4, 4)):
        return Image.new("RGBA", size, color)
    return _create
