# parto/resources/icons.py
"""
Parto v0.3.0 - Canonical High-Resolution Vector Icon Generation System
Crisp, geometric vector icons generated with QPainter. Resolution-independent,
cached, optically balanced, and dynamically adaptive to any theme color palette.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
import math
import logging
from typing import Dict, Tuple
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QPainterPath, QPen, QColor, QBrush, QFont
)

logger = logging.getLogger("parto.icons")

_ICON_CACHE: Dict[Tuple[str, str, int], QIcon] = {}

# Canonical name aliases
ICON_ALIASES: Dict[str, str] = {
    # Actions
    "rot_cw": "rotate-right",
    "rotate_cw": "rotate-right",
    "rotate-cw": "rotate-right",
    "rot_ccw": "rotate-left",
    "rotate_ccw": "rotate-left",
    "rotate-ccw": "rotate-left",
    "flip-h": "flip-horizontal",
    "flip_h": "flip-horizontal",
    "flip-v": "flip-vertical",
    "flip_v": "flip-vertical",
    # Layers
    "add_layer": "layer-add",
    "new_layer": "layer-add",
    "duplicate_layer": "layer-duplicate",
    "dup_layer": "layer-duplicate",
    "delete_layer": "layer-delete",
    "del_layer": "layer-delete",
    "move_up": "layer-up",
    "move_down": "layer-down",
    "merge_down": "layer-merge",
    "layer-visible": "eye",
    "layer-hidden": "eye-off",
    # Tools
    "hand": "move",
    "pan": "move",
    "dropper": "eyedropper",
    "paint": "brush",
}


def clear_icon_cache() -> None:
    """Clear cached QIcon instances when theme changes."""
    _ICON_CACHE.clear()


def get_parto_icon(name: str, color_hex: str = "#e0e0e0", size: int = 24) -> QIcon:
    """
    Generate or retrieve cached crisp, resolution-independent vector icons.
    Supports canonical names, registered aliases, and fallback rendering.
    """
    canonical_name = ICON_ALIASES.get(name.lower(), name.lower())
    cache_key = (canonical_name, color_hex, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    pen = QPen(QColor(color_hex))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    s = float(size)
    pad = s * 0.15

    # 1. Document & File Actions
    if canonical_name == "new":
        # Document with folded corner and plus badge
        path = QPainterPath()
        path.moveTo(pad, pad)
        path.lineTo(s - pad - s * 0.22, pad)
        path.lineTo(s - pad, pad + s * 0.22)
        path.lineTo(s - pad, s - pad)
        path.lineTo(pad, s - pad)
        path.closeSubpath()
        painter.drawPath(path)
        # Folded line
        painter.drawLine(QPointF(s - pad - s * 0.22, pad), QPointF(s - pad - s * 0.22, pad + s * 0.22))
        painter.drawLine(QPointF(s - pad - s * 0.22, pad + s * 0.22), QPointF(s - pad, pad + s * 0.22))
        # Plus in center-bottom
        cx, cy = s * 0.46, s * 0.58
        d = s * 0.14
        painter.drawLine(QPointF(cx - d, cy), QPointF(cx + d, cy))
        painter.drawLine(QPointF(cx, cy - d), QPointF(cx, cy + d))

    elif canonical_name == "open":
        path = QPainterPath()
        path.moveTo(pad, pad + s * 0.2)
        path.lineTo(pad + s * 0.25, pad + s * 0.2)
        path.lineTo(pad + s * 0.35, pad + s * 0.32)
        path.lineTo(s - pad, pad + s * 0.32)
        path.lineTo(s - pad, s - pad)
        path.lineTo(pad, s - pad)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(pad, pad + s * 0.36), QPointF(s - pad, pad + s * 0.36))

    elif canonical_name == "save":
        path = QPainterPath()
        path.moveTo(pad, pad)
        path.lineTo(s - pad - s * 0.15, pad)
        path.lineTo(s - pad, pad + s * 0.15)
        path.lineTo(s - pad, s - pad)
        path.lineTo(pad, s - pad)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawRect(QRectF(pad + s * 0.15, pad, s * 0.4, s * 0.25))
        painter.drawRect(QRectF(pad + s * 0.12, s - pad - s * 0.28, s * 0.46, s * 0.28))

    elif canonical_name == "save-as":
        path = QPainterPath()
        path.moveTo(pad, pad)
        path.lineTo(s - pad - s * 0.15, pad)
        path.lineTo(s - pad, pad + s * 0.15)
        path.lineTo(s - pad, s - pad - s * 0.2)
        path.moveTo(pad + s * 0.25, s - pad)
        path.lineTo(pad, s - pad)
        path.lineTo(pad, pad)
        painter.drawPath(path)
        cx, cy = s - pad - s * 0.1, s - pad - s * 0.1
        painter.drawLine(QPointF(cx - s * 0.12, cy), QPointF(cx + s * 0.12, cy))
        painter.drawLine(QPointF(cx, cy - s * 0.12), QPointF(cx, cy + s * 0.12))

    elif canonical_name == "export":
        painter.drawRoundedRect(QRectF(pad, pad + s * 0.2, s - 2 * pad, s * 0.5), 2, 2)
        painter.drawLine(QPointF(s * 0.5, s - pad), QPointF(s * 0.5, pad))
        ah = QPainterPath()
        ah.moveTo(s * 0.5 - s * 0.15, pad + s * 0.15)
        ah.lineTo(s * 0.5, pad)
        ah.lineTo(s * 0.5 + s * 0.15, pad + s * 0.15)
        painter.drawPath(ah)

    # 2. History Actions
    elif canonical_name == "undo":
        path = QPainterPath()
        path.moveTo(s - pad, s - pad)
        path.quadTo(s - pad, pad + s * 0.1, pad + s * 0.25, pad + s * 0.2)
        painter.drawPath(path)
        tip_x, tip_y = pad + s * 0.15, pad + s * 0.2
        ah = QPainterPath()
        ah.moveTo(tip_x + s * 0.18, tip_y - s * 0.15)
        ah.lineTo(tip_x, tip_y)
        ah.lineTo(tip_x + s * 0.18, tip_y + s * 0.15)
        painter.drawPath(ah)

    elif canonical_name == "redo":
        path = QPainterPath()
        path.moveTo(pad, s - pad)
        path.quadTo(pad, pad + s * 0.1, s - pad - s * 0.25, pad + s * 0.2)
        painter.drawPath(path)
        tip_x, tip_y = s - pad - s * 0.15, pad + s * 0.2
        ah = QPainterPath()
        ah.moveTo(tip_x - s * 0.18, tip_y - s * 0.15)
        ah.lineTo(tip_x, tip_y)
        ah.lineTo(tip_x - s * 0.18, tip_y + s * 0.15)
        painter.drawPath(ah)

    # 3. Geometry & Transformations
    elif canonical_name == "crop":
        l = pad + s * 0.08
        r = s - pad - s * 0.08
        t = pad + s * 0.08
        b = s - pad - s * 0.08
        painter.drawLine(QPointF(pad, t + s * 0.18), QPointF(r, t + s * 0.18))
        painter.drawLine(QPointF(l + s * 0.18, pad), QPointF(l + s * 0.18, b))
        painter.drawLine(QPointF(l, b - s * 0.18), QPointF(s - pad, b - s * 0.18))
        painter.drawLine(QPointF(r - s * 0.18, t), QPointF(r - s * 0.18, s - pad))

    elif canonical_name == "resize":
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 2, 2)
        painter.drawLine(QPointF(pad + s * 0.15, s - pad - s * 0.15), QPointF(s - pad - s * 0.15, pad + s * 0.15))
        x1, y1 = s - pad - s * 0.15, pad + s * 0.15
        painter.drawLine(QPointF(x1 - s * 0.14, y1), QPointF(x1, y1))
        painter.drawLine(QPointF(x1, y1 + s * 0.14), QPointF(x1, y1))

    elif canonical_name == "rotate-left":
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 45 * 16, 270 * 16)
        ax, ay = pad + s * 0.18, pad + s * 0.35
        ah = QPainterPath()
        ah.moveTo(ax - s * 0.12, ay - s * 0.06)
        ah.lineTo(ax, ay + s * 0.12)
        ah.lineTo(ax + s * 0.12, ay)
        painter.drawPath(ah)

    elif canonical_name == "rotate-right":
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 45 * 16, -270 * 16)
        ax, ay = s - pad - s * 0.18, pad + s * 0.35
        ah = QPainterPath()
        ah.moveTo(ax + s * 0.12, ay - s * 0.06)
        ah.lineTo(ax, ay + s * 0.12)
        ah.lineTo(ax - s * 0.12, ay)
        painter.drawPath(ah)

    elif canonical_name == "rotate-180":
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 0, -180 * 16)
        ax, ay = s * 0.5, s - pad - s * 0.05
        ah = QPainterPath()
        ah.moveTo(ax + s * 0.1, ay - s * 0.12)
        ah.lineTo(ax - s * 0.04, ay)
        ah.lineTo(ax + s * 0.1, ay + s * 0.12)
        painter.drawPath(ah)

    elif canonical_name in ("flip-horizontal", "flip-h"):
        cx = s * 0.5
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(cx, pad), QPointF(cx, s - pad))
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        t1 = QPainterPath()
        t1.moveTo(cx - s * 0.06, pad + s * 0.15)
        t1.lineTo(pad + s * 0.05, s * 0.5)
        t1.lineTo(cx - s * 0.06, s - pad - s * 0.15)
        t1.closeSubpath()
        painter.drawPath(t1)
        t2 = QPainterPath()
        t2.moveTo(cx + s * 0.06, pad + s * 0.15)
        t2.lineTo(s - pad - s * 0.05, s * 0.5)
        t2.lineTo(cx + s * 0.06, s - pad - s * 0.15)
        t2.closeSubpath()
        painter.drawPath(t2)

    elif canonical_name in ("flip-vertical", "flip-v"):
        cy = s * 0.5
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(pad, cy), QPointF(s - pad, cy))
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        t1 = QPainterPath()
        t1.moveTo(pad + s * 0.15, cy - s * 0.06)
        t1.lineTo(s * 0.5, pad + s * 0.05)
        t1.lineTo(s - pad - s * 0.15, cy - s * 0.06)
        t1.closeSubpath()
        painter.drawPath(t1)
        t2 = QPainterPath()
        t2.moveTo(pad + s * 0.15, cy + s * 0.06)
        t2.lineTo(s * 0.5, s - pad - s * 0.05)
        t2.lineTo(s - pad - s * 0.15, cy + s * 0.06)
        t2.closeSubpath()
        painter.drawPath(t2)

    # 4. Adjustments & Filters
    elif canonical_name == "adjust":
        y1, y2, y3 = pad + s * 0.15, s * 0.5, s - pad - s * 0.15
        painter.drawLine(QPointF(pad, y1), QPointF(s - pad, y1))
        painter.drawLine(QPointF(pad, y2), QPointF(s - pad, y2))
        painter.drawLine(QPointF(pad, y3), QPointF(s - pad, y3))
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(pad + s * 0.22, y1), s * 0.08, s * 0.08)
        painter.drawEllipse(QPointF(s - pad - s * 0.22, y2), s * 0.08, s * 0.08)
        painter.drawEllipse(QPointF(pad + s * 0.4, y3), s * 0.08, s * 0.08)

    elif canonical_name == "filter":
        painter.drawLine(QPointF(pad + s * 0.1, s - pad - s * 0.1), QPointF(s * 0.55, s * 0.45))
        for cx, cy, rad in [(s * 0.65, pad + s * 0.18, s * 0.12), (s - pad - s * 0.08, s * 0.4, s * 0.08)]:
            painter.drawLine(QPointF(cx - rad, cy), QPointF(cx + rad, cy))
            painter.drawLine(QPointF(cx, cy - rad), QPointF(cx, cy + rad))

    elif canonical_name == "compare":
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 3, 3)
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.5, s - pad))
        painter.drawLine(QPointF(pad, pad + s * 0.3), QPointF(pad + s * 0.3, pad))
        painter.drawLine(QPointF(pad, pad + s * 0.55), QPointF(s * 0.5, pad + s * 0.05))

    # 5. Zoom & View Controls
    elif canonical_name == "zoom-in":
        r = s * 0.26
        cx, cy = pad + r + s * 0.04, pad + r + s * 0.04
        painter.drawEllipse(QPointF(cx, cy), r, r)
        hx, hy = cx + r * 0.707, cy + r * 0.707
        painter.drawLine(QPointF(hx, hy), QPointF(s - pad, s - pad))
        painter.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))
        painter.drawLine(QPointF(cx, cy - r * 0.5), QPointF(cx, cy + r * 0.5))

    elif canonical_name == "zoom-out":
        r = s * 0.26
        cx, cy = pad + r + s * 0.04, pad + r + s * 0.04
        painter.drawEllipse(QPointF(cx, cy), r, r)
        hx, hy = cx + r * 0.707, cy + r * 0.707
        painter.drawLine(QPointF(hx, hy), QPointF(s - pad, s - pad))
        painter.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))

    elif canonical_name == "zoom-fit":
        d = s * 0.22
        painter.drawLine(QPointF(pad, pad + d), QPointF(pad, pad))
        painter.drawLine(QPointF(pad, pad), QPointF(pad + d, pad))
        painter.drawLine(QPointF(s - pad - d, pad), QPointF(s - pad, pad))
        painter.drawLine(QPointF(s - pad, pad), QPointF(s - pad, pad + d))
        painter.drawLine(QPointF(pad, s - pad - d), QPointF(pad, s - pad))
        painter.drawLine(QPointF(pad, s - pad), QPointF(pad + d, s - pad))
        painter.drawLine(QPointF(s - pad - d, s - pad), QPointF(s - pad, s - pad))
        painter.drawLine(QPointF(s - pad, s - pad), QPointF(s - pad, s - pad - d))

    elif canonical_name == "zoom-actual":
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 2, 2)
        font = painter.font()
        font.setPixelSize(max(8, int(s * 0.30)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(pen)
        painter.drawText(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), Qt.AlignCenter, "1:1")

    # 6. Interactive Tools
    elif canonical_name == "brush":
        tip = QPainterPath()
        tip.moveTo(pad, s - pad)
        tip.lineTo(pad + s * 0.2, s - pad - s * 0.1)
        tip.lineTo(pad + s * 0.1, s - pad - s * 0.2)
        tip.closeSubpath()
        painter.drawPath(tip)
        painter.drawLine(QPointF(pad + s * 0.15, s - pad - s * 0.15), QPointF(s - pad, pad))

    elif canonical_name == "eyedropper":
        path = QPainterPath()
        path.moveTo(pad, s - pad)
        path.lineTo(pad + s * 0.15, s - pad - s * 0.05)
        path.lineTo(s - pad - s * 0.15, pad + s * 0.25)
        path.lineTo(s - pad - s * 0.05, pad + s * 0.15)
        path.lineTo(s - pad, pad + s * 0.1)
        path.lineTo(s - pad - s * 0.1, pad)
        path.lineTo(pad + s * 0.05, s - pad - s * 0.15)
        path.closeSubpath()
        painter.drawPath(path)

    elif canonical_name == "move":
        cx, cy = s * 0.5, s * 0.5
        painter.drawLine(QPointF(pad, cy), QPointF(s - pad, cy))
        painter.drawLine(QPointF(cx, pad), QPointF(cx, s - pad))
        for pt, d in [
            (QPointF(pad, cy), (-1, 0)),
            (QPointF(s - pad, cy), (1, 0)),
            (QPointF(cx, pad), (0, -1)),
            (QPointF(cx, s - pad), (0, 1)),
        ]:
            painter.drawLine(pt, QPointF(pt.x() - d[0] * 3 - d[1] * 3, pt.y() - d[1] * 3 - d[0] * 3))
            painter.drawLine(pt, QPointF(pt.x() - d[0] * 3 + d[1] * 3, pt.y() - d[1] * 3 + d[0] * 3))

    # 7. Layer Management Icons
    elif canonical_name == "layers":
        for offset_y in (0, s * 0.16, s * 0.32):
            path = QPainterPath()
            path.moveTo(s * 0.5, pad + offset_y)
            path.lineTo(s - pad, pad + s * 0.16 + offset_y)
            path.lineTo(s * 0.5, pad + s * 0.32 + offset_y)
            path.lineTo(pad, pad + s * 0.16 + offset_y)
            path.closeSubpath()
            painter.drawPath(path)

    elif canonical_name in ("layer-add", "add_layer"):
        painter.drawRect(QRectF(pad, pad + s * 0.15, s * 0.45, s * 0.45))
        cx, cy = s - pad - s * 0.15, s - pad - s * 0.15
        painter.drawLine(QPointF(cx - s * 0.15, cy), QPointF(cx + s * 0.15, cy))
        painter.drawLine(QPointF(cx, cy - s * 0.15), QPointF(cx, cy + s * 0.15))

    elif canonical_name in ("layer-duplicate", "duplicate_layer"):
        # Two overlapping offset rectangles
        r_w, r_h = s * 0.42, s * 0.42
        # Back rect
        painter.drawRoundedRect(QRectF(s - pad - r_w, pad, r_w, r_h), 2, 2)
        # Front rect
        painter.drawRoundedRect(QRectF(pad, s - pad - r_h, r_w, r_h), 2, 2)

    elif canonical_name in ("layer-delete", "delete_layer"):
        painter.drawLine(QPointF(pad + s * 0.1, pad + s * 0.2), QPointF(s - pad - s * 0.1, pad + s * 0.2))
        painter.drawRect(QRectF(pad + s * 0.2, pad + s * 0.2, s * 0.4, s * 0.45))
        painter.drawLine(QPointF(s * 0.5, pad + s * 0.1), QPointF(s * 0.5, pad + s * 0.2))

    elif canonical_name in ("eye", "layer-visible"):
        path = QPainterPath()
        path.moveTo(pad, s * 0.5)
        path.quadTo(s * 0.5, pad + s * 0.1, s - pad, s * 0.5)
        path.quadTo(s * 0.5, s - pad - s * 0.1, pad, s * 0.5)
        painter.drawPath(path)
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(s * 0.5, s * 0.5), s * 0.12, s * 0.12)

    elif canonical_name in ("eye-off", "layer-hidden"):
        path = QPainterPath()
        path.moveTo(pad, s * 0.5)
        path.quadTo(s * 0.5, pad + s * 0.1, s - pad, s * 0.5)
        path.quadTo(s * 0.5, s - pad - s * 0.1, pad, s * 0.5)
        painter.drawPath(path)
        painter.drawLine(QPointF(pad, s - pad), QPointF(s - pad, pad))

    elif canonical_name in ("layer-up", "move_up"):
        painter.drawLine(QPointF(s * 0.5, s - pad), QPointF(s * 0.5, pad))
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.3, pad + s * 0.25))
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.7, pad + s * 0.25))

    elif canonical_name in ("layer-down", "move_down"):
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.5, s - pad))
        painter.drawLine(QPointF(s * 0.5, s - pad), QPointF(s * 0.3, s - pad - s * 0.25))
        painter.drawLine(QPointF(s * 0.5, s - pad), QPointF(s * 0.7, s - pad - s * 0.25))

    elif canonical_name in ("layer-merge", "merge_down"):
        painter.drawLine(QPointF(pad, pad + s * 0.2), QPointF(s - pad, pad + s * 0.2))
        painter.drawLine(QPointF(pad, s - pad - s * 0.2), QPointF(s - pad, s - pad - s * 0.2))
        painter.drawLine(QPointF(s * 0.5, pad + s * 0.2), QPointF(s * 0.5, s * 0.45))
        painter.drawLine(QPointF(s * 0.5, s - pad - s * 0.2), QPointF(s * 0.5, s * 0.55))

    # 8. Help, Info, Themes, Settings & App Icons
    elif canonical_name == "info":
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.5 - pad
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(cx, cy - r * 0.45), s * 0.05, s * 0.05)
        painter.drawLine(QPointF(cx, cy - r * 0.15), QPointF(cx, cy + r * 0.5))

    elif canonical_name == "theme":
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.5 - pad
        painter.drawEllipse(QPointF(cx, cy), r, r)
        path = QPainterPath()
        path.moveTo(cx, cy - r)
        path.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 90, -180)
        path.closeSubpath()
        painter.fillPath(path, QBrush(QColor(color_hex)))

    elif canonical_name == "shortcuts":
        painter.drawRoundedRect(QRectF(pad, pad + s * 0.15, s - 2 * pad, s * 0.45), 3, 3)
        for kx in (pad + s * 0.15, pad + s * 0.35, pad + s * 0.55):
            painter.drawLine(QPointF(kx, pad + s * 0.28), QPointF(kx + s * 0.08, pad + s * 0.28))
        painter.drawLine(QPointF(pad + s * 0.2, pad + s * 0.45), QPointF(s - pad - s * 0.2, pad + s * 0.45))

    elif canonical_name == "settings":
        cx, cy = s * 0.5, s * 0.5
        r_inner = s * 0.15
        r_outer = s * 0.32
        painter.drawEllipse(QPointF(cx, cy), r_inner, r_inner)
        for i in range(6):
            ang = i * (math.pi / 3)
            x1 = cx + (r_inner + 2) * math.cos(ang)
            y1 = cy + (r_inner + 2) * math.sin(ang)
            x2 = cx + r_outer * math.cos(ang)
            y2 = cy + r_outer * math.sin(ang)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    elif canonical_name == "logo":
        cx, cy = s * 0.5, s * 0.5
        center_r = s * 0.2
        painter.setBrush(QBrush(QColor("#0284c7")))
        pen.setColor(QColor("#38bdf8"))
        pen.setWidthF(2.0)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), center_r, center_r)
        num_rays = 8
        ray_inner = s * 0.28
        ray_outer = s * 0.44
        for i in range(num_rays):
            ang = i * (2 * math.pi / num_rays)
            x1 = cx + ray_inner * math.cos(ang)
            y1 = cy + ray_inner * math.sin(ang)
            x2 = cx + ray_outer * math.cos(ang)
            y2 = cy + ray_outer * math.sin(ang)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    else:
        # Fallback icon for missing/unrecognized icon names
        logger.warning(f"[Parto Icon Warning] Missing icon '{name}' (canonical: '{canonical_name}')")
        box = QRectF(pad, pad, s - 2 * pad, s - 2 * pad)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawRoundedRect(box, 3, 3)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(s * 0.5, s * 0.5), 1.5, 1.5)

    painter.end()
    icon = QIcon(pixmap)
    _ICON_CACHE[cache_key] = icon
    return icon
