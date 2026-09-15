# image.py
import os
from PIL import Image
from PySide6.QtGui import QImage, QPixmap

# Try registering optional HEIF format support for Apple devices
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

def get_image_info(filepath: str) -> dict:
    """
    Extract size, format, and dimension of the image file safely.
    """
    if not filepath or not os.path.exists(filepath):
        return {}
    
    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)
    size_str = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{size_bytes / 1024:.1f} KB"
    
    try:
        with Image.open(filepath) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "size_str": size_str
            }
    except Exception:
        return {}

def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """
    Convert a PIL Image to PySide6 QPixmap safely using copy() 
    to prevent memory collection bugs during rapid operations.
    """
    if pil_img is None:
        return QPixmap()
    
    # Handle transparent channel if available, otherwise fallback to RGB
    if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
        pil_img_converted = pil_img.convert("RGBA")
        data = pil_img_converted.tobytes("raw", "RGBA")
        # Copy the image data to ensure Qt keeps ownership of the memory buffer
        qimg = QImage(data, pil_img_converted.width, pil_img_converted.height, QImage.Format_RGBA8888).copy()
    else:
        pil_img_converted = pil_img.convert("RGB")
        data = pil_img_converted.tobytes("raw", "RGB")
        # Copy the image data to avoid native memory access faults
        qimg = QImage(data, pil_img_converted.width, pil_img_converted.height, QImage.Format_RGB888).copy()
        
    return QPixmap.fromImage(qimg)