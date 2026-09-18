# window.py
"""
Parto - Main Window & UI Components
Author: Ali Kamrani (MRThugh)
Version: 0.2.0
"""

import os
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer, QPropertyAnimation, QSettings, QSize
from PySide6.QtGui import (
    QAction, QKeySequence, QPixmap, QImage, QPen, QColor, QIcon, QPainter,
    QBrush, QClipboard, QGuiApplication
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem,
    QFileDialog, QDialog, QLineEdit, QListWidget, QFormLayout, QSpinBox, QCheckBox,
    QDialogButtonBox, QDockWidget, QSlider, QStyle, QApplication, QToolBar,
    QMessageBox, QComboBox, QGraphicsOpacityEffect, QFrame, QButtonGroup, QRadioButton
)
from editor import EditorEngine
from image import pil_to_qpixmap, get_image_info
from icons import get_parto_icon

# Modern, refined Dark Theme
DARK_STYLE = """
    QMainWindow, QDialog, QDockWidget { 
        background-color: #18181b; 
        color: #f4f4f5; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    QLabel, QCheckBox, QRadioButton, QGroupBox, QSpinBox { 
        color: #f4f4f5; 
    }
    QMenuBar { 
        background-color: #18181b; 
        color: #e4e4e7; 
        border-bottom: 1px solid #27272a; 
        padding: 2px 6px;
    }
    QMenuBar::item { 
        background: transparent; 
        padding: 6px 10px;
        border-radius: 4px;
    }
    QMenuBar::item:selected { 
        background-color: #27272a; 
        color: #ffffff;
    }
    QMenu { 
        background-color: #27272a; 
        color: #f4f4f5; 
        border: 1px solid #3f3f46; 
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected { 
        background-color: #0284c7; 
        color: #ffffff; 
    }
    QMenu::separator {
        height: 1px;
        background-color: #3f3f46;
        margin: 4px 0px;
    }
    QToolBar { 
        background-color: #1e1e24; 
        border-bottom: 1px solid #27272a; 
        spacing: 4px; 
        padding: 4px 8px; 
    }
    QToolBar::separator {
        width: 1px;
        background-color: #3f3f46;
        margin: 4px 6px;
    }
    QToolBar QToolButton { 
        color: #e4e4e7; 
        background: transparent; 
        border: 1px solid transparent; 
        padding: 6px; 
        border-radius: 6px; 
    }
    QToolBar QToolButton:hover { 
        background-color: #27272a; 
        border: 1px solid #3f3f46;
    }
    QToolBar QToolButton:pressed, QToolBar QToolButton:checked { 
        background-color: #0284c7; 
        color: #ffffff;
        border: 1px solid #0369a1;
    }
    QToolBar QToolButton:disabled {
        color: #52525b;
    }
    QStatusBar { 
        background-color: #18181b; 
        border-top: 1px solid #27272a; 
        color: #a1a1aa; 
        font-size: 12px;
        padding: 3px 8px;
    }
    QStatusBar QLabel { 
        color: #a1a1aa; 
    }
    QPushButton { 
        background-color: #27272a; 
        color: #f4f4f5; 
        border: 1px solid #3f3f46; 
        border-radius: 6px; 
        padding: 6px 14px; 
        font-weight: 500;
        font-size: 13px;
    }
    QPushButton:hover { 
        background-color: #3f3f46; 
        border-color: #52525b;
    }
    QPushButton:pressed { 
        background-color: #18181b; 
    }
    QPushButton:disabled {
        background-color: #27272a;
        color: #52525b;
        border-color: #27272a;
    }
    QPushButton.primary {
        background-color: #0284c7;
        color: #ffffff;
        border: 1px solid #0369a1;
        font-weight: 600;
    }
    QPushButton.primary:hover {
        background-color: #0369a1;
        border-color: #0284c7;
    }
    QLineEdit, QSpinBox, QComboBox { 
        background-color: #27272a; 
        border: 1px solid #3f3f46; 
        border-radius: 6px; 
        padding: 6px 10px; 
        color: #ffffff; 
        selection-background-color: #0284c7;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #0284c7;
    }
    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }
    QListWidget { 
        background-color: #27272a; 
        border: 1px solid #3f3f46; 
        border-radius: 6px; 
        color: #ffffff; 
        padding: 4px;
    }
    QListWidget::item {
        padding: 6px 8px;
        border-radius: 4px;
    }
    QListWidget::item:selected { 
        background-color: #0284c7; 
        color: #ffffff; 
    }
    QSlider::groove:horizontal { 
        border: none; 
        height: 4px; 
        background: #3f3f46; 
        border-radius: 2px; 
    }
    QSlider::sub-page:horizontal {
        background: #0284c7;
        border-radius: 2px;
    }
    QSlider::handle:horizontal { 
        background: #ffffff; 
        border: 2px solid #0284c7;
        width: 14px; 
        margin-top: -5px; 
        margin-bottom: -5px; 
        border-radius: 7px; 
    }
    QSlider::handle:horizontal:hover {
        background: #e0f2fe;
    }
    QDockWidget {
        border: 1px solid #27272a;
    }
    QDockWidget::title {
        background-color: #1e1e24;
        padding: 8px;
        font-weight: 600;
        border-bottom: 1px solid #27272a;
    }
"""

# Modern, refined Light Theme
LIGHT_STYLE = """
    QMainWindow, QDialog, QDockWidget { 
        background-color: #f8fafc; 
        color: #0f172a; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    QLabel, QCheckBox, QRadioButton, QGroupBox, QSpinBox { 
        color: #0f172a; 
    }
    QMenuBar { 
        background-color: #f8fafc; 
        color: #334155; 
        border-bottom: 1px solid #e2e8f0; 
        padding: 2px 6px;
    }
    QMenuBar::item { 
        background: transparent; 
        padding: 6px 10px;
        border-radius: 4px;
    }
    QMenuBar::item:selected { 
        background-color: #e2e8f0; 
        color: #0f172a;
    }
    QMenu { 
        background-color: #ffffff; 
        color: #0f172a; 
        border: 1px solid #cbd5e1; 
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }
    QMenu::item:selected { 
        background-color: #0284c7; 
        color: #ffffff; 
    }
    QMenu::separator {
        height: 1px;
        background-color: #e2e8f0;
        margin: 4px 0px;
    }
    QToolBar { 
        background-color: #ffffff; 
        border-bottom: 1px solid #e2e8f0; 
        spacing: 4px; 
        padding: 4px 8px; 
    }
    QToolBar::separator {
        width: 1px;
        background-color: #e2e8f0;
        margin: 4px 6px;
    }
    QToolBar QToolButton { 
        color: #334155; 
        background: transparent; 
        border: 1px solid transparent; 
        padding: 6px; 
        border-radius: 6px; 
    }
    QToolBar QToolButton:hover { 
        background-color: #f1f5f9; 
        border: 1px solid #cbd5e1;
    }
    QToolBar QToolButton:pressed, QToolBar QToolButton:checked { 
        background-color: #0284c7; 
        color: #ffffff;
        border: 1px solid #0369a1;
    }
    QToolBar QToolButton:disabled {
        color: #94a3b8;
    }
    QStatusBar { 
        background-color: #f8fafc; 
        border-top: 1px solid #e2e8f0; 
        color: #64748b; 
        font-size: 12px;
        padding: 3px 8px;
    }
    QStatusBar QLabel { 
        color: #64748b; 
    }
    QPushButton { 
        background-color: #ffffff; 
        color: #0f172a; 
        border: 1px solid #cbd5e1; 
        border-radius: 6px; 
        padding: 6px 14px; 
        font-weight: 500;
        font-size: 13px;
    }
    QPushButton:hover { 
        background-color: #f1f5f9; 
        border-color: #94a3b8;
    }
    QPushButton:pressed { 
        background-color: #e2e8f0; 
    }
    QPushButton:disabled {
        background-color: #f1f5f9;
        color: #94a3b8;
        border-color: #e2e8f0;
    }
    QPushButton.primary {
        background-color: #0284c7;
        color: #ffffff;
        border: 1px solid #0369a1;
        font-weight: 600;
    }
    QPushButton.primary:hover {
        background-color: #0369a1;
        border-color: #0284c7;
    }
    QLineEdit, QSpinBox, QComboBox { 
        background-color: #ffffff; 
        border: 1px solid #cbd5e1; 
        border-radius: 6px; 
        padding: 6px 10px; 
        color: #0f172a; 
        selection-background-color: #0284c7;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border: 1px solid #0284c7;
    }
    QComboBox::drop-down {
        border: none;
        padding-right: 8px;
    }
    QListWidget { 
        background-color: #ffffff; 
        border: 1px solid #cbd5e1; 
        border-radius: 6px; 
        color: #0f172a; 
        padding: 4px;
    }
    QListWidget::item {
        padding: 6px 8px;
        border-radius: 4px;
    }
    QListWidget::item:selected { 
        background-color: #0284c7; 
        color: #ffffff; 
    }
    QSlider::groove:horizontal { 
        border: none; 
        height: 4px; 
        background: #e2e8f0; 
        border-radius: 2px; 
    }
    QSlider::sub-page:horizontal {
        background: #0284c7;
        border-radius: 2px;
    }
    QSlider::handle:horizontal { 
        background: #ffffff; 
        border: 2px solid #0284c7;
        width: 14px; 
        margin-top: -5px; 
        margin-bottom: -5px; 
        border-radius: 7px; 
    }
    QSlider::handle:horizontal:hover {
        background: #e0f2fe;
    }
    QDockWidget {
        border: 1px solid #e2e8f0;
    }
    QDockWidget::title {
        background-color: #ffffff;
        padding: 8px;
        font-weight: 600;
        border-bottom: 1px solid #e2e8f0;
    }
"""


class Toast(QWidget):
    """
    Subtle, non-intrusive floating feedback notification with smooth opacity animation.
    """

    def __init__(self, parent, message: str, duration: int = 2500):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.label = QLabel(message, self)
        self.label.setStyleSheet("""
            background-color: rgba(24, 24, 27, 235);
            color: #f4f4f5;
            border: 1px solid #3f3f46;
            padding: 8px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.adjustSize()

        parent_rect = parent.geometry()
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + parent_rect.height() - self.height() - 50
        self.move(x, y)

        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(160)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        QTimer.singleShot(duration, self.fade_out)

    def fade_out(self):
        self.anim_out = QPropertyAnimation(self, b"windowOpacity")
        self.anim_out.setDuration(160)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(self.deleteLater)
        self.anim_out.start()


class WelcomeScreen(QWidget):
    """
    Modern desktop welcome screen with clear actions, branding, format badges, and drop zone.
    """
    open_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Brand Icon
        icon_label = QLabel(self)
        logo_icon = get_parto_icon("logo", color_hex="#0284c7", size=72)
        icon_label.setPixmap(logo_icon.pixmap(72, 72))
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        # App Title & Persian Name
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title_label = QLabel("Parto", self)
        title_label.setStyleSheet("font-size: 34px; font-weight: 800; letter-spacing: -0.5px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_box.addWidget(title_label)

        persian_subtitle = QLabel("پرتو  •  A Fast, Lightweight Image Editor", self)
        persian_subtitle.setStyleSheet("font-size: 15px; font-weight: 500; color: #0284c7;")
        persian_subtitle.setAlignment(Qt.AlignCenter)
        title_box.addWidget(persian_subtitle)
        layout.addLayout(title_box)

        # Primary Action Button
        self.open_btn = QPushButton("Open Image", self)
        self.open_btn.setProperty("class", "primary")
        self.open_btn.setIcon(get_parto_icon("open", "#ffffff", 20))
        self.open_btn.setIconSize(QSize(20, 20))
        self.open_btn.setStyleSheet("""
            background-color: #0284c7;
            color: #ffffff;
            border: 1px solid #0369a1;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 14px;
        """)
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.setToolTip("Open an image from your computer (Ctrl+O)")
        self.open_btn.clicked.connect(self.open_requested.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)

        # Drag and drop hint
        hint = QLabel("Drag & drop an image anywhere on window\n— or press Ctrl+O —", self)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 13px; color: #888888; line-height: 1.4;")
        layout.addWidget(hint, alignment=Qt.AlignCenter)

        # Format badges row
        badge_frame = QFrame(self)
        badge_layout = QHBoxLayout(badge_frame)
        badge_layout.setSpacing(6)
        badge_layout.setContentsMargins(0, 10, 0, 0)

        formats = ["PNG", "JPG / JPEG", "WEBP", "BMP", "TIFF", "HEIC"]
        for fmt in formats:
            lbl = QLabel(fmt, badge_frame)
            lbl.setStyleSheet("""
                background-color: rgba(2, 132, 199, 0.12);
                color: #0284c7;
                border: 1px solid rgba(2, 132, 199, 0.25);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            """)
            badge_layout.addWidget(lbl)

        layout.addWidget(badge_frame, alignment=Qt.AlignCenter)

        # Version & Credits
        footer = QLabel("Parto v0.2.0 • Created by Ali Kamrani (MRThugh)", self)
        footer.setStyleSheet("font-size: 11px; color: #71717a; margin-top: 16px;")
        layout.addWidget(footer, alignment=Qt.AlignCenter)


class Canvas(QGraphicsView):
    """
    QGraphicsView supporting smooth pan, mouse wheel zoom, pixel coordinate inspection,
    and interactive crop with aspect ratio presets.
    """
    crop_applied = Signal(tuple)
    crop_cancelled = Signal()

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        self.crop_mode = False
        self.crop_aspect_ratio: float | None = None  # None = Free
        self.crop_rect_item: QGraphicsRectItem | None = None
        self.crop_start_pos: QPointF | None = None

        self.setMouseTracking(True)

    def set_image(self, qpixmap: QPixmap):
        self.pixmap_item.setPixmap(qpixmap)
        self.scene.setSceneRect(QRectF(qpixmap.rect()))
        self.pixmap_item.setPos(0, 0)

    def wheelEvent(self, event):
        if self.pixmap_item.pixmap().isNull():
            return

        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor

        if event.angleDelta().y() > 0:
            scale_factor = zoom_in_factor
        else:
            scale_factor = zoom_out_factor

        self.scale(scale_factor, scale_factor)
        if self.main_window and hasattr(self.main_window, "update_status_bar"):
            self.main_window.update_status_bar()

    def set_crop_mode(self, enabled: bool, aspect_ratio: float | None = None):
        self.crop_mode = enabled
        self.crop_aspect_ratio = aspect_ratio
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.CrossCursor)
            if self.main_window and hasattr(self.main_window, "status_msg"):
                self.main_window.status_msg.setText(
                    "Crop Mode: Drag to select crop area, press ENTER to Apply, ESC to Cancel"
                )
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ArrowCursor)
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = None
            if self.main_window and hasattr(self.main_window, "status_msg"):
                self.main_window.status_msg.setText("Ready")

    def mousePressEvent(self, event):
        if self.crop_mode and event.button() == Qt.LeftButton:
            self.crop_start_pos = self.mapToScene(event.pos())
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
            self.crop_rect_item = QGraphicsRectItem()
            self.crop_rect_item.setPen(QPen(QColor("#0284c7"), 2, Qt.DashLine))
            self.crop_rect_item.setBrush(QColor(2, 132, 199, 40))
            self.scene.addItem(self.crop_rect_item)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.crop_mode and self.crop_start_pos and event.buttons() & Qt.LeftButton:
            curr_pos = self.mapToScene(event.pos())
            img_rect = self.pixmap_item.boundingRect()

            dx = curr_pos.x() - self.crop_start_pos.x()
            dy = curr_pos.y() - self.crop_start_pos.y()

            # Apply aspect ratio constraints if requested
            if self.crop_aspect_ratio:
                sign_x = 1 if dx >= 0 else -1
                sign_y = 1 if dy >= 0 else -1
                width = abs(dx)
                height = width / self.crop_aspect_ratio
                curr_pos = QPointF(
                    self.crop_start_pos.x() + sign_x * width,
                    self.crop_start_pos.y() + sign_y * height
                )

            rect = QRectF(self.crop_start_pos, curr_pos).normalized()
            rect = rect.intersected(img_rect)
            if self.crop_rect_item:
                self.crop_rect_item.setRect(rect)
                if self.main_window and hasattr(self.main_window, "status_msg"):
                    w_int = int(rect.width())
                    h_int = int(rect.height())
                    self.main_window.status_msg.setText(
                        f"Crop Selection: {w_int} × {h_int} px  (Press Enter to Apply, Esc to Cancel)"
                    )
        else:
            super().mouseMoveEvent(event)

        # Update pixel RGB inspection
        if not self.pixmap_item.pixmap().isNull() and self.main_window:
            scene_pos = self.mapToScene(event.pos())
            local_pos = self.pixmap_item.mapFromScene(scene_pos)
            if self.pixmap_item.boundingRect().contains(local_pos):
                x, y = int(local_pos.x()), int(local_pos.y())
                rgb_str = self.main_window.get_pixel_rgb(x, y)
                self.main_window.update_hover_info(x, y, rgb_str)
            else:
                self.main_window.clear_hover_info()

    def mouseReleaseEvent(self, event):
        if self.crop_mode and event.button() == Qt.LeftButton:
            self.crop_start_pos = None
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.crop_mode:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.crop_rect_item:
                    rect = self.crop_rect_item.rect()
                    if rect.width() >= 2 and rect.height() >= 2:
                        box = (int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom()))
                        self.crop_applied.emit(box)
                self.set_crop_mode(False)
            elif event.key() == Qt.Key_Escape:
                self.set_crop_mode(False)
                self.crop_cancelled.emit()
        else:
            super().keyPressEvent(event)


class CropBar(QWidget):
    """
    Floating or toolbar-adjacent bar displaying crop aspect ratio controls, Apply, and Cancel buttons.
    """
    aspect_changed = Signal(object)
    apply_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        lbl = QLabel("Crop Aspect Ratio:", self)
        lbl.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(lbl)

        self.ratio_combo = QComboBox(self)
        self.ratio_combo.addItem("Free", None)
        self.ratio_combo.addItem("1:1 (Square)", 1.0)
        self.ratio_combo.addItem("4:3 (Standard)", 4.0 / 3.0)
        self.ratio_combo.addItem("16:9 (Widescreen)", 16.0 / 9.0)
        self.ratio_combo.currentIndexChanged.connect(self.on_ratio_changed)
        layout.addWidget(self.ratio_combo)

        layout.addStretch()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton("Apply Crop", self)
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        self.apply_btn.clicked.connect(self.apply_requested.emit)
        layout.addWidget(self.apply_btn)

        self.setStyleSheet("background-color: rgba(39, 39, 42, 0.95); border-bottom: 1px solid #3f3f46;")

    def on_ratio_changed(self, idx):
        ratio_val = self.ratio_combo.itemData(idx)
        self.aspect_changed.emit(ratio_val)


class ResizeDialog(QDialog):
    """
    Polished image resize utility with aspect ratio lock, percentage presets, and dimension preview.
    """

    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image — Parto")
        self.setModal(True)
        self.setMinimumWidth(320)

        self.orig_w = width
        self.orig_h = height
        self.aspect_ratio = width / height if height > 0 else 1.0
        self.updating = False

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Original dimensions banner
        orig_lbl = QLabel(f"Original Resolution: {width} × {height} px", self)
        orig_lbl.setStyleSheet("font-size: 12px; color: #0284c7; font-weight: 600;")
        layout.addWidget(orig_lbl)

        # Preset Percentage Buttons
        preset_box = QHBoxLayout()
        preset_box.setSpacing(4)
        for pct in (25, 50, 75, 100, 150, 200):
            btn = QPushButton(f"{pct}%", self)
            btn.setStyleSheet("padding: 4px 8px; font-size: 11px;")
            btn.clicked.connect(lambda checked=False, p=pct: self.apply_preset(p))
            preset_box.addWidget(btn)
        layout.addLayout(preset_box)

        form = QFormLayout()
        form.setSpacing(10)

        self.w_spin = QSpinBox(self)
        self.w_spin.setRange(1, 99999)
        self.w_spin.setValue(width)
        self.w_spin.setSuffix(" px")

        self.h_spin = QSpinBox(self)
        self.h_spin.setRange(1, 99999)
        self.h_spin.setValue(height)
        self.h_spin.setSuffix(" px")

        self.aspect_cb = QCheckBox("Preserve aspect ratio", self)
        self.aspect_cb.setChecked(True)

        form.addRow("Width:", self.w_spin)
        form.addRow("Height:", self.h_spin)
        form.addRow("", self.aspect_cb)
        layout.addLayout(form)

        # Resulting Megapixels
        self.mp_label = QLabel(self)
        self.update_mp_label()
        layout.addWidget(self.mp_label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.w_spin.valueChanged.connect(self.on_w_changed)
        self.h_spin.valueChanged.connect(self.on_h_changed)

    def apply_preset(self, pct: int):
        self.updating = True
        new_w = max(1, int(self.orig_w * pct / 100.0))
        new_h = max(1, int(self.orig_h * pct / 100.0))
        self.w_spin.setValue(new_w)
        self.h_spin.setValue(new_h)
        self.updating = False
        self.update_mp_label()

    def on_w_changed(self, val):
        if self.aspect_cb.isChecked() and not self.updating:
            self.updating = True
            new_h = max(1, int(val / self.aspect_ratio))
            self.h_spin.setValue(new_h)
            self.updating = False
        self.update_mp_label()

    def on_h_changed(self, val):
        if self.aspect_cb.isChecked() and not self.updating:
            self.updating = True
            new_w = max(1, int(val * self.aspect_ratio))
            self.w_spin.setValue(new_w)
            self.updating = False
        self.update_mp_label()

    def update_mp_label(self):
        w = self.w_spin.value()
        h = self.h_spin.value()
        mp = (w * h) / 1_000_000.0
        self.mp_label.setText(f"Result: {w} × {h} px ({mp:.2f} Megapixels)")

    def get_dimensions(self) -> tuple[int, int]:
        return self.w_spin.value(), self.h_spin.value()


class AdjustmentDock(QDockWidget):
    """
    Non-intrusive side-dock panel for editing brightness, contrast, and saturation,
    featuring individual resets, percentage badges, and Before/After preview.
    """
    preview_changed = Signal(float, float, float)
    applied = Signal(float, float, float)
    cancelled = Signal()
    before_preview_requested = Signal(bool)  # True = show original, False = show adjusted

    def __init__(self, parent=None):
        super().__init__("Color Adjustments", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(14, 14, 14, 14)

        # Brightness row
        b_header = QHBoxLayout()
        b_lbl = QLabel("Brightness", self)
        b_lbl.setStyleSheet("font-weight: 600;")
        self.b_val = QLabel("100%", self)
        self.b_val.setStyleSheet("color: #0284c7; font-weight: 600;")
        b_reset = QPushButton("↺", self)
        b_reset.setFixedSize(24, 24)
        b_reset.setToolTip("Reset Brightness")
        b_reset.clicked.connect(lambda: self.bright_slider.setValue(100))
        b_header.addWidget(b_lbl)
        b_header.addStretch()
        b_header.addWidget(self.b_val)
        b_header.addWidget(b_reset)
        layout.addLayout(b_header)

        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(20, 200)
        self.bright_slider.setValue(100)
        layout.addWidget(self.bright_slider)

        # Contrast row
        c_header = QHBoxLayout()
        c_lbl = QLabel("Contrast", self)
        c_lbl.setStyleSheet("font-weight: 600;")
        self.c_val = QLabel("100%", self)
        self.c_val.setStyleSheet("color: #0284c7; font-weight: 600;")
        c_reset = QPushButton("↺", self)
        c_reset.setFixedSize(24, 24)
        c_reset.setToolTip("Reset Contrast")
        c_reset.clicked.connect(lambda: self.contrast_slider.setValue(100))
        c_header.addWidget(c_lbl)
        c_header.addStretch()
        c_header.addWidget(self.c_val)
        c_header.addWidget(c_reset)
        layout.addLayout(c_header)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(20, 200)
        self.contrast_slider.setValue(100)
        layout.addWidget(self.contrast_slider)

        # Saturation row
        s_header = QHBoxLayout()
        s_lbl = QLabel("Saturation", self)
        s_lbl.setStyleSheet("font-weight: 600;")
        self.s_val = QLabel("100%", self)
        self.s_val.setStyleSheet("color: #0284c7; font-weight: 600;")
        s_reset = QPushButton("↺", self)
        s_reset.setFixedSize(24, 24)
        s_reset.setToolTip("Reset Saturation")
        s_reset.clicked.connect(lambda: self.sat_slider.setValue(100))
        s_header.addWidget(s_lbl)
        s_header.addStretch()
        s_header.addWidget(self.s_val)
        s_header.addWidget(s_reset)
        layout.addLayout(s_header)

        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setRange(0, 200)
        self.sat_slider.setValue(100)
        layout.addWidget(self.sat_slider)

        # Before / After compare button (press and hold)
        self.compare_btn = QPushButton("Hold to View Original", self)
        self.compare_btn.setIcon(get_parto_icon("compare", "#0284c7", 18))
        self.compare_btn.setToolTip("Press and hold to compare with original image state")
        self.compare_btn.pressed.connect(lambda: self.before_preview_requested.emit(True))
        self.compare_btn.released.connect(lambda: self.before_preview_requested.emit(False))
        layout.addWidget(self.compare_btn)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.reset_all_btn = QPushButton("Reset All")
        self.cancel_btn = QPushButton("Cancel")
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")

        btn_layout.addWidget(self.reset_all_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

        self.setWidget(container)

        self.bright_slider.valueChanged.connect(self.on_slider_move)
        self.contrast_slider.valueChanged.connect(self.on_slider_move)
        self.sat_slider.valueChanged.connect(self.on_slider_move)

        self.reset_all_btn.clicked.connect(self.reset_values)
        self.cancel_btn.clicked.connect(self.cancel_action)
        self.apply_btn.clicked.connect(self.apply_values)

    def on_slider_move(self):
        b = self.bright_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        s = self.sat_slider.value() / 100.0
        self.b_val.setText(f"{self.bright_slider.value()}%")
        self.c_val.setText(f"{self.contrast_slider.value()}%")
        self.s_val.setText(f"{self.sat_slider.value()}%")
        self.preview_changed.emit(b, c, s)

    def reset_values(self):
        self.bright_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.sat_slider.blockSignals(True)
        self.bright_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.sat_slider.setValue(100)
        self.b_val.setText("100%")
        self.c_val.setText("100%")
        self.s_val.setText("100%")
        self.bright_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)
        self.sat_slider.blockSignals(False)
        self.cancelled.emit()

    def cancel_action(self):
        self.reset_values()
        self.close()

    def apply_values(self):
        b = self.bright_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        s = self.sat_slider.value() / 100.0
        self.applied.emit(b, c, s)
        self.close()

    def closeEvent(self, event):
        self.cancelled.emit()
        super().closeEvent(event)


class FilterDialog(QDialog):
    """
    Dedicated filter selection panel supporting Grayscale, Sepia, and Invert
    with real-time preview and Before/After comparison.
    """
    filter_preview_requested = Signal(str)
    before_preview_requested = Signal(bool)
    filter_applied = Signal(str)
    filter_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Photo Filters — Parto")
        self.setModal(True)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        desc = QLabel("Select a filter to apply:", self)
        desc.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(desc)

        self.selected_filter = "grayscale"
        self.button_group = QButtonGroup(self)

        filters = [
            ("grayscale", "Grayscale", "Classic black & white monochrome tone"),
            ("sepia", "Sepia", "Warm vintage photographic amber tone"),
            ("invert", "Invert", "Invert all colors for negative effect"),
        ]

        for code, label, tip in filters:
            radio = QRadioButton(label, self)
            radio.setToolTip(tip)
            if code == "grayscale":
                radio.setChecked(True)
            self.button_group.addButton(radio)
            layout.addWidget(radio)
            radio.toggled.connect(lambda checked, c=code: self.on_filter_toggled(checked, c))

        # Hold to compare button
        self.compare_btn = QPushButton("Hold to View Original", self)
        self.compare_btn.setIcon(get_parto_icon("compare", "#0284c7", 18))
        self.compare_btn.pressed.connect(lambda: self.before_preview_requested.emit(True))
        self.compare_btn.released.connect(lambda: self.before_preview_requested.emit(False))
        layout.addWidget(self.compare_btn)

        # Dialog buttons
        btns = QHBoxLayout()
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        apply_btn = QPushButton("Apply Filter", self)
        apply_btn.setProperty("class", "primary")
        apply_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold;")
        apply_btn.clicked.connect(self.on_apply)

        btns.addWidget(cancel_btn)
        btns.addWidget(apply_btn)
        layout.addLayout(btns)

    def on_filter_toggled(self, checked: bool, code: str):
        if checked:
            self.selected_filter = code
            self.filter_preview_requested.emit(code)

    def on_apply(self):
        self.filter_applied.emit(self.selected_filter)
        self.accept()

    def reject(self):
        self.filter_cancelled.emit()
        super().reject()


class ImageInfoDialog(QDialog):
    """
    Displays verified, accurate technical information about the current image.
    """

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Properties — Parto")
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel(info.get("filename", "Untitled"), self)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0284c7;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)

        def add_row(label, val):
            lbl_val = QLabel(str(val), self)
            lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl_val.setStyleSheet("font-family: monospace; font-size: 13px;")
            form.addRow(f"<b>{label}:</b>", lbl_val)

        add_row("Resolution", info.get("dimensions_str", "N/A"))
        add_row("Aspect Ratio", info.get("aspect_ratio", "N/A"))
        add_row("Megapixels", info.get("megapixels", "N/A"))
        add_row("File Format", info.get("format", "N/A"))
        add_row("Color Mode", info.get("mode", "N/A"))
        add_row("Transparency", "Yes (Alpha channel)" if info.get("has_transparency") else "No")
        add_row("File Size", info.get("size_str", "N/A"))

        layout.addLayout(form)

        # File path section
        path_box = QVBoxLayout()
        path_box.setSpacing(4)
        path_lbl = QLabel("File Location:", self)
        path_lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
        path_box.addWidget(path_lbl)

        path_edit = QLineEdit(info.get("filepath", "In-memory"), self)
        path_edit.setReadOnly(True)
        path_box.addWidget(path_edit)

        copy_btn = QPushButton("Copy Path", self)
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(info.get("filepath", "")))
        path_box.addWidget(copy_btn, alignment=Qt.AlignRight)

        layout.addLayout(path_box)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)


class CommandPalette(QDialog):
    """
    Searchable command runner popup triggered with Ctrl+Shift+P.
    """

    def __init__(self, parent, commands: dict):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.commands = commands

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Type a command to run...")
        self.search_edit.setStyleSheet("font-size: 14px; padding: 8px;")
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)

        self.search_edit.textChanged.connect(self.filter_commands)
        self.search_edit.returnPressed.connect(self.trigger_selected)
        self.list_widget.itemActivated.connect(self.trigger_selected)

        self.populate_list()
        self.resize(380, 260)

        geom = parent.geometry()
        x = geom.x() + (geom.width() - self.width()) // 2
        y = geom.y() + 80
        self.move(x, y)

    def populate_list(self):
        self.list_widget.clear()
        for name in sorted(self.commands.keys()):
            self.list_widget.addItem(name)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def filter_commands(self, text):
        self.list_widget.clear()
        for name in sorted(self.commands.keys()):
            if text.lower() in name.lower():
                self.list_widget.addItem(name)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def trigger_selected(self):
        item = self.list_widget.currentItem()
        if item:
            callback = self.commands.get(item.text())
            if callback:
                self.accept()
                callback()
        else:
            self.reject()


class MainWindow(QMainWindow):
    """
    Main application window orchestrating menus, vector toolbar, canvas view,
    status bar, adjustment panels, filters, shortcuts, and themes.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parto — Lightweight Image Editor")
        self.setMinimumSize(980, 640)
        self.setAcceptDrops(True)

        self.engine = EditorEngine()
        self.theme_mode = "dark"
        self.recent_files: list[str] = []
        self.qimage_cache: QImage | None = None
        self.is_comparing = False

        # Set Window Vector Icon
        self.setWindowIcon(get_parto_icon("logo", "#0284c7", 32))

        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()
        self.load_settings()

        self.apply_theme(self.theme_mode)
        self.show_welcome_screen()

    def init_ui(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Welcome view (page 0)
        self.welcome = WelcomeScreen(self)
        self.welcome.open_requested.connect(self.open_image)
        self.stack.addWidget(self.welcome)

        # Canvas view (page 1)
        canvas_container = QWidget(self)
        c_layout = QVBoxLayout(canvas_container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Crop bar (hidden by default)
        self.crop_bar = CropBar(canvas_container)
        self.crop_bar.hide()
        self.crop_bar.aspect_changed.connect(self.on_crop_aspect_changed)
        self.crop_bar.apply_requested.connect(self.apply_crop_from_bar)
        self.crop_bar.cancel_requested.connect(self.cancel_crop_mode)
        c_layout.addWidget(self.crop_bar)

        self.canvas = Canvas(canvas_container, main_window=self)
        self.canvas.crop_applied.connect(self.apply_crop)
        self.canvas.crop_cancelled.connect(self.cancel_crop_mode)
        c_layout.addWidget(self.canvas)

        self.stack.addWidget(canvas_container)

        # Color Adjustment Dock
        self.dock = AdjustmentDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.close()
        self.dock.preview_changed.connect(self.preview_adjustments)
        self.dock.applied.connect(self.commit_adjustments)
        self.dock.cancelled.connect(self.cancel_adjustments)
        self.dock.before_preview_requested.connect(self.toggle_before_preview)

    def init_menus(self):
        menubar = self.menuBar()
        color_hex = "#f4f4f5" if self.theme_mode == "dark" else "#0f172a"

        # --- File Menu ---
        file_menu = menubar.addMenu("File")

        open_act = QAction(get_parto_icon("open", color_hex), "Open Image...", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self.open_image)
        file_menu.addAction(open_act)

        self.recent_menu = file_menu.addMenu("Recent Files")

        file_menu.addSeparator()

        save_act = QAction(get_parto_icon("save", color_hex), "Save", self)
        save_act.setShortcut(QKeySequence("Ctrl+S"))
        save_act.triggered.connect(self.save_image)
        file_menu.addAction(save_act)

        save_as_act = QAction(get_parto_icon("save-as", color_hex), "Save As...", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        info_act = QAction(get_parto_icon("info", color_hex), "Image Properties...", self)
        info_act.setShortcut(QKeySequence("Ctrl+I"))
        info_act.triggered.connect(self.show_image_info)
        file_menu.addAction(info_act)

        file_menu.addSeparator()

        exit_act = QAction("Exit", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # --- Edit Menu ---
        edit_menu = menubar.addMenu("Edit")

        self.undo_act = QAction(get_parto_icon("undo", color_hex), "Undo", self)
        self.undo_act.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_act.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_act)

        self.redo_act = QAction(get_parto_icon("redo", color_hex), "Redo", self)
        self.redo_act.setShortcut(QKeySequence("Ctrl+Y"))
        self.redo_act.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_act)

        # --- View Menu ---
        view_menu = menubar.addMenu("View")

        zi_act = QAction(get_parto_icon("zoom-in", color_hex), "Zoom In", self)
        zi_act.setShortcut(QKeySequence("Ctrl++"))
        zi_act.triggered.connect(self.zoom_in)
        view_menu.addAction(zi_act)

        zo_act = QAction(get_parto_icon("zoom-out", color_hex), "Zoom Out", self)
        zo_act.setShortcut(QKeySequence("Ctrl+-"))
        zo_act.triggered.connect(self.zoom_out)
        view_menu.addAction(zo_act)

        fit_act = QAction(get_parto_icon("zoom-fit", color_hex), "Fit to Window", self)
        fit_act.setShortcut(QKeySequence("Ctrl+0"))
        fit_act.triggered.connect(self.fit_to_screen)
        view_menu.addAction(fit_act)

        act_size = QAction(get_parto_icon("zoom-actual", color_hex), "Actual Size (100%)", self)
        act_size.setShortcut(QKeySequence("Ctrl+1"))
        act_size.triggered.connect(self.actual_size)
        view_menu.addAction(act_size)

        view_menu.addSeparator()

        self.compare_act = QAction(get_parto_icon("compare", color_hex), "Toggle Before / After", self)
        self.compare_act.setCheckable(True)
        self.compare_act.triggered.connect(self.toggle_compare_mode)
        view_menu.addAction(self.compare_act)

        view_menu.addSeparator()

        theme_act = QAction(get_parto_icon("theme", color_hex), "Toggle Dark / Light Theme", self)
        theme_act.setShortcut(QKeySequence("Ctrl+T"))
        theme_act.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_act)

        # --- Image Menu ---
        img_menu = menubar.addMenu("Image")

        crop_act = QAction(get_parto_icon("crop", color_hex), "Crop...", self)
        crop_act.setShortcut(QKeySequence("Ctrl+K"))
        crop_act.triggered.connect(self.toggle_crop_mode)
        img_menu.addAction(crop_act)

        resize_act = QAction(get_parto_icon("resize", color_hex), "Resize...", self)
        resize_act.setShortcut(QKeySequence("Ctrl+R"))
        resize_act.triggered.connect(self.show_resize_dialog)
        img_menu.addAction(resize_act)

        img_menu.addSeparator()

        rl_act = QAction(get_parto_icon("rotate-left", color_hex), "Rotate Left (90°)", self)
        rl_act.setShortcut(QKeySequence("Ctrl+Shift+L"))
        rl_act.triggered.connect(self.rotate_left)
        img_menu.addAction(rl_act)

        rr_act = QAction(get_parto_icon("rotate-right", color_hex), "Rotate Right (90°)", self)
        rr_act.setShortcut(QKeySequence("Ctrl+Shift+R"))
        rr_act.triggered.connect(self.rotate_right)
        img_menu.addAction(rr_act)

        r180_act = QAction(get_parto_icon("rotate-180", color_hex), "Rotate 180°", self)
        r180_act.triggered.connect(self.rotate_180)
        img_menu.addAction(r180_act)

        img_menu.addSeparator()

        fh_act = QAction(get_parto_icon("flip-h", color_hex), "Flip Horizontal", self)
        fh_act.triggered.connect(self.flip_horizontal)
        img_menu.addAction(fh_act)

        fv_act = QAction(get_parto_icon("flip-v", color_hex), "Flip Vertical", self)
        fv_act.triggered.connect(self.flip_vertical)
        img_menu.addAction(fv_act)

        # --- Filters Menu ---
        filter_menu = menubar.addMenu("Filters")

        adj_act = QAction(get_parto_icon("adjust", color_hex), "Color Adjustments...", self)
        adj_act.triggered.connect(self.show_adjustments_dock)
        filter_menu.addAction(adj_act)

        filter_menu.addSeparator()

        gray_act = QAction("Apply Grayscale", self)
        gray_act.triggered.connect(lambda: self.apply_direct_filter("grayscale"))
        filter_menu.addAction(gray_act)

        sepia_act = QAction("Apply Sepia", self)
        sepia_act.triggered.connect(lambda: self.apply_direct_filter("sepia"))
        filter_menu.addAction(sepia_act)

        inv_act = QAction("Apply Invert", self)
        inv_act.triggered.connect(lambda: self.apply_direct_filter("invert"))
        filter_menu.addAction(inv_act)

        filter_menu.addSeparator()

        filter_dialog_act = QAction(get_parto_icon("filter", color_hex), "Filter Gallery...", self)
        filter_dialog_act.triggered.connect(self.show_filter_dialog)
        filter_menu.addAction(filter_dialog_act)

        # --- Help Menu ---
        help_menu = menubar.addMenu("Help")

        palette_act = QAction("Command Palette...", self)
        palette_act.setShortcut(QKeySequence("Ctrl+Shift+P"))
        palette_act.triggered.connect(self.open_command_palette)
        help_menu.addAction(palette_act)
        self.addAction(palette_act)

        help_menu.addSeparator()

        about_act = QAction("About Parto...", self)
        about_act.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_act)

    def init_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar", self)
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        color_hex = "#f4f4f5" if self.theme_mode == "dark" else "#0f172a"

        # 1. File Actions
        self.tb_open = self.toolbar.addAction(get_parto_icon("open", color_hex), "Open")
        self.tb_open.setToolTip("Open Image (Ctrl+O)")
        self.tb_open.triggered.connect(self.open_image)

        self.tb_save = self.toolbar.addAction(get_parto_icon("save", color_hex), "Save")
        self.tb_save.setToolTip("Save Image (Ctrl+S)")
        self.tb_save.triggered.connect(self.save_image)

        self.tb_save_as = self.toolbar.addAction(get_parto_icon("save-as", color_hex), "Save As")
        self.tb_save_as.setToolTip("Save Image As (Ctrl+Shift+S)")
        self.tb_save_as.triggered.connect(self.save_image_as)

        self.toolbar.addSeparator()

        # 2. History Actions
        self.tb_undo = self.toolbar.addAction(get_parto_icon("undo", color_hex), "Undo")
        self.tb_undo.setToolTip("Undo Last Action (Ctrl+Z)")
        self.tb_undo.triggered.connect(self.undo)

        self.tb_redo = self.toolbar.addAction(get_parto_icon("redo", color_hex), "Redo")
        self.tb_redo.setToolTip("Redo (Ctrl+Y)")
        self.tb_redo.triggered.connect(self.redo)

        self.toolbar.addSeparator()

        # 3. Geometry Tools
        self.tb_crop = self.toolbar.addAction(get_parto_icon("crop", color_hex), "Crop")
        self.tb_crop.setToolTip("Crop Image (Ctrl+K)")
        self.tb_crop.setCheckable(True)
        self.tb_crop.triggered.connect(self.toggle_crop_mode)

        self.tb_resize = self.toolbar.addAction(get_parto_icon("resize", color_hex), "Resize")
        self.tb_resize.setToolTip("Resize Dimensions (Ctrl+R)")
        self.tb_resize.triggered.connect(self.show_resize_dialog)

        self.toolbar.addSeparator()

        # 4. Rotation & Flip Tools
        self.tb_rot_l = self.toolbar.addAction(get_parto_icon("rotate-left", color_hex), "Rotate Left")
        self.tb_rot_l.setToolTip("Rotate 90° Left (Ctrl+Shift+L)")
        self.tb_rot_l.triggered.connect(self.rotate_left)

        self.tb_rot_r = self.toolbar.addAction(get_parto_icon("rotate-right", color_hex), "Rotate Right")
        self.tb_rot_r.setToolTip("Rotate 90° Right (Ctrl+Shift+R)")
        self.tb_rot_r.triggered.connect(self.rotate_right)

        self.tb_flip_h = self.toolbar.addAction(get_parto_icon("flip-h", color_hex), "Flip H")
        self.tb_flip_h.setToolTip("Flip Horizontally")
        self.tb_flip_h.triggered.connect(self.flip_horizontal)

        self.tb_flip_v = self.toolbar.addAction(get_parto_icon("flip-v", color_hex), "Flip V")
        self.tb_flip_v.setToolTip("Flip Vertically")
        self.tb_flip_v.triggered.connect(self.flip_vertical)

        self.toolbar.addSeparator()

        # 5. Color & Filters
        self.tb_adj = self.toolbar.addAction(get_parto_icon("adjust", color_hex), "Adjust")
        self.tb_adj.setToolTip("Color Adjustments (Brightness, Contrast, Saturation)")
        self.tb_adj.triggered.connect(self.show_adjustments_dock)

        self.tb_filter = self.toolbar.addAction(get_parto_icon("filter", color_hex), "Filters")
        self.tb_filter.setToolTip("Photo Filters (Grayscale, Sepia, Invert)")
        self.tb_filter.triggered.connect(self.show_filter_dialog)

        self.toolbar.addSeparator()

        # 6. Before / After Compare Button
        self.tb_compare = self.toolbar.addAction(get_parto_icon("compare", color_hex), "Compare")
        self.tb_compare.setToolTip("Toggle Before / After (Compare with Original Image)")
        self.tb_compare.setCheckable(True)
        self.tb_compare.triggered.connect(self.toggle_compare_mode)

        self.toolbar.addSeparator()

        # 7. Zoom & View Controls
        self.tb_zoom_in = self.toolbar.addAction(get_parto_icon("zoom-in", color_hex), "Zoom In")
        self.tb_zoom_in.setToolTip("Zoom In (Ctrl++)")
        self.tb_zoom_in.triggered.connect(self.zoom_in)

        self.tb_zoom_out = self.toolbar.addAction(get_parto_icon("zoom-out", color_hex), "Zoom Out")
        self.tb_zoom_out.setToolTip("Zoom Out (Ctrl+-)")
        self.tb_zoom_out.triggered.connect(self.zoom_out)

        self.tb_fit = self.toolbar.addAction(get_parto_icon("zoom-fit", color_hex), "Fit")
        self.tb_fit.setToolTip("Fit Image to Window (Ctrl+0)")
        self.tb_fit.triggered.connect(self.fit_to_screen)

        self.tb_actual = self.toolbar.addAction(get_parto_icon("zoom-actual", color_hex), "100%")
        self.tb_actual.setToolTip("Actual Size 100% (Ctrl+1)")
        self.tb_actual.triggered.connect(self.actual_size)

        self.toolbar.addSeparator()

        # 8. Info & Theme
        self.tb_info = self.toolbar.addAction(get_parto_icon("info", color_hex), "Info")
        self.tb_info.setToolTip("Image Properties (Ctrl+I)")
        self.tb_info.triggered.connect(self.show_image_info)

        self.tb_theme = self.toolbar.addAction(get_parto_icon("theme", color_hex), "Theme")
        self.tb_theme.setToolTip("Toggle Dark/Light Theme (Ctrl+T)")
        self.tb_theme.triggered.connect(self.toggle_theme)

    def init_statusbar(self):
        sb = self.statusBar()

        self.status_msg = QLabel("Ready")
        self.status_hover = QLabel("")
        self.status_res = QLabel("")
        self.status_aspect = QLabel("")
        self.status_format = QLabel("")
        self.status_size = QLabel("")
        self.status_zoom = QLabel("")

        sb.addWidget(self.status_msg, 2)
        sb.addPermanentWidget(self.status_hover, 2)
        sb.addPermanentWidget(self.status_res)
        sb.addPermanentWidget(self.status_aspect)
        sb.addPermanentWidget(self.status_format)
        sb.addPermanentWidget(self.status_size)
        sb.addPermanentWidget(self.status_zoom)

        self.update_undo_redo_actions()

    def update_undo_redo_actions(self):
        has_undo = self.engine.can_undo
        has_redo = self.engine.can_redo
        self.undo_act.setEnabled(has_undo)
        self.redo_act.setEnabled(has_redo)
        self.tb_undo.setEnabled(has_undo)
        self.tb_redo.setEnabled(has_redo)

    def show_welcome_screen(self):
        self.stack.setCurrentIndex(0)
        self.qimage_cache = None
        self.crop_bar.hide()
        self.update_status_bar()
        self.clear_hover_info()

    def show_canvas(self):
        self.stack.setCurrentIndex(1)

    def open_image(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Image — Parto", "",
            "All Supported Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.heic);;"
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;WebP Images (*.webp);;All Files (*)"
        )
        if filepath:
            self.open_image_by_path(filepath)

    def open_image_by_path(self, filepath: str):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.engine.load_image(filepath)
            self.cache_qimage_data()
            self.display_current_image()
            self.show_canvas()
            self.add_to_recent(filepath)
            self.cancel_crop_mode()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            filename = os.path.basename(filepath)
            self.show_toast(f"Opened {filename}")
            self.status_msg.setText(f"Opened {filename}")
        except Exception as e:
            self.show_toast(f"Could not open image: {str(e)}")
            QMessageBox.critical(self, "Error Opening Image", f"Could not open this image:\n{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    def display_current_image(self):
        if self.engine.current_image:
            qpix = pil_to_qpixmap(self.engine.current_image)
            self.canvas.set_image(qpix)
            self.update_status_bar()

    def cache_qimage_data(self):
        if self.engine.current_image:
            pil_img = self.engine.current_image
            mode = pil_img.mode
            if mode in ("RGBA", "LA") or (mode == "P" and "transparency" in getattr(pil_img, "info", {})):
                pil_conv = pil_img.convert("RGBA")
                data = pil_conv.tobytes("raw", "RGBA")
                self.qimage_cache = QImage(data, pil_conv.width, pil_conv.height, pil_conv.width * 4, QImage.Format_RGBA8888).copy()
            elif mode == "L":
                pil_conv = pil_img.convert("L")
                data = pil_conv.tobytes("raw", "L")
                self.qimage_cache = QImage(data, pil_conv.width, pil_conv.height, pil_conv.width, QImage.Format_Grayscale8).copy()
            else:
                pil_conv = pil_img.convert("RGB")
                data = pil_conv.tobytes("raw", "RGB")
                self.qimage_cache = QImage(data, pil_conv.width, pil_conv.height, pil_conv.width * 3, QImage.Format_RGB888).copy()

    def get_pixel_rgb(self, x: int, y: int) -> str:
        if self.qimage_cache:
            if 0 <= x < self.qimage_cache.width() and 0 <= y < self.qimage_cache.height():
                col = self.qimage_cache.pixelColor(x, y)
                if self.qimage_cache.hasAlphaChannel():
                    return f"R:{col.red()} G:{col.green()} B:{col.blue()} A:{col.alpha()}"
                return f"R:{col.red()} G:{col.green()} B:{col.blue()}"
        return ""

    def update_hover_info(self, x: int, y: int, rgb: str):
        self.status_hover.setText(f"X: {x}  Y: {y}  |  {rgb}  |")

    def clear_hover_info(self):
        self.status_hover.setText("")

    def save_image(self):
        if not self.engine.current_image:
            self.show_toast("No image loaded to save")
            return
        if self.engine.filepath:
            try:
                self.engine.save_image(self.engine.filepath)
                self.cache_qimage_data()
                self.update_status_bar()
                self.show_toast("Image saved successfully")
                self.status_msg.setText("Image saved successfully")
            except Exception as e:
                self.show_toast(f"Error saving: {str(e)}")
                QMessageBox.critical(self, "Save Error", f"Could not save image:\n{str(e)}")
        else:
            self.save_image_as()

    def save_image_as(self):
        if not self.engine.current_image:
            self.show_toast("No image loaded to save")
            return
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image As — Parto", "",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;WebP Image (*.webp);;All Files (*)"
        )
        if filepath:
            try:
                self.engine.save_image(filepath)
                self.cache_qimage_data()
                self.add_to_recent(filepath)
                self.update_status_bar()
                filename = os.path.basename(filepath)
                self.show_toast(f"Saved as {filename}")
                self.status_msg.setText(f"Saved as {filename}")
            except Exception as e:
                self.show_toast(f"Error saving: {str(e)}")
                QMessageBox.critical(self, "Save As Error", f"Could not save image:\n{str(e)}")

    def undo(self):
        if self.engine.undo():
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Undo applied")
            self.status_msg.setText("Undo applied")

    def redo(self):
        if self.engine.redo():
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Redo applied")
            self.status_msg.setText("Redo applied")

    def zoom_in(self):
        self.canvas.scale(1.2, 1.2)
        self.update_status_bar()

    def zoom_out(self):
        self.canvas.scale(0.8, 0.8)
        self.update_status_bar()

    def fit_to_screen(self):
        if not self.canvas.pixmap_item.pixmap().isNull():
            self.canvas.fitInView(self.canvas.pixmap_item, Qt.KeepAspectRatio)
            self.update_status_bar()

    def actual_size(self):
        self.canvas.resetTransform()
        self.update_status_bar()

    def rotate_left(self):
        if self.engine.current_image:
            self.engine.rotate_left()
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Rotated left 90°")

    def rotate_right(self):
        if self.engine.current_image:
            self.engine.rotate_right()
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Rotated right 90°")

    def rotate_180(self):
        if self.engine.current_image:
            self.engine.rotate_180()
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Rotated 180°")

    def flip_horizontal(self):
        if self.engine.current_image:
            self.engine.flip_horizontal()
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Flipped horizontally")

    def flip_vertical(self):
        if self.engine.current_image:
            self.engine.flip_vertical()
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Flipped vertically")

    def toggle_crop_mode(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        is_active = not self.canvas.crop_mode
        self.canvas.set_crop_mode(is_active)
        self.tb_crop.setChecked(is_active)
        if is_active:
            self.crop_bar.show()
        else:
            self.crop_bar.hide()

    def on_crop_aspect_changed(self, aspect_ratio):
        self.canvas.crop_aspect_ratio = aspect_ratio

    def apply_crop_from_bar(self):
        if self.canvas.crop_rect_item:
            rect = self.canvas.crop_rect_item.rect()
            if rect.width() >= 2 and rect.height() >= 2:
                box = (int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom()))
                self.apply_crop(box)
                return
        self.show_toast("No crop selection area defined")

    def cancel_crop_mode(self):
        self.canvas.set_crop_mode(False)
        self.tb_crop.setChecked(False)
        self.crop_bar.hide()

    def apply_crop(self, box: tuple):
        try:
            self.engine.crop(box)
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.cancel_crop_mode()
            self.update_undo_redo_actions()
            self.show_toast("Image cropped successfully")
            self.status_msg.setText("Image cropped successfully")
        except Exception as e:
            self.show_toast(f"Crop failed: {str(e)}")

    def show_resize_dialog(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        w, h = self.engine.current_image.size
        dialog = ResizeDialog(w, h, self)
        if dialog.exec() == QDialog.Accepted:
            new_w, new_h = dialog.get_dimensions()
            try:
                self.engine.resize(new_w, new_h)
                self.cache_qimage_data()
                self.display_current_image()
                self.fit_to_screen()
                self.update_undo_redo_actions()
                self.show_toast(f"Resized to {new_w} × {new_h} px")
                self.status_msg.setText(f"Resized to {new_w} × {new_h} px")
            except Exception as e:
                self.show_toast(f"Resize failed: {str(e)}")

    def show_adjustments_dock(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        self.dock.show()
        self.dock.raise_()

    def preview_adjustments(self, b: float, c: float, s: float):
        preview_img = self.engine.get_adjusted_preview(b, c, s)
        if preview_img:
            self.canvas.set_image(pil_to_qpixmap(preview_img))

    def commit_adjustments(self, b: float, c: float, s: float):
        self.engine.apply_adjustments(b, c, s)
        self.cache_qimage_data()
        self.display_current_image()
        self.update_undo_redo_actions()
        self.show_toast("Color adjustments applied")
        self.status_msg.setText("Color adjustments applied")

    def cancel_adjustments(self):
        self.display_current_image()

    def toggle_before_preview(self, show_original: bool):
        """
        Hold or toggle Before/After preview.
        """
        if not self.engine.current_image:
            return
        if show_original and self.engine.original_image:
            self.canvas.set_image(pil_to_qpixmap(self.engine.original_image))
            self.status_msg.setText("Showing Original (Before)")
        else:
            self.display_current_image()
            self.status_msg.setText("Showing Current")

    def toggle_compare_mode(self, checked: bool):
        self.is_comparing = checked
        self.toggle_before_preview(checked)
        if not checked:
            self.show_toast("Returned to current view")

    def show_filter_dialog(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        dlg = FilterDialog(self)
        dlg.filter_preview_requested.connect(self.preview_filter)
        dlg.before_preview_requested.connect(self.toggle_before_preview)
        dlg.filter_applied.connect(self.commit_filter)
        dlg.filter_cancelled.connect(self.display_current_image)
        # Show initial preview for grayscale
        self.preview_filter("grayscale")
        dlg.exec()

    def preview_filter(self, filter_name: str):
        preview_img = self.engine.get_filter_preview(filter_name)
        if preview_img:
            self.canvas.set_image(pil_to_qpixmap(preview_img))

    def commit_filter(self, filter_name: str):
        self.engine.apply_filter(filter_name)
        self.cache_qimage_data()
        self.display_current_image()
        self.update_undo_redo_actions()
        self.show_toast(f"Applied {filter_name.capitalize()} filter")
        self.status_msg.setText(f"Applied {filter_name.capitalize()} filter")

    def apply_direct_filter(self, filter_name: str):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        self.commit_filter(filter_name)

    def show_image_info(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        info = get_image_info(self.engine.filepath, self.engine.current_image)
        dlg = ImageInfoDialog(info, self)
        dlg.exec()

    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("About Parto")
        dialog.setFixedSize(360, 260)

        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # Vector logo
        icon_label = QLabel(dialog)
        logo = get_parto_icon("logo", "#0284c7", 48)
        icon_label.setPixmap(logo.pixmap(48, 48))
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        title = QLabel("Parto — پرتو", dialog)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0284c7;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        desc = QLabel(
            "<b>Version 0.2.0</b><br>"
            "A fast, lightweight, and modern desktop image editor.<br>"
            "Released under the MIT License.",
            dialog
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 13px; line-height: 1.4;")
        layout.addWidget(desc, alignment=Qt.AlignCenter)

        author = QLabel("Created by <b>Ali Kamrani</b>", dialog)
        author.setAlignment(Qt.AlignCenter)
        layout.addWidget(author, alignment=Qt.AlignCenter)

        links = QLabel(
            "<a href='https://github.com/MRThugh/Parto' style='color:#0284c7;'>GitHub Repository</a> • "
            "<a href='https://github.com/MRThugh' style='color:#0284c7;'>@MRThugh</a>",
            dialog
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignCenter)
        layout.addWidget(links, alignment=Qt.AlignCenter)

        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dialog.exec()

    def toggle_theme(self):
        """
        Transition between Dark and Light mode with a smooth fade-out overlay animation.
        """
        pixmap = self.grab()
        overlay = QLabel(self)
        overlay.setPixmap(pixmap)
        overlay.setGeometry(self.rect())
        overlay.show()

        if self.theme_mode == "dark":
            self.apply_theme("light")
        else:
            self.apply_theme("dark")

        opacity_effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(opacity_effect)

        anim = QPropertyAnimation(opacity_effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)

        def cleanup():
            overlay.deleteLater()
            opacity_effect.deleteLater()

        anim.finished.connect(cleanup)
        anim.start()
        self._theme_anim = anim

    def apply_theme(self, theme: str):
        self.theme_mode = theme
        if theme == "dark":
            self.setStyleSheet(DARK_STYLE)
            self.canvas.setBackgroundBrush(QColor("#1e1e24"))
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.canvas.setBackgroundBrush(QColor("#e2e8f0"))

        # Re-theme toolbar vector icons to match high contrast palette
        color_hex = "#f4f4f5" if theme == "dark" else "#0f172a"
        self.tb_open.setIcon(get_parto_icon("open", color_hex))
        self.tb_save.setIcon(get_parto_icon("save", color_hex))
        self.tb_save_as.setIcon(get_parto_icon("save-as", color_hex))
        self.tb_undo.setIcon(get_parto_icon("undo", color_hex))
        self.tb_redo.setIcon(get_parto_icon("redo", color_hex))
        self.tb_crop.setIcon(get_parto_icon("crop", color_hex))
        self.tb_resize.setIcon(get_parto_icon("resize", color_hex))
        self.tb_rot_l.setIcon(get_parto_icon("rotate-left", color_hex))
        self.tb_rot_r.setIcon(get_parto_icon("rotate-right", color_hex))
        self.tb_flip_h.setIcon(get_parto_icon("flip-h", color_hex))
        self.tb_flip_v.setIcon(get_parto_icon("flip-v", color_hex))
        self.tb_adj.setIcon(get_parto_icon("adjust", color_hex))
        self.tb_filter.setIcon(get_parto_icon("filter", color_hex))
        self.tb_compare.setIcon(get_parto_icon("compare", color_hex))
        self.tb_zoom_in.setIcon(get_parto_icon("zoom-in", color_hex))
        self.tb_zoom_out.setIcon(get_parto_icon("zoom-out", color_hex))
        self.tb_fit.setIcon(get_parto_icon("zoom-fit", color_hex))
        self.tb_actual.setIcon(get_parto_icon("zoom-actual", color_hex))
        self.tb_info.setIcon(get_parto_icon("info", color_hex))
        self.tb_theme.setIcon(get_parto_icon("theme", color_hex))

        self.update_status_bar()

    def update_status_bar(self):
        if self.engine.current_image:
            w, h = self.engine.current_image.size
            self.status_res.setText(f"  {w} × {h} px  |")

            info = get_image_info(self.engine.filepath, self.engine.current_image)
            aspect = info.get("aspect_ratio", "")
            fmt = info.get("format", "RAW")
            mode = info.get("mode", "")
            size = info.get("size_str", "N/A")

            self.status_aspect.setText(f"  {aspect}  |")
            self.status_format.setText(f"  {fmt} ({mode})  |")
            self.status_size.setText(f"  {size}  |")

            zoom_level = int(self.canvas.transform().m11() * 100)
            self.status_zoom.setText(f"  {zoom_level}%  ")
        else:
            self.status_res.setText("")
            self.status_aspect.setText("")
            self.status_format.setText("")
            self.status_size.setText("")
            self.status_zoom.setText("")

    def show_toast(self, msg: str):
        toast = Toast(self, msg)
        toast.show()

    def open_command_palette(self):
        commands = {
            "Open Image": self.open_image,
            "Save": self.save_image,
            "Save As...": self.save_image_as,
            "Undo": self.undo,
            "Redo": self.redo,
            "Crop Tool": self.toggle_crop_mode,
            "Resize Dimensions": self.show_resize_dialog,
            "Rotate Left 90°": self.rotate_left,
            "Rotate Right 90°": self.rotate_right,
            "Rotate 180°": self.rotate_180,
            "Flip Horizontal": self.flip_horizontal,
            "Flip Vertical": self.flip_vertical,
            "Color Adjustments": self.show_adjustments_dock,
            "Filter Gallery": self.show_filter_dialog,
            "Apply Grayscale": lambda: self.apply_direct_filter("grayscale"),
            "Apply Sepia": lambda: self.apply_direct_filter("sepia"),
            "Apply Invert": lambda: self.apply_direct_filter("invert"),
            "Before / After Compare": lambda: self.toggle_compare_mode(not self.is_comparing),
            "Zoom In": self.zoom_in,
            "Zoom Out": self.zoom_out,
            "Fit to Window": self.fit_to_screen,
            "Actual Size 100%": self.actual_size,
            "Image Properties": self.show_image_info,
            "Toggle Dark/Light Theme": self.toggle_theme,
            "About Parto": self.show_about_dialog,
        }
        palette = CommandPalette(self, commands)
        palette.exec()

    def add_to_recent(self, path: str):
        if not isinstance(self.recent_files, list):
            self.recent_files = []
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:6]
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_files or not isinstance(self.recent_files, list):
            no_act = QAction("No Recent Files", self)
            no_act.setEnabled(False)
            self.recent_menu.addAction(no_act)
            return

        for path in self.recent_files:
            name = os.path.basename(path)
            act = QAction(name, self)
            act.triggered.connect(lambda checked=False, p=path: self.open_image_by_path(p))
            self.recent_menu.addAction(act)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and path.lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".heic")
            ):
                self.open_image_by_path(path)
                break

    def load_settings(self):
        settings = QSettings("Parto", "Main")
        theme_val = settings.value("theme", "dark")
        self.theme_mode = theme_val if isinstance(theme_val, str) else "dark"
        rec = settings.value("recent_files", [])
        self.recent_files = rec if isinstance(rec, list) else []
        self.update_recent_menu()

    def closeEvent(self, event):
        settings = QSettings("Parto", "Main")
        settings.setValue("theme", self.theme_mode)
        settings.setValue("recent_files", self.recent_files if isinstance(self.recent_files, list) else [])
        super().closeEvent(event)
