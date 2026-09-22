# parto/ui/dock_animator.py
"""
Parto v0.3.0 - Smooth QDockWidget Animation Helper
Subtle, high-performance slide/expand animation for dockable panels.
Preserves Qt dock area management, tabification, floating windows, and resize handles.
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QObject, QVariantAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget


class DockAnimator(QObject):
    """
    Manages smooth, non-blocking open/close transitions for a QDockWidget.
    Preserves tabification with companion docks, dock resizing, and floating state.
    """

    animation_finished = Signal(bool)  # emits visible state when done

    def __init__(
        self,
        main_window: QMainWindow,
        dock: QDockWidget,
        target_width: int = 280,
        duration_ms: int = 200,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.dock = dock
        self.target_width = target_width
        self.duration_ms = duration_ms
        self.anim: Optional[QVariantAnimation] = None
        self._target_visible: bool = dock.isVisible()

        # Keep target visible in sync if user closes dock through title bar 'X'
        self.dock.visibilityChanged.connect(self._on_dock_visibility_changed)

    def _on_dock_visibility_changed(self, visible: bool) -> None:
        if not self.is_animating():
            self._target_visible = visible

    def is_animating(self) -> bool:
        return self.anim is not None and self.anim.state() == QVariantAnimation.Running

    @property
    def target_visible(self) -> bool:
        return self._target_visible

    def _is_companion_dock_visible_in_area(self) -> bool:
        """Check if any other docked (non-floating) panel in the same dock area is visible."""
        area = self.main_window.dockWidgetArea(self.dock)
        for child in self.main_window.findChildren(QDockWidget):
            if child is not self.dock and not child.isFloating() and child.isVisible():
                if self.main_window.dockWidgetArea(child) == area:
                    return True
        return False

    def toggle(self, animate: bool = True) -> None:
        """Toggle dock open or closed."""
        self.set_visible(not self._target_visible, animate=animate)

    def show_dock(self, animate: bool = True) -> None:
        """Open the dock widget."""
        self.set_visible(True, animate=animate)

    def hide_dock(self, animate: bool = True) -> None:
        """Close the dock widget."""
        self.set_visible(False, animate=animate)

    def set_visible(self, visible: bool, animate: bool = True) -> None:
        """
        Transition dock visibility smoothly without breaking dock area constraints.
        Handles interruption and rapid re-toggling gracefully.
        """
        self._target_visible = visible
        container = self.dock.widget()

        # Floating docks, missing containers, or non-animated requests
        if self.dock.isFloating() or not container or not animate:
            if self.is_animating() and self.anim:
                self.anim.stop()
            self.dock.setVisible(visible)
            if visible:
                self.dock.raise_()
            if container:
                container.setMaximumWidth(16777215)
            self.animation_finished.emit(visible)
            return

        companion_visible = self._is_companion_dock_visible_in_area()

        if visible:
            if companion_visible:
                # Tabbed companion is already expanded: just show and bring tab to front
                if self.is_animating() and self.anim:
                    self.anim.stop()
                container.setMaximumWidth(16777215)
                self.dock.show()
                self.dock.raise_()
                self.animation_finished.emit(True)
                return

            # Expanding dock area
            if self.is_animating() and self.anim:
                self.anim.stop()

            current_w = container.width() if self.dock.isVisible() else 0
            start_w = max(0, current_w)
            end_w = max(self.target_width, container.sizeHint().width())

            self.dock.show()
            self.dock.raise_()
            container.setMaximumWidth(start_w)

            self.anim = QVariantAnimation(self)
            self.anim.setDuration(self.duration_ms)
            self.anim.setEasingCurve(QEasingCurve.OutCubic)
            self.anim.setStartValue(start_w)
            self.anim.setEndValue(end_w)

            def _on_expand_step(val):
                v = int(val)
                container.setMaximumWidth(v)
                self.main_window.resizeDocks([self.dock], [max(1, v)], Qt.Horizontal)

            def _on_expand_done():
                container.setMaximumWidth(16777215)
                self.animation_finished.emit(True)

            self.anim.valueChanged.connect(_on_expand_step)
            self.anim.finished.connect(_on_expand_done)
            self.anim.start()

        else:
            if companion_visible:
                # Companion dock remains visible: hide without collapsing dock area
                if self.is_animating() and self.anim:
                    self.anim.stop()
                container.setMaximumWidth(16777215)
                self.dock.hide()
                self.animation_finished.emit(False)
                return

            # Collapsing dock area
            if self.is_animating() and self.anim:
                self.anim.stop()

            current_w = container.width() if self.dock.isVisible() else self.target_width
            start_w = max(0, current_w)
            end_w = 0

            self.anim = QVariantAnimation(self)
            self.anim.setDuration(max(100, int(self.duration_ms * 0.95)))
            self.anim.setEasingCurve(QEasingCurve.InCubic)
            self.anim.setStartValue(start_w)
            self.anim.setEndValue(end_w)

            def _on_collapse_step(val):
                v = int(val)
                container.setMaximumWidth(v)
                self.main_window.resizeDocks([self.dock], [max(1, v)], Qt.Horizontal)

            def _on_collapse_done():
                container.setMaximumWidth(16777215)
                if not self._target_visible:
                    self.dock.hide()
                self.animation_finished.emit(False)

            self.anim.valueChanged.connect(_on_collapse_step)
            self.anim.finished.connect(_on_collapse_done)
            self.anim.start()
