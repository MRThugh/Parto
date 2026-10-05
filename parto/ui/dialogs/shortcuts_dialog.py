# parto/ui/dialogs/shortcuts_dialog.py
"""
Parto Keyboard Shortcuts & Preferences Dialog
Searchable, editable, conflict-aware shortcut customization and reference manager.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, List
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QWidget,
    QMessageBox,
    QKeySequenceEdit,
    QLabel,
    QDialogButtonBox,
)
from parto.shortcuts.manager import get_shortcut_manager, ShortcutDefinition


class KeySequenceInputDialog(QDialog):
    """Modal dialog for capturing a new keyboard shortcut sequence."""

    def __init__(self, action_name: str, current_key: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Shortcut — {action_name}")
        self.setModal(True)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl = QLabel(f"Press new key combination for:\n<b>{action_name}</b>", self)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.key_edit = QKeySequenceEdit(self)
        if current_key:
            self.key_edit.setKeySequence(QKeySequence(current_key))
        layout.addWidget(self.key_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def key_sequence(self) -> str:
        return self.key_edit.keySequence().toString()


class ShortcutsDialog(QDialog):
    """
    Searchable, editable, conflict-aware reference and customization dialog
    for all application keyboard shortcuts.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts — Parto")
        self.setModal(True)
        self.setMinimumSize(660, 480)
        self.resize(720, 520)

        self._shortcuts_data: List[ShortcutDefinition] = []
        self._init_ui()
        self._populate_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Search Bar and Category Row
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Filter shortcuts by action, key, or category...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._populate_table)
        top_row.addWidget(self.search_input, stretch=3)

        self.category_combo = QComboBox(self)
        self.category_combo.addItem("All Categories")
        self.category_combo.addItem("Brush")
        self.category_combo.addItem("Tools")
        self.category_combo.addItem("File")
        self.category_combo.addItem("Edit")
        self.category_combo.addItem("View")
        self.category_combo.addItem("Image")
        self.category_combo.addItem("Layers")
        self.category_combo.addItem("Filters")
        self.category_combo.addItem("App")
        self.category_combo.currentTextChanged.connect(self._populate_table)
        top_row.addWidget(self.category_combo, stretch=2)

        layout.addLayout(top_row)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Category", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_edit_selected)
        layout.addWidget(self.table)

        # Action Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_edit = QPushButton("Edit Shortcut...", self)
        self.btn_edit.setToolTip("Customize the selected action's shortcut key combination")
        self.btn_edit.clicked.connect(self._on_edit_selected)
        btn_layout.addWidget(self.btn_edit)

        self.btn_clear = QPushButton("Clear", self)
        self.btn_clear.setToolTip("Remove keyboard shortcut from selected action")
        self.btn_clear.clicked.connect(self._on_clear_selected)
        btn_layout.addWidget(self.btn_clear)

        self.btn_reset_action = QPushButton("Reset Action", self)
        self.btn_reset_action.setToolTip("Reset selected action to factory default shortcut")
        self.btn_reset_action.clicked.connect(self._on_reset_selected_action)
        btn_layout.addWidget(self.btn_reset_action)

        self.btn_reset_all = QPushButton("Reset All to Defaults", self)
        self.btn_reset_all.setToolTip("Restore all application shortcuts to default bindings")
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        btn_layout.addWidget(self.btn_reset_all)

        btn_layout.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.setObjectName("PrimaryAction")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _populate_table(self, *_) -> None:
        self.table.setRowCount(0)
        q = self.search_input.text().lower().strip()
        cat_filter = self.category_combo.currentText()
        if cat_filter == "All Categories":
            cat_filter = ""

        sm = get_shortcut_manager()
        all_shortcuts = sm.get_all()

        matching = []
        for defn in all_shortcuts:
            if cat_filter and defn.category.lower() != cat_filter.lower():
                continue
            if not q or (
                q in defn.name.lower()
                or q in defn.key_sequence.lower()
                or q in defn.category.lower()
                or q in defn.description.lower()
            ):
                matching.append(defn)

        self._shortcuts_data = matching
        self.table.setRowCount(len(matching))
        for row, defn in enumerate(matching):
            item_name = QTableWidgetItem(defn.name)
            item_name.setData(Qt.UserRole, defn.action_id)
            self.table.setItem(row, 0, item_name)

            item_key = QTableWidgetItem(defn.key_sequence or "(None)")
            if not defn.key_sequence:
                item_key.setForeground(Qt.gray)
            self.table.setItem(row, 1, item_key)

            self.table.setItem(row, 2, QTableWidgetItem(defn.category))
            self.table.setItem(row, 3, QTableWidgetItem(defn.description))

    def _get_selected_definition(self) -> Optional[ShortcutDefinition]:
        row = self.table.currentRow()
        if 0 <= row < len(self._shortcuts_data):
            return self._shortcuts_data[row]
        return None

    def _on_edit_selected(self) -> None:
        defn = self._get_selected_definition()
        if not defn:
            return

        dlg = KeySequenceInputDialog(defn.name, defn.key_sequence, self)
        if dlg.exec():
            new_key = dlg.key_sequence().strip()
            if new_key == defn.key_sequence:
                return

            sm = get_shortcut_manager()
            # Mandatory Shortcut Conflict Detection
            if new_key:
                conflict = sm.find_conflict_for(defn.action_id, new_key)
                if conflict:
                    ans = QMessageBox.question(
                        self,
                        "Shortcut Conflict",
                        f"'{new_key}' is already assigned to:\n<b>{conflict.name}</b> ({conflict.category})\n\n"
                        f"Replace existing shortcut?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if ans == QMessageBox.Yes:
                        sm.resolve_conflict(new_key, defn.action_id)
                    else:
                        return
                else:
                    sm.remap_shortcut(defn.action_id, new_key)
            else:
                sm.unbind_shortcut(defn.action_id)

            self._populate_table()

    def _on_clear_selected(self) -> None:
        defn = self._get_selected_definition()
        if not defn:
            return
        sm = get_shortcut_manager()
        sm.unbind_shortcut(defn.action_id)
        self._populate_table()

    def _on_reset_selected_action(self) -> None:
        defn = self._get_selected_definition()
        if not defn:
            return
        sm = get_shortcut_manager()
        sm.reset_action_to_default(defn.action_id)
        self._populate_table()

    def _on_reset_all(self) -> None:
        ans = QMessageBox.question(
            self,
            "Reset All Shortcuts",
            "Are you sure you want to restore all shortcuts to factory defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            sm = get_shortcut_manager()
            sm.reset_to_defaults()
            self._populate_table()
