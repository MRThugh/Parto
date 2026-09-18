# icons.py
"""
Parto - Vector Icon System
Crisp, theme-adaptive geometric vector icons generated with QPainter.
Replaces emoji-based UI elements with a cohesive, modern icon set.
Author: Ali Kamrani (MRThugh)
Version: 0.2.0
"""

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QPen, QColor, QBrush


def get_parto_icon(name: str, color_hex: str = "#e0e0e0", size: int = 24) -> QIcon:
    """
    Generate crisp, resolution-independent vector icons for UI toolbars, buttons, and menus.
    """
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

    if name == "open":
        # Folder icon
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

    elif name == "save":
        # Floppy disk icon
        path = QPainterPath()
        path.moveTo(pad, pad)
        path.lineTo(s - pad - s * 0.15, pad)
        path.lineTo(s - pad, pad + s * 0.15)
        path.lineTo(s - pad, s - pad)
        path.lineTo(pad, s - pad)
        path.closeSubpath()
        painter.drawPath(path)
        # Inner rectangle (label)
        painter.drawRect(QRectF(pad + s * 0.15, pad, s * 0.4, s * 0.25))
        # Shutter line
        painter.drawRect(QRectF(pad + s * 0.12, s - pad - s * 0.28, s * 0.46, s * 0.28))

    elif name == "save-as":
        # Save disk with pencil / plus
        path = QPainterPath()
        path.moveTo(pad, pad)
        path.lineTo(s - pad - s * 0.15, pad)
        path.lineTo(s - pad, pad + s * 0.15)
        path.lineTo(s - pad, s - pad - s * 0.2)
        path.moveTo(pad + s * 0.25, s - pad)
        path.lineTo(pad, s - pad)
        path.lineTo(pad, pad)
        painter.drawPath(path)
        # Plus marker at bottom right
        cx, cy = s - pad - s * 0.1, s - pad - s * 0.1
        painter.drawLine(QPointF(cx - s * 0.12, cy), QPointF(cx + s * 0.12, cy))
        painter.drawLine(QPointF(cx, cy - s * 0.12), QPointF(cx, cy + s * 0.12))

    elif name == "undo":
        # Curved undo arrow
        path = QPainterPath()
        path.moveTo(s - pad, s - pad)
        path.quadTo(s - pad, pad + s * 0.1, pad + s * 0.25, pad + s * 0.2)
        painter.drawPath(path)
        # Arrowhead
        tip_x, tip_y = pad + s * 0.15, pad + s * 0.2
        ah = QPainterPath()
        ah.moveTo(tip_x + s * 0.18, tip_y - s * 0.15)
        ah.lineTo(tip_x, tip_y)
        ah.lineTo(tip_x + s * 0.18, tip_y + s * 0.15)
        painter.drawPath(ah)

    elif name == "redo":
        # Curved redo arrow
        path = QPainterPath()
        path.moveTo(pad, s - pad)
        path.quadTo(pad, pad + s * 0.1, s - pad - s * 0.25, pad + s * 0.2)
        painter.drawPath(path)
        # Arrowhead
        tip_x, tip_y = s - pad - s * 0.15, pad + s * 0.2
        ah = QPainterPath()
        ah.moveTo(tip_x - s * 0.18, tip_y - s * 0.15)
        ah.lineTo(tip_x, tip_y)
        ah.lineTo(tip_x - s * 0.18, tip_y + s * 0.15)
        painter.drawPath(ah)

    elif name == "crop":
        # Intersecting crop brackets
        l = pad + s * 0.08
        r = s - pad - s * 0.08
        t = pad + s * 0.08
        b = s - pad - s * 0.08
        # Top-left bracket
        painter.drawLine(QPointF(pad, t + s * 0.18), QPointF(r, t + s * 0.18))
        painter.drawLine(QPointF(l + s * 0.18, pad), QPointF(l + s * 0.18, b))
        # Bottom-right bracket
        painter.drawLine(QPointF(l, b - s * 0.18), QPointF(s - pad, b - s * 0.18))
        painter.drawLine(QPointF(r - s * 0.18, t), QPointF(r - s * 0.18, s - pad))

    elif name == "resize":
        # Diagonal double-ended arrows inside frame
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 2, 2)
        painter.drawLine(QPointF(pad + s * 0.15, s - pad - s * 0.15), QPointF(s - pad - s * 0.15, pad + s * 0.15))
        # Arrowheads
        x1, y1 = s - pad - s * 0.15, pad + s * 0.15
        painter.drawLine(QPointF(x1 - s * 0.14, y1), QPointF(x1, y1))
        painter.drawLine(QPointF(x1, y1 + s * 0.14), QPointF(x1, y1))

    elif name == "rotate-left":
        # 90 deg counter-clockwise arrow around center
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 45 * 16, 270 * 16)
        # Arrowhead
        ax, ay = pad + s * 0.18, pad + s * 0.35
        ah = QPainterPath()
        ah.moveTo(ax - s * 0.12, ay - s * 0.06)
        ah.lineTo(ax, ay + s * 0.12)
        ah.lineTo(ax + s * 0.12, ay)
        painter.drawPath(ah)

    elif name == "rotate-right":
        # 90 deg clockwise arrow
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 45 * 16, -270 * 16)
        # Arrowhead
        ax, ay = s - pad - s * 0.18, pad + s * 0.35
        ah = QPainterPath()
        ah.moveTo(ax + s * 0.12, ay - s * 0.06)
        ah.lineTo(ax, ay + s * 0.12)
        ah.lineTo(ax - s * 0.12, ay)
        painter.drawPath(ah)

    elif name == "rotate-180":
        # 180 deg rotation arrow
        rect = QRectF(pad + s * 0.05, pad + s * 0.05, s - 2 * pad - s * 0.1, s - 2 * pad - s * 0.1)
        painter.drawArc(rect, 0, -180 * 16)
        # Arrowhead at bottom
        ax, ay = s * 0.5, s - pad - s * 0.05
        ah = QPainterPath()
        ah.moveTo(ax + s * 0.1, ay - s * 0.12)
        ah.lineTo(ax - s * 0.04, ay)
        ah.lineTo(ax + s * 0.1, ay + s * 0.12)
        painter.drawPath(ah)

    elif name == "flip-h":
        # Horizontal flip: central dashed line and two opposing triangles
        cx = s * 0.5
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(cx, pad), QPointF(cx, s - pad))
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        # Left triangle
        t1 = QPainterPath()
        t1.moveTo(cx - s * 0.06, pad + s * 0.15)
        t1.lineTo(pad + s * 0.05, s * 0.5)
        t1.lineTo(cx - s * 0.06, s - pad - s * 0.15)
        t1.closeSubpath()
        painter.drawPath(t1)
        # Right triangle
        t2 = QPainterPath()
        t2.moveTo(cx + s * 0.06, pad + s * 0.15)
        t2.lineTo(s - pad - s * 0.05, s * 0.5)
        t2.lineTo(cx + s * 0.06, s - pad - s * 0.15)
        t2.closeSubpath()
        painter.drawPath(t2)

    elif name == "flip-v":
        # Vertical flip: central horizontal line and two opposing triangles
        cy = s * 0.5
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(pad, cy), QPointF(s - pad, cy))
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        # Top triangle
        t1 = QPainterPath()
        t1.moveTo(pad + s * 0.15, cy - s * 0.06)
        t1.lineTo(s * 0.5, pad + s * 0.05)
        t1.lineTo(s - pad - s * 0.15, cy - s * 0.06)
        t1.closeSubpath()
        painter.drawPath(t1)
        # Bottom triangle
        t2 = QPainterPath()
        t2.moveTo(pad + s * 0.15, cy + s * 0.06)
        t2.lineTo(s * 0.5, s - pad - s * 0.05)
        t2.lineTo(s - pad - s * 0.15, cy + s * 0.06)
        t2.closeSubpath()
        painter.drawPath(t2)

    elif name == "adjust":
        # Sliders icon (horizontal tracks with thumb knobs)
        y1, y2, y3 = pad + s * 0.15, s * 0.5, s - pad - s * 0.15
        painter.drawLine(QPointF(pad, y1), QPointF(s - pad, y1))
        painter.drawLine(QPointF(pad, y2), QPointF(s - pad, y2))
        painter.drawLine(QPointF(pad, y3), QPointF(s - pad, y3))
        # Knobs
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(pad + s * 0.22, y1), s * 0.08, s * 0.08)
        painter.drawEllipse(QPointF(s - pad - s * 0.22, y2), s * 0.08, s * 0.08)
        painter.drawEllipse(QPointF(pad + s * 0.4, y3), s * 0.08, s * 0.08)

    elif name == "filter":
        # Magic wand / sparkles filter icon
        # Wand body
        painter.drawLine(QPointF(pad + s * 0.1, s - pad - s * 0.1), QPointF(s * 0.55, s * 0.45))
        # Sparkles
        for cx, cy, rad in [(s * 0.65, pad + s * 0.18, s * 0.12), (s - pad - s * 0.08, s * 0.4, s * 0.08)]:
            painter.drawLine(QPointF(cx - rad, cy), QPointF(cx + rad, cy))
            painter.drawLine(QPointF(cx, cy - rad), QPointF(cx, cy + rad))

    elif name == "compare":
        # Split comparison / Before-After eye/card icon
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 3, 3)
        painter.drawLine(QPointF(s * 0.5, pad), QPointF(s * 0.5, s - pad))
        # Diagonal hatch on left half to denote "before"
        painter.drawLine(QPointF(pad, pad + s * 0.3), QPointF(pad + s * 0.3, pad))
        painter.drawLine(QPointF(pad, pad + s * 0.55), QPointF(s * 0.5, pad + s * 0.05))

    elif name == "zoom-in":
        # Magnifying glass with plus
        r = s * 0.26
        cx, cy = pad + r + s * 0.04, pad + r + s * 0.04
        painter.drawEllipse(QPointF(cx, cy), r, r)
        # Handle
        handle_start_x = cx + r * 0.707
        handle_start_y = cy + r * 0.707
        painter.drawLine(QPointF(handle_start_x, handle_start_y), QPointF(s - pad, s - pad))
        # Plus inside
        painter.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))
        painter.drawLine(QPointF(cx, cy - r * 0.5), QPointF(cx, cy + r * 0.5))

    elif name == "zoom-out":
        # Magnifying glass with minus
        r = s * 0.26
        cx, cy = pad + r + s * 0.04, pad + r + s * 0.04
        painter.drawEllipse(QPointF(cx, cy), r, r)
        handle_start_x = cx + r * 0.707
        handle_start_y = cy + r * 0.707
        painter.drawLine(QPointF(handle_start_x, handle_start_y), QPointF(s - pad, s - pad))
        # Minus inside
        painter.drawLine(QPointF(cx - r * 0.5, cy), QPointF(cx + r * 0.5, cy))

    elif name == "zoom-fit":
        # Fit to screen frame (corners pointing outward)
        d = s * 0.22
        # Top-left
        painter.drawLine(QPointF(pad, pad + d), QPointF(pad, pad))
        painter.drawLine(QPointF(pad, pad), QPointF(pad + d, pad))
        # Top-right
        painter.drawLine(QPointF(s - pad - d, pad), QPointF(s - pad, pad))
        painter.drawLine(QPointF(s - pad, pad), QPointF(s - pad, pad + d))
        # Bottom-left
        painter.drawLine(QPointF(pad, s - pad - d), QPointF(pad, s - pad))
        painter.drawLine(QPointF(pad, s - pad), QPointF(pad + d, s - pad))
        # Bottom-right
        painter.drawLine(QPointF(s - pad - d, s - pad), QPointF(s - pad, s - pad))
        painter.drawLine(QPointF(s - pad, s - pad), QPointF(s - pad, s - pad - d))

    elif name == "zoom-actual":
        # 1:1 Actual size box
        painter.drawRoundedRect(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), 2, 2)
        # "1:1" indicator
        font = painter.font()
        font.setPixelSize(int(s * 0.32))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(pad, pad, s - 2 * pad, s - 2 * pad), Qt.AlignCenter, "1:1")

    elif name == "info":
        # Information circle
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.5 - pad
        painter.drawEllipse(QPointF(cx, cy), r, r)
        # Dot
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawEllipse(QPointF(cx, cy - r * 0.45), s * 0.05, s * 0.05)
        # Stem
        painter.drawLine(QPointF(cx, cy - r * 0.15), QPointF(cx, cy + r * 0.5))

    elif name == "theme":
        # Half-sun, half-moon icon
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.5 - pad
        painter.drawEllipse(QPointF(cx, cy), r, r)
        # Fill right half for dark/light duality
        path = QPainterPath()
        path.moveTo(cx, cy - r)
        path.arcTo(QRectF(cx - r, cy - r, 2 * r, 2 * r), 90, -180)
        path.closeSubpath()
        painter.fillPath(path, QBrush(QColor(color_hex)))

    elif name == "logo":
        # Parto (پرتو - Ray/Beam of Light) geometric sunburst logo
        cx, cy = s * 0.5, s * 0.5
        center_r = s * 0.2
        painter.setBrush(QBrush(QColor("#0284c7")))
        pen.setColor(QColor("#38bdf8"))
        pen.setWidthF(2.0)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), center_r, center_r)
        # Rays
        import math
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

    painter.end()
    return QIcon(pixmap)
