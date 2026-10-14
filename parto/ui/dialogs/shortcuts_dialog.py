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
from parto.localization import t


class KeySequenceInputDialog(QDialog):
    """Modal dialog for capturing a new keyboard shortcut sequence."""

    def __init__(self, action_name: str, current_key: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog.shortcuts.edit_title", action=action_name, default=f"Edit Shortcut — {action_name}"))
        self.setModal(True)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl = QLabel(t("dialog.shortcuts.edit_prompt", action=action_name, default=f"Press new key combination for:\n<b>{action_name}</b>"), self)
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
        self.setWindowTitle(t("dialog.shortcuts.title", default="Keyboard Shortcuts — Parto"))
        self.setModal(True)
        self.setMinimumSize(660, 480)
        self.resize(720, 520)

        self._shortcuts_data: List[ShortcutDefinition] = []
        self._init_ui()
        self._populate_table()

        try:
            from parto.localization import get_localization_manager
            self._lm = get_localization_manager()
            if hasattr(self._lm, "locale_changed"):
                self._lm.locale_changed.connect(self.retranslate_ui)
                self.finished.connect(self._on_finished)
        except Exception:
            pass

    def _on_finished(self, *_) -> None:
        try:
            if hasattr(self, "_lm") and hasattr(self._lm, "locale_changed"):
                self._lm.locale_changed.disconnect(self.retranslate_ui)
        except Exception:
            pass

    def _init_categories(self) -> None:
        cat_items = [
            (t("dialog.shortcuts.category_all", default="All Categories"), ""),
            (t("menu.brush", default="Brush").replace("&", ""), "Brush"),
            (t("menu.tools", default="Tools").replace("&", ""), "Tools"),
            (t("menu.file", default="File").replace("&", ""), "File"),
            (t("menu.edit", default="Edit").replace("&", ""), "Edit"),
            (t("menu.view", default="View").replace("&", ""), "View"),
            (t("menu.image", default="Image").replace("&", ""), "Image"),
            (t("menu.layers", default="Layers").replace("&", ""), "Layers"),
            (t("menu.filters", default="Filters").replace("&", ""), "Filters"),
            (t("dialog.shortcuts.category_app", default="App"), "App"),
            (t("menu.help", default="Help").replace("&", ""), "Help"),
        ]
        for label, data in cat_items:
            self.category_combo.addItem(label, data)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Search Bar and Category Row
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(t("dialog.shortcuts.filter_placeholder", default="Filter shortcuts by action, key, or category..."))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._populate_table)
        top_row.addWidget(self.search_input, stretch=3)

        self.category_combo = QComboBox(self)
        self._init_categories()
        self.category_combo.currentIndexChanged.connect(self._populate_table)
        top_row.addWidget(self.category_combo, stretch=2)

        layout.addLayout(top_row)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            t("dialog.shortcuts.header_action", default="Action"),
            t("dialog.shortcuts.header_key", default="Shortcut"),
            t("dialog.shortcuts.header_category", default="Category"),
            t("dialog.shortcuts.header_description", default="Description"),
        ])
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

        self.btn_edit = QPushButton(t("dialog.shortcuts.edit_btn", default="Edit Shortcut..."), self)
        self.btn_edit.setToolTip(t("dialog.shortcuts.edit_tip", default="Customize the selected action's shortcut key combination"))
        self.btn_edit.clicked.connect(self._on_edit_selected)
        btn_layout.addWidget(self.btn_edit)

        self.btn_clear = QPushButton(t("dialog.shortcuts.clear_btn", default="Clear"), self)
        self.btn_clear.setToolTip(t("dialog.shortcuts.clear_tip", default="Remove keyboard shortcut from selected action"))
        self.btn_clear.clicked.connect(self._on_clear_selected)
        btn_layout.addWidget(self.btn_clear)

        self.btn_reset_action = QPushButton(t("dialog.shortcuts.reset_action_btn", default="Reset Action"), self)
        self.btn_reset_action.setToolTip(t("dialog.shortcuts.reset_action_tip", default="Reset selected action to factory default shortcut"))
        self.btn_reset_action.clicked.connect(self._on_reset_selected_action)
        btn_layout.addWidget(self.btn_reset_action)

        self.btn_reset_all = QPushButton(t("dialog.shortcuts.reset_all_btn", default="Reset All to Defaults"), self)
        self.btn_reset_all.setToolTip(t("dialog.shortcuts.reset_all_tip", default="Restore all application shortcuts to default bindings"))
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        btn_layout.addWidget(self.btn_reset_all)

        btn_layout.addStretch()

        self.btn_close = QPushButton(t("dialog.common.close", default="Close"), self)
        self.btn_close.setObjectName("PrimaryAction")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def retranslate_ui(self) -> None:
        """Update shortcuts dialog title, headers, combo, and buttons on language change."""
        from parto.localization import t, get_localization_manager
        lm = get_localization_manager()
        self.setWindowTitle(t("dialog.shortcuts.title", default="Keyboard Shortcuts — Parto"))
        self.setLayoutDirection(Qt.RightToLeft if lm.is_rtl else Qt.LeftToRight)

        if hasattr(self, "search_input"):
            self.search_input.setPlaceholderText(
                t("dialog.shortcuts.filter_placeholder", default="Filter shortcuts by action, key, or category...")
            )

        if hasattr(self, "category_combo"):
            current_data = self.category_combo.currentData()
            self.category_combo.blockSignals(True)
            self.category_combo.clear()
            self._init_categories()
            matched = False
            for idx in range(self.category_combo.count()):
                if self.category_combo.itemData(idx) == current_data:
                    self.category_combo.setCurrentIndex(idx)
                    matched = True
                    break
            if not matched and self.category_combo.count() > 0:
                self.category_combo.setCurrentIndex(0)
            self.category_combo.blockSignals(False)

        if hasattr(self, "table"):
            self.table.setHorizontalHeaderLabels([
                t("dialog.shortcuts.header_action", default="Action"),
                t("dialog.shortcuts.header_key", default="Shortcut"),
                t("dialog.shortcuts.header_category", default="Category"),
                t("dialog.shortcuts.header_description", default="Description"),
            ])

        if hasattr(self, "btn_edit"):
            self.btn_edit.setText(t("dialog.shortcuts.edit_btn", default="Edit Shortcut..."))
            self.btn_edit.setToolTip(t("dialog.shortcuts.edit_tip", default="Customize the selected action's shortcut key combination"))
        if hasattr(self, "btn_clear"):
            self.btn_clear.setText(t("dialog.shortcuts.clear_btn", default="Clear"))
            self.btn_clear.setToolTip(t("dialog.shortcuts.clear_tip", default="Remove keyboard shortcut from selected action"))
        if hasattr(self, "btn_reset_action"):
            self.btn_reset_action.setText(t("dialog.shortcuts.reset_action_btn", default="Reset Action"))
            self.btn_reset_action.setToolTip(t("dialog.shortcuts.reset_action_tip", default="Reset selected action to factory default shortcut"))
        if hasattr(self, "btn_reset_all"):
            self.btn_reset_all.setText(t("dialog.shortcuts.reset_all_btn", default="Reset All to Defaults"))
            self.btn_reset_all.setToolTip(t("dialog.shortcuts.reset_all_tip", default="Restore all application shortcuts to default bindings"))
        if hasattr(self, "btn_close"):
            self.btn_close.setText(t("dialog.common.close", default="Close"))

        self._populate_table()

    def _populate_table(self, *_) -> None:
        self.table.setRowCount(0)
        q = self.search_input.text().lower().strip()
        cat_filter = self.category_combo.currentData()
        if cat_filter is None:
            cat_text = self.category_combo.currentText()
            cat_filter = "" if cat_text in ("All Categories", t("dialog.shortcuts.category_all", default="All Categories")) else cat_text

        sm = get_shortcut_manager()
        all_shortcuts = sm.get_all()
        if not all_shortcuts:
            try:
                from parto.actions.builtins import get_all_builtin_actions
                for act in get_all_builtin_actions():
                    sc = act.shortcut or act.default_shortcut
                    if sc:
                        sm.register(act.id, act.name, act.category, sc, act.description)
                all_shortcuts = sm.get_all()
            except Exception:
                pass

        cat_map = {
            "file": t("menu.file", default="File").replace("&", ""),
            "edit": t("menu.edit", default="Edit").replace("&", ""),
            "view": t("menu.view", default="View").replace("&", ""),
            "image": t("menu.image", default="Image").replace("&", ""),
            "layers": t("menu.layers", default="Layers").replace("&", ""),
            "filters": t("menu.filters", default="Filters").replace("&", ""),
            "tools": t("menu.tools", default="Tools").replace("&", ""),
            "brush": t("menu.brush", default="Brush").replace("&", ""),
            "app": t("dialog.shortcuts.category_app", default="App"),
            "help": t("menu.help", default="Help").replace("&", ""),
        }

        matching = []
        for defn in all_shortcuts:
            if cat_filter and defn.category.lower() != str(cat_filter).lower():
                continue
            cat_display = cat_map.get(defn.category.lower(), defn.category)
            if not q or (
                q in defn.name.lower()
                or q in defn.key_sequence.lower()
                or q in defn.category.lower()
                or q in cat_display.lower()
                or q in defn.description.lower()
            ):
                matching.append(defn)

        self._shortcuts_data = matching
        self.table.setRowCount(len(matching))
        none_label = t("dialog.shortcuts.none", default="(None)")
        for row, defn in enumerate(matching):
            item_name = QTableWidgetItem(defn.name)
            item_name.setData(Qt.UserRole, defn.action_id)
            self.table.setItem(row, 0, item_name)

            item_key = QTableWidgetItem(defn.key_sequence or none_label)
            if not defn.key_sequence:
                item_key.setForeground(Qt.gray)
            self.table.setItem(row, 1, item_key)

            cat_display = cat_map.get(defn.category.lower(), defn.category)
            self.table.setItem(row, 2, QTableWidgetItem(cat_display))
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
                        t("dialog.shortcuts.conflict_title", default="Shortcut Conflict"),
                        t(
                            "dialog.shortcuts.conflict_msg",
                            key=new_key,
                            name=conflict.name,
                            category=conflict.category,
                            default=f"'{new_key}' is already assigned to:\n<b>{conflict.name}</b> ({conflict.category})\n\nReplace existing shortcut?",
                        ),
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
            t("dialog.shortcuts.reset_all_title", default="Reset All Shortcuts"),
            t("dialog.shortcuts.reset_all_msg", default="Are you sure you want to restore all shortcuts to factory defaults?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            sm = get_shortcut_manager()
            sm.reset_to_defaults()
            self._populate_table()
