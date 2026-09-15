# window.py
import os
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer, QPropertyAnimation, QSettings, QSize
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QImage, QPen, QColor, QIcon, QPainter
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsItem,
    QFileDialog, QDialog, QLineEdit, QListWidget, QFormLayout, QSpinBox, QCheckBox,
    QDialogButtonBox, QDockWidget, QSlider, QStyle, QApplication, QToolBar, QMenuBar, QStatusBar,
    QGraphicsOpacityEffect
)
from editor import EditorEngine
from image import pil_to_qpixmap, get_image_info

# Highly specific Dark Stylesheet to prevent text vanishing bugs
DARK_STYLE = """
    QMainWindow, QDialog, QDockWidget { background-color: #1e1e1e; }
    QLabel, QCheckBox, QRadioButton, QGroupBox, QSpinBox { color: #e0e0e0; font-family: 'Inter', 'Segoe UI', sans-serif; }
    QMenuBar { background-color: #252526; color: #e0e0e0; border-bottom: 1px solid #333333; }
    QMenuBar::item { background: transparent; }
    QMenuBar::item:selected { background-color: #37373d; }
    QMenu { background-color: #252526; color: #e0e0e0; border: 1px solid #3e3e42; }
    QMenu::item:selected { background-color: #37373d; }
    QToolBar { background-color: #2d2d30; border-bottom: 1px solid #3e3e42; spacing: 8px; padding: 4px; }
    QToolBar QToolButton { color: #e0e0e0; background: transparent; border: none; padding: 4px; border-radius: 4px; }
    QToolBar QToolButton:hover { background-color: #3e3e42; }
    QStatusBar { background-color: #2d2d30; border-top: 1px solid #3e3e42; color: #aaaaaa; }
    QStatusBar QLabel { color: #aaaaaa; }
    QPushButton { background-color: #3e3e42; color: #f0f0f0; border: 1px solid #555555; border-radius: 4px; padding: 6px 12px; }
    QPushButton:hover { background-color: #4e4e52; }
    QPushButton:pressed { background-color: #2d2d30; }
    QLineEdit { background-color: #2d2d30; border: 1px solid #555555; border-radius: 4px; padding: 6px; color: #ffffff; }
    QListWidget { background-color: #2d2d30; border: 1px solid #555555; border-radius: 4px; color: #ffffff; }
    QListWidget::item:selected { background-color: #007acc; color: #ffffff; }
    QSlider::groove:horizontal { border: 1px solid #555555; height: 4px; background: #3e3e42; border-radius: 2px; }
    QSlider::handle:horizontal { background: #007acc; width: 14px; margin-top: -5px; margin-bottom: -5px; border-radius: 7px; }
"""

# Highly specific Light Stylesheet to keep text readable and highly contrasted
LIGHT_STYLE = """
    QMainWindow, QDialog, QDockWidget { background-color: #f3f3f3; }
    QLabel, QCheckBox, QRadioButton, QGroupBox, QSpinBox { color: #202020; font-family: 'Inter', 'Segoe UI', sans-serif; }
    QMenuBar { background-color: #e0e0e0; color: #202020; border-bottom: 1px solid #cccccc; }
    QMenuBar::item { background: transparent; }
    QMenuBar::item:selected { background-color: #d0d0d0; }
    QMenu { background-color: #ffffff; color: #202020; border: 1px solid #cccccc; }
    QMenu::item:selected { background-color: #f0f0f0; }
    QToolBar { background-color: #f3f3f3; border-bottom: 1px solid #cccccc; spacing: 8px; padding: 4px; }
    QToolBar QToolButton { color: #202020; background: transparent; border: none; padding: 4px; border-radius: 4px; }
    QToolBar QToolButton:hover { background-color: #e0e0e0; }
    QStatusBar { background-color: #e0e0e0; border-top: 1px solid #cccccc; color: #444444; }
    QStatusBar QLabel { color: #444444; }
    QPushButton { background-color: #ffffff; color: #202020; border: 1px solid #cccccc; border-radius: 4px; padding: 6px 12px; }
    QPushButton:hover { background-color: #f0f0f0; }
    QPushButton:pressed { background-color: #e0e0e0; }
    QLineEdit { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 6px; color: #202020; }
    QListWidget { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; color: #202020; }
    QListWidget::item:selected { background-color: #007acc; color: #ffffff; }
    QSlider::groove:horizontal { border: 1px solid #cccccc; height: 4px; background: #e0e0e0; border-radius: 2px; }
    QSlider::handle:horizontal { background: #007acc; width: 14px; margin-top: -5px; margin-bottom: -5px; border-radius: 7px; }
"""

class Toast(QWidget):
    """
    Subtle overlay toast notification at the bottom.
    """
    def __init__(self, parent, message, duration=2500):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.label = QLabel(message, self)
        self.label.setStyleSheet("""
            background-color: rgba(30, 30, 30, 210);
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 13px;
        """)
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.adjustSize()
        
        parent_rect = parent.geometry()
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + parent_rect.height() - self.height() - 60
        self.move(x, y)
        
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
        QTimer.singleShot(duration, self.fade_out)
        
    def fade_out(self):
        self.anim_out = QPropertyAnimation(self, b"windowOpacity")
        self.anim_out.setDuration(150)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(self.deleteLater)
        self.anim_out.start()


class WelcomeScreen(QWidget):
    """
    Default center widget shown when no file is loaded.
    """
    open_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        
        # Load local logo.png if it exists, otherwise fall back to text logo
        logo_label = QLabel(self)
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale logo cleanly
            logo_label.setPixmap(pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("☀️ Parto")
            logo_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #007acc; background: transparent;")
            
        layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        hint = QLabel("Drop image here\n— or —", self)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 15px; color: #888888; line-height: 1.4; background: transparent;")
        layout.addWidget(hint, alignment=Qt.AlignCenter)
        
        self.open_btn = QPushButton("Open Image", self)
        self.open_btn.setStyleSheet("""
            background-color: #007acc; color: white; border: none; 
            border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 14px;
        """)
        self.open_btn.clicked.connect(self.open_requested.emit)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)


class Canvas(QGraphicsView):
    """
    Graphics scene view handling zoom, mouse drag pan, crop, and pixel inspections.
    """
    crop_applied = Signal(tuple)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.crop_mode = False
        self.crop_rect_item = None
        self.crop_start_pos = None
        
        self.setMouseTracking(True)
        
    def set_image(self, qpixmap):
        self.pixmap_item.setPixmap(qpixmap)
        self.scene.setSceneRect(QRectF(qpixmap.rect()))
        self.pixmap_item.setPos(0, 0)
        
    def wheelEvent(self, event):
        if self.pixmap_item.pixmap().isNull():
            return
        
        zoom_in_factor = 1.15
        zoom_out_factor = 0.85
        
        old_scene_pos = self.mapToScene(event.position().toPoint())
        
        if event.angleDelta().y() > 0:
            scale_factor = zoom_in_factor
        else:
            scale_factor = zoom_out_factor
            
        self.scale(scale_factor, scale_factor)
        
        new_scene_pos = self.mapToScene(event.position().toPoint())
        delta = new_scene_pos - old_scene_pos
        self.translate(delta.x(), delta.y())
        
        self.parent_window.update_status_bar()
        
    def set_crop_mode(self, enabled: bool):
        self.crop_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.CrossCursor)
            self.parent_window.status_msg.setText("Crop Mode: Drag selection, then press ENTER to Apply or ESC to Cancel")
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ArrowCursor)
            self.parent_window.status_msg.setText("Ready")
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = None
                
    def mousePressEvent(self, event):
        if self.crop_mode and event.button() == Qt.LeftButton:
            self.crop_start_pos = self.mapToScene(event.pos())
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
            self.crop_rect_item = QGraphicsRectItem()
            self.crop_rect_item.setPen(QPen(QColor("#007acc"), 2, Qt.DashLine))
            self.crop_rect_item.setBrush(QColor(0, 122, 204, 30))
            self.scene.addItem(self.crop_rect_item)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self.crop_mode and self.crop_start_pos and event.buttons() & Qt.LeftButton:
            curr_pos = self.mapToScene(event.pos())
            img_rect = self.pixmap_item.boundingRect()
            rect = QRectF(self.crop_start_pos, curr_pos).normalized()
            rect = rect.intersected(img_rect)
            self.crop_rect_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)
            
        if not self.pixmap_item.pixmap().isNull():
            scene_pos = self.mapToScene(event.pos())
            local_pos = self.pixmap_item.mapFromScene(scene_pos)
            if self.pixmap_item.boundingRect().contains(local_pos):
                x, y = int(local_pos.x()), int(local_pos.y())
                rgb_str = self.parent_window.get_pixel_rgb(x, y)
                self.parent_window.update_hover_info(x, y, rgb_str)
            else:
                self.parent_window.clear_hover_info()
                
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
                    if rect.width() > 1 and rect.height() > 1:
                        box = (int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom()))
                        self.crop_applied.emit(box)
                    self.set_crop_mode(False)
            elif event.key() == Qt.Key_Escape:
                self.set_crop_mode(False)
        else:
            super().keyPressEvent(event)


class CommandPalette(QDialog):
    """
    Floating, borderless search window for running operations swiftly (Ctrl+Shift+P).
    """
    def __init__(self, parent, commands):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.commands = commands
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search commands...")
        self.search_edit.setStyleSheet("font-size: 14px; padding: 8px;")
        layout.addWidget(self.search_edit)
        
        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget)
        
        self.search_edit.textChanged.connect(self.filter_commands)
        self.search_edit.returnPressed.connect(self.trigger_selected)
        self.list_widget.itemActivated.connect(self.trigger_selected)
        
        self.populate_list()
        self.resize(380, 240)
        
        geom = parent.geometry()
        x = geom.x() + (geom.width() - self.width()) // 2
        y = geom.y() + 80
        self.move(x, y)
        
    def populate_list(self):
        self.list_widget.clear()
        for name in self.commands.keys():
            self.list_widget.addItem(name)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
    def filter_commands(self, text):
        self.list_widget.clear()
        for name in self.commands.keys():
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


class ResizeDialog(QDialog):
    """
    Clean window sizing utility.
    """
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image")
        self.setModal(True)
        self.setMinimumWidth(280)
        
        self.aspect_ratio = width / height
        self.updating = False
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.w_spin = QSpinBox(self)
        self.w_spin.setRange(1, 99999)
        self.w_spin.setValue(width)
        
        self.h_spin = QSpinBox(self)
        self.h_spin.setRange(1, 99999)
        self.h_spin.setValue(height)
        
        self.aspect_cb = QCheckBox("Keep aspect ratio", self)
        self.aspect_cb.setChecked(True)
        
        form.addRow("Width:", self.w_spin)
        form.addRow("Height:", self.h_spin)
        form.addRow(self.aspect_cb)
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.w_spin.valueChanged.connect(self.on_w_changed)
        self.h_spin.valueChanged.connect(self.on_h_changed)
        
    def on_w_changed(self, val):
        if self.aspect_cb.isChecked() and not self.updating:
            self.updating = True
            self.h_spin.setValue(int(val / self.aspect_ratio))
            self.updating = False
            
    def on_h_changed(self, val):
        if self.aspect_cb.isChecked() and not self.updating:
            self.updating = True
            self.w_spin.setValue(int(val * self.aspect_ratio))
            self.updating = False
            
    def get_dimensions(self):
        return self.w_spin.value(), self.h_spin.value()


class AdjustmentDock(QDockWidget):
    """
    Non-intrusive side-dock panel for editing brightness, contrast, and saturation.
    """
    preview_changed = Signal(float, float, float)
    applied = Signal(float, float, float)
    cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Color Adjustments", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable)
        
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)
        
        layout.addWidget(QLabel("Brightness"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(50, 200)
        self.bright_slider.setValue(100)
        layout.addWidget(self.bright_slider)
        
        layout.addWidget(QLabel("Contrast"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        layout.addWidget(self.contrast_slider)
        
        layout.addWidget(QLabel("Saturation"))
        self.sat_slider = QSlider(Qt.Horizontal)
        self.sat_slider.setRange(50, 200)
        self.sat_slider.setValue(100)
        layout.addWidget(self.sat_slider)
        
        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setStyleSheet("background-color: #007acc; color: white; font-weight: bold;")
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setWidget(container)
        
        self.bright_slider.valueChanged.connect(self.on_slider_move)
        self.contrast_slider.valueChanged.connect(self.on_slider_move)
        self.sat_slider.valueChanged.connect(self.on_slider_move)
        
        self.reset_btn.clicked.connect(self.reset_values)
        self.apply_btn.clicked.connect(self.apply_values)
        
    def on_slider_move(self):
        b = self.bright_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        s = self.sat_slider.value() / 100.0
        self.preview_changed.emit(b, c, s)
        
    def reset_values(self):
        self.bright_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.sat_slider.blockSignals(True)
        self.bright_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self.sat_slider.setValue(100)
        self.bright_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)
        self.sat_slider.blockSignals(False)
        self.cancelled.emit()
        
    def apply_values(self):
        b = self.bright_slider.value() / 100.0
        c = self.contrast_slider.value() / 100.0
        s = self.sat_slider.value() / 100.0
        self.applied.emit(b, c, s)
        self.close()
        
    def closeEvent(self, event):
        self.cancelled.emit()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    """
    Main app orchestrator implementing the File, Edit, View menus, shortcuts and views.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parto")
        self.setMinimumSize(960, 620)
        self.setAcceptDrops(True)
        
        # Load Application Favicon if available
        self.load_app_icon()
        
        self.engine = EditorEngine()
        self.theme_mode = "dark"
        self.recent_files = []
        self.qimage_cache = None
        
        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()
        self.load_settings()
        
        self.apply_theme(self.theme_mode)
        self.show_welcome_screen()
        
    def load_app_icon(self):
        """
        Detect and load custom favicon icon asset from local folder path.
        """
        for ext in ("png", "ico", "svg"):
            icon_path = os.path.join(os.path.dirname(__file__), f"favicon.{ext}")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break
                
    def init_ui(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        
        self.welcome = WelcomeScreen(self)
        self.welcome.open_requested.connect(self.open_image)
        self.stack.addWidget(self.welcome)
        
        self.canvas = Canvas(self)
        self.canvas.crop_applied.connect(self.apply_crop)
        self.stack.addWidget(self.canvas)
        
        self.dock = AdjustmentDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.close()
        self.dock.preview_changed.connect(self.preview_adjustments)
        self.dock.applied.connect(self.commit_adjustments)
        self.dock.cancelled.connect(self.cancel_adjustments)
        
    def init_menus(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        open_act = QAction("Open Image", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self.open_image)
        file_menu.addAction(open_act)
        
        self.recent_menu = file_menu.addMenu("Recent Files")
        
        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence("Ctrl+S"))
        save_act.triggered.connect(self.save_image)
        file_menu.addAction(save_act)
        
        save_as_act = QAction("Save As...", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_act)
        
        file_menu.addSeparator()
        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        
        # Edit Menu
        edit_menu = menubar.addMenu("Edit")
        
        self.undo_act = QAction("Undo", self)
        self.undo_act.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_act.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_act)
        
        self.redo_act = QAction("Redo", self)
        self.redo_act.setShortcut(QKeySequence("Ctrl+Y"))
        self.redo_act.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_act)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        zo_act = QAction("Zoom Out", self)
        zo_act.setShortcut(QKeySequence("Ctrl+-"))
        zo_act.triggered.connect(self.zoom_out)
        view_menu.addAction(zo_act)
        
        zi_act = QAction("Zoom In", self)
        zi_act.setShortcut(QKeySequence("Ctrl++"))
        zi_act.triggered.connect(self.zoom_in)
        view_menu.addAction(zi_act)
        
        fit_act = QAction("Fit to Screen", self)
        fit_act.setShortcut(QKeySequence("Ctrl+0"))
        fit_act.triggered.connect(self.fit_to_screen)
        view_menu.addAction(fit_act)
        
        act_size = QAction("Actual Size", self)
        act_size.triggered.connect(self.actual_size)
        view_menu.addAction(act_size)
        
        view_menu.addSeparator()
        theme_act = QAction("Toggle Dark/Light Theme", self)
        theme_act.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_act)
        
        # Image Menu
        img_menu = menubar.addMenu("Image")
        
        resize_act = QAction("Resize...", self)
        resize_act.triggered.connect(self.show_resize_dialog)
        img_menu.addAction(resize_act)
        
        rl_act = QAction("Rotate Left", self)
        rl_act.triggered.connect(lambda: self.rotate_image(90))
        img_menu.addAction(rl_act)
        
        rr_act = QAction("Rotate Right", self)
        rr_act.triggered.connect(lambda: self.rotate_image(270))
        img_menu.addAction(rr_act)
        
        fh_act = QAction("Flip Horizontal", self)
        fh_act.triggered.connect(self.flip_horizontal)
        img_menu.addAction(fh_act)
        
        fv_act = QAction("Flip Vertical", self)
        fv_act.triggered.connect(self.flip_vertical)
        img_menu.addAction(fv_act)
        
        crop_act = QAction("Interactive Crop", self)
        crop_act.setShortcut(QKeySequence("Delete"))
        crop_act.triggered.connect(self.toggle_crop_mode)
        img_menu.addAction(crop_act)
        
        # Color Menu
        color_menu = menubar.addMenu("Color")
        adj_act = QAction("Adjust Color Properties", self)
        adj_act.triggered.connect(self.show_adjustments_dock)
        color_menu.addAction(adj_act)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_act)
        
        palette_act = QAction("Command Palette", self)
        palette_act.setShortcut(QKeySequence("Ctrl+Shift+P"))
        palette_act.triggered.connect(self.open_command_palette)
        self.addAction(palette_act)
        
    def init_toolbar(self):
        toolbar = QToolBar("ToolBar", self)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)
        
        style = self.style()
        
        open_btn = toolbar.addAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Open")
        open_btn.triggered.connect(self.open_image)
        
        save_btn = toolbar.addAction(style.standardIcon(QStyle.SP_DialogSaveButton), "Save")
        save_btn.triggered.connect(self.save_image)
        
        toolbar.addSeparator()
        
        self.tb_undo = toolbar.addAction(style.standardIcon(QStyle.SP_ArrowBack), "Undo")
        self.tb_undo.triggered.connect(self.undo)
        
        self.tb_redo = toolbar.addAction(style.standardIcon(QStyle.SP_ArrowForward), "Redo")
        self.tb_redo.triggered.connect(self.redo)
        
        toolbar.addSeparator()
        
        crop_btn = toolbar.addAction("✂ Crop")
        crop_btn.triggered.connect(self.toggle_crop_mode)
        
        rot_l = toolbar.addAction("↶ Rot L")
        rot_l.triggered.connect(lambda: self.rotate_image(90))
        
        rot_r = toolbar.addAction("↷ Rot R")
        rot_r.triggered.connect(lambda: self.rotate_image(270))
        
        flip_h = toolbar.addAction("↔ Flip H")
        flip_h.triggered.connect(self.flip_horizontal)
        
        toolbar.addSeparator()
        
        col_btn = toolbar.addAction("🎨 Adjust Color")
        col_btn.triggered.connect(self.show_adjustments_dock)
        
        zoom_i = toolbar.addAction("🔍+")
        zoom_i.triggered.connect(self.zoom_in)
        
        zoom_o = toolbar.addAction("🔍−")
        zoom_o.triggered.connect(self.zoom_out)
        
        fit_b = toolbar.addAction("Fit")
        fit_b.triggered.connect(self.fit_to_screen)
        
    def init_statusbar(self):
        sb = self.statusBar()
        
        self.status_msg = QLabel("Ready")
        self.status_hover = QLabel("")
        self.status_res = QLabel("")
        self.status_format = QLabel("")
        self.status_size = QLabel("")
        self.status_zoom = QLabel("")
        
        sb.addWidget(self.status_msg, 2)
        sb.addPermanentWidget(self.status_hover, 2)
        sb.addPermanentWidget(self.status_res)
        sb.addPermanentWidget(self.status_format)
        sb.addPermanentWidget(self.status_size)
        sb.addPermanentWidget(self.status_zoom)
        
        self.update_undo_redo_actions()
        
    def update_undo_redo_actions(self):
        has_undo = len(self.engine.undo_stack) > 0
        has_redo = len(self.engine.redo_stack) > 0
        self.undo_act.setEnabled(has_undo)
        self.redo_act.setEnabled(has_redo)
        self.tb_undo.setEnabled(has_undo)
        self.tb_redo.setEnabled(has_redo)
        
    def show_welcome_screen(self):
        self.stack.setCurrentIndex(0)
        self.qimage_cache = None
        self.update_status_bar()
        self.clear_hover_info()
        
    def show_canvas(self):
        self.stack.setCurrentIndex(1)
        
    def open_image(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.heic);;All Files (*)"
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
            self.canvas.set_crop_mode(False)
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Image Loaded Successfully")
        except Exception as e:
            self.show_toast(f"Error loading image: {str(e)}")
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
            if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                pil_conv = pil_img.convert("RGBA")
                data = pil_conv.tobytes("raw", "RGBA")
                self.qimage_cache = QImage(data, pil_conv.width, pil_conv.height, QImage.Format_RGBA8888).copy()
            else:
                pil_conv = pil_img.convert("RGB")
                data = pil_conv.tobytes("raw", "RGB")
                self.qimage_cache = QImage(data, pil_conv.width, pil_conv.height, QImage.Format_RGB888).copy()
                
    def get_pixel_rgb(self, x, y) -> str:
        if self.qimage_cache:
            if 0 <= x < self.qimage_cache.width() and 0 <= y < self.qimage_cache.height():
                col = self.qimage_cache.pixelColor(x, y)
                return f"{col.red()} {col.green()} {col.blue()}"
        return ""
        
    def update_hover_info(self, x, y, rgb):
        self.status_hover.setText(f"X:{x}  Y:{y}  RGB: {rgb}  |")
        
    def clear_hover_info(self):
        self.status_hover.setText("")
        
    def save_image(self):
        if not self.engine.current_image:
            return
        if self.engine.filepath:
            try:
                self.engine.save_image(self.engine.filepath)
                self.cache_qimage_data()
                self.update_status_bar()
                self.show_toast("Image Saved")
            except Exception as e:
                self.show_toast(f"Error saving: {str(e)}")
        else:
            self.save_image_as()
            
    def save_image_as(self):
        if not self.engine.current_image:
            return
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Image As", "",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;WebP Image (*.webp);;All Files (*)"
        )
        if filepath:
            try:
                self.engine.save_image(filepath)
                self.cache_qimage_data()
                self.update_status_bar()
                self.show_toast("Image Saved")
            except Exception as e:
                self.show_toast(f"Error saving: {str(e)}")
                
    def undo(self):
        if self.engine.undo():
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Undo applied")
            
    def redo(self):
        if self.engine.redo():
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            self.show_toast("Redo applied")
            
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
        
    def rotate_image(self, angle):
        if self.engine.current_image:
            self.engine.rotate(angle)
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            
    def flip_horizontal(self):
        if self.engine.current_image:
            self.engine.flip_horizontal()
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            
    def flip_vertical(self):
        if self.engine.current_image:
            self.engine.flip_vertical()
            self.cache_qimage_data()
            self.display_current_image()
            self.update_undo_redo_actions()
            
    def toggle_crop_mode(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        self.canvas.set_crop_mode(not self.canvas.crop_mode)
        
    def apply_crop(self, box):
        try:
            self.engine.crop(box)
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Image cropped")
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
            self.engine.resize(new_w, new_h)
            self.cache_qimage_data()
            self.display_current_image()
            self.fit_to_screen()
            self.update_undo_redo_actions()
            self.show_toast("Image resized")
            
    def show_adjustments_dock(self):
        if not self.engine.current_image:
            self.show_toast("Open an image first")
            return
        self.dock.show()
        self.dock.raise_()
        
    def preview_adjustments(self, b, c, s):
        preview_img = self.engine.get_adjusted_preview(b, c, s)
        if preview_img:
            self.canvas.set_image(pil_to_qpixmap(preview_img))
            
    def commit_adjustments(self, b, c, s):
        self.engine.apply_adjustments(b, c, s)
        self.cache_qimage_data()
        self.display_current_image()
        self.update_undo_redo_actions()
        self.show_toast("Adjustments applied")
        
    def cancel_adjustments(self):
        self.display_current_image()
        
    def show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("About Parto")
        dialog.setFixedSize(300, 180)
        
        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("☀️ Parto", dialog)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #007acc;")
        
        version = QLabel("v0.1.0\nLightweight Native Image Editor\nMIT License", dialog)
        version.setAlignment(Qt.AlignCenter)
        
        # GitHub Link Updated
        github = QLabel("<a href='https://github.com/MRThugh'>GitHub Repository</a>", dialog)
        github.setOpenExternalLinks(True)
        
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        
        layout.addWidget(title, alignment=Qt.AlignCenter)
        layout.addWidget(version, alignment=Qt.AlignCenter)
        layout.addWidget(github, alignment=Qt.AlignCenter)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        dialog.exec()
        
    def toggle_theme(self):
        """
        Transition between Dark and Light mode using a smooth fade-out animation.
        """
        # 1. Capture snapshot of the current window state
        pixmap = self.grab()
        
        # 2. Overlay a temporary QLabel over the MainWindow
        overlay = QLabel(self)
        overlay.setPixmap(pixmap)
        overlay.setGeometry(self.rect())
        overlay.show()
        
        # 3. Change stylesheets underneath the overlay
        if self.theme_mode == "dark":
            self.apply_theme("light")
        else:
            self.apply_theme("dark")
            
        # 4. Fade-out the overlay smoothly
        opacity_effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(opacity_effect)
        
        anim = QPropertyAnimation(opacity_effect, b"opacity", self)
        anim.setDuration(220)  # Fluid 220ms animation length
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        
        def cleanup():
            overlay.deleteLater()
            opacity_effect.deleteLater()
            
        anim.finished.connect(cleanup)
        anim.start()
        
        # Persist animation reference to prevent garbage collection issues
        self._theme_transition_anim = anim
        
    def apply_theme(self, theme):
        self.theme_mode = theme
        if theme == "dark":
            self.setStyleSheet(DARK_STYLE)
            self.canvas.setBackgroundBrush(QColor("#2d2d2d"))
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.canvas.setBackgroundBrush(QColor("#e5e5e5"))
        self.update_status_bar()
        
    def update_status_bar(self):
        if self.engine.current_image:
            w, h = self.engine.current_image.size
            self.status_res.setText(f"  {w}×{h}  |")
            
            info = get_image_info(self.engine.filepath) if self.engine.filepath else {}
            fmt = info.get("format", "MEM")
            size = info.get("size_str", "N/A")
            
            self.status_format.setText(f"  {fmt}  |")
            self.status_size.setText(f"  {size}  |")
            
            zoom_level = int(self.canvas.transform().m11() * 100)
            self.status_zoom.setText(f"  {zoom_level}%  ")
        else:
            self.status_res.setText("")
            self.status_format.setText("")
            self.status_size.setText("")
            self.status_zoom.setText("")
            
    def show_toast(self, msg):
        toast = Toast(self, msg)
        toast.show()
        
    def open_command_palette(self):
        commands = {
            "Open Image": self.open_image,
            "Save": self.save_image,
            "Save As...": self.save_image_as,
            "Undo": self.undo,
            "Redo": self.redo,
            "Zoom In": self.zoom_in,
            "Zoom Out": self.zoom_out,
            "Fit to Screen": self.fit_to_screen,
            "Actual Size": self.actual_size,
            "Resize...": self.show_resize_dialog,
            "Rotate Left": lambda: self.rotate_image(90),
            "Rotate Right": lambda: self.rotate_image(270),
            "Flip Horizontal": self.flip_horizontal,
            "Flip Vertical": self.flip_vertical,
            "Interactive Crop": self.toggle_crop_mode,
            "Adjust Color Properties": self.show_adjustments_dock,
            "Toggle Theme": self.toggle_theme,
            "About Parto": self.show_about_dialog
        }
        palette = CommandPalette(self, commands)
        palette.exec()
        
    def add_to_recent(self, path):
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:5]
        self.update_recent_menu()
        
    def update_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_files:
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
            if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.heic')):
                self.open_image_by_path(path)
                break
                
    def load_settings(self):
        settings = QSettings("Parto", "Main")
        self.theme_mode = settings.value("theme", "dark")
        self.recent_files = settings.value("recent_files", [])
        self.update_recent_menu()
        
    def closeEvent(self, event):
        settings = QSettings("Parto", "Main")
        settings.setValue("theme", self.theme_mode)
        settings.setValue("recent_files", self.recent_files)
        super().closeEvent(event)